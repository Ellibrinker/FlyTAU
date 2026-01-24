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

The system explicitly enforces real-world airline business rules and operational constraints, including:

### **Role-based access & separation**
- Managers are automatically redirected from the public homepage to the admin dashboard.
- Managers are strictly prohibited from purchasing flight tickets, either as registered users or as guests.
- Managers cannot be assigned as flight crew:
  - Workers with a managerial role are excluded from pilot and flight-attendant selection lists.
  - Backend validation blocks assigning a manager to any crew role.
- Manager login prevents invalid role configurations where a single ID exists as both **Manager** and **AirCrew**.

### **Registration & guest usage rules**
- Customer email addresses must be unique.
- At least one phone number is required during registration; empty or duplicate phone entries are ignored.
- Guests can retrieve an order only by providing both the order code (order_id) and the associated email address.

### **Flight publication & lifecycle**
- Once a flight is successfully created by a manager, it is automatically published and becomes available for customer booking.
- Flight duration and landing time are calculated automatically based on the selected route and are not entered manually by the manager.
- Customers and managers view different flight boards:
  - Customers see only flights that are relevant for booking.
  - Managers can view all flights, including active, full, completed, and cancelled flights.

### **Flight visibility & booking eligibility**
- Customers can only view flights that are eligible for booking:
  - Not cancelled
  - Departure time is in the future
  - At least one seat is available
- Flights whose departure time has passed are not displayed to customers.
- Operational actions (booking, crew assignment, flight cancellation) are blocked on flights that have already departed.

### **Search validation (server-side)**
- Origin, destination, and departure date are mandatory search parameters.
- Origin and destination airports must be different.
- The system verifies that a valid route (`Airway`) exists between the selected origin and destination.

### **Seat selection & booking protection**
- Booking is blocked for cancelled flights, past/departed flights, and fully booked flights.
- Seat selection is allowed only from the pool of available seats for the chosen flight.
- Mixed-class booking is supported:
  - A single order may include seats from multiple classes (Regular and Business).
  - Pricing is calculated per seat according to its class type.

### **Pricing rules**
- Regular class pricing is mandatory for all flights.
- Business class pricing is available only for aircraft classified as **Big Planes**.

### **Order status & customer cancellation policy**
- Order status is derived from the flight’s departure time:
  - **Active**: paid order for a future flight
  - **Done**: paid order for a past flight
- Only paid orders can be cancelled.
- Customer cancellation is allowed only up to **36 hours** before departure.
- A fixed **5% cancellation fee** is applied to the total order amount.
- Partial cancellation of seats within an order is not allowed.
- Upon cancellation, all seats in the order are released back to availability.

### **Long vs. short flights**
- Flights longer than **360 minutes** are classified as *long flights*.
- Only aircraft classified as **Big Planes** may be assigned to long flights.
- Only crew members who are qualified for long flights may be assigned to long flights.

### **Availability, overlap prevention & scheduling buffers**
- Aircraft and crew members cannot be assigned to overlapping flights.
- Buffer times are enforced to prevent unrealistic scheduling:
  - Aircraft require a **60-minute** buffer between flights.
  - Crew members require a **120-minute** buffer between flights.
- Overlaps are checked using padded time windows to ensure safe scheduling.

### **Admin flight creation validations**
- Flights cannot be created in the past (server-side enforcement).
- A valid route must exist in the `Airway` table before a flight can be created.
- Crew requirements depend on aircraft size:
  - **Big Plane**: 3 pilots and 6 flight attendants
  - **Small Plane**: 2 pilots and 3 flight attendants
- Seat inventory must exist for the selected aircraft before flight creation.

### **Flight cancellation policy (Admin)**
- Only active/open flights can be cancelled (not full, not completed, not already cancelled).
- Flight cancellation is blocked less than **72 hours** before departure.
- Cancelling a flight triggers:
  - System cancellation of all active orders (full refund, total payment set to 0)
  - Release of all flight seats back to availability
  - Release of assigned aircraft and crew, making them available for other flights in the same time window.

### **Data consistency safeguards**
- Invalid `FlightSeat` records (seats that do not match the flight’s aircraft) are removed automatically.
- If `FlightSeat` records are missing for a flight, they are generated automatically from the aircraft’s seat inventory.

---

## ✍️ Authors

- Elli Brinker
- Noa Meyron
- Stav Abraham
