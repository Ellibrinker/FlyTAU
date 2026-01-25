from flask import Blueprint, render_template, request, redirect, session
from datetime import datetime, date, timedelta

flights_bp = Blueprint("flights", __name__)


@flights_bp.route("/search_flights", methods=["GET"])
def search_flights():
    '''
    מנהל את דף חיפוש הטיסות לפי מוצא יעד ותאריך (אופציונלי), בודק האם קיימות טיסות רלוונטיות ומציג אותן 
    '''
    origin = (request.args.get("origin") or "").strip()
    destination = (request.args.get("destination") or "").strip()
    departure_date = (request.args.get("departure_date") or "").strip()  # אופציונלי

    if not origin and not destination and not departure_date:
        return render_template(
            "search_flights.html",
            errors=[],
            flights=[],
            origin="",
            destination="",
            departure_date=""
        )

    errors = []

    if not origin:
        errors.append("Origin field is required")
    if not destination:
        errors.append("Destination field is required")
    if origin and destination and origin == destination:
        errors.append("Origin and destination cannot be the same")

    if departure_date:
        try:
            datetime.strptime(departure_date, "%Y-%m-%d")
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

    flights = get_bookable_flights(origin, destination, departure_date)

    if not flights:
        errors.append(
            "No flights available for booking on this route"
            + (" on this date" if departure_date else "")
        )

    return render_template(
        "search_flights.html",
        flights=flights,
        errors=errors,
        origin=origin,
        destination=destination,
        departure_date=departure_date
    )


def get_bookable_flights(origin, destination, departure_date=None):
    '''
    מחזירה טיסות מהן ניתן להזמין
    ממיינת לפי טיסה עתידית לא מבוטלת, ושקיים בה לפחות מושב אחד שזמין לרכישה
    אם הוזן תאריך ספציפי, הוא יציג את הטיסות בתאריךזה. אם לא, יוצגו כל הטיסות העתידיות בין שדות המקור והיעד שמולאו
    '''
    from main import db_cur

    base_query = """
        SELECT
            f.flight_id,
            f.origin_airport,
            f.destination_airport,
            f.departure_date,
            f.departure_time,
            reg.price AS regular_price,
            bus.price AS business_price,
            (SELECT COUNT(*)
             FROM FlightSeat fs
             WHERE fs.flight_id = f.flight_id
               AND LOWER(fs.status) = 'available'
            ) AS available_seats
        FROM Flight f
        LEFT JOIN FlightPricing reg
          ON reg.flight_id = f.flight_id AND reg.class_type='Regular'
        LEFT JOIN FlightPricing bus
          ON bus.flight_id = f.flight_id AND bus.class_type='Business'
        WHERE f.origin_airport=%s
          AND f.destination_airport=%s
          AND LOWER(f.status) <> 'cancelled'
          AND TIMESTAMP(f.departure_date, f.departure_time) > NOW()
          AND EXISTS (
              SELECT 1
              FROM FlightSeat fs2
              WHERE fs2.flight_id = f.flight_id
                AND LOWER(fs2.status) = 'available'
          )
    """

    params = [origin, destination]

    # ✅ אם הוזן תאריך -> מוסיפים תנאי
    if departure_date:
        base_query += " AND f.departure_date=%s"
        params.append(departure_date)

    base_query += " ORDER BY f.departure_date, f.departure_time"

    with db_cur() as cursor:
        cursor.execute(base_query, tuple(params))
        return cursor.fetchall()


@flights_bp.route("/select_seats", methods=["GET", "POST"])
def select_seats():
    '''
    ניהול תהליך בחירת המושבים והשלמת ההזמנה
    בGET- מוודאים שהטיסה קיימץ, עתידית ולא מבוטלת
    בודק זמינות של מושבים 
    טוען את מפת המושבים התפוסים והפנויים, מסווגים למחלקות
    מונע ממשתמש מנהל לרכוש כרטיסים

    POST- קולט את המושבים שנבחרו על ידי הלקוח
    בודק את פרטי האורח
    מחשב מחיר סופי למושבים
    פותח הזמנה, מעדכן את מסד הנתונים במושבים שנרכשו ובפרטי הלקוח
    '''
    from main import db_cur

    flight_id = (
        request.args.get("flight_id", type=int)
        if request.method == "GET"
        else request.form.get("flight_id", type=int)
    )
    if not flight_id:
        return redirect("/search_flights")

    with db_cur() as cursor:
        cursor.execute(
            """
            SELECT
              f.flight_id,
              f.origin_airport,
              f.destination_airport,
              f.departure_date,
              f.departure_time,
              f.status,
              f.plane_id,
              reg.price AS regular_price,
              bus.price AS business_price
            FROM Flight f
            LEFT JOIN FlightPricing reg ON reg.flight_id=f.flight_id AND reg.class_type='Regular'
            LEFT JOIN FlightPricing bus ON bus.flight_id=f.flight_id AND bus.class_type='Business'
            WHERE f.flight_id=%s
            """,
            (flight_id,),
        )
        flight = cursor.fetchone()

    if not flight:
        return render_template(
            "select_seats.html",
            error="Flight not found",
            flight=None,
            seats_by_class={},
            grid_by_class={},
        )

    if str(flight.get("status", "")).lower() == "cancelled":
        return render_template(
            "select_seats.html",
            flight=flight,
            seats_by_class={},
            grid_by_class={},
            error="This flight is cancelled.",
        )

    dep_time = flight["departure_time"]
    if isinstance(dep_time, timedelta):
        dep_time = (datetime.min + dep_time).time()

    dep_dt = datetime.combine(flight["departure_date"], dep_time)
    if dep_dt <= datetime.now():
        return render_template(
            "select_seats.html",
            flight=flight,
            seats_by_class={},
            grid_by_class={},
            error="This flight has already departed.",
        )

    with db_cur() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM FlightSeat
            WHERE flight_id=%s AND LOWER(status)='available'
            LIMIT 1
            """,
            (flight_id,),
        )
        has_any_available = cursor.fetchone() is not None

    if not has_any_available:
        return render_template(
            "select_seats.html",
            flight=flight,
            seats_by_class={},
            grid_by_class={},
            error="This flight is fully booked.",
        )

    seats_by_class, grid_by_class = _get_seats_and_grids_by_class(
        flight_id, flight["plane_id"]
    )

    if session.get("is_manager"):
        return render_template(
            "select_seats.html",
            flight=flight,
            seats_by_class=seats_by_class,
            grid_by_class=grid_by_class,
            error="Managers are not allowed to purchase tickets.",
        )

    if request.method == "POST":
        selected_ids = request.form.getlist("flight_seat_id")

        # logged-in user OR guest email
        guest_email = (request.form.get("guest_email") or "").strip().lower()
        email = (session.get("user_email") or guest_email or "").strip().lower()

        if not email:
            return render_template(
                "select_seats.html",
                flight=flight,
                seats_by_class=seats_by_class,
                grid_by_class=grid_by_class,
                error="Please enter an email to continue as a guest.",
            )

        if not selected_ids:
            return render_template(
                "select_seats.html",
                flight=flight,
                seats_by_class=seats_by_class,
                grid_by_class=grid_by_class,
                error="Please select at least one seat.",
            )

        with db_cur() as cursor:
            fmt = ",".join(["%s"] * len(selected_ids))
            cursor.execute(
                f"""
                SELECT fs.flight_seat_id, fs.status, s.class_type, s.plane_id
                FROM FlightSeat fs
                JOIN Seat s ON s.seat_id = fs.seat_id
                WHERE fs.flight_id=%s AND fs.flight_seat_id IN ({fmt})
                """,
                (flight_id, *selected_ids),
            )
            rows = cursor.fetchall()

        if len(rows) != len(selected_ids):
            return redirect(f"/select_seats?flight_id={flight_id}")

        reg_price = flight["regular_price"]
        bus_price = flight["business_price"]  # may be None

        total_payment = 0.0
        for r in rows:
            if str(r["status"]).lower() != "available":
                return redirect(f"/select_seats?flight_id={flight_id}")
            if int(r["plane_id"]) != int(flight["plane_id"]):
                return redirect(f"/select_seats?flight_id={flight_id}")

            ct = r["class_type"]
            if ct == "Regular":
                if reg_price is None:
                    return redirect(f"/select_seats?flight_id={flight_id}")
                total_payment += float(reg_price)
            elif ct == "Business":
                if bus_price is None:
                    return redirect(f"/select_seats?flight_id={flight_id}")
                total_payment += float(bus_price)
            else:
                return redirect(f"/select_seats?flight_id={flight_id}")

        is_logged_in = bool(session.get("user_email"))

        guest_full_name = (request.form.get("guest_full_name") or "").strip()
        guest_phones = request.form.getlist("guest_phone[]")  # from modal

        clean_phones = []
        seen = set()
        for p in guest_phones:
            p = (p or "").strip()
            if not p or p in seen:
                continue
            seen.add(p)
            clean_phones.append(p)

        if not is_logged_in:
            if not guest_full_name:
                return render_template(
                    "select_seats.html",
                    flight=flight,
                    seats_by_class=seats_by_class,
                    grid_by_class=grid_by_class,
                    error="Please enter your full name.",
                )
            if len(clean_phones) == 0:
                return render_template(
                    "select_seats.html",
                    flight=flight,
                    seats_by_class=seats_by_class,
                    grid_by_class=grid_by_class,
                    error="Please enter at least one phone number.",
                )
            if any(not is_valid_phone(p) for p in clean_phones):
                return render_template(
                    "select_seats.html",
                    flight=flight,
                    seats_by_class=seats_by_class,
                    grid_by_class=grid_by_class,
                    error="Invalid phone number format. Use digits only (8–15), optionally starting with +.",
                )

        g_first, g_last = "Guest", ""
        if guest_full_name:
            parts = guest_full_name.split(" ", 1)
            g_first = parts[0]
            g_last = parts[1] if len(parts) > 1 else ""

        with db_cur() as cursor:
            # Does customer exist?
            cursor.execute(
                "SELECT email, first_name, last_name FROM Customer WHERE email=%s",
                (email,),
            )
            customer = cursor.fetchone()

            if not customer:
                if is_logged_in:
                    return render_template(
                        "select_seats.html",
                        flight=flight,
                        seats_by_class=seats_by_class,
                        grid_by_class=grid_by_class,
                        error="Account data is missing. Please log out and log in again, or contact support.",
                    )
                else:
                    cursor.execute(
                        "INSERT INTO Customer (email, first_name, last_name) VALUES (%s, %s, %s)",
                        (email, g_first, g_last),
                    )
            else:
                # If guest: optionally upgrade "Guest" name to actual provided name (one-time cleanup)
                if not is_logged_in and guest_full_name:
                    cur_fn = (customer.get("first_name") or "").strip()
                    cur_ln = (customer.get("last_name") or "").strip()
                    if (cur_fn.lower() == "guest" and not cur_ln) or (
                        not cur_fn and not cur_ln
                    ):
                        cursor.execute(
                            "UPDATE Customer SET first_name=%s, last_name=%s WHERE email=%s",
                            (g_first, g_last, email),
                        )

            if not is_logged_in:
                for phone in clean_phones:
                    cursor.execute(
                        "INSERT IGNORE INTO CustomerPhone (email, phone_number) VALUES (%s, %s)",
                        (email, phone),
                    )

            cursor.execute(
                """
                INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (flight_id, email, date.today(), "paid", total_payment),
            )

            cursor.execute("SELECT LAST_INSERT_ID() AS order_id")
            order_id = cursor.fetchone()["order_id"]

            cursor.executemany(
                "INSERT INTO OrderItem (order_id, flight_seat_id) VALUES (%s, %s)",
                [(order_id, fsid) for fsid in selected_ids],
            )

            cursor.execute(
                f"UPDATE FlightSeat SET status='booked' WHERE flight_id=%s AND flight_seat_id IN ({fmt})",
                (flight_id, *selected_ids),
            )

        return redirect(f"/order_success?order_id={order_id}&email={email}")

    return render_template(
        "select_seats.html",
        flight=flight,
        seats_by_class=seats_by_class,
        grid_by_class=grid_by_class,
        error=None,
    )



def _get_seats_and_grids_by_class(flight_id, plane_id):
    '''
    פונקציה הבונה את מפת המושבים למטוס הספציפי, בחלוקה למחלקה רגילה ועסקים (אם קיימת)
    '''
    from main import db_cur

    with db_cur() as cursor:
        cursor.execute(
            """
            DELETE fs
            FROM FlightSeat fs
            JOIN Seat s ON s.seat_id = fs.seat_id
            WHERE fs.flight_id=%s AND s.plane_id<>%s
            """,
            (flight_id, plane_id),
        )

    with db_cur() as cursor:
        cursor.execute("SELECT COUNT(*) AS cnt FROM FlightSeat WHERE flight_id=%s", (flight_id,))
        if cursor.fetchone()["cnt"] == 0:
            cursor.execute("SELECT seat_id FROM Seat WHERE plane_id=%s", (plane_id,))
            seat_ids = [r["seat_id"] for r in cursor.fetchall()]
            if seat_ids:
                cursor.executemany(
                    "INSERT INTO FlightSeat (flight_id, seat_id, status) VALUES (%s, %s, 'available')",
                    [(flight_id, sid) for sid in seat_ids],
                )

    seats_by_class = {}
    grid_by_class = {}

    for class_type in ("Regular", "Business"):
        with db_cur() as cursor:
            cursor.execute(
                """
                SELECT rows_number, columns_number
                FROM Class
                WHERE plane_id=%s AND class_type=%s
                """,
                (plane_id, class_type),
            )
            meta = cursor.fetchone()

            cursor.execute(
                """
                SELECT
                  fs.flight_seat_id,
                  fs.status,
                  s.row_num,
                  s.column_number,
                  s.class_type
                FROM FlightSeat fs
                JOIN Seat s ON s.seat_id = fs.seat_id
                WHERE fs.flight_id=%s
                  AND s.class_type=%s
                  AND s.plane_id=%s
                ORDER BY s.row_num, s.column_number
                """,
                (flight_id, class_type, plane_id),
            )
            seats = cursor.fetchall()

        if seats:
            seats_by_class[class_type] = seats
            grid_by_class[class_type] = {
                "rows": meta["rows_number"] if meta else 0,
                "cols": meta["columns_number"] if meta else 6,
            }

    return seats_by_class, grid_by_class
