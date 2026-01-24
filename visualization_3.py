import pandas as pd
import matplotlib.pyplot as plt
import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="ellibrinker$flytau"
)

query = """
SELECT
  w.id AS worker_id,
  CONCAT(w.first_name, ' ', w.last_name) AS full_name,
  CASE
    WHEN pl.id IS NOT NULL THEN 'Pilot'
    WHEN fa.id IS NOT NULL THEN 'Flight Attendant'
    ELSE 'AirCrew'
  END AS role,
  COALESCE(SUM(CASE WHEN aw.duration <= 360 THEN aw.duration ELSE 0 END), 0) AS short_minutes,
  COALESCE(SUM(CASE WHEN aw.duration > 360 THEN aw.duration ELSE 0 END), 0) AS long_minutes,
  COALESCE(SUM(aw.duration), 0) AS total_minutes
FROM Worker w
JOIN AirCrew ac ON ac.id = w.id
LEFT JOIN Pilot pl ON pl.id = w.id
LEFT JOIN FlightAttendant fa ON fa.id = w.id
JOIN FlightCrewPlacement fcp ON fcp.id = ac.id
JOIN Flight f ON f.flight_id = fcp.flight_id
JOIN Airway aw
  ON aw.origin_airport = f.origin_airport
 AND aw.destination_airport = f.destination_airport
WHERE LOWER(f.status) <> 'cancelled'
GROUP BY w.id, w.first_name, w.last_name, role
ORDER BY total_minutes DESC;
"""

df = pd.read_sql(query, conn)
conn.close()

df = df.sort_values(by="total_minutes", ascending=False)

fig, ax = plt.subplots(figsize=(12, 7))

bar_short = ax.bar(
    df["full_name"],
    df["short_minutes"],
    label="Short Flights (≤ 360 min)",
    color="#4688ad"
)

bar_long = ax.bar(
    df["full_name"],
    df["long_minutes"],
    bottom=df["short_minutes"],
    label="Long Flights (> 360 min)",
    color="#f5a652"
)

for bar in bar_short:
    height = bar.get_height()
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        height + 20,
        f"{int(height)}",
        ha="center",
        va="bottom",
        fontweight="bold",
        fontsize=10
    )

ax.set_title(
    "Flight Duration Distribution per Worker",
    fontweight="bold",
    fontsize=14,
    pad=40
)

ax.set_ylim(0, df["total_minutes"].max() * 1.2)
ax.set_xlabel("Worker Name", fontweight="bold", labelpad=15)
ax.set_ylabel("Total Duration (min)", fontweight="bold", labelpad=15)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, linestyle="--", alpha=0.2)
ax.set_axisbelow(True)

plt.xticks(rotation=45, ha="right")
ax.legend(frameon=False, loc="upper right")

plt.tight_layout()
plt.show()
