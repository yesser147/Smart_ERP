"""
Charts pinned from the HR assistant to the dashboard ("My charts").

Only the question, the SQL and the chart description are stored: every time
the dashboard is opened the SQL is re-checked and re-run on the read-only
connection, so a pinned chart always shows today's data.
"""

import json
import logging

import pandas as pd
from sqlalchemy import text

from database import ai_engine, engine
from models.nl_assistant.chart_spec import suggest_chart, validate_spec
from models.nl_assistant.nl_query_assistant import validate_sql

log = logging.getLogger(__name__)

MAX_ROWS = 500
MAX_CHARTS_PER_USER = 24


class SavedChartError(Exception):
    pass


def _run(sql_query: str) -> pd.DataFrame:
    """Re-checks and runs a chatbot query on the read-only connection."""
    if not validate_sql(sql_query):
        raise SavedChartError("Only read-only queries on the HR analytics views can be used.")
    with ai_engine.connect() as conn:
        return pd.read_sql_query(text(sql_query), conn).head(MAX_ROWS)


def chart_for_query(question: str, sql_query: str) -> dict:
    """The "Create a chart" button: the AI chooses a chart for an answer already shown."""
    df = _run(sql_query)
    spec = suggest_chart(question, df)
    if spec is None:
        raise SavedChartError("No chart fits this result (for example a single number or only text).")
    return spec


def save_chart(owner: str, title: str, question: str, sql_query: str, chart: dict) -> int:
    df = _run(sql_query)
    spec = validate_spec(chart, df)
    if spec is None:
        raise SavedChartError("This chart does not match the query result.")

    with engine.begin() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM ai_saved_charts WHERE owner_email = :o"),
                             {"o": owner}).scalar()
        if count >= MAX_CHARTS_PER_USER:
            raise SavedChartError(f"You can pin at most {MAX_CHARTS_PER_USER} charts: remove one first.")
        return conn.execute(text("""
            INSERT INTO ai_saved_charts (owner_email, title, question, sql_query, chart_spec)
            VALUES (:o, :t, :q, :s, CAST(:c AS jsonb))
            RETURNING id
        """), {"o": owner, "t": (title or spec["title"] or question or "Chart")[:200],
               "q": question, "s": sql_query, "c": json.dumps(spec)}).scalar()


def list_charts(owner: str) -> list[dict]:
    """The user's pinned charts, each with fresh rows (or an error message)."""
    with engine.connect() as conn:
        saved = conn.execute(text("""
            SELECT id, title, question, sql_query, chart_spec, created_at
            FROM ai_saved_charts WHERE owner_email = :o ORDER BY created_at
        """), {"o": owner}).fetchall()

    charts = []
    for c in saved:
        spec = c.chart_spec if isinstance(c.chart_spec, dict) else json.loads(c.chart_spec)
        item = {"id": c.id, "title": c.title, "question": c.question, "chart": spec,
                "rows": [], "error": None, "created_at": c.created_at.isoformat() if c.created_at else None}
        try:
            df = _run(c.sql_query)
            if validate_spec(spec, df) is None:
                raise SavedChartError("the data no longer matches the chart")
            item["rows"] = json.loads(df.to_json(orient="records", date_format="iso"))
        except Exception as e:
            log.warning("Pinned chart %s could not be refreshed: %s", c.id, e)
            item["error"] = "This chart could not be refreshed. Ask the question again and pin the new chart."
        charts.append(item)
    return charts


def delete_chart(owner: str, chart_id: int) -> bool:
    with engine.begin() as conn:
        return conn.execute(text("DELETE FROM ai_saved_charts WHERE id = :id AND owner_email = :o"),
                            {"id": chart_id, "o": owner}).rowcount > 0
