# ✈️ Flight Management & Booking System

A web-based flight management and booking system developed as part of academic coursework in **Database Systems Design** and **Information Systems Engineering**.

The system supports operational flight management, customer bookings, and a dedicated administrative interface for managers, including management reports for business analysis and decision-making.

🔗 **Live system:**
👉 [https://ellibrinker.pythonanywhere.com/](https://ellibrinker.pythonanywhere.com/)

---

## 📌 Project Overview

The project is divided into two main academic components:

1. **Database Systems Design** – relational schema design, SQL queries, constraints, and analytical reports.
2. **Information Systems Engineering** – web application development, user interfaces, role-based access, and management dashboards.

---

## 🛠️ Technologies Used

* **Backend:** Python, Flask
* **Database:** MySQL
* **Frontend:** HTML, CSS (Jinja templates)
* **Deployment:** PythonAnywhere

---

## 👥 User Roles

### 🧑 Customer

* Browse available flights
* Make flight bookings
* Select seats
* View personal orders

### 👨‍💼 Manager (Admin)

* Secure login
* Add new flights (with resource availability checks)
* Cancel flights (policy-based cancellation)
* View all flights
* Access management reports for analysis

---

## 📊 Management Reports (Admin)

The system includes a dedicated **Management Reports Interface**, aligned with the business requirements of the course.

The interface is designed to support the following reports:

* **Average occupancy of completed flights**
* **Revenue by aircraft size, manufacturer, and class**
* **Accumulated flight hours per employee (long vs. short flights)**
* **Purchase cancellation rate by month**
* **Monthly activity summary per aircraft**, including:

  * Number of performed flights
  * Number of cancelled flights
  * Utilization percentage (assumed 30 days/month)
  * Dominant origin–destination route

> 📎 Note:
> The interface is implemented as part of the **Information Systems Engineering** component.
> The full SQL queries, explanations, sample outputs, and visualizations are provided separately as part of the **Database Systems Design** submission.

---

## 🔐 Access & Security

* Role-based access control with strict separation between customers and managers.

---

## 📁 Repository Structure

```project/
├── static/                 # CSS and static assets
├── templates/              # HTML templates (Jinja)
│   ├── admin_*.html        # Admin / managerial pages
│   └── customer-*.html     # Customer-facing pages
├── admin.py                # Admin (manager) logic
├── flights.py              # Customer flight & booking logic
├── main.py                 # Application entry point
├── schema.sql               # Database schema (tables, constraints)
├── seed.sql                 # Initial data
└── reports_queries.sql      # Management reports SQL queries
```

---

## ⚙️ Business Rules & Edge Cases

The system explicitly enforces real-world airline business rules, including:

* **Role-based access & separation**
  - Managers are automatically redirected from the public homepage to the admin dashboard.
  - Managers cannot purchase tickets (blocked in both GET and POST booking flows).
  - Managers cannot be assigned as flight crew:
    - Workers marked as managers are excluded from pilot/flight-attendant selection lists.
    - Backend validation blocks assigning a manager as Pilot/Flight Attendant.
  - Manager login blocks invalid role configuration where the same ID exists as both **Manager** and **AirCrew**.

* **Registration & guest usage rules**
  - Emails are normalized (lowercased).
  - At least one phone number is required; empty/duplicate phone entries are ignored.
  - Guests can retrieve an order only by providing both email and order code (order_id).

* **Flight visibility & booking eligibility**
  - Customers can only see flights that are bookable:
    not cancelled, depart in the future, and have at least one available seat.
  - Past flights (already departed) are not displayed to customers.
  - Operational actions (booking, crew assignment, cancellation) are blocked on flights that already departed.

* **Search validation (server-side)**
  - Origin, destination, and departure date are required.
  - Origin and destination cannot be identical.
  - The system verifies that an `Airway` exists for the requested route.

* **Seat selection & booking protection**
  - Booking is blocked for cancelled flights, past/departed flights, and fully booked flights.
  - Mixed-class booking is supported:
    a single order can include seats from multiple classes (Regular + Business),
    with pricing calculated per seat based on its class type.

* **Pricing rules**
  - Regular class pricing is mandatory for all flights.
  - Business class pricing is available only for Big Planes.

* **Order status & cancellation policy (Customer)**
  - “Active” vs “Done” is derived from the flight departure timestamp:
    - Active = paid + departure in the future
    - Done = paid + departure in the past
  - Only paid orders can be cancelled.
  - Customer cancellation is allowed only up to **36 hours** before departure.
  - A **5% fee** is charged, and all seats in the order are released back to availability.

* **Long vs. short flights**
  - Flights longer than **360 minutes** are classified as *long flights*.
  - Only aircraft classified as **Big Planes** may be assigned to long flights.
  - Only crew members with `long_flight_training = true` are selectable for long flights.

* **Availability, overlap prevention & scheduling buffers**
  - Aircraft and crew cannot be assigned to overlapping flights.
  - Buffer times are enforced to prevent unrealistic scheduling:
    - Aircraft require a **60-minute** buffer between flights.
    - Crew require a **120-minute** buffer between flights.
  - Overlaps are checked using padded time windows (existing_start < padded_end AND existing_end > padded_start).

* **Admin flight creation validations**
  - Flights cannot be created in the past (server-side enforcement).
  - A route must exist in `Airway` before a flight can be created.
  - Crew requirements depend on plane size:
    - Big Plane: **3 pilots + 6 attendants**
    - Small Plane: **2 pilots + 3 attendants**
  - Seat inventory must exist for the selected aircraft before creating a flight.

* **Flight cancellation policy (Admin)**
  - Only active/open flights can be cancelled (not full, not completed, not already cancelled).
  - Cancellation is blocked less than **72 hours** before departure.
  - Cancelling a flight triggers:
    - System cancellation of all active orders (refund = 0)
    - Release of all flight seats back to availability

* **Data consistency safeguards**
  - Invalid `FlightSeat` records (seats not matching the flight’s plane) are removed automatically.
  - If `FlightSeat` records are missing for a flight, they are generated from the plane’s `Seat` inventory.

---

## ✍️ Authors

- Elli Brinker
- Noa Meyron
- Stav Abraham
