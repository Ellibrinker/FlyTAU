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

The system explicitly enforces real-world airline business rules to ensure operational correctness, safety, and data consistency:

### **Role-based access & separation**
- Strict separation is enforced between **customers** and **managers**.
- Managers are automatically redirected from the public homepage to the admin dashboard.
- Managers are not allowed to purchase flight tickets, neither as registered users nor as guests.
- Managers cannot be assigned as flight crew (pilots or flight attendants).
- The system prevents invalid role configurations in which a single individual holds both managerial and air-crew roles.

---

### **Registration & guest usage rules**
- Customer emails are normalized (stored in lowercase) to prevent duplicates.
- At least one phone number is required during registration; empty or duplicate phone entries are ignored.
- Guests can retrieve an order only by providing both the email address and the unique order code.

---

### **Flight visibility & booking eligibility**
- Customers are shown **only flights that are eligible for booking**:
  - Not cancelled  
  - Scheduled for a future departure  
  - Contain at least one available seat
- Flights whose departure time has already passed are not displayed to customers.
- Operational actions (booking, crew assignment, cancellation) are blocked for flights that have already departed.

---

### **Search validation**
- Origin airport, destination airport, and departure date are mandatory.
- Origin and destination airports cannot be identical.
- A flight route must exist in the system (`Airway`) in order to be searchable or schedulable.

---

### **Seat selection & booking protection**
- Seat selection and booking are blocked for:
  - Cancelled flights
  - Flights that already departed
  - Fully booked flights
- A single order may include seats from multiple classes (Regular and Business), with pricing calculated per seat according to its class.

---

### **Pricing rules**
- Regular-class pricing is mandatory for all flights.
- Business-class pricing is available only on flights operated by **Big Planes**.
- Ticket prices defined for a flight are also used for calculating cancellation fees.

---

### **Order status & cancellation policy (Customer)**
- Order status is derived from payment state and flight departure time:
  - **Active** – paid order for a future flight  
  - **Done** – paid order for a past flight
- Only fully paid orders can be cancelled.
- Customer cancellation is allowed only up to **36 hours** before departure.
- A fixed **5% cancellation fee** is charged.
- Partial cancellation of an order is not allowed; all seats in the order are cancelled together and released back to availability.
- Order statuses include: active/paid, completed, customer-cancelled, and system-cancelled.

---

### **Long vs. short flights**
- Flights longer than **360 minutes (6 hours)** are classified as *long flights*.
- Only **Big Planes** may be assigned to long flights.
- Only crew members who have completed **long-flight training** may be assigned to long flights.

---

### **Availability, overlap prevention & scheduling buffers**
- Aircraft and crew members cannot be assigned to overlapping flights.
- Buffer times are enforced to prevent unrealistic scheduling:
  - Aircraft require a **60-minute** buffer between flights.
  - Crew members require a **120-minute** buffer between flights.
- Overlap checks are performed using padded time windows to ensure safe scheduling.

---

### **Admin flight creation rules**
- Flights cannot be created in the past.
- A valid route (`Airway`) must exist before a flight can be created.
- Landing date and time are computed automatically based on route duration and are not entered manually.
- Crew requirements depend on aircraft size:
  - **Big Plane:** 3 pilots and 6 flight attendants  
  - **Small Plane:** 2 pilots and 3 flight attendants
- Seat inventory must exist for the selected aircraft before a flight can be published.

---

### **Flight cancellation policy (Admin)**
- Only active/open flights may be cancelled (not full, not completed, not already cancelled).
- Flight cancellation is blocked less than **72 hours** before departure.
- Cancelling a flight triggers:
  - System cancellation of all active orders (full refund, total payment set to 0)
  - Release of all seats back to availability

---

### **Data consistency safeguards**
- Seat records that do not match the aircraft assigned to a flight are automatically removed.
- If seat records are missing for a flight, they are automatically generated from the aircraft’s seat configuration.

---

## ✍️ Authors

- Elli Brinker
- Noa Meyron
- Stav Abraham
