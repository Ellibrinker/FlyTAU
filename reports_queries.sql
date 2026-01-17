/* =========================================================
1) Average occupancy of flights that actually took place
   (exclude cancelled flights, only past flights)
========================================================= */

SELECT ROUND(AVG(t.occ_pct), 2) AS avg_occupancy_percent
FROM (
  SELECT fs.flight_id,
         SUM(CASE WHEN LOWER(fs.status) <> 'available' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS occ_pct
  FROM FlightSeat fs
  GROUP BY fs.flight_id
) AS t
JOIN Flight AS f ON f.flight_id = t.flight_id
WHERE LOWER(f.status) <> 'cancelled'
  AND f.departure_date < CURDATE();


/* =========================================================
2) Revenue by plane size, manufacturer and class
   - paid            -> 100%
   - customer_cancelled -> 5%
   - system_cancelled   -> 0%
   - cancelled flights excluded
========================================================= */

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


/* =========================================================
3) Accumulated flight hours per worker
   - split short / long flights (threshold: 360 minutes)
   - exclude cancelled flights
========================================================= */

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


/* =========================================================
4) Purchase cancellation rate by month
   - includes customer_cancelled AND system_cancelled
========================================================= */

SELECT
  YEAR(fo.execution_date) AS year,
  MONTH(fo.execution_date) AS month_num,
  MONTHNAME(fo.execution_date) AS month,
  ROUND(
    SUM(
      CASE
        WHEN LOWER(fo.status) IN ('customer_cancelled', 'system_cancelled') THEN 1
        ELSE 0
      END
    ) * 100.0 / COUNT(*),
    2
  ) AS cancellation_rate_percentage
FROM FlightOrder fo
GROUP BY
  YEAR(fo.execution_date),
  MONTH(fo.execution_date),
  MONTHNAME(fo.execution_date)
ORDER BY year, month_num;


/* =========================================================
5) Monthly plane activity summary  (utilization by ACTIVE DAYS)
Active day definition:
- A day is "active" if the plane had either:
  (1) a departure that day (non-cancelled), OR
  (2) an arrival that day (non-cancelled, computed from Airway.duration)

utilization % = active_days / 30 * 100
dominant route = most frequent performed route in that month
========================================================= */

SELECT
  ms.plane_id,
  ms.manufacturer,
  ms.flight_month,
  ms.performed_flights,
  ms.cancelled_flights,
  ms.active_days,
  (
    SELECT CONCAT(f3.origin_airport, '-', f3.destination_airport)
    FROM Flight f3
    WHERE f3.plane_id = ms.plane_id
      AND DATE_FORMAT(f3.departure_date, '%Y-%m') = ms.flight_month
      AND LOWER(f3.status) <> 'cancelled'
    GROUP BY f3.origin_airport, f3.destination_airport
    ORDER BY COUNT(*) DESC
    LIMIT 1
  ) AS dominant_route,
  ROUND((ms.active_days / 30.0) * 100, 1) AS utilization_percentage
FROM (
  SELECT
    p.plane_id,
    p.manufacturer,
    DATE_FORMAT(f.departure_date, '%Y-%m') AS flight_month,

    /* flights counts */
    SUM(CASE WHEN LOWER(f.status) <> 'cancelled' THEN 1 ELSE 0 END) AS performed_flights,
    SUM(CASE WHEN LOWER(f.status) = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_flights,

    /* active days = distinct (departure day) + distinct (arrival day when different) */
    COUNT(DISTINCT d.active_day) AS active_days

  FROM Plane p
  JOIN Flight f ON f.plane_id = p.plane_id
  JOIN Airway aw
    ON aw.origin_airport = f.origin_airport
   AND aw.destination_airport = f.destination_airport

  /* build a small "days" set per flight: departure day always, arrival day if different */
  JOIN (
    SELECT 1 AS kind
    UNION ALL
    SELECT 2 AS kind
  ) k

  /* compute active_day per kind */
  CROSS JOIN LATERAL (
    SELECT
      CASE
        WHEN k.kind = 1 THEN DATE(f.departure_date)
        WHEN k.kind = 2 THEN
          CASE
            WHEN DATE(
              DATE_ADD(
                TIMESTAMP(f.departure_date, f.departure_time),
                INTERVAL aw.duration MINUTE
              )
            ) <> DATE(f.departure_date)
            THEN DATE(
              DATE_ADD(
                TIMESTAMP(f.departure_date, f.departure_time),
                INTERVAL aw.duration MINUTE
              )
            )
            ELSE NULL
          END
      END AS active_day
  ) d

  WHERE d.active_day IS NOT NULL
    AND LOWER(f.status) <> 'cancelled'

  GROUP BY p.plane_id, p.manufacturer, flight_month
) AS ms
ORDER BY ms.flight_month DESC, ms.performed_flights DESC;
