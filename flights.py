from flask import Blueprint, render_template, request
from datetime import datetime

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
        SELECT flight_id, origin_airport, destination_airport, departure_date, departure_time
        FROM Flight
        WHERE origin_airport=%s
          AND destination_airport=%s
          AND departure_date=%s
          AND LOWER(status) = 'open'
    """
    with db_cur() as cursor:
        cursor.execute(query, (origin, destination, departure_date))
        return cursor.fetchall()
