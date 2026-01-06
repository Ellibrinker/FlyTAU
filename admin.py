from flask import Blueprint, render_template, request, redirect, session
from datetime import datetime, date, timedelta

admin_bp = Blueprint("admin", __name__)  # <-- בלי url_prefix כאן


# =========================
# Availability buffers (industry-ish defaults)
# =========================
PLANE_BUFFER_MIN = 60
CREW_BUFFER_MIN = 120


def _require_admin():
    if not session.get("is_manager"):
        return redirect("/admin/login")
    return None


def _flight_window(dep_date_str: str, dep_time_str: str, duration_min: int):
    """
    Returns (start_dt, end_dt) for a flight based on date+time strings and duration (minutes).
    dep_time_str can be 'HH:MM' or 'HH:MM:SS'
    """
    d = datetime.fromisoformat(dep_date_str).date()

    t = dep_time_str.strip()
    if len(t) <= 5:
        tm = datetime.strptime(t, "%H:%M").time()
    else:
        tm = datetime.strptime(t, "%H:%M:%S").time()

    start_dt = datetime.combine(d, tm)
    end_dt = start_dt + timedelta(minutes=int(duration_min))
    return start_dt, end_dt


def _overlap_exists(cursor, *, start_dt, end_dt, buffer_min, where_sql, params):
    """
    Checks if there exists an existing (non-cancelled) flight that overlaps
    [start_dt-buffer, end_dt+buffer] for a given condition (plane / crew etc).

    Overlap definition:
      existing_start < padded_end AND existing_end > padded_start

    existing_end is computed using Airway.duration.
    """
    padded_start = start_dt - timedelta(minutes=buffer_min)
    padded_end = end_dt + timedelta(minutes=buffer_min)

    sql = f"""
        SELECT 1
        FROM Flight f
        JOIN Airway a
          ON a.origin_airport = f.origin_airport
         AND a.destination_airport = f.destination_airport
        WHERE LOWER(f.status) != 'cancelled'
          AND ({where_sql})
          AND TIMESTAMP(f.departure_date, f.departure_time) < %s
          AND DATE_ADD(TIMESTAMP(f.departure_date, f.departure_time), INTERVAL a.duration MINUTE) > %s
        LIMIT 1
    """
    cursor.execute(sql, tuple(params) + (padded_end, padded_start))
    return cursor.fetchone() is not None


def _fetch_step2_lists(cursor, *, is_long: bool, new_start_dt: datetime, new_end_dt: datetime):
    """
    Returns (planes, pilots, attendants) filtered by eligibility + availability window (with buffers).
    IMPORTANT: This is used both in Step 1 and Step 2 (re-render), so the data is consistent.
    """
    # ---------- Planes (availability filtered) ----------
    plane_padded_end = new_end_dt + timedelta(minutes=PLANE_BUFFER_MIN)
    plane_padded_start = new_start_dt - timedelta(minutes=PLANE_BUFFER_MIN)

    planes_sql = """
        SELECT p.plane_id, p.manufacturer
        FROM Plane p
    """
    if is_long:
        planes_sql += " JOIN BigPlane bp ON bp.plane_id = p.plane_id "

    planes_sql += """
        WHERE NOT EXISTS (
            SELECT 1
            FROM Flight f2
            JOIN Airway a2
              ON a2.origin_airport = f2.origin_airport
             AND a2.destination_airport = f2.destination_airport
            WHERE f2.plane_id = p.plane_id
              AND LOWER(f2.status) != 'cancelled'
              AND TIMESTAMP(f2.departure_date, f2.departure_time) < %s
              AND DATE_ADD(TIMESTAMP(f2.departure_date, f2.departure_time), INTERVAL a2.duration MINUTE) > %s
        )
        ORDER BY p.plane_id
    """
    cursor.execute(planes_sql, (plane_padded_end, plane_padded_start))
    planes = cursor.fetchall()

    # ---------- Crew (availability filtered) ----------
    crew_padded_end = new_end_dt + timedelta(minutes=CREW_BUFFER_MIN)
    crew_padded_start = new_start_dt - timedelta(minutes=CREW_BUFFER_MIN)

    if is_long:
        cursor.execute(
            """
            SELECT w.id, w.first_name, w.last_name
            FROM Pilot p
            JOIN AirCrew ac ON ac.id = p.id
            JOIN Worker w ON w.id = ac.id
            LEFT JOIN Manager m ON m.id = w.id
            WHERE ac.long_flight_training = 1
              AND m.id IS NULL
              AND NOT EXISTS (
                SELECT 1
                FROM FlightCrewPlacement fcp
                JOIN Flight f2 ON f2.flight_id = fcp.flight_id
                JOIN Airway a2
                  ON a2.origin_airport = f2.origin_airport
                 AND a2.destination_airport = f2.destination_airport
                WHERE fcp.id = w.id
                  AND LOWER(f2.status) != 'cancelled'
                  AND TIMESTAMP(f2.departure_date, f2.departure_time) < %s
                  AND DATE_ADD(TIMESTAMP(f2.departure_date, f2.departure_time), INTERVAL a2.duration MINUTE) > %s
              )
            ORDER BY w.id
            """,
            (crew_padded_end, crew_padded_start),
        )
        pilots = cursor.fetchall()

        cursor.execute(
            """
            SELECT w.id, w.first_name, w.last_name
            FROM FlightAttendant fa
            JOIN AirCrew ac ON ac.id = fa.id
            JOIN Worker w ON w.id = ac.id
            LEFT JOIN Manager m ON m.id = w.id
            WHERE ac.long_flight_training = 1
              AND m.id IS NULL
              AND NOT EXISTS (
                SELECT 1
                FROM FlightCrewPlacement fcp
                JOIN Flight f2 ON f2.flight_id = fcp.flight_id
                JOIN Airway a2
                  ON a2.origin_airport = f2.origin_airport
                 AND a2.destination_airport = f2.destination_airport
                WHERE fcp.id = w.id
                  AND LOWER(f2.status) != 'cancelled'
                  AND TIMESTAMP(f2.departure_date, f2.departure_time) < %s
                  AND DATE_ADD(TIMESTAMP(f2.departure_date, f2.departure_time), INTERVAL a2.duration MINUTE) > %s
              )
            ORDER BY w.id
            """,
            (crew_padded_end, crew_padded_start),
        )
        attendants = cursor.fetchall()
    else:
        cursor.execute(
            """
            SELECT w.id, w.first_name, w.last_name
            FROM Pilot p
            JOIN Worker w ON w.id = p.id
            LEFT JOIN Manager m ON m.id = w.id
            WHERE m.id IS NULL
              AND NOT EXISTS (
                SELECT 1
                FROM FlightCrewPlacement fcp
                JOIN Flight f2 ON f2.flight_id = fcp.flight_id
                JOIN Airway a2
                  ON a2.origin_airport = f2.origin_airport
                 AND a2.destination_airport = f2.destination_airport
                WHERE fcp.id = w.id
                  AND LOWER(f2.status) != 'cancelled'
                  AND TIMESTAMP(f2.departure_date, f2.departure_time) < %s
                  AND DATE_ADD(TIMESTAMP(f2.departure_date, f2.departure_time), INTERVAL a2.duration MINUTE) > %s
              )
            ORDER BY w.id
            """,
            (crew_padded_end, crew_padded_start),
        )
        pilots = cursor.fetchall()

        cursor.execute(
            """
            SELECT w.id, w.first_name, w.last_name
            FROM FlightAttendant fa
            JOIN Worker w ON w.id = fa.id
            LEFT JOIN Manager m ON m.id = w.id
            WHERE m.id IS NULL
              AND NOT EXISTS (
                SELECT 1
                FROM FlightCrewPlacement fcp
                JOIN Flight f2 ON f2.flight_id = fcp.flight_id
                JOIN Airway a2
                  ON a2.origin_airport = f2.origin_airport
                 AND a2.destination_airport = f2.destination_airport
                WHERE fcp.id = w.id
                  AND LOWER(f2.status) != 'cancelled'
                  AND TIMESTAMP(f2.departure_date, f2.departure_time) < %s
                  AND DATE_ADD(TIMESTAMP(f2.departure_date, f2.departure_time), INTERVAL a2.duration MINUTE) > %s
              )
            ORDER BY w.id
            """,
            (crew_padded_end, crew_padded_start),
        )
        attendants = cursor.fetchall()

    return planes, pilots, attendants


@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        tz = request.form.get("tz", type=int)
        password = request.form.get("password", "")

        if not tz or not password:
            return render_template("admin_login.html", error="Please enter ID and password.")

        from main import db_cur
        with db_cur() as cursor:
            cursor.execute(
                """
                SELECT w.id, w.first_name, w.last_name
                FROM Manager m
                JOIN Worker w ON w.id = m.id
                WHERE m.id=%s AND m.password=%s
                """,
                (tz, password),
            )
            manager = cursor.fetchone()

        if not manager:
            return render_template("admin_login.html", error="Invalid ID or password.")

        with db_cur() as cursor:
            cursor.execute("SELECT 1 FROM AirCrew WHERE id=%s", (manager["id"],))
            if cursor.fetchone():
                return render_template(
                    "admin_login.html",
                    error="Invalid role configuration: this ID is both Manager and AirCrew.",
                )

        session.clear()
        session["is_manager"] = True
        session["manager_id"] = manager["id"]
        session["manager_name"] = f'{manager["first_name"]} {manager["last_name"]}'.strip()
        return redirect("/admin/")

    return render_template("admin_login.html", error=None)


@admin_bp.route("/logout")
def admin_logout():
    session.clear()
    return redirect("/")


@admin_bp.route("/flights")
def admin_flights():
    guard = _require_admin()
    if guard:
        return guard

    origin = request.args.get("origin", "").strip()
    destination = request.args.get("destination", "").strip()
    dep_date = request.args.get("departure_date", "").strip()
    status = request.args.get("status", "").strip().lower()

    created = request.args.get("created", "").strip()  # ✅ success flag

    from main import db_cur
    query = """
        SELECT flight_id, origin_airport, destination_airport, departure_date, departure_time, status
        FROM Flight
        WHERE 1=1
    """
    params = []

    if origin:
        query += " AND origin_airport=%s"
        params.append(origin)
    if destination:
        query += " AND destination_airport=%s"
        params.append(destination)
    if dep_date:
        query += " AND departure_date=%s"
        params.append(dep_date)
    if status:
        query += " AND LOWER(status)=%s"
        params.append(status)

    query += " ORDER BY departure_date, departure_time"

    with db_cur() as cursor:
        cursor.execute(query, tuple(params))
        flights = cursor.fetchall()

    return render_template("admin_flights.html", flights=flights, created=created)


@admin_bp.route("/flights/new", methods=["GET", "POST"])
def admin_add_flight():
    guard = _require_admin()
    if guard:
        return guard

    from main import db_cur

    if request.method == "GET":
        return render_template("admin_add_flight.html", step=1, error=None, data=None)

    step = request.form.get("step", type=int, default=1)

    # =========================
    # STEP 1
    # =========================
    if step == 1:
        origin = request.form.get("origin", "").strip()
        destination = request.form.get("destination", "").strip()
        dep_date = request.form.get("departure_date", "").strip()
        dep_time = request.form.get("departure_time", "").strip()

        if not origin or not destination or not dep_date or not dep_time:
            return render_template("admin_add_flight.html", step=1, error="All fields are required.", data=None)

        with db_cur() as cursor:
            cursor.execute(
                """
                SELECT duration
                FROM Airway
                WHERE origin_airport=%s AND destination_airport=%s
                """,
                (origin, destination),
            )
            airway = cursor.fetchone()

        if not airway:
            return render_template("admin_add_flight.html", step=1, error="No airway exists for this route.", data=None)

        duration_min = airway["duration"]
        is_long = duration_min > 360

        pilots_needed = 3 if is_long else 2
        fa_needed = 6 if is_long else 3

        new_start_dt, new_end_dt = _flight_window(dep_date, dep_time, duration_min)

        with db_cur() as cursor:
            planes, pilots, attendants = _fetch_step2_lists(
                cursor, is_long=is_long, new_start_dt=new_start_dt, new_end_dt=new_end_dt
            )

        data = {
            "origin": origin,
            "destination": destination,
            "departure_date": dep_date,
            "departure_time": dep_time,
            "duration_min": duration_min,
            "is_long": is_long,
            "pilots_needed": pilots_needed,
            "fa_needed": fa_needed,
            "planes": planes,
            "pilots": pilots,
            "attendants": attendants,
        }

        return render_template("admin_add_flight.html", step=2, error=None, data=data)

    # =========================
    # STEP 2
    # =========================
    if step == 2:
        origin = request.form.get("origin")
        destination = request.form.get("destination")
        dep_date = request.form.get("departure_date")
        dep_time = request.form.get("departure_time")

        plane_id = request.form.get("plane_id", type=int)
        pilot_ids = request.form.getlist("pilot_ids")
        fa_ids = request.form.getlist("fa_ids")

        regular_price = request.form.get("regular_price", type=float)
        business_price = request.form.get("business_price", type=float)

        with db_cur() as cursor:
            cursor.execute(
                """
                SELECT duration
                FROM Airway
                WHERE origin_airport=%s AND destination_airport=%s
                """,
                (origin, destination),
            )
            airway = cursor.fetchone()

        if not airway:
            return render_template("admin_add_flight.html", step=1, error="No airway exists for this route.", data=None)

        duration_min = airway["duration"]
        is_long = duration_min > 360
        pilots_needed = 3 if is_long else 2
        fa_needed = 6 if is_long else 3

        new_start_dt, new_end_dt = _flight_window(dep_date, dep_time, duration_min)

        with db_cur() as cursor:
            planes, pilots, attendants = _fetch_step2_lists(
                cursor, is_long=is_long, new_start_dt=new_start_dt, new_end_dt=new_end_dt
            )

        data = {
            "origin": origin,
            "destination": destination,
            "departure_date": dep_date,
            "departure_time": dep_time,
            "duration_min": duration_min,
            "is_long": is_long,
            "pilots_needed": pilots_needed,
            "fa_needed": fa_needed,
            "planes": planes,
            "pilots": pilots,
            "attendants": attendants,
            "selected_plane_id": plane_id,
            "selected_pilot_ids": set(str(x) for x in pilot_ids),
            "selected_fa_ids": set(str(x) for x in fa_ids),
            "regular_price": regular_price,
            "business_price": business_price,
        }

        if not plane_id:
            return render_template("admin_add_flight.html", step=2, error="Plane is required.", data=data)

        if len(pilot_ids) != pilots_needed or len(fa_ids) != fa_needed:
            return render_template("admin_add_flight.html", step=2, error="Crew selection count is incorrect.", data=data)

        if not regular_price or regular_price <= 0:
            return render_template("admin_add_flight.html", step=2, error="Regular price is required.", data=data)

        with db_cur() as cursor:
            cursor.execute(
                """
                SELECT 1 FROM Class
                WHERE plane_id=%s AND class_type='Business'
                """,
                (plane_id,),
            )
            has_business = cursor.fetchone() is not None

        if has_business and (business_price is None or business_price <= 0):
            return render_template(
                "admin_add_flight.html",
                step=2,
                error="Business price is required for big planes.",
                data=data,
            )

        if not has_business:
            business_price = None
            data["business_price"] = None

        with db_cur() as cursor:
            for pid in pilot_ids:
                cursor.execute("SELECT 1 FROM Pilot WHERE id=%s", (pid,))
                if not cursor.fetchone():
                    return render_template("admin_add_flight.html", step=2, error=f"Worker {pid} is not a Pilot", data=data)

                cursor.execute("SELECT 1 FROM Manager WHERE id=%s", (pid,))
                if cursor.fetchone():
                    return render_template(
                        "admin_add_flight.html",
                        step=2,
                        error=f"Worker {pid} is a Manager and cannot be assigned as Pilot",
                        data=data,
                    )

            for fid in fa_ids:
                cursor.execute("SELECT 1 FROM FlightAttendant WHERE id=%s", (fid,))
                if not cursor.fetchone():
                    return render_template(
                        "admin_add_flight.html",
                        step=2,
                        error=f"Worker {fid} is not a Flight Attendant",
                        data=data,
                    )

                cursor.execute("SELECT 1 FROM Manager WHERE id=%s", (fid,))
                if cursor.fetchone():
                    return render_template(
                        "admin_add_flight.html",
                        step=2,
                        error=f"Worker {fid} is a Manager and cannot be assigned as Attendant",
                        data=data,
                    )

        with db_cur() as cursor:
            if _overlap_exists(
                cursor,
                start_dt=new_start_dt,
                end_dt=new_end_dt,
                buffer_min=PLANE_BUFFER_MIN,
                where_sql="f.plane_id = %s",
                params=(plane_id,),
            ):
                return render_template(
                    "admin_add_flight.html",
                    step=2,
                    error="Selected plane is not available at this time (overlap).",
                    data=data,
                )

            for pid in pilot_ids:
                if _overlap_exists(
                    cursor,
                    start_dt=new_start_dt,
                    end_dt=new_end_dt,
                    buffer_min=CREW_BUFFER_MIN,
                    where_sql="""
                        EXISTS (
                            SELECT 1
                            FROM FlightCrewPlacement fcp
                            WHERE fcp.flight_id = f.flight_id
                              AND fcp.id = %s
                        )
                    """,
                    params=(pid,),
                ):
                    return render_template(
                        "admin_add_flight.html",
                        step=2,
                        error=f"Pilot {pid} is not available at this time (overlap).",
                        data=data,
                    )

            for fid in fa_ids:
                if _overlap_exists(
                    cursor,
                    start_dt=new_start_dt,
                    end_dt=new_end_dt,
                    buffer_min=CREW_BUFFER_MIN,
                    where_sql="""
                        EXISTS (
                            SELECT 1
                            FROM FlightCrewPlacement fcp
                            WHERE fcp.flight_id = f.flight_id
                              AND fcp.id = %s
                        )
                    """,
                    params=(fid,),
                ):
                    return render_template(
                        "admin_add_flight.html",
                        step=2,
                        error=f"Flight attendant {fid} is not available at this time (overlap).",
                        data=data,
                    )

        # ✅ Transaction-safe create
        from main import db_cur
        try:
            with db_cur() as cursor:
                conn = cursor.connection
                conn.autocommit(False)

                cursor.execute(
                    """
                    INSERT INTO Flight (plane_id, origin_airport, destination_airport,
                                        departure_date, departure_time, status)
                    VALUES (%s, %s, %s, %s, %s, 'open')
                    """,
                    (plane_id, origin, destination, dep_date, dep_time),
                )
                cursor.execute("SELECT LAST_INSERT_ID() AS flight_id")
                flight_id = cursor.fetchone()["flight_id"]

                cursor.execute(
                    """
                    INSERT INTO FlightPricing (flight_id, class_type, price)
                    VALUES (%s, 'Regular', %s)
                    """,
                    (flight_id, regular_price),
                )

                if has_business:
                    cursor.execute(
                        """
                        INSERT INTO FlightPricing (flight_id, class_type, price)
                        VALUES (%s, 'Business', %s)
                        """,
                        (flight_id, business_price),
                    )

                crew_ids = [int(x) for x in pilot_ids] + [int(x) for x in fa_ids]
                cursor.executemany(
                    """
                    INSERT INTO FlightCrewPlacement (flight_id, id)
                    VALUES (%s, %s)
                    """,
                    [(flight_id, cid) for cid in crew_ids],
                )

                cursor.execute("SELECT seat_id FROM Seat WHERE plane_id=%s", (plane_id,))
                seat_ids = [r["seat_id"] for r in cursor.fetchall()]
                if seat_ids:
                    cursor.executemany(
                        """
                        INSERT INTO FlightSeat (flight_id, seat_id, status)
                        VALUES (%s, %s, 'available')
                        """,
                        [(flight_id, sid) for sid in seat_ids],
                    )

                conn.commit()
        except Exception:
            # rollback if anything failed
            try:
                with db_cur() as cursor:
                    cursor.connection.rollback()
            except Exception:
                pass
            return render_template(
                "admin_add_flight.html",
                step=2,
                error="Failed to create flight due to an internal error. Please try again.",
                data=data,
            )

        # ✅ success flag
        return redirect("/admin/flights?created=1")

    return render_template("admin_add_flight.html", step=1, error="Invalid step.", data=None)


@admin_bp.route("/flights/cancel/<int:flight_id>", methods=["GET", "POST"])
def admin_cancel_flight(flight_id):
    guard = _require_admin()
    if guard:
        return guard

    from main import db_cur
    with db_cur() as cursor:
        cursor.execute(
            """
            SELECT flight_id, departure_date, departure_time, status
            FROM Flight
            WHERE flight_id=%s
            """,
            (flight_id,),
        )
        flight = cursor.fetchone()

    if not flight:
        return "Flight not found", 404

    # ✅ Only allow cancellation for OPEN flights
    if request.method == "GET":
        return render_template("admin_cancel_flight.html", flight=flight, error=None)

    # POST - confirm cancel
    if str(flight.get("status", "")).lower() != "open":
        return render_template(
            "admin_cancel_flight.html",
            flight=flight,
            error="Only flights with status 'open' can be cancelled.",
        )

    dep_time = flight["departure_time"]
    if isinstance(dep_time, timedelta):
        dep_time = (datetime.min + dep_time).time()

    dep_dt = datetime.combine(flight["departure_date"], dep_time)
    now = datetime.now()
    hours_left = (dep_dt - now).total_seconds() / 3600

    if hours_left < 72:
        return render_template(
            "admin_cancel_flight.html",
            flight=flight,
            error="Cannot cancel less than 72 hours before departure.",
        )

    with db_cur() as cursor:
        cursor.execute("UPDATE Flight SET status='cancelled' WHERE flight_id=%s", (flight_id,))
        cursor.execute(
            """
            UPDATE FlightOrder
            SET status='system_cancelled',
                total_payment=0
            WHERE flight_id=%s
              AND LOWER(status) IN ('paid','active')
            """,
            (flight_id,),
        )
        cursor.execute(
            """
            UPDATE FlightSeat
            SET status='available'
            WHERE flight_id=%s
            """,
            (flight_id,),
        )

    return redirect("/admin/flights")


@admin_bp.route("/", methods=["GET"])
def admin_home():
    guard = _require_admin()
    if guard:
        return guard
    return render_template("admin_home.html")


@admin_bp.route("/reports", methods=["GET"])
def admin_reports():
    guard = _require_admin()
    if guard:
        return guard

    today = date.today()
    date_from = request.args.get("date_from") or today.replace(day=1).isoformat()
    date_to = request.args.get("date_to") or today.isoformat()

    report = request.args.get("report", "revenue_route")

    from main import db_cur
    data = []
    kpis = {}

    with db_cur() as cursor:
        if report == "revenue_route":
            cursor.execute(
                """
                SELECT
                    f.origin_airport,
                    f.destination_airport,
                    COUNT(*) AS orders_count,
                    ROUND(SUM(fo.total_payment), 2) AS revenue
                FROM FlightOrder fo
                JOIN Flight f ON f.flight_id = fo.flight_id
                WHERE fo.execution_date BETWEEN %s AND %s
                GROUP BY f.origin_airport, f.destination_airport
                ORDER BY revenue DESC
                """,
                (date_from, date_to),
            )
            data = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS orders_count,
                    ROUND(SUM(total_payment), 2) AS revenue
                FROM FlightOrder
                WHERE execution_date BETWEEN %s AND %s
                """,
                (date_from, date_to),
            )
            kpis = cursor.fetchone() or {}

        elif report == "occupancy_flight":
            cursor.execute(
                """
                SELECT
                    f.flight_id,
                    f.origin_airport,
                    f.destination_airport,
                    f.departure_date,
                    f.departure_time,
                    LOWER(f.status) AS flight_status,
                    SUM(CASE WHEN LOWER(fs.status)='booked' THEN 1 ELSE 0 END) AS sold_seats,
                    COUNT(*) AS total_seats,
                    ROUND(100 * SUM(CASE WHEN LOWER(fs.status)='booked' THEN 1 ELSE 0 END) / COUNT(*), 1) AS occupancy_percent
                FROM Flight f
                JOIN FlightSeat fs ON fs.flight_id = f.flight_id
                WHERE f.departure_date BETWEEN %s AND %s
                GROUP BY f.flight_id, f.origin_airport, f.destination_airport, f.departure_date, f.departure_time, f.status
                ORDER BY f.departure_date, f.departure_time
                """,
                (date_from, date_to),
            )
            data = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    ROUND(AVG(100 * sold.cnt / totals.cnt), 1) AS avg_occupancy_percent
                FROM
                    (SELECT flight_id, SUM(CASE WHEN LOWER(status)='booked' THEN 1 ELSE 0 END) AS cnt
                     FROM FlightSeat GROUP BY flight_id) sold
                JOIN
                    (SELECT flight_id, COUNT(*) AS cnt FROM FlightSeat GROUP BY flight_id) totals
                ON totals.flight_id = sold.flight_id
                """
            )
            kpis = cursor.fetchone() or {}

        elif report == "cancellations":
            cursor.execute(
                """
                SELECT
                    status,
                    COUNT(*) AS orders_count,
                    ROUND(SUM(total_payment), 2) AS amount_sum
                FROM FlightOrder
                WHERE execution_date BETWEEN %s AND %s
                  AND LOWER(status) IN ('customer_cancelled','system_cancelled')
                GROUP BY status
                ORDER BY orders_count DESC
                """,
                (date_from, date_to),
            )
            data = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS customer_cancelled_count,
                    ROUND(SUM(total_payment), 2) AS cancellation_fees_sum
                FROM FlightOrder
                WHERE execution_date BETWEEN %s AND %s
                  AND LOWER(status)='customer_cancelled'
                """,
                (date_from, date_to),
            )
            kpis = cursor.fetchone() or {}

        elif report == "crew_utilization":
            cursor.execute(
                """
                SELECT
                    w.id,
                    CONCAT(w.first_name, ' ', w.last_name) AS full_name,
                    COUNT(*) AS flights_assigned
                FROM FlightCrewPlacement fcp
                JOIN Worker w ON w.id = fcp.id
                JOIN Flight f ON f.flight_id = fcp.flight_id
                WHERE f.departure_date BETWEEN %s AND %s
                GROUP BY w.id, w.first_name, w.last_name
                ORDER BY flights_assigned DESC, w.id
                """,
                (date_from, date_to),
            )
            data = cursor.fetchall()

            cursor.execute(
                """
                SELECT COUNT(*) AS total_assignments
                FROM FlightCrewPlacement fcp
                JOIN Flight f ON f.flight_id = fcp.flight_id
                WHERE f.departure_date BETWEEN %s AND %s
                """,
                (date_from, date_to),
            )
            kpis = cursor.fetchone() or {}

        else:
            report = "revenue_route"
            return redirect(f"/admin/reports?report={report}&date_from={date_from}&date_to={date_to}")

    return render_template(
        "admin_reports.html",
        report=report,
        date_from=date_from,
        date_to=date_to,
        data=data,
        kpis=kpis,
    )
