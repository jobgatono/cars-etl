"""
Car Import Dealer ETL
  Extract : raw CSVs in ../01_raw_data/
  Transform: clean + standardise with pandas, validate referential integrity
  Load    : relational SQLite database (schema.sql) -> car_dealer.db
Usage: python etl.py
"""
import re
import sqlite3
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent
RAW = BASE.parent / "01_raw_data"
DB = BASE / "car_dealer.db"
SCHEMA = BASE / "schema.sql"

rejects = []  # (source_file, record_key, reason)


def reject(df, file, key, reason):
    for k in df[key]:
        rejects.append((file, str(k), reason))


# ---------------------------------------------------------------- EXTRACT
def extract():
    names = ["car_models", "suppliers", "customers", "orders", "shipments", "customer_reviews"]
    data = {n: pd.read_csv(RAW / f"{n}.csv", dtype=str, keep_default_na=False) for n in names}
    for n, d in data.items():
        print(f"[extract]   {n:<17} {len(d):>5} rows")
    return data


# ---------------------------------------------------------------- TRANSFORM helpers
def strip_all(df):
    return df.apply(lambda c: c.str.strip()).replace("", pd.NA)


def parse_dates(s):
    """Handle ISO (YYYY-MM-DD), DD/MM/YYYY and MM-DD-YYYY, return ISO strings."""
    iso = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
    dmy = pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")
    mdy = pd.to_datetime(s, format="%m-%d-%Y", errors="coerce")
    return iso.fillna(dmy).fillna(mdy).dt.strftime("%Y-%m-%d")


def dedupe(df, key, file):
    dup = df[df.duplicated(key, keep="first")]
    if len(dup):
        print(f"[transform] {file}: dropped {len(dup)} duplicate rows")
    return df.drop_duplicates(key, keep="first")


def clean_phone(p):
    if pd.isna(p):
        return pd.NA
    digits = re.sub(r"\D", "", p)
    if digits.startswith("254"):
        digits = digits[3:]
    elif digits.startswith("0"):
        digits = digits[1:]
    return f"+254{digits}" if len(digits) == 9 else pd.NA


def money(s):
    return pd.to_numeric(s.str.replace(r"[^\d.\-]", "", regex=True), errors="coerce")


# ---------------------------------------------------------------- TRANSFORM
def transform(d):
    t = {}

    t["car_models"] = strip_all(d["car_models"])
    t["car_models"]["engine_cc"] = pd.to_numeric(t["car_models"]["engine_cc"]).astype("Int64")
    t["car_models"]["base_fob_price_usd"] = pd.to_numeric(t["car_models"]["base_fob_price_usd"])

    t["suppliers"] = strip_all(d["suppliers"])
    t["suppliers"]["rating"] = pd.to_numeric(t["suppliers"]["rating"])

    c = strip_all(d["customers"])
    c = dedupe(c, "customer_id", "customers")
    c["full_name"] = c["full_name"].str.title()
    c["email"] = c["email"].str.lower()
    c["phone"] = c["phone"].map(clean_phone)
    c["county"] = c["county"].str.title()
    c["registration_date"] = parse_dates(c["registration_date"])
    t["customers"] = c

    o = strip_all(d["orders"])
    o = dedupe(o, "order_id", "orders")
    o["order_date"] = parse_dates(o["order_date"])
    o["order_status"] = o["order_status"].str.title()
    o["color"] = o["color"].str.title()
    o["payment_method"] = o["payment_method"].fillna("Unknown")
    for col in ["manufacture_year", "mileage_km"]:
        o[col] = pd.to_numeric(o[col]).astype("Int64")
    for col in ["fob_price_usd", "freight_usd", "insurance_usd", "usd_kes_rate",
                "import_duty_kes", "excise_duty_kes", "vat_kes", "total_price_kes"]:
        o[col] = money(o[col])
    bad = o[o["order_date"].isna()]
    reject(bad, "orders.csv", "order_id", "unparseable order_date")
    t["orders"] = o.drop(bad.index)

    s = strip_all(d["shipments"])
    s = dedupe(s, "shipment_id", "shipments")
    for col in ["departure_date", "arrival_date", "customs_clearance_date", "delivery_date"]:
        s[col] = parse_dates(s[col])
    s["delay_reason"] = s["delay_reason"].str.capitalize().str.replace("Kra", "KRA")
    t["shipments"] = s

    r = strip_all(d["customer_reviews"])
    r = dedupe(r, "review_id", "customer_reviews")
    r["rating"] = pd.to_numeric(r["rating"].str.extract(r"^(\d)")[0]).astype("Int64")
    r["review_date"] = parse_dates(r["review_date"])
    t["reviews"] = r

    # ---- referential integrity: reject orphans before they hit the DB
    ok = (t["orders"].customer_id.isin(t["customers"].customer_id)
          & t["orders"].model_id.isin(t["car_models"].model_id)
          & t["orders"].supplier_id.isin(t["suppliers"].supplier_id))
    reject(t["orders"][~ok], "orders.csv", "order_id", "orphan foreign key")
    t["orders"] = t["orders"][ok]

    ok = t["shipments"].order_id.isin(t["orders"].order_id)
    reject(t["shipments"][~ok], "shipments.csv", "shipment_id", "order_id not in orders")
    t["shipments"] = t["shipments"][ok]

    ok = t["reviews"].order_id.isin(t["orders"].order_id) & t["reviews"].rating.between(1, 5)
    reject(t["reviews"][~ok], "customer_reviews.csv", "review_id", "orphan order or invalid rating")
    t["reviews"] = t["reviews"][ok]

    for n, df in t.items():
        print(f"[transform] {n:<17} {len(df):>5} clean rows")
    return t


# ---------------------------------------------------------------- LOAD
def load(t):
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA.read_text())
    con.execute("PRAGMA foreign_keys = ON")
    # parents first, children last
    for table in ["car_models", "suppliers", "customers", "orders", "shipments", "reviews"]:
        df = t[table].astype(object).where(t[table].notna(), None)
        df.to_sql(table, con, if_exists="append", index=False)
        print(f"[load]      {table:<17} {len(df):>5} rows")
    con.executemany("INSERT INTO etl_rejects(source_file, record_key, reason) VALUES (?,?,?)", rejects)
    con.commit()
    bad = con.execute("PRAGMA foreign_key_check").fetchall()
    print(f"[load]      FK violations: {len(bad)} | rejected rows logged: {len(rejects)}")
    con.close()


if __name__ == "__main__":
    load(transform(extract()))
    print(f"\nDone -> {DB.name}")
