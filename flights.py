from flask import Blueprint, render_template, request, redirect, session
from datetime import datetime, date

flights_bp = Blueprint("flights", __name__)

@flights_bp.route("/search_flights", methods=["GET"])
def search_flights():
    origin = request.args.get("origin")
    destination = request.args.get("destination")
    departure_date = request.args.get("departure_date")

    # כניסה ראשונה לדף - בלי שגיאות
    if origin is None and destination is None and departure_date is None:
        return render_template("search_flights.html", errors=[], flights=[], departure_date="")

    errors = []

    if not origin:
        errors.append("Origin field is required")
    if not destination:
        errors.append("Destination field is required")
    if origin and destination and origin == destination:
        errors.append("Origin and destination cannot be the same")

    try:
        if departure_date:
            datetime.strptime(departure_date, "%Y-%m-%d")
        else:
            errors.append("Departure date is required")
    except (ValueError, TypeError):
        errors.append("Invalid date")

    if errors:
        return render_template(
            "search_flights.html",
            errors=errors,
            flights=[],
            origin=origin,
            destination=destination,
            departure_date=departure_date
        )

    from main import db_cur

    with db_cur() as cursor:
        cursor.execute("""
            SELECT 1
            FROM Airway
            WHERE origin_airport=%s
              AND destination_airport=%s
        """, (origin, destination))
        if not cursor.fetchone():
            errors.append("No flights exist between these airports")
            return render_template(
                "search_flights.html",
                errors=errors,
                flights=[],
                origin=origin,
                destination=destination,
                departure_date=departure_date
            )

    flights = get_open_flights(origin, destination, departure_date)

    if not flights:
        errors.append("No open flights found on this date")

    return render_template(
        "search_flights.html",
        flights=flights,
        errors=errors,
        origin=origin,
        destination=destination,
        departure_date=departure_date
    )


def get_open_flights(origin, destination, departure_date):
    from main import db_cur

    query = """
        SELECT
            f.flight_id,
            f.origin_airport,
            f.destination_airport,
            f.departure_date,
            f.departure_time,
            reg.price AS regular_price,
            bus.price AS business_price
        FROM Flight f
        LEFT JOIN FlightPricing reg
          ON reg.flight_id = f.flight_id AND reg.class_type='Regular'
        LEFT JOIN FlightPricing bus
          ON bus.flight_id = f.flight_id AND bus.class_type='Business'
        WHERE f.origin_airport=%s
          AND f.destination_airport=%s
          AND f.departure_date=%s
          AND LOWER(f.status) = 'open'
    """
    with db_cur() as cursor:
        cursor.execute(query, (origin, destination, departure_date))
        return cursor.fetchall()


@flights_bp.route("/select_seats", methods=["GET", "POST"])
def select_seats():
    from main import db_cur

    flight_id = request.args.get("flight_id", type=int) if request.method == "GET" else request.form.get("flight_id", type=int)
    if not flight_id:
        return redirect("/search_flights")

    # 1) פרטי טיסה + מחירים (Regular/Business)
    with db_cur() as cursor:
        cursor.execute("""
            SELECT
              f.flight_id,
              f.origin_airport,
              f.destination_airport,
              f.departure_date,
              f.departure_time,
              f.plane_id,
              reg.price AS regular_price,
              bus.price AS business_price
            FROM Flight f
            LEFT JOIN FlightPricing reg ON reg.flight_id=f.flight_id AND reg.class_type='Regular'
            LEFT JOIN FlightPricing bus ON bus.flight_id=f.flight_id AND bus.class_type='Business'
            WHERE f.flight_id=%s
        """, (flight_id,))
        flight = cursor.fetchone()

    if not flight:
        return render_template("select_seats.html", error="Flight not found", flight=None, seats=[], class_type="Regular", grid_meta={"rows":0,"cols":0})

    # איזה class_type מציגים כרגע
    class_type = request.args.get("class_type", "Regular")
    if class_type not in ("Regular", "Business"):
        class_type = "Regular"

    # אם אין Business מחיר בכלל, לא מאפשרים Business
    if class_type == "Business" and not flight["business_price"]:
        class_type = "Regular"

    # 2) אם זו בקשת POST = אישור הזמנה
    if request.method == "POST":
        # טוענים מושבים כדי שנוכל להציג את הדף עם הודעת שגיאה
        seats, grid_meta = _get_seats_and_grid(flight_id, flight["plane_id"], class_type)

        # חסימת מנהלים מרכישה (גם אם הגיעו לעמוד)
        if session.get("is_manager"):
            return render_template(
                "select_seats.html",
                flight=flight,
                seats=seats,
                class_type=class_type,
                grid_meta=grid_meta,
                error="Managers are not allowed to purchase tickets."
            )

        selected_ids = request.form.getlist("flight_seat_id")
        guest_email = request.form.get("guest_email", "").strip()

        # אימייל להזמנה: מחובר -> מהסשן, אחרת מהטופס
        email = session.get("user_email") or guest_email
        if not email:
            # להחזיר לדף עם שגיאה
            seats, grid_meta = _get_seats_and_grid(flight_id, flight["plane_id"], class_type)
            return render_template(
                "select_seats.html",
                flight=flight,
                seats=seats,
                class_type=class_type,
                grid_meta=grid_meta,
                error="Please enter an email to continue as a guest."
            )

        if not selected_ids:
            seats, grid_meta = _get_seats_and_grid(flight_id, flight["plane_id"], class_type)
            return render_template(
                "select_seats.html",
                flight=flight,
                seats=seats,
                class_type=class_type,
                grid_meta=grid_meta,
                error="Please select at least one seat."
            )

        # מבטיחים שהמושבים עדיין available ושייכים למחלקה הנוכחית
        with db_cur() as cursor:
            format_strings = ",".join(["%s"] * len(selected_ids))
            cursor.execute(f"""
                SELECT fs.flight_seat_id, fs.status, s.class_type
                FROM FlightSeat fs
                JOIN Seat s ON s.seat_id = fs.seat_id
                WHERE fs.flight_id=%s AND fs.flight_seat_id IN ({format_strings})
            """, (flight_id, *selected_ids))
            rows = cursor.fetchall()

        if len(rows) != len(selected_ids):
            return redirect(f"/select_seats?flight_id={flight_id}&class_type={class_type}")

        for r in rows:
            if str(r["status"]).lower() != "available" or r["class_type"] != class_type:
                return redirect(f"/select_seats?flight_id={flight_id}&class_type={class_type}")

        # מחיר לפי מחלקה
        price_per_seat = flight["regular_price"] if class_type == "Regular" else flight["business_price"]
        total_payment = float(price_per_seat) * len(selected_ids)

        # יוצרים הזמנה + פריטים + מעדכנים מושבים
        with db_cur() as cursor:
            # חשוב: האורח חייב להופיע גם ב-Customer לפי הסכמה שלך (FlightOrder.email FK -> Customer.email)
            # אם האורח לא קיים, ניצור Customer מינימלי.
            cursor.execute("SELECT email FROM Customer WHERE email=%s", (email,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO Customer (email, first_name, last_name) VALUES (%s, %s, %s)",
                    (email, "Guest", "")
                )

            cursor.execute("""
                INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment)
                VALUES (%s, %s, %s, %s, %s)
            """, (flight_id, email, date.today(), "paid", total_payment))

            cursor.execute("SELECT LAST_INSERT_ID() AS order_id")
            order_id = cursor.fetchone()["order_id"]

            # OrderItem לכל מושב
            cursor.executemany(
                "INSERT INTO OrderItem (order_id, flight_seat_id) VALUES (%s, %s)",
                [(order_id, fsid) for fsid in selected_ids]
            )

            # עדכון מושבים ל-booked
            cursor.execute(
                f"UPDATE FlightSeat SET status='booked' WHERE flight_id=%s AND flight_seat_id IN ({format_strings})",
                (flight_id, *selected_ids)
            )

        # מעבר לדף “כרטיסים/אישור”
        return redirect(f"/order_success?order_id={order_id}&email={email}")

    # 3) GET: להביא מושבים ולהציג
    seats, grid_meta = _get_seats_and_grid(flight_id, flight["plane_id"], class_type)

    return render_template(
        "select_seats.html",
        flight=flight,
        seats=seats,
        class_type=class_type,
        grid_meta=grid_meta,
        error=None
    )


def _get_seats_and_grid(flight_id, plane_id, class_type):
    from main import db_cur

    # אם אין FlightSeat לטיסה — ניצור לפי כל מושבי המטוס
    with db_cur() as cursor:
        cursor.execute("SELECT COUNT(*) AS cnt FROM FlightSeat WHERE flight_id=%s", (flight_id,))
        if cursor.fetchone()["cnt"] == 0:
            cursor.execute("SELECT seat_id FROM Seat WHERE plane_id=%s", (plane_id,))
            seat_ids = [r["seat_id"] for r in cursor.fetchall()]
            if seat_ids:
                cursor.executemany(
                    "INSERT INTO FlightSeat (flight_id, seat_id, status) VALUES (%s, %s, 'available')",
                    [(flight_id, sid) for sid in seat_ids]
                )

    with db_cur() as cursor:
        cursor.execute("""
            SELECT rows_number, columns_number
            FROM Class
            WHERE plane_id=%s AND class_type=%s
        """, (plane_id, class_type))
        meta = cursor.fetchone() or {"rows_number": 0, "columns_number": 0}

        cursor.execute("""
            SELECT
              fs.flight_seat_id,
              fs.status,
              s.row_num,
              s.column_number
            FROM FlightSeat fs
            JOIN Seat s ON s.seat_id = fs.seat_id
            WHERE fs.flight_id=%s AND s.class_type=%s
            ORDER BY s.row_num, s.column_number
        """, (flight_id, class_type))
        seats = cursor.fetchall()

    return seats, {"rows": meta["rows_number"], "cols": meta["columns_number"]}