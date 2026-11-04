"""Run every query in queries.sql against car_dealer.db and print the results."""
import sqlite3
from pathlib import Path
import pandas as pd

base = Path(__file__).parent
con = sqlite3.connect(base.parent / "02_database" / "car_dealer.db")
for i, q in enumerate([q.strip() for q in (base / "queries.sql").read_text().split(";") if q.strip()], 1):
    title = q.splitlines()[0].lstrip("- ").strip()
    print(f"\n=== {title} ===")
    print(pd.read_sql_query(q, con).to_string(index=False))
