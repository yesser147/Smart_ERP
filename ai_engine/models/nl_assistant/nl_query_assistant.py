import json
import logging
import re
import time
from collections import OrderedDict

import pandas as pd
from sqlalchemy import text

from database import ai_engine  # Restricted read-only engine
from models.recruitment.llm_client import chat

log = logging.getLogger(__name__)

ALLOWED_VIEWS = [
    "v_department_turnover",
    "v_closed_departments",
    "v_department_type_turnover",
    "v_employee_performance_engagement",
    "v_salary_distribution",
    "v_recruitment_funnel_ats",
    "v_training_analytics",
    "v_ai_training_budget_features",
    "v_ai_exit_reason_frequencies",
    "v_ai_retention_features"
]
_ALLOWED_LOWER = {v.lower() for v in ALLOWED_VIEWS}

FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE", "GRANT",
    "REVOKE", "EXEC", "EXECUTE", "COPY", "CALL", "DO", "LISTEN", "NOTIFY", "VACUUM",
    "SET", "RESET", "LOCK", "PREPARE", "DEALLOCATE", "INTO",
]
# System / file / network functions a read query never needs
FORBIDDEN_FUNCTION = re.compile(
    r"\b(pg_\w+|dblink\w*|lo_\w+|set_config|current_setting|query_to_xml\w*|"
    r"table_to_xml\w*|database_to_xml\w*|txid_\w+)\s*\(",
    re.IGNORECASE,
)
# Functions whose syntax contains the word FROM without reading a table
FROM_KEYWORD_FUNCTIONS = re.compile(
    r"\b(EXTRACT|SUBSTRING|TRIM|OVERLAY|POSITION)\s*\([^()]*\)", re.IGNORECASE
)
CLAUSE_END = r"(?=\bWHERE\b|\bGROUP\b|\bORDER\b|\bLIMIT\b|\bHAVING\b|\bUNION\b|\bEXCEPT\b|" \
             r"\bINTERSECT\b|\bWINDOW\b|\bOFFSET\b|\bFETCH\b|\bJOIN\b|\bON\b|\bLEFT\b|\bRIGHT\b|" \
             r"\bINNER\b|\bFULL\b|\bCROSS\b|\)|$)"

MAX_CONVERSATIONS = 200
HISTORY_MESSAGES = 6
SCHEMA_CACHE_SECONDS = 600


def _strip_literals_and_comments(sql: str) -> str:
    sql = re.sub(r"--[^\n]*", " ", sql)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"'(?:[^']|'')*'", "''", sql)
    return sql


def referenced_tables(sql: str) -> list[str]:
    """Every relation read after FROM / JOIN, including comma-separated
    FROM lists. CTE names and FROM inside EXTRACT(... FROM ...) etc. are
    handled by the caller / removed here."""
    sql = FROM_KEYWORD_FUNCTIONS.sub("0", sql)
    tables = re.findall(r'\bJOIN\s+(?:LATERAL\s+)?"?([a-zA-Z_][\w$]*)"?', sql, re.IGNORECASE)
    # the lookahead finds every FROM, including the ones nested in sub-queries
    for segment in re.findall(r"(?=\bFROM\s+(.*?)" + CLAUSE_END + ")", sql, re.IGNORECASE | re.DOTALL):
        for item in segment.split(","):
            item = item.strip()
            if not item or item.startswith("("):
                continue   # sub-query: its own FROM is found by the regex
            m = re.match(r'(?:LATERAL\s+)?"?([a-zA-Z_][\w$]*)"?', item, re.IGNORECASE)
            if m:
                tables.append(m.group(1))
    return tables


def validate_sql(sql_query: str) -> bool:
    """First safety layer (the second is the read-only database role, which
    only has SELECT on the analytics views and a statement timeout):
    one read-only statement that reads ONLY the allowed views."""
    if not sql_query or not sql_query.strip():
        return False
    clean = _strip_literals_and_comments(sql_query).strip().rstrip(";").strip()

    if ";" in clean:
        return False

    upper = clean.upper()
    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        return False
    if any(re.search(rf"\b{kw}\b", upper) for kw in FORBIDDEN_KEYWORDS):
        return False
    if FORBIDDEN_FUNCTION.search(clean):
        return False

    # CTE names ("WITH top AS (...)") are allowed as sources
    cte_names = {n.lower() for n in re.findall(r"(?:\bWITH\b|,)\s*(?:RECURSIVE\s+)?([a-zA-Z_]\w*)\s+AS\s*\(",
                                              clean, re.IGNORECASE)}

    tables = referenced_tables(clean)
    if not tables:
        return False
    return all(t.lower() in _ALLOWED_LOWER or t.lower() in cte_names for t in tables)


class HRQueryAssistant:
    def __init__(self):
        # one short history per conversation, so users never share context
        self._histories: "OrderedDict[str, list[dict]]" = OrderedDict()
        self._schema_context = None
        self._schema_loaded_at = 0.0

    # ------------------------------------------------------------- helpers

    def _get_schema_context(self) -> str:
        """Column details for the allowed views (cached: they only change with a migration)."""
        if self._schema_context and time.time() - self._schema_loaded_at < SCHEMA_CACHE_SECONDS:
            return self._schema_context

        schema_info = []
        with ai_engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_name = ANY(:views)
                ORDER BY table_name, ordinal_position
            """), {"views": ALLOWED_VIEWS}).fetchall()
        by_view = {}
        for view, column, dtype in rows:
            by_view.setdefault(view, []).append(f"{column} ({dtype})")
        for view in ALLOWED_VIEWS:
            if view in by_view:
                schema_info.append(f"VIEW {view}:\n  Columns: {', '.join(by_view[view])}")

        self._schema_context = "\n\n".join(schema_info)
        self._schema_loaded_at = time.time()
        return self._schema_context

    def _history(self, conversation_id: str) -> list[dict]:
        history = self._histories.pop(conversation_id, [])
        self._histories[conversation_id] = history          # most recent last
        while len(self._histories) > MAX_CONVERSATIONS:
            self._histories.popitem(last=False)
        return history

    # kept for backwards compatibility with older callers
    def _validate_sql_safety(self, sql_query: str) -> bool:
        return validate_sql(sql_query)

    # ------------------------------------------------------------- LLM steps

    def generate_sql(self, user_question: str, history: list[dict]) -> str:
        """Generates SQL using view schema context, domain value mappings, and chat memory."""
        schema_context = self._get_schema_context()

        system_prompt = f"""You are a PostgreSQL SQL Expert for a Smart ERP system.
Convert the user's natural language question into a single, valid SQL SELECT query.

AVAILABLE DATABASE VIEWS:
{schema_context}

RULES:
1. Use ONLY the views listed above. Do NOT query raw base tables. NEVER invent
   a view or table name that is not listed above -- if no listed view has the
   data needed to answer the question, pick the closest available view and
   note the limitation is acceptable; do not fabricate a name.
2. Produce ONLY a standard PostgreSQL SELECT query.
3. CONVERSATIONAL MEMORY: Use chat history to resolve references (e.g., if the user asks "What about that department?", filter using the department_id or business_unit from the preceding turn).
4. OPTIMIZATION: Default to LIMIT 10 unless explicit limits are requested.
5. DOMAIN VALUE MAPPINGS:
   - Active job postings in `v_recruitment_funnel_ats`: Always filter with `UPPER(posting_status) IN ('OPEN', 'ACTIVE')`.
   - Terminated employees: Account for status variations using `UPPER(employee_status) LIKE '%TERMINATED%'`.
   - Defunct / Shut down departments: Query `v_closed_departments`.
   - Active employee counts / per-employee questions (headcount, individual
     salary, individual performance, individual engagement): Query
     `v_ai_retention_features`, which is one row per employee and includes
     employee_status, salary, performance_score, business_unit, and
     engagement/satisfaction scores.
6. CASE-INSENSITIVE MATCHING: Use `ILIKE` or `UPPER()` for string criteria.
7. OUTPUT FORMAT: Return ONLY valid JSON in this exact structure:
{{
    "sql_query": "SELECT ... FROM ... WHERE ...;"
}}"""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({
            "role": "user",
            "content": f'Question: "{user_question}"\nRemember to return ONLY JSON.'
        })

        payload = json.loads(chat(messages, json_mode=True, temperature=0.0))
        return str(payload.get("sql_query", "")).strip()

    def synthesize_answer(self, user_question: str, df: pd.DataFrame, history: list[dict]) -> str:
        """Generates a concise executive response based on returned data and history."""
        if df.empty:
            return "No matching records were found in the database for your query."

        data_preview = df.head(50).to_dict(orient="records")

        system_prompt = f"""You are an Executive AI HR Advisor.
Analyze the SQL query result and summarize the key business takeaway in 2-3 direct sentences.
Use the conversation history to make your answer contextual.

QUERY RESULT DATA:
{json.dumps(data_preview, default=str)}

Respond directly. Do not repeat raw JSON. Do not explain the SQL."""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_question})

        return chat(messages, temperature=0.2, max_tokens=250)

    # ------------------------------------------------------------- entry point

    def ask(self, user_question: str, conversation_id: str = "default") -> dict:
        history = self._history(conversation_id)
        try:
            sql_query = self.generate_sql(user_question, history)

            if not validate_sql(sql_query):
                log.warning("Blocked generated SQL: %s", sql_query)
                return {"error": "Query blocked: only read-only SELECT queries on the HR analytics views are allowed."}

            with ai_engine.connect() as conn:
                df = pd.read_sql_query(text(sql_query), conn)

            summary = self.synthesize_answer(user_question, df, history)

            history.append({"role": "user", "content": user_question})
            history.append({"role": "assistant", "content": summary})
            del history[:-HISTORY_MESSAGES]

            return {
                "question": user_question,
                "sql_query": sql_query,
                "tabular_data": json.loads(df.to_json(orient="records", date_format="iso")),
                "summary": summary
            }

        except Exception as e:
            log.exception("AI chat pipeline failed")
            return {"error": f"Pipeline execution error: {str(e)}"}
