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

## 🛠️ Technologies Used

* **Backend:** Python, Flask
* **Database:** MySQL
* **Frontend:** HTML, CSS (Jinja templates)
* **Deployment:** PythonAnywhere

---

## 🔐 Access & Security

* Role-based access control (Customer / Manager)
* Admin routes are protected and accessible only to authenticated managers
* Business rules enforced at both database and application levels

---

## 📁 Repository Structure (High-Level)

```
/app
  /templates
    admin_*.html
    customer_*.html
  /static
  admin.py
  main.py
/database
  schema.sql
  seed.sql
```

---

## 📚 Academic Notes

* No SQL `VIEW`s are used in the database-reporting component, in accordance with course instructions.
* Business constraints (flight availability, crew overlap, cancellations) are enforced explicitly.
* The system emphasizes clarity, correctness, and alignment with real-world airline operations.

---

## ✍️ Authors

- Elli Brinker
- Noa Meyron
- Stav Abraham
