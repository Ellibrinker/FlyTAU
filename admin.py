from flask import Blueprint, render_template, request, redirect, session
from datetime import datetime, date

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def _require_admin():
    if not session.get("is_manager"):
        return redirect("/admin/login")   # שימי לב: זה ה-route שלך בתוך ה-blueprint
    return None

@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        tz = request.form.get("tz", type=int)
        password = request.form.get("password", "")

        if not tz or not password:
            return render_template("admin_login.html", error="Please enter ID and password.")

        from main import db_cur
        with db_cur() as cursor:
            cursor.execute("""
                SELECT w.id, w.first_name, w.last_name
                FROM Manager m
                JOIN Worker w ON w.id = m.id
                WHERE m.id=%s AND m.password=%s
            """, (tz, password))
            manager = cursor.fetchone()

        if not manager:
            return render_template("admin_login.html", error="Invalid ID or password.")

        session.clear()
        session["is_manager"] = True
        session["manager_id"] = manager["id"]
        session["manager_name"] = f'{manager["first_name"]} {manager["last_name"]}'.strip()
        return redirect("/admin/flights")

    return render_template("admin_login.html", error=None)


@admin_bp.route("/logout")
def admin_logout():
    session.clear()
    return redirect("/")

@admin_bp.route("/flights")
def admin_flights():
    guard = _require_admin()
    if guard: return guard

    origin = request.args.get("origin", "").strip()
    destination = request.args.get("destination", "").strip()
    dep_date = request.args.get("departure_date", "").strip()
    status = request.args.get("status", "").strip().lower()

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

    return render_template("admin_flights.html", flights=flights)


@admin_bp.route("/flights/new", methods=["GET", "POST"])
def admin_add_flight():
    guard = _require_admin()
    if guard: return guard

    from main import db_cur

    if request.method == "GET":
        return render_template("admin_add_flight.html", step=1, error=None, data=None)

    # POST
    step = request.form.get("step", type=int, default=1)

    # ---- STEP 1: תאריך/שעה/מקור/יעד -> משך טיסה -> קצר/ארוך -> מטוסים+צוות כשיר
    if step == 1:
        origin = request.form.get("origin", "").strip()
        destination = request.form.get("destination", "").strip()
        dep_date = request.form.get("departure_date", "").strip()
        dep_time = request.form.get("departure_time", "").strip()

        if not origin or not destination or not dep_date or not dep_time:
            return render_template("admin_add_flight.html", step=1, error="All fields are required.", data=None)

        # duration from Airway
        with db_cur() as cursor:
            cursor.execute("""
                SELECT duration
                FROM Airway
                WHERE origin_airport=%s AND destination_airport=%s
            """, (origin, destination))
            airway = cursor.fetchone()

        if not airway:
            return render_template("admin_add_flight.html", step=1, error="No airway exists for this route.", data=None)

        duration_min = airway["duration"]
        is_long = duration_min > 360  # מעל 6 שעות

        # planes
        with db_cur() as cursor:
            if is_long:
                cursor.execute("""
                    SELECT p.plane_id, p.manufacturer
                    FROM Plane p
                    JOIN BigPlane bp ON bp.plane_id = p.plane_id
                    ORDER BY p.plane_id
                """)
            else:
                cursor.execute("""
                    SELECT p.plane_id, p.manufacturer
                    FROM Plane p
                    ORDER BY p.plane_id
                """)
            planes = cursor.fetchall()

        if not planes:
            return render_template("admin_add_flight.html", step=1, error="No suitable planes found.", data=None)

        # crew eligibility
        pilots_needed = 3 if is_long else 2
        fa_needed = 6 if is_long else 3

        with db_cur() as cursor:
            if is_long:
                cursor.execute("""
                    SELECT w.id, w.first_name, w.last_name
                    FROM Pilot p
                    JOIN AirCrew ac ON ac.id=p.id
                    JOIN Worker w ON w.id=ac.id
                    WHERE ac.long_flight_training=1
                    ORDER BY w.id
                """)
                pilots = cursor.fetchall()

                cursor.execute("""
                    SELECT w.id, w.first_name, w.last_name
                    FROM FlightAttendant fa
                    JOIN AirCrew ac ON ac.id=fa.id
                    JOIN Worker w ON w.id=ac.id
                    WHERE ac.long_flight_training=1
                    ORDER BY w.id
                """)
                attendants = cursor.fetchall()
            else:
                cursor.execute("""
                    SELECT w.id, w.first_name, w.last_name
                    FROM Pilot p
                    JOIN Worker w ON w.id=p.id
                    ORDER BY w.id
                """)
                pilots = cursor.fetchall()

                cursor.execute("""
                    SELECT w.id, w.first_name, w.last_name
                    FROM FlightAttendant fa
                    JOIN Worker w ON w.id=fa.id
                    ORDER BY w.id
                """)
                attendants = cursor.fetchall()

        if len(pilots) < pilots_needed or len(attendants) < fa_needed:
            return render_template(
                "admin_add_flight.html",
                step=1,
                error="Not enough qualified crew for this flight type.",
                data=None
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
            "attendants": attendants
        }
        return render_template("admin_add_flight.html", step=2, error=None, data=data)

    # ---- STEP 2: בחירת מטוס + צוות + תמחור -> יצירה בפועל
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

        # שוב duration + long/short
        with db_cur() as cursor:
            cursor.execute("""
                SELECT duration
                FROM Airway
                WHERE origin_airport=%s AND destination_airport=%s
            """, (origin, destination))
            airway = cursor.fetchone()
        if not airway:
            return render_template("admin_add_flight.html", step=1, error="No airway exists for this route.", data=None)

        duration_min = airway["duration"]
        is_long = duration_min > 360
        pilots_needed = 3 if is_long else 2
        fa_needed = 6 if is_long else 3

        if not plane_id:
            return render_template("admin_add_flight.html", step=1, error="Plane is required.", data=None)

        if len(pilot_ids) != pilots_needed or len(fa_ids) != fa_needed:
            return render_template("admin_add_flight.html", step=1, error="Crew selection count is incorrect.", data=None)

        if not regular_price or regular_price <= 0:
            return render_template("admin_add_flight.html", step=1, error="Regular price is required.", data=None)

        # האם למטוס יש Business class?
        with db_cur() as cursor:
            cursor.execute("""
                SELECT 1 FROM Class
                WHERE plane_id=%s AND class_type='Business'
            """, (plane_id,))
            has_business = cursor.fetchone() is not None

        if has_business and (business_price is None or business_price <= 0):
            return render_template("admin_add_flight.html", step=1, error="Business price is required for big planes.", data=None)

        if (not has_business):
            business_price = None

        # יצירת טיסה + pricing + crew + flightseat
        from main import db_cur
        with db_cur() as cursor:
            # 1) Flight
            cursor.execute("""
                INSERT INTO Flight (plane_id, origin_airport, destination_airport, departure_date, departure_time, status)
                VALUES (%s, %s, %s, %s, %s, 'open')
            """, (plane_id, origin, destination, dep_date, dep_time))
            cursor.execute("SELECT LAST_INSERT_ID() AS flight_id")
            flight_id = cursor.fetchone()["flight_id"]

            # 2) Pricing
            cursor.execute("""
                INSERT INTO FlightPricing (flight_id, class_type, price)
                VALUES (%s, 'Regular', %s)
            """, (flight_id, regular_price))

            if has_business:
                cursor.execute("""
                    INSERT INTO FlightPricing (flight_id, class_type, price)
                    VALUES (%s, 'Business', %s)
                """, (flight_id, business_price))

            # 3) Crew placement
            crew_ids = [int(x) for x in pilot_ids] + [int(x) for x in fa_ids]
            cursor.executemany("""
                INSERT INTO FlightCrewPlacement (flight_id, id)
                VALUES (%s, %s)
            """, [(flight_id, cid) for cid in crew_ids])

            # 4) Create FlightSeat for all plane seats
            cursor.execute("SELECT seat_id FROM Seat WHERE plane_id=%s", (plane_id,))
            seat_ids = [r["seat_id"] for r in cursor.fetchall()]
            if seat_ids:
                cursor.executemany("""
                    INSERT INTO FlightSeat (flight_id, seat_id, status)
                    VALUES (%s, %s, 'available')
                """, [(flight_id, sid) for sid in seat_ids])

        return redirect("/admin/flights")

@admin_bp.route("/flights/cancel/<int:flight_id>", methods=["GET", "POST"])
def admin_cancel_flight(flight_id):
    guard = _require_admin()
    if guard: return guard

    from main import db_cur
    with db_cur() as cursor:
        cursor.execute("""
            SELECT flight_id, departure_date, departure_time, status
            FROM Flight
            WHERE flight_id=%s
        """, (flight_id,))
        flight = cursor.fetchone()

    if not flight:
        return "Flight not found", 404

    # זמן יציאה
    dep_dt = datetime.combine(flight["departure_date"], flight["departure_time"])

    if request.method == "GET":
        return render_template("admin_cancel_flight.html", flight=flight)

    # POST - confirm cancel
    now = datetime.now()
    hours_left = (dep_dt - now).total_seconds() / 3600

    if hours_left < 72:
        return render_template("admin_cancel_flight.html", flight=flight,
                               error="Cannot cancel less than 72 hours before departure.")

    with db_cur() as cursor:
        # 1) cancel flight
        cursor.execute("UPDATE Flight SET status='cancelled' WHERE flight_id=%s", (flight_id,))

        # 2) full refund for active orders
        cursor.execute("""
            UPDATE FlightOrder
            SET status='system_cancelled',
                total_payment=0
            WHERE flight_id=%s
              AND LOWER(status) IN ('paid','active')
        """, (flight_id,))

        # 3) optional: release seats (לא חובה כי הטיסה בוטלה, אבל לא מזיק)
        cursor.execute("""
            UPDATE FlightSeat
            SET status='available'
            WHERE flight_id=%s
        """, (flight_id,))

    return redirect("/admin/flights")
