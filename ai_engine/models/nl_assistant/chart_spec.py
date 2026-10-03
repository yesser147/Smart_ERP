"""
Chart chosen by the AI for a chatbot answer.

The LLM never sees the data and never writes code: it receives the question
and the result's columns (name, type, a few example values) and returns a
small description, e.g.

    {"type": "bar", "title": "...", "x": "department_type",
     "y": ["avg_salary"], "series": "gender", "y_format": "money"}

which is checked against the real columns before being sent to the frontend,
where one drawing function per chart type turns it into a chart.

A chart is only drawn when the question asks for one (wants_chart); otherwise the
user can still ask for it afterwards with the "Create a chart" button.
"""

import logging
import re

import pandas as pd

from models.recruitment.llm_client import generate_json

log = logging.getLogger(__name__)

CHART_TYPES = ("bar", "horizontal-bar", "stacked-bar", "line", "pie", "donut", "scatter")
Y_FORMATS = ("number", "money", "percent")

# English and French words that mean "draw it"
_CHART_WORDS = re.compile(
    r"\b(chart|charts|graph|graphs|plot|plotted|visuali[sz]e|visuali[sz]ation|diagram|histogram|"
    r"pie|donut|doughnut|scatter|curve|"
    r"(as|in) an? (bar|bars|line|lines)|(as|in) (bars|lines)|"   # "as a line", not "line managers"
    r"graphique|graphe|courbe|camembert|histogramme|diagramme|visualiser)\b",
    re.IGNORECASE)


def wants_chart(question: str) -> bool:
    """True when the user asked for a visual ("... as a pie chart", "plot ...", "graphique ...")."""
    return bool(_CHART_WORDS.search(question or ""))
MAX_PIE_SLICES = 12


def _columns(df: pd.DataFrame) -> list[dict]:
    cols = []
    for name in df.columns:
        numeric = pd.api.types.is_numeric_dtype(df[name]) and not pd.api.types.is_bool_dtype(df[name])
        examples = [str(v)[:40] for v in df[name].dropna().unique()[:3]]
        cols.append({"name": str(name), "kind": "number" if numeric else "text", "examples": examples})
    return cols


def validate_spec(spec: dict, df: pd.DataFrame) -> dict | None:
    """Keeps only a spec that can really be drawn from these rows."""
    if not isinstance(spec, dict) or df.empty:
        return None
    cols = {c["name"]: c["kind"] for c in _columns(df)}
    chart_type = str(spec.get("type", "")).lower()
    x = spec.get("x")
    y = spec.get("y") or []
    if isinstance(y, str):
        y = [y]
    series = spec.get("series") or None

    if chart_type not in CHART_TYPES or x not in cols:
        return None
    y = [c for c in y if cols.get(c) == "number" and c != x][:3]
    if not y:
        return None
    if series is not None and (series not in cols or series in (x, *y) or cols[series] != "text"):
        series = None
    if chart_type in ("pie", "donut"):
        if series or len(y) != 1 or len(df) > MAX_PIE_SLICES:
            chart_type = "bar"            # too many slices or several measures: a pie can't show it
    if chart_type == "scatter" and cols[x] != "number":
        chart_type = "bar"

    y_format = str(spec.get("y_format", "number")).lower()
    return {
        "type": chart_type,
        "title": str(spec.get("title") or "")[:120],
        "x": x,
        "y": y,
        "series": series,
        "y_format": y_format if y_format in Y_FORMATS else "number",
    }


def suggest_chart(question: str, df: pd.DataFrame, previous_questions: list[str] = ()) -> dict | None:
    """Asks the LLM which chart answers the question best; None when no chart fits."""
    if df.empty or len(df.columns) < 2:
        return None
    context = ""
    if previous_questions:
        context = "Earlier questions in this conversation (for follow-ups like 'as a pie chart'):\n" + \
                  "\n".join(f"- {q}" for q in previous_questions[-2:]) + "\n\n"
    prompt = f"""You choose the chart that best answers an HR question.

{context}QUESTION: {question}

THE QUERY RESULT HAS {len(df)} ROWS AND THESE COLUMNS:
{_columns(df)}

Chart types:
- "bar": compare categories; "horizontal-bar": many categories or long names;
- "stacked-bar": parts of a total per category (needs "series");
- "line": evolution over time (x is a date, month or year);
- "pie" / "donut": shares of ONE total, at most {MAX_PIE_SLICES} rows;
- "scatter": relation between two numeric columns (x numeric).
If the user explicitly asks for a chart type, use it.

Rules:
- "x": the column for the categories / time axis (use exactly a column name above);
- "y": 1 to 3 NUMBER columns to plot;
- "series": a TEXT column whose values become separate bars or lines (e.g. gender), or null;
- "y_format": "money" for salaries / costs / budgets, "percent" for rates and %, else "number";
- "title": a short chart title.
If no chart makes sense (e.g. a single number, or only text), return {{"type": null}}.

Return ONLY a valid JSON object:
{{"type": "bar", "title": "...", "x": "...", "y": ["..."], "series": null, "y_format": "number"}}"""
    try:
        spec = generate_json(prompt, temperature=0.0, timeout=30)
    except Exception as e:
        log.warning("Chart suggestion failed: %s", e)
        return None
    if not spec or spec.get("type") in (None, "null", "none"):
        return None
    valid = validate_spec(spec, df)
    if valid is None:
        log.info("Chart suggestion rejected (does not match the columns): %s", spec)
    return valid
