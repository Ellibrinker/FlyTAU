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

    # Date filter (still shown in UI; queries below match the updated SQL you provided)
    today = date.today()
    date_from = request.args.get("date_from") or today.replace(day=1).isoformat()
    date_to = request.args.get("date_to") or today.isoformat()

    report = request.args.get("report", "avg_occupancy_completed")

    from main import db_cur

    data = []
    kpis = {}
    meta = {
        "title": "",
        "subtitle": "",
        "columns": [],  # list of {"key": "...", "label": "..."}
        "notes": [],
    }

    def _set_table(columns):
        meta["columns"] = columns

    def _set_title(title, subtitle=""):
        meta["title"] = title
        meta["subtitle"] = subtitle

    with db_cur() as cursor:

        # =========================================================
        # 1) Average occupancy of flights that actually took place
        #    (exclude cancelled flights, only past flights)
        # =========================================================
        if report == "avg_occupancy_completed":
            _set_title(
                "Average Occupancy (Flights That Took Place)",
                "Average occupancy percent for non-cancelled flights that already departed.",
            )
            _set_table([
                {"key": "avg_occupancy_percent", "label": "Avg Occupancy (%)"},
            ])
            meta["notes"] = [
                "Occupancy is calculated per flight as: occupied seats / total seats in FlightSeat.",
                "Occupied seat = any FlightSeat.status other than 'available'.",
                "Includes only flights with departure_date < CURDATE() and status != cancelled.",
            ]

            query = """
                SELECT ROUND(AVG(t.occ_pct), 2) AS avg_occupancy_percent
                FROM (
                  SELECT
                    fs.flight_id,
                    SUM(CASE WHEN LOWER(fs.status) <> 'available' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS occ_pct
                  FROM FlightSeat fs
                  GROUP BY fs.flight_id
                ) AS t
                JOIN Flight AS f ON f.flight_id = t.flight_id
                WHERE LOWER(f.status) <> 'cancelled'
                  AND f.departure_date < CURDATE();
            """
            cursor.execute(query)
            row = cursor.fetchone()
            val = row["avg_occupancy_percent"] if row else None
            data = [{"avg_occupancy_percent": f"{val}%" if val is not None else "No data"}]

        # =========================================================
        # 2) Revenue by plane size, manufacturer and class
        #    - paid               -> 100%
        #    - customer_cancelled -> 5%
        #    - system_cancelled   -> 0%
        #    - cancelled flights excluded
        # =========================================================
        elif report == "revenue_plane_size_manu_class":
            _set_title(
                "Revenue by Plane Size / Manufacturer / Class",
                "Revenue breakdown by aircraft size, manufacturer and ticket class.",
            )
            _set_table([
                {"key": "plane_size", "label": "Plane Size"},
                {"key": "manufacturer", "label": "Manufacturer"},
                {"key": "class_type", "label": "Class"},
                {"key": "revenue", "label": "Revenue"},
            ])
            meta["notes"] = [
                "Revenue is derived from FlightPricing.price per sold seat (via OrderItem -> FlightSeat -> Seat.class_type).",
                "customer_cancelled contributes 5% of the ticket price; system_cancelled contributes 0%.",
                "Cancelled flights are excluded.",
            ]

            query = """
                SELECT
                  CASE WHEN bp.plane_id IS NOT NULL THEN 'Big' ELSE 'Small' END AS plane_size,
                  p.manufacturer AS manufacturer,
                  s.class_type AS class_type,
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
                GROUP BY plane_size, manufacturer, class_type
                ORDER BY plane_size, manufacturer, class_type;
            """
            cursor.execute(query)
            data = cursor.fetchall()

            total_revenue = sum((row.get("revenue") or 0) for row in data)
            kpis = {"total_revenue": round(total_revenue, 2)}

        # =========================================================
        # 3) Accumulated flight hours per worker
        #    - split short/long flights (threshold: 360 minutes)
        #    - exclude cancelled flights
        # =========================================================
        elif report == "crew_hours_long_short":
            _set_title(
                "Crew Flight Hours (Short vs Long)",
                "Total accumulated flight minutes per worker, split by short/long flights (<= 360 vs > 360).",
            )
            _set_table([
                {"key": "worker_id", "label": "Worker ID"},
                {"key": "full_name", "label": "Name"},
                {"key": "role", "label": "Role"},
                {"key": "short_minutes", "label": "Short Minutes"},
                {"key": "long_minutes", "label": "Long Minutes"},
                {"key": "total_minutes", "label": "Total Minutes"},
            ])
            meta["notes"] = [
                "Flight duration is taken from Airway.duration (minutes) by matching Flight origin/destination.",
                "Short flight: duration <= 360 minutes; Long flight: duration > 360 minutes.",
                "Cancelled flights are excluded.",
            ]

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
            cursor.execute(query)
            data = cursor.fetchall()

        # =========================================================
        # 4) Purchase cancellation rate by month
        #    - includes customer_cancelled AND system_cancelled
        # =========================================================
        elif report == "purchase_cancel_rate_monthly":
            _set_title(
                "Purchase Cancellation Rate (Monthly)",
                "Cancellation rate of purchases/orders by month.",
            )
            _set_table([
                {"key": "year", "label": "Year"},
                {"key": "month", "label": "Month"},
                {"key": "cancellation_rate_percentage", "label": "Cancel Rate (%)"},
            ])
            meta["notes"] = [
                "Cancellation statuses: customer_cancelled and system_cancelled.",
                "Grouping is by execution_date month.",
            ]

            query = """
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
            """
            cursor.execute(query)
            data = cursor.fetchall()
            for row in data:
                row["cancellation_rate_percentage"] = f"{row['cancellation_rate_percentage']}%"

        # =========================================================
        # 5) Monthly plane activity summary
        # =========================================================
        elif report == "monthly_plane_activity":
            _set_title(
                "Monthly Plane Activity Summary",
                "Per aircraft: performed flights, cancelled flights, utilization % (assume 30 days), dominant route.",
            )
            _set_table([
                {"key": "plane_id", "label": "Plane ID"},
                {"key": "manufacturer", "label": "Manufacturer"},
                {"key": "flight_month", "label": "Month"},
                {"key": "performed_flights", "label": "Performed"},
                {"key": "cancelled_flights", "label": "Cancelled"},
                {"key": "dominant_route", "label": "Dominant Route"},
                {"key": "utilization_percentage", "label": "Utilization (%)"},
            ])
            meta["notes"] = [
                "Utilization is calculated as (performed_flights / 30) * 100.",
                "Dominant route is calculated from performed flights only.",
            ]

            query = """
                SELECT
                  ms.plane_id,
                  ms.manufacturer,
                  ms.flight_month,
                  ms.performed_flights,
                  ms.cancelled_flights,
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
                  ROUND((ms.performed_flights / 30.0) * 100, 1) AS utilization_percentage
                FROM (
                  SELECT
                    p.plane_id,
                    p.manufacturer,
                    DATE_FORMAT(f.departure_date, '%Y-%m') AS flight_month,
                    SUM(CASE WHEN LOWER(f.status) <> 'cancelled' THEN 1 ELSE 0 END) AS performed_flights,
                    SUM(CASE WHEN LOWER(f.status) = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_flights
                  FROM Plane p
                  JOIN Flight f ON f.plane_id = p.plane_id
                  GROUP BY p.plane_id, p.manufacturer, flight_month
                ) AS ms
                ORDER BY ms.flight_month DESC, ms.performed_flights DESC;
            """
            cursor.execute(query)
            data = cursor.fetchall()
            for row in data:
                row["utilization_percentage"] = f"{row['utilization_percentage']}%"

        else:
            return redirect(
                f"/admin/reports?report=avg_occupancy_completed&date_from={date_from}&date_to={date_to}"
            )

    return render_template(
        "admin_reports.html",
        report=report,
        date_from=date_from,
        date_to=date_to,
        data=data,
        kpis=kpis,
        meta=meta,
    )

