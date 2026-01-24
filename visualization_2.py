import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import mysql.connector

# =========================
# DB Connection
# =========================
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="ellibrinker$flytau"
)

query = """
SELECT
  CASE WHEN bp.plane_id IS NOT NULL THEN 'Big' ELSE 'Small' END AS plane_size,
  p.manufacturer,
  s.class_type,
  ROUND(SUM(
    CASE
      WHEN LOWER(fo.status) = 'system_cancelled' THEN 0
      WHEN LOWER(fo.status) = 'customer_cancelled' THEN fp.price * 0.05
      ELSE fp.price
    END
  ), 2) AS revenue
FROM Flight f
JOIN Plane p ON p.plane_id = f.plane_id
LEFT JOIN BigPlane bp ON bp.plane_id = f.plane_id
JOIN FlightSeat fs ON fs.flight_id = f.flight_id
JOIN Seat s ON s.seat_id = fs.seat_id
JOIN OrderItem oi ON oi.flight_seat_id = fs.flight_seat_id
JOIN FlightOrder fo ON fo.order_id = oi.order_id
JOIN FlightPricing fp
  ON fp.flight_id = f.flight_id
 AND fp.class_type = s.class_type
WHERE LOWER(f.status) <> 'cancelled'
GROUP BY plane_size, p.manufacturer, s.class_type;
"""

df = pd.read_sql(query, conn)
conn.close()


sns.set_theme(style="whitegrid")

g = sns.catplot(
    data=df,
    kind="bar",
    x="manufacturer",
    y="revenue",
    hue="plane_size",
    col="class_type",
    col_wrap=2,
    height=5,
    aspect=1.2,
    palette=["#003366", "#4DA6FF"],
    edgecolor="white",
    linewidth=1.5
)

plt.ylim(0, df["revenue"].max() * 1.2)

g.set_titles("{col_name}")

for ax in g.axes.flat:
    for container in ax.containers:
        ax.bar_label(container,fmt="{:,.0f} ₪", padding=3, fontweight="bold", fontsize=12)

    ax.set_xlabel("Manufacturer", fontweight="bold")
    ax.set_ylabel("Revenue (₪)", fontweight="bold")

g.fig.suptitle("Airline Revenue Analysis: Manufacturer & Plane Size", fontsize=16, fontweight="bold", y=0.98)

g.fig.subplots_adjust(top=0.85)

plt.show()


