from flask import Flask, render_template, redirect, session, request
import mysql.connector
from contextlib import contextmanager
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = 'flytau123'


@contextmanager
def db_cur():
    mydb = None
    cursor = None
    try:
        mydb = mysql.connector.connect(
            host="ellibrinker.mysql.pythonanywhere-services.com",
            user="ellibrinker",
            password="elli2003",
            database="ellibrinker$flytau",
            autocommit=True
        )
        cursor = mydb.cursor(dictionary=True)
        yield cursor
    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()


@app.route('/')
def homepage():
    return render_template('homepage.html', user_name=session.get('user_name'))


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        user_email = request.form.get('email')
        user_password = request.form.get('password')

        with db_cur() as cursor:
            sql = """
                SELECT c.first_name, rc.email AS email
                FROM Customer c
                JOIN RegisteredCustomer rc ON c.email = rc.email
                WHERE rc.email = %s AND rc.password = %s
            """
            cursor.execute(sql, (user_email, user_password))
            user = cursor.fetchone()

        if user:
            session['user_email'] = user['email']
            session['user_name'] = user['first_name']
            return redirect('/')
        else:
            return render_template("login.html", error="Invalid email or password")

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def sign_up_page():
    if request.method == 'POST':
        full_name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phones = request.form.getlist('phone')

        name_parts = full_name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        with db_cur() as cursor:
            sql_customer = "INSERT INTO Customer (email, first_name, last_name) VALUES (%s, %s, %s)"
            cursor.execute(sql_customer, (email, first_name, last_name))

            sql_reg = """
                INSERT INTO RegisteredCustomer (email, password, registration_date)
                VALUES (%s, %s, %s)
            """
            cursor.execute(sql_reg, (email, password, date.today()))

            sql_phones = "INSERT INTO CustomerPhone (email, phone_number) VALUES (%s, %s)"
            for phone in phones:
                if phone.strip():
                    cursor.execute(sql_phones, (email, phone))

        return redirect('/login')

    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route("/order_success")
def order_success():
    order_id = request.args.get("order_id", type=int)
    email = request.args.get("email", "")

    from main import db_cur
    with db_cur() as cursor:
        cursor.execute("""
            SELECT fo.order_id, fo.flight_id, fo.email, fo.execution_date, fo.status, fo.total_payment
            FROM FlightOrder fo
            WHERE fo.order_id=%s AND fo.email=%s
        """, (order_id, email))
        order = cursor.fetchone()

        cursor.execute("""
            SELECT s.row_num, s.column_number
            FROM OrderItem oi
            JOIN FlightSeat fs ON fs.flight_seat_id = oi.flight_seat_id
            JOIN Seat s ON s.seat_id = fs.seat_id
            WHERE oi.order_id=%s
            ORDER BY s.row_num, s.column_number
        """, (order_id,))
        seats = cursor.fetchall()

    return render_template("order_success.html", order=order, seats=seats)

@app.route("/my_orders")
def my_orders():
    email = session.get("user_email")
    if not email:
        return redirect("/login")

    status_filter = request.args.get("status", "").strip()  # paid/done/customer_cancelled/system_cancelled או ריק

    with db_cur() as cursor:
        # האם המשתמש רשום?
        cursor.execute("SELECT 1 FROM RegisteredCustomer WHERE email=%s", (email,))
        if not cursor.fetchone():
            # אם בעתיד יהיה מצב של "מחובר כאורח" - כאן נחסום
            return redirect("/")

        base_query = """
            SELECT
                fo.order_id,
                fo.flight_id,
                fo.email,
                fo.execution_date,
                fo.status,
                fo.total_payment,
                f.origin_airport,
                f.destination_airport,
                f.departure_date,
                f.departure_time,
                TIMESTAMP(f.departure_date, f.departure_time) AS departure_dt
            FROM FlightOrder fo
            JOIN Flight f ON f.flight_id = fo.flight_id
            WHERE fo.email=%s
        """
        params = [email]

        if status_filter:
            base_query += " AND fo.status=%s"
            params.append(status_filter)

        base_query += " ORDER BY departure_dt DESC"

        cursor.execute(base_query, tuple(params))
        orders = cursor.fetchall()

        # נביא מושבים לכל הזמנה
        order_ids = [o["order_id"] for o in orders]
        seats_by_order = {oid: [] for oid in order_ids}
        if order_ids:
            fmt = ",".join(["%s"] * len(order_ids))
            cursor.execute(f"""
                SELECT
                    oi.order_id,
                    s.row_num,
                    s.column_number,
                    s.class_type
                FROM OrderItem oi
                JOIN FlightSeat fs ON fs.flight_seat_id = oi.flight_seat_id
                JOIN Seat s ON s.seat_id = fs.seat_id
                WHERE oi.order_id IN ({fmt})
                ORDER BY oi.order_id, s.row_num, s.column_number
            """, tuple(order_ids))
            for r in cursor.fetchall():
                seats_by_order[r["order_id"]].append(r)

    return render_template(
        "my_orders.html",
        orders=orders,
        seats_by_order=seats_by_order,
        status_filter=status_filter,
        now=datetime.now()
    )

@app.route("/order_lookup", methods=["GET", "POST"])
def order_lookup():
    if request.method == "GET":
        return render_template("order_lookup.html", error=None, order=None, seats=[])

    email = request.form.get("email", "").strip()
    order_id = request.form.get("order_id", type=int)

    if not email or not order_id:
        return render_template("order_lookup.html", error="Please enter both email and order code.", order=None, seats=[])

    with db_cur() as cursor:
        cursor.execute("""
            SELECT
                fo.order_id, fo.flight_id, fo.email, fo.execution_date, fo.status, fo.total_payment,
                f.origin_airport, f.destination_airport, f.departure_date, f.departure_time,
                TIMESTAMP(f.departure_date, f.departure_time) AS departure_dt
            FROM FlightOrder fo
            JOIN Flight f ON f.flight_id = fo.flight_id
            WHERE fo.order_id=%s AND fo.email=%s
        """, (order_id, email))
        order = cursor.fetchone()

        if not order:
            return render_template("order_lookup.html", error="Order not found.", order=None, seats=[])

        cursor.execute("""
            SELECT s.row_num, s.column_number, s.class_type
            FROM OrderItem oi
            JOIN FlightSeat fs ON fs.flight_seat_id = oi.flight_seat_id
            JOIN Seat s ON s.seat_id = fs.seat_id
            WHERE oi.order_id=%s
            ORDER BY s.row_num, s.column_number
        """, (order_id,))
        seats = cursor.fetchall()

    return render_template("order_lookup.html", error=None, order=order, seats=seats, now=datetime.now())


@app.route("/cancel_order", methods=["POST"])
def cancel_order():
    order_id = request.form.get("order_id", type=int)

    # מי מבטל? מחובר -> email מהסשן, אורח -> מהטופס
    email = session.get("user_email") or request.form.get("email", "").strip()
    if not order_id or not email:
        return redirect("/")

    with db_cur() as cursor:
        cursor.execute("""
            SELECT
                fo.order_id, fo.email, fo.status, fo.total_payment,
                f.departure_date, f.departure_time,
                TIMESTAMP(f.departure_date, f.departure_time) AS departure_dt
            FROM FlightOrder fo
            JOIN Flight f ON f.flight_id = fo.flight_id
            WHERE fo.order_id=%s AND fo.email=%s
        """, (order_id, email))
        order = cursor.fetchone()

        if not order:
            return redirect("/order_lookup")

        # אפשר לבטל רק הזמנה פעילה
        if order["status"] != "paid":
            return redirect(f"/order_success?order_id={order_id}&email={email}")

        departure_dt = order["departure_dt"]
        now = datetime.now()

        # 36 שעות לפני
        hours_left = (departure_dt - now).total_seconds() / 3600
        if hours_left < 36:
            # לא מאפשרים ביטול
            # נחזיר למסך המתאים עם הודעה
            if session.get("user_email"):
                return redirect("/my_orders")
            return redirect("/order_lookup")

        # דמי ביטול: 5% מסך העלות
        fee = float(order["total_payment"]) * 0.05

        # 1) משחררים את כל המושבים של ההזמנה
        cursor.execute("""
            UPDATE FlightSeat fs
            JOIN OrderItem oi ON oi.flight_seat_id = fs.flight_seat_id
            SET fs.status='available'
            WHERE oi.order_id=%s
        """, (order_id,))

        # 2) מעדכנים סטטוס + total_payment לדמי ביטול (הלקוח "שילם" רק 5%)
        cursor.execute("""
            UPDATE FlightOrder
            SET status='customer_cancelled', total_payment=%s
            WHERE order_id=%s
        """, (fee, order_id))

    # אחרי ביטול נחזור למסך
    if session.get("user_email"):
        return redirect("/my_orders")
    return redirect("/order_lookup")


from flights import flights_bp
app.register_blueprint(flights_bp)

from admin import admin_bp
app.register_blueprint(admin_bp, url_prefix="/admin")

if __name__ == "__main__":
    app.run(debug=True)
