"""
Joint SQL queries + analysis + charts for the car import database.
Run:  python analysis.py      (needs car_dealer.db from etl.py)
Output: charts/*.png and charts/dashboard.png
"""
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BASE = Path(__file__).parent
OUT = BASE / "charts"
OUT.mkdir(exist_ok=True)
con = sqlite3.connect(BASE.parent / "02_database" / "car_dealer.db")

plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "font.size": 10})
C = ["#2563eb", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#64748b"]

# ------------------------------------------------------------------ SQL (all multi-table joins)
Q = {}

# orders + shipments + car_models  (via view)
Q["shipping_stages"] = """
SELECT origin_country,
       ROUND(AVG(transit_days),1)   AS transit,
       ROUND(AVG(clearance_days),1) AS clearance,
       ROUND(AVG(last_mile_days),1) AS last_mile
FROM v_order_shipping
WHERE order_status = 'Delivered'
GROUP BY origin_country
ORDER BY transit + clearance + last_mile
"""

# reviews + shipments + orders + car_models
Q["delay_vs_rating"] = """
SELECT m.origin_country,
       CASE WHEN s.delay_reason IS NULL THEN 'On time' ELSE 'Delayed' END AS shipment,
       ROUND(AVG(r.rating),2) AS avg_rating
FROM reviews r
JOIN orders o     ON o.order_id = r.order_id
JOIN shipments s  ON s.order_id = o.order_id
JOIN car_models m ON m.model_id = o.model_id
GROUP BY m.origin_country, shipment
"""

# orders only, with window function for 3-month rolling average
Q["monthly_revenue"] = """
WITH monthly AS (
    SELECT strftime('%Y-%m', order_date) AS month,
           COUNT(*) AS orders,
           SUM(total_price_kes)/1e6 AS revenue_m
    FROM orders
    WHERE order_status <> 'Cancelled' AND order_date < '2026-11-01'
    GROUP BY month
)
SELECT month, orders, revenue_m,
       AVG(revenue_m) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS rolling_3m
FROM monthly
"""

# orders + car_models
Q["revenue_by_make"] = """
SELECT m.make,
       ROUND(SUM(o.total_price_kes)/1e6,0) AS revenue_m,
       COUNT(*) AS units
FROM orders o JOIN car_models m ON m.model_id = o.model_id
WHERE o.order_status <> 'Cancelled'
GROUP BY m.make ORDER BY revenue_m DESC LIMIT 8
"""

# shipments + orders + car_models
Q["delay_reasons"] = """
SELECT s.delay_reason,
       COUNT(*) AS shipments,
       ROUND(AVG(julianday(s.customs_clearance_date) - julianday(s.arrival_date)),1) AS avg_clearance_days
FROM shipments s
WHERE s.delay_reason IS NOT NULL AND s.customs_clearance_date IS NOT NULL
GROUP BY s.delay_reason
ORDER BY avg_clearance_days DESC
"""

# suppliers + orders + reviews + shipments
Q["supplier_scorecard"] = """
SELECT sp.supplier_name,
       ROUND(AVG(r.rating),2) AS avg_rating,
       ROUND(AVG(julianday(s.delivery_date) - julianday(o.order_date)),1) AS avg_days_to_deliver,
       COUNT(*) AS reviews
FROM suppliers sp
JOIN orders o    ON o.supplier_id = sp.supplier_id
JOIN shipments s ON s.order_id = o.order_id
JOIN reviews r   ON r.order_id = o.order_id
WHERE s.delivery_date IS NOT NULL
GROUP BY sp.supplier_id
HAVING reviews >= 25
"""

# customers + orders
Q["revenue_by_county"] = """
SELECT c.county,
       ROUND(SUM(o.total_price_kes)/1e6,0) AS revenue_m,
       COUNT(DISTINCT c.customer_id)       AS customers
FROM customers c JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_status <> 'Cancelled'
GROUP BY c.county ORDER BY revenue_m DESC LIMIT 8
"""

# orders + car_models: landed-cost breakdown per origin (shows tax burden)
Q["cost_breakdown"] = """
SELECT m.origin_country,
       AVG(o.fob_price_usd * o.usd_kes_rate)                          AS vehicle_cost,
       AVG((o.freight_usd + o.insurance_usd) * o.usd_kes_rate)        AS freight_insurance,
       AVG(o.import_duty_kes + o.excise_duty_kes)                     AS duties,
       AVG(o.vat_kes)                                                 AS vat
FROM orders o JOIN car_models m ON m.model_id = o.model_id
WHERE o.order_status <> 'Cancelled'
GROUP BY m.origin_country
"""

D = {k: pd.read_sql_query(v, con) for k, v in Q.items()}
for k, df in D.items():
    print(f"\n--- {k} ---\n{df.to_string(index=False)}")

# ------------------------------------------------------------------ CHARTS
fig, axes = plt.subplots(4, 2, figsize=(15, 22))
ax = axes.ravel()

# 1 shipping stages (stacked horizontal)
d = D["shipping_stages"].set_index("origin_country")
d.plot.barh(stacked=True, ax=ax[0], color=C[:3], width=0.65)
ax[0].set_title("Order journey: average days per stage (delivered orders)")
ax[0].set_xlabel("Days"); ax[0].set_ylabel(""); ax[0].legend(["Sea transit", "Customs clearance", "Mombasa to Nairobi"], frameon=False)

# 2 delay vs rating by origin
d = D["delay_vs_rating"].pivot(index="origin_country", columns="shipment", values="avg_rating")[["On time", "Delayed"]]
d.plot.bar(ax=ax[1], color=[C[2], C[3]], width=0.75, rot=20)
ax[1].set_title("Customer rating: on-time vs delayed shipments"); ax[1].set_ylabel("Avg rating (1-5)"); ax[1].set_xlabel("")
ax[1].set_ylim(0, 5); ax[1].legend(frameon=False)

# 3 monthly revenue
d = D["monthly_revenue"]
ax[2].bar(d["month"], d["revenue_m"], color=C[0], alpha=0.35, label="Monthly revenue")
ax[2].plot(d["month"], d["rolling_3m"], color=C[0], lw=2.2, label="3-month average")
ax[2].set_title("Monthly revenue (KES millions)"); ax[2].set_ylabel("KES m")
ax[2].set_xticks(range(0, len(d), 4)); ax[2].set_xticklabels(d["month"][::4], rotation=45, ha="right"); ax[2].legend(frameon=False)

# 4 revenue by make
d = D["revenue_by_make"].iloc[::-1]
bars = ax[3].barh(d["make"], d["revenue_m"], color=C[0])
ax[3].bar_label(bars, labels=[f"{u} cars" for u in d["units"]], padding=3, fontsize=9)
ax[3].set_title("Revenue by make (KES millions)"); ax[3].set_xlim(0, d["revenue_m"].max() * 1.15)

# 5 delay reasons -> clearance days
d = D["delay_reasons"].iloc[::-1]
colors = [C[3] if v > 12 else C[5] for v in d["avg_clearance_days"]]
ax[4].barh(d["delay_reason"], d["avg_clearance_days"], color=colors)
ax[4].set_title("Avg customs clearance days by delay reason\n(red = customs/paperwork issues)"); ax[4].set_xlabel("Days")

# 6 supplier scorecard scatter
d = D["supplier_scorecard"]
ax[5].scatter(d["avg_days_to_deliver"], d["avg_rating"], s=d["reviews"] * 2.2, color=C[4], alpha=0.6)
for _, r in d.iterrows():
    ax[5].annotate(r["supplier_name"], (r["avg_days_to_deliver"], r["avg_rating"]), fontsize=8, xytext=(5, 4), textcoords="offset points")
ax[5].set_title("Supplier scorecard: speed vs satisfaction\n(bubble size = number of reviews)")
ax[5].set_xlabel("Avg days from order to delivery"); ax[5].set_ylabel("Avg customer rating")

# 7 revenue by county
d = D["revenue_by_county"].iloc[::-1]
ax[6].barh(d["county"], d["revenue_m"], color=C[2])
ax[6].set_title("Top counties by revenue (KES millions)")

# 8 landed cost breakdown (stacked, % share)
d = D["cost_breakdown"].set_index("origin_country")
share = d.div(d.sum(axis=1), axis=0) * 100
share.plot.bar(stacked=True, ax=ax[7], color=[C[0], C[1], C[3], C[4]], rot=20, width=0.7)
ax[7].set_title("Where the customer's money goes (% of landed cost)"); ax[7].set_ylabel("%"); ax[7].set_xlabel("")
ax[7].legend(["Vehicle", "Freight + insurance", "Import + excise duty", "VAT"], frameon=False, fontsize=8, loc="upper center", ncol=4, bbox_to_anchor=(0.5, -0.18))

fig.suptitle("Car Import Dealer - Operations & Sales Dashboard", fontsize=18, fontweight="bold", y=0.995)
fig.tight_layout()
fig.savefig(OUT / "dashboard.png", dpi=110)
print("\nSaved charts/dashboard.png")

# also save every panel as its own PNG
fig.canvas.draw()
names = ["shipping_stages", "delay_vs_rating", "monthly_revenue", "revenue_by_make",
         "delay_reasons", "supplier_scorecard", "revenue_by_county", "cost_breakdown"]
for a, n in zip(ax, names):
    ext = a.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted()).expanded(1.04, 1.06)
    fig.savefig(OUT / f"{n}.png", bbox_inches=ext, dpi=110)
print(f"Saved {len(names)} individual charts to charts/")
