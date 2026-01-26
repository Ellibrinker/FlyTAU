# ✈️ Flight Management & Booking System

A web-based flight management and booking system developed as part of academic coursework in **Database Systems Design** and **Information Systems Engineering**.

The system supports operational flight management, customer bookings, and a dedicated administrative interface for managers, including management reports for business analysis and decision-making.

🔗 **Live system:**
👉 [https://ellibrinker.pythonanywhere.com/](https://ellibrinker.pythonanywhere.com/)

---

## 📌 Project Overview

The project is divided into two academic components:

1. **Database Systems Design** – relational schema design, SQL queries, constraints, and analytical reports.
2. **Information Systems Engineering** – web application development, user interfaces, role-based access, and management dashboards.

---

## 🛠️ Technologies Used

- **Backend:** Python (Flask)
- **Database:** MySQL
- **Frontend:** HTML, CSS (Jinja templates)
- **Deployment:** PythonAnywhere

---

## 👥 User Roles

### 🧑 Customer

* Browse available flights
* Make flight bookings
* Select seats
* View personal orders

### 👨‍💼 Manager (Admin)

* Secure login
* Centralized admin dashboard
* Add operational resources (aircraft and crew)
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
├── static/                 # Static assets (CSS, images)
├── templates/              # HTML templates (Jinja)
│   ├── admin_*.html        # Admin interface pages
│   └── customer-*.html     # Customer-facing pages
├── admin.py                # Admin logic
├── flights.py              # Customer flight & booking logic
├── main.py                 # Application entry point & order management
├── schema.sql               # Database schema (tables, constraints)
├── seed.sql                 # Initial data
└── reports_queries.sql      # Management reports SQL queries
```

---

## ⚙️ Business Rules & Edge Cases

The system explicitly enforces real-world airline business rules and operational constraints, including:

---

### **Role-based access & separation**
- Managers are automatically redirected from the public homepage to the admin dashboard.
- Managers cannot purchase tickets and cannot be assigned as flight crew.
- Flight visibility is role-based:
  - Customers see only flights that are eligible for booking  
    (not cancelled, departure time is in the future, and at least one seat is available).
  - Managers can view all flights, including active, full, completed, and cancelled flights.

---

### **Registration & guest usage rules**
- For registered customers, personal details (email, passport number, and contact information) are validated server-side and must meet format and uniqueness constraints.
- Registered customer data is persisted and reused automatically for future orders.
- Guests may place orders and retrieve them using the order code (`order_id`) and associated email address.

---

### **Search validation**
- Origin and destination airports are mandatory search parameters.
- Origin and destination must be different.
- Departure date is optional; when provided, results are filtered to that date.

---

### **Seat selection & booking**
- Seat selection is allowed only from the pool of seats marked as available for the selected flight.
- **Single-flight order constraint:** each order is associated with exactly one flight; seats from different flights cannot be combined.
- Mixed-class booking is supported within a single flight:
  - A single order may include seats from both Regular and Business classes.

---

### **Pricing rules**
- Pricing is defined per flight and per seat class (Regular / Business).
- Regular class pricing is mandatory for all flights.
- Business class pricing is available only for flights operated by **Big Planes**.
- The total order price is calculated as the sum of the prices of all selected seats, based on their class type.

---

### **Order status & customer cancellation policy**
- Order status is derived from the flight’s departure time:
  - **Active**: paid order for a future flight
  - **Done**: paid order for a past flight
- Only paid orders can be cancelled.
- Customer cancellation is allowed only up to **36 hours** before departure.
- A fixed **5% cancellation fee** is applied to the total order amount.
- Partial cancellation of seats within an order is not allowed.
- Upon cancellation, all seats in the order are released back to availability.

---

### **Admin flight creation validations**
- Flights cannot be created in the past (server-side enforcement).
- A valid route must exist in the `Airway` table before flight creation.
- Flights longer than **360 minutes** are classified as *long flights*.
- Long flights have additional constraints:
  - Only aircraft classified as **Big Planes** may be assigned.
  - Only crew members explicitly marked as long-flight qualified may be assigned.
- Crew requirements depend on aircraft size:
  - **Big Plane**: 3 pilots and 6 flight attendants
  - **Small Plane**: 2 pilots and 3 flight attendants
- Seat inventory must exist for the selected aircraft before a flight can be created.

---

### **Resource location & timeline-based availability (Aircraft & Crew)**

To reflect real-world airline scheduling, **both aircraft and crew members (pilots & attendants) are treated as being physically located at a specific airport at any point in time**.

#### **Availability checks (time + location)**
When creating a new flight, resources shown to the manager must satisfy:

1. **Time overlap prevention:**
- A resource cannot be assigned to overlapping flights.

2. **Location consistency at departure:**
- A resource may be assigned **only** to a flight that departs from the airport where it is located at the departure time.
- The system does **not** assume that a plane or crew member “moved” between flights, regardless of how much time passed.
- Resource location is derived dynamically from the flight timeline, without maintaining a separate location field.
- **Initial assignment rule (default base):**  
  If a resource has no previous flights, it is assumed to be **initially stationed at TLV** and may be assigned **only** to flights departing from TLV.

#### **Cancelled flights behavior**
Cancelled flights are treated as non-existent for scheduling purposes:
- Cancelled flights do not block availability.
- Cancelled flights do not affect derived resource location.
- Cancelling a flight has **no cascading effect** on future flights; the system does not attempt to repair dependent scheduling chains.

---

### **Flight cancellation policy (Admin)**
- Only active/open flights can be cancelled (not full, not completed, and not already cancelled).
- Flight cancellation is blocked less than **72 hours** before departure.
- Cancelling a flight triggers:
  - System cancellation of all active orders (full refund, total payment set to 0)
  - Release of all flight seats back to availability
  - Release of assigned aircraft and crew for future scheduling

---

### **Data consistency safeguards**
- Invalid `FlightSeat` records (seats that do not match the flight’s aircraft) are removed automatically.
- If `FlightSeat` records are missing for a flight, they are generated automatically from the aircraft’s seat inventory.

---

## ✍️ Authors

- Elli Brinker
- Noa Meyron
- Stav Abraham
