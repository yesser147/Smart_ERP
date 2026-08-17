"""
Tracks every fix / flag made while cleaning the data so you end up with a
paper trail instead of a black box. Call .log() everywhere clean.py touches
a row, then .save() at the end to get a CSV + a printed summary.
"""

import pandas as pd


class DataQualityReport:
    def __init__(self):
        self.rows = []

    def log(self, table, rule, count, description):
        """Record that `rule` affected `count` rows in `table`."""
        if count and count > 0:
            self.rows.append({
                "table": table,
                "rule": rule,
                "rows_affected": count,
                "description": description,
            })

    def as_dataframe(self):
        if not self.rows:
            return pd.DataFrame(columns=["table", "rule", "rows_affected", "description"])
        return pd.DataFrame(self.rows)

    def print_summary(self):
        df = self.as_dataframe()
        print("\n" + "=" * 78)
        print("DATA QUALITY REPORT")
        print("=" * 78)
        if df.empty:
            print("No issues found.")
        else:
            for table in df["table"].unique():
                sub = df[df["table"] == table]
                print(f"\n[{table}]  ({sub['rows_affected'].sum()} rows touched total)")
                for _, r in sub.iterrows():
                    print(f"  - {r['rule']}: {r['rows_affected']} rows -- {r['description']}")
        print("=" * 78 + "\n")

    def save(self, path):
        self.as_dataframe().to_csv(path, index=False)
        print(f"Quality report saved to {path}")
