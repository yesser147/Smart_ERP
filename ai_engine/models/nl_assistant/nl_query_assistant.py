import json
import re
import pandas as pd
from sqlalchemy import text
from database import ai_engine  # Restricted read-only engine
from groq import Groq
import config

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

class HRQueryAssistant:
    def __init__(self):
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.GROQ_MODEL
        self.chat_history = []

    def _get_schema_context(self) -> str:
        """Fetches column details for allowed views to ground the LLM."""
        schema_info = []
        with ai_engine.connect() as conn:
            for view in ALLOWED_VIEWS:
                query = text(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{view}';
                """)
                columns = conn.execute(query).fetchall()
                if columns:
                    col_fmt = ", ".join([f"{c[0]} ({c[1]})" for c in columns])
                    schema_info.append(f"VIEW {view}:\n  Columns: {col_fmt}")
        return "\n\n".join(schema_info)

    def _validate_sql_safety(self, sql_query: str) -> bool:
        """Enforces strict read-only constraints, blocks query chaining, AND
        verifies every referenced table is one of the actual allowed views --
        not just that no destructive keyword appears. Without this last
        check, a hallucinated table name (the model inventing "v_employees"
        when no such view exists) reaches Postgres as a live query instead
        of being rejected here."""
        clean_query = sql_query.strip().rstrip(';')

        if ';' in clean_query:
            return False

        clean_upper = clean_query.upper()
        forbidden_keywords = [
            "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
            "TRUNCATE", "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE"
        ]

        if any(re.search(rf"\b{kw}\b", clean_upper) for kw in forbidden_keywords):
            return False

        if not (clean_upper.startswith("SELECT") or clean_upper.startswith("WITH")):
            return False

        # NEW: extract every table/view name following FROM or JOIN and
        # reject the query unless ALL of them are in ALLOWED_VIEWS. This is
        # the actual security boundary against hallucinated or arbitrary
        # table names -- the keyword checks above only stop destructive
        # statements, not reads from the wrong (or nonexistent) table.
        referenced_tables = re.findall(r'\b(?:FROM|JOIN)\s+"?([a-zA-Z_][a-zA-Z0-9_]*)"?', sql_query, re.IGNORECASE)
        if not referenced_tables:
            return False

        allowed_lower = {v.lower() for v in ALLOWED_VIEWS}
        if any(t.lower() not in allowed_lower for t in referenced_tables):
            return False

        return True

    def generate_sql(self, user_question: str) -> str:
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
        messages.extend(self.chat_history)
        messages.append({
            "role": "user", 
            "content": f'Question: "{user_question}"\nRemember to return ONLY JSON.'
        })

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        payload = json.loads(response.choices[0].message.content)
        return payload.get("sql_query", "").strip()

    def synthesize_answer(self, user_question: str, df: pd.DataFrame) -> str:
        """Generates a concise executive response based on returned data and history."""
        if df.empty:
            return "No matching records were found in the database for your query."

        data_preview = df.to_dict(orient="records")

        system_prompt = f"""You are an Executive AI HR Advisor.
Analyze the SQL query result and summarize the key business takeaway in 2-3 direct sentences. 
Use the conversation history to make your answer contextual.

QUERY RESULT DATA:
{json.dumps(data_preview, default=str)}

Respond directly. Do not repeat raw JSON. Do not explain the SQL."""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.chat_history)
        messages.append({"role": "user", "content": user_question})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=250
        )
        return response.choices[0].message.content.strip()

    def ask(self, user_question: str) -> dict:
        try:
            sql_query = self.generate_sql(user_question)
            
            if not self._validate_sql_safety(sql_query):
                return {"error": "Query blocked: Only read-only SELECT operations are allowed."}

            with ai_engine.connect() as conn:
                df = pd.read_sql_query(text(sql_query), conn)
                
            summary = self.synthesize_answer(user_question, df)

            self.chat_history.append({"role": "user", "content": user_question})
            self.chat_history.append({"role": "assistant", "content": summary})

            if len(self.chat_history) > 6:
                self.chat_history = self.chat_history[-6:]

            return {
                "question": user_question,
                "sql_query": sql_query,
                "tabular_data": df.to_dict(orient="records"),
                "summary": summary
            }

        except Exception as e:
            # THIS WILL PRINT THE EXACT REASON TO YOUR TERMINAL
            import traceback
            print("\n" + "="*30)
            print("🚨 CRASH DETECTED IN AI CHAT:")
            traceback.print_exc()
            print("="*30 + "\n")
            
            return {"error": f"Pipeline execution error: {str(e)}"}