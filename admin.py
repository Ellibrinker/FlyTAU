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

    # Date filter (default: current month)
    today = date.today()
    date_from = request.args.get("date_from") or today.replace(day=1).isoformat()
    date_to = request.args.get("date_to") or today.isoformat()

    # Report selector (aligned with the real requirements)
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
        # 1) Average occupancy of flights that took place
        #    (ממוצע תפוסת טיסות שהתקיימו)
        # =========================================================
        if report == "avg_occupancy_completed":
            _set_title(
                "Average Occupancy (Completed Flights)",
                "Average occupancy percent for flights that actually took place (exclude cancelled)."
            )
            _set_table([
                {"key": "total_avg_occupancy", "label": "avg_occupancy (%)"}
            ])
            meta["notes"] = [
                "The calculation is based on the ratio of occupied seats to the total seats available in the FlightSeat table.",
                "Flights with a 'cancelled' status are excluded from the calculation.",
                "The report includes only flights with a departure date that has already passed"
            ]
		elif report == "flight_occupancy_stats":
            _set_title(
                "Average Flight Occupancy",
                "Calculates the occupancy percentage for all completed and non-cancelled flights."
            )
            _set_table([
                {"key": "avg_occupancy_percent", "label": "Average Occupancy (%)"}
            ])

            query = """
                SELECT 
                    ROUND(AVG(stats.occupancy), 2) AS avg_occupancy_percent
                FROM Flight f
                JOIN (
                    SELECT 
                        flight_id, 
                        (COUNT(CASE WHEN status != 'available' THEN 1 END) * 100.0 / COUNT(*)) AS occupancy
                    FROM FlightSeat
                    GROUP BY flight_id
                ) AS stats ON f.flight_id = stats.flight_id
                WHERE f.status != 'cancelled'
                  AND f.departure_date < CURDATE()
                  AND f.departure_date BETWEEN %s AND %s;
            """
            cursor.execute(query, (date_from, date_to))
            row = cursor.fetchone()

            # המרה של התוצאה הבודדת למבנה שהטבלה מצפה לו
            data = []
            if row and row[0] is not None:
                data.append({"avg_occupancy_percent": f"{row[0]}%"})
            else:
                data.append({"avg_occupancy_percent": "No data available"})

        # =========================================================
        # 2) Revenue by plane size, manufacturer, and class
        #    (הכנסות בחתך גודל מטוס, יצרנית מטוס ומחלקה)
        # =========================================================
    elif report == "revenue_plane_size_manu_class":
            _set_title(
                "Revenue by Plane Size / Manufacturer / Class",
                "Revenue breakdown by aircraft size, manufacturer and ticket class."
            )
            _set_table([
                {"key": "plane_size", "label": "Plane Size (Big/Small)"},
                {"key": "manufacturer", "label": "Manufacturer"},
                {"key": "class_type", "label": "Class"},
                {"key": "revenue", "label": "Revenue"},
            ])
            meta["notes"] = [
                "Revenue is calculated per sold seat based on flight pricing.",
                "Customer-cancelled orders contribute 5% of the ticket price.",
                "Cancelled flights are excluded from the report."
            ]

            cursor.execute("""
                SELECT
                    CASE
            		    WHEN bp.plane_id IS NOT NULL THEN "Big"
            		    ELSE "Small"
	                END AS plane_size,
                    p.manufacturer AS manufacturer,
                    fp.class_type AS class_type,
                    ROUND(
		                SUM(
		                CASE
			                WHEN fo.status = "customer cancelled" THEN fp.price*0.05
			                ELSE fp.price
		                END),2)
                        AS revenue
                FROM flight f
                    JOIN plane p ON f.plane_id = p.plane_id
                    LEFT JOIN bigplane bp ON f.plane_id = bp.plane_id
                    JOIN flightseat fs ON f.flight_id = fs.flight_id
                    JOIN seat s ON fs.seat_id = s.seat_id
                    JOIN orderitem oi ON fs.flight_seat_id = oi.flight_seat_id
                    JOIN flightorder fo ON oi.order_id = fo.order_id
                    JOIN flightpricing fp ON f.flight_id = fp.flight_id AND s.class_type = fp.class_type
                WHERE f.status != "cancelled"
                    AND f.departure_date BETWEEN %s AND %s
                GROUP BY 
                    plane_size,
                    manufacturer,
                    class_type;
             """, (date_from, date_to))
            data = cursor.fetchall()
            total_revenue = sum(row["revenue"] for row in data)
            kpis = {"total_revenue": total_revenue}

        # =========================================================
        # 3) Accumulated flight hours per worker, split long/short
        #    (שעות טיסה מצטברות של העובדים, בהפרדה לטיסות ארוכות/קצרות)
        # =========================================================
        elif report == "crew_hours_long_short":
            _set_title(
                "Crew Flight Hours (Long vs Short)",
                "Total accumulated flight minutes/hours per worker, split by long/short flights."
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
                "TODO: Define long flight threshold (currently: duration > 360 minutes).",
                "TODO: Join via FlightCrewPlacement + Flight + Airway.duration.",
                "TODO: Exclude cancelled flights."
            ]

            sql_query = """
            SELECT 
                w.id AS worker_id,
                CASE 
                        WHEN p.id IS NOT NULL THEN 'Pilot'
                        WHEN fa.id IS NOT NULL THEN 'Flight Attendant'
                        ELSE 'AirCrew'
                END AS role,
                CONCAT(w.first_name, ' ', w.last_name) AS full_name,
                COALESCE(SUM(CASE WHEN aw.duration <= 360 THEN aw.duration ELSE 0 END), 0) AS short_flights_hours,
                COALESCE(SUM(CASE WHEN aw.duration > 360 THEN aw.duration ELSE 0 END), 0) AS long_flights_hours,
                COALESCE(SUM(aw.duration), 0) AS total_flight_hours
            FROM Worker w
            JOIN AirCrew ac ON w.id = ac.id
            JOIN FlightCrewPlacement fcp ON ac.id = fcp.id
            JOIN Flight f ON fcp.flight_id = f.flight_id
            JOIN Airway aw ON f.origin_airport = aw.origin_airport 
               AND f.destination_airport = aw.destination_airport
            WHERE f.departure_date BETWEEN %s AND %s
            GROUP BY w.id, w.first_name, w.last_name
            ORDER BY total_flight_hours DESC;
            """    
            cursor.execute(sql_query, (date_from, date_to))
            data = [
                {
                    "worker_id": row[0],
                    "full_name": row[1],
                    "role": row[2],
                    "short_minutes": row[3],
                    "long_minutes": row[4],
                    "total_minutes": row[5]
                }
                for row in cursor.fetchall()
            ]
        # =========================================================
        # 4) Purchase cancellation rate by month
        #    (שיעור ביטולי רכישות לפי חודש)
        # =========================================================
        elif report == "purchase_cancel_rate_monthly":
            _set_title(
                "Purchase Cancellation Rate (Monthly)",
                "Cancellation rate of purchases/orders by month."
            )
            _set_table([
                {"key": "year", "label": "Year"},
                {"key": "month", "label": "Month"},
                {"key": "cancellation_rate_percentage", "label": "Cancel Rate %"},
            ])
            meta["notes"] = [
                "Cancelled orders include statuses: customer cancelled.",
                 "Using execution_date for month/year grouping."
            ]

            cursor.execute("""
                SELECT
                    YEAR(fo.execution_date) AS year,
                    MONTHNAME(fo.execution_date) AS month,
                    CONCAT(
                        ROUND(
                            SUM(CASE WHEN fo.status = 'customer cancelled' THEN 1 ELSE 0 END) * 100 / COUNT(*),
                            2
                        ),
                        '%'
                    ) AS cancellation_rate_percentage
                FROM flightorder fo
                WHERE fo.execution_date BETWEEN %s AND %s
                GROUP BY 
                    YEAR(fo.execution_date), 
                    MONTH(fo.execution_date),
                    MONTHNAME(fo.execution_date)
                ORDER BY 
                    year ASC, 
                    MONTH(fo.execution_date) ASC;
            """, (date_from, date_to))
            data = cursor.fetchall()

        # =========================================================
        # 5) Monthly activity summary per plane
        #    (סיכום פעילות חודשית לכל מטוס: #performed, #cancelled, utilization%, dominant route)
        # =========================================================
        elif report == "monthly_plane_activity":
            _set_title(
                "Monthly Plane Activity Summary",
                "Per aircraft: performed flights, cancelled flights, utilization % (assume 30 days), dominant route."
            )
            _set_table([
                {"key": "plane_id", "label": "Plane ID"},
                {"key": "manufacturer", "label": "Manufacturer"},
                {"key": "month", "label": "Month"},
                {"key": "total_flights", "label": "Total Flights"},
                {"key": "cancelled_flights", "label": "Cancelled"},
                {"key": "top_route", "label": "Dominant Route"},
                {"key": "utilization", "label": "Utilization (%)"},
            ])
            meta["notes"] = [
                "TODO: Define utilization calculation clearly (e.g., total flight time / (30*24*60)).",
                "TODO: Dominant route = most frequent origin-destination pair for that plane in month.",
                "TODO: Separate performed vs cancelled flights."
            ]

            query = """
                WITH MonthlyStats AS (
                    SELECT 
                        p.plane_id,
                        p.manufacturer,
                        DATE_FORMAT(f.departure_date, '%%Y-%%m') AS flight_month,
                        COUNT(*) AS total_flights,
                        SUM(CASE WHEN f.status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_count
                    FROM Plane p
                    JOIN Flight f ON p.plane_id = f.plane_id
                    WHERE f.departure_date BETWEEN %s AND %s
                    GROUP BY p.plane_id, p.manufacturer, flight_month
                )
                SELECT 
                    ms.plane_id,
                    ms.manufacturer,
                    ms.flight_month,
                    ms.total_flights,
                    ms.cancelled_count,
                    (SELECT CONCAT(f3.origin_airport, '-', f3.destination_airport)
                     FROM Flight f3
                     WHERE f3.plane_id = ms.plane_id 
                       AND DATE_FORMAT(f3.departure_date, '%%Y-%%m') = ms.flight_month
                     GROUP BY f3.origin_airport, f3.destination_airport
                     ORDER BY COUNT(*) DESC 
                     LIMIT 1) AS top_route
                FROM MonthlyStats ms
                ORDER BY ms.flight_month DESC, ms.total_flights DESC;
            """
            cursor.execute(query, (date_from, date_to))
            data = []
            for row in cursor.fetchall():
                total = row[3]
                cancelled = row[4]
                actual_flights = total - cancelled
                utilization_pct = round((actual_flights / 30.0) * 100, 1)
                
                data.append({
                    "plane_id": row[0],
                    "manufacturer": row[1],
                    "month": row[2],
                    "total_flights": total,
                    "cancelled_flights": cancelled,
                    "top_route": row[5] if row[5] else "N/A",
                    "utilization": f"{utilization_pct}%"
                })

        else:
            # fallback to a valid report key
            return redirect(f"/admin/reports?report=avg_occupancy_completed&date_from={date_from}&date_to={date_to}")

    return render_template(
        "admin_reports.html",
        report=report,
        date_from=date_from,
        date_to=date_to,
        data=data,
        kpis=kpis,
        meta=meta,
    )

