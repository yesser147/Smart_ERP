-- Charts pinned from the HR assistant to the dashboard (AI engine, models/nl_assistant/saved_charts.py).
-- Only the question, the SQL and the chart description are kept: the data is re-queried on every view.
CREATE TABLE IF NOT EXISTS ai_saved_charts (
    id          BIGSERIAL PRIMARY KEY,
    owner_email VARCHAR(255) NOT NULL,
    title       VARCHAR(200) NOT NULL,
    question    TEXT,
    sql_query   TEXT NOT NULL,
    chart_spec  JSONB NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_saved_charts_owner ON ai_saved_charts(owner_email, created_at);
