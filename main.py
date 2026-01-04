from flask import Flask, render_template, redirect, session, request
import mysql.connector
from contextlib import contextmanager
from datetime import date

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

@app.route("/select_seats")
def select_seats():
    flight_id = request.args.get("flight_id")
    return render_template("select_seats.html", flight_id=flight_id)

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

from flights import flights_bp
app.register_blueprint(flights_bp)


if __name__ == "__main__":
    app.run(debug=True)
