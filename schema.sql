/* יצירת סכמה לניהול נתונים על לקוחות, עובדי צוות אוויר, מנהלים, מטוסים והזמנות */

CREATE DATABASE IF NOT EXISTS `ellibrinker$flytau`;
USE `ellibrinker$flytau`;

/* פרטים עבור לקוחות, ופרטים נוספים עבור לקוחות רשומים */
CREATE TABLE Customer (
  email VARCHAR(255) NOT NULL,
  first_name VARCHAR(50),
  last_name  VARCHAR(50),
  PRIMARY KEY (email)
);

CREATE TABLE CustomerPhone (
  email VARCHAR(255) NOT NULL,
  phone_number VARCHAR(20) NOT NULL,
  PRIMARY KEY (email, phone_number),
  FOREIGN KEY (email) REFERENCES Customer(email)
);

CREATE TABLE RegisteredCustomer (
  email VARCHAR(255) NOT NULL,
  passport_number VARCHAR(20),
  date_of_birth DATE,
  registration_date DATE,
  password VARCHAR(255),
  PRIMARY KEY (email),
  FOREIGN KEY (email) REFERENCES Customer(email)
);

/* ניהול נתונים עבור עבד כללי, והזנת נתונים נוספים לפי סוג העובד */

CREATE TABLE Worker (
  id INT NOT NULL,
  first_name VARCHAR(50),
  last_name  VARCHAR(50),
  phone_number VARCHAR(20),
  city VARCHAR(50),
  street VARCHAR(50),
  house_num INT,
  start_date DATE,
  PRIMARY KEY (id)
);

CREATE TABLE Manager (
  id INT NOT NULL,
  password VARCHAR(255) NOT NULL,
  PRIMARY KEY (id),
  FOREIGN KEY (id) REFERENCES Worker(id)
    ON DELETE CASCADE
);

CREATE TABLE AirCrew (
  id INT NOT NULL,
  long_flight_training BOOLEAN NOT NULL,
  PRIMARY KEY (id),
  FOREIGN KEY (id) REFERENCES Worker(id)
    ON DELETE CASCADE
);

CREATE TABLE Pilot (
  id INT NOT NULL,
  PRIMARY KEY (id),
  FOREIGN KEY (id) REFERENCES AirCrew(id)
    ON DELETE CASCADE
);

CREATE TABLE FlightAttendant (
  id INT NOT NULL,
  PRIMARY KEY (id),
  FOREIGN KEY (id) REFERENCES AirCrew(id)
    ON DELETE CASCADE
);

/* ניהול נתונים על מטוסים, מחלקות ומושבים במטוסים */

CREATE TABLE Plane (
  plane_id INT NOT NULL AUTO_INCREMENT,
  manufacturer VARCHAR(50) NOT NULL,
  purchase_date DATE NOT NULL,
  PRIMARY KEY (plane_id)
);

CREATE TABLE BigPlane (
  plane_id INT NOT NULL,
  PRIMARY KEY (plane_id),
  FOREIGN KEY (plane_id) REFERENCES Plane(plane_id)
);

CREATE TABLE SmallPlane (
  plane_id INT NOT NULL,
  PRIMARY KEY (plane_id),
  FOREIGN KEY (plane_id) REFERENCES Plane(plane_id)
);

CREATE TABLE Class (
  plane_id INT NOT NULL,
  class_type VARCHAR(50) NOT NULL,
  rows_number INT NOT NULL,
  columns_number INT NOT NULL,
  PRIMARY KEY (plane_id, class_type),
  FOREIGN KEY (plane_id) REFERENCES Plane(plane_id)
);

CREATE TABLE Seat (
  seat_id INT NOT NULL AUTO_INCREMENT,
  row_num INT NOT NULL,
  column_number INT NOT NULL,
  plane_id INT NOT NULL,
  class_type VARCHAR(50) NOT NULL,
  PRIMARY KEY (seat_id),
  FOREIGN KEY (plane_id, class_type) REFERENCES Class(plane_id, class_type),
  UNIQUE (plane_id, row_num, column_number)
);

/* ניהול נתונים על טיסות והזמנתן - נתיבי אוויר, תמחור, מושבים בטיסה ושיבוץ עובדים לטיסה ספציפית */

CREATE TABLE Airway (
  origin_airport VARCHAR(255) NOT NULL,
  destination_airport VARCHAR(255) NOT NULL,
  duration INT NOT NULL,
  PRIMARY KEY (origin_airport, destination_airport)
);

CREATE TABLE Flight (
  flight_id INT NOT NULL AUTO_INCREMENT,
  plane_id INT NOT NULL,
  origin_airport VARCHAR(255) NOT NULL,
  destination_airport VARCHAR(255) NOT NULL,
  departure_date DATE NOT NULL,
  departure_time TIME NOT NULL,
  status VARCHAR(50) NOT NULL,
  PRIMARY KEY (flight_id),
  FOREIGN KEY (plane_id) REFERENCES Plane(plane_id),
  FOREIGN KEY (origin_airport, destination_airport) REFERENCES Airway(origin_airport, destination_airport)
);

CREATE TABLE FlightPricing (
  flight_id INT NOT NULL,
  class_type VARCHAR(50) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (flight_id, class_type),
  FOREIGN KEY (flight_id) REFERENCES Flight(flight_id)
);

CREATE TABLE FlightOrder (
  order_id INT NOT NULL AUTO_INCREMENT,
  flight_id INT NOT NULL,
  email VARCHAR(255) NOT NULL,
  execution_date DATE NOT NULL,
  status VARCHAR(50) NOT NULL,
  total_payment DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (order_id),
  FOREIGN KEY (flight_id) REFERENCES Flight(flight_id),
  FOREIGN KEY (email) REFERENCES Customer(email)
);

CREATE TABLE FlightSeat (
  flight_seat_id INT NOT NULL AUTO_INCREMENT,
  flight_id INT NOT NULL,
  seat_id INT NOT NULL,
  status VARCHAR(50) NOT NULL,
  PRIMARY KEY (flight_seat_id),
  FOREIGN KEY (flight_id) REFERENCES Flight(flight_id),
  FOREIGN KEY (seat_id) REFERENCES Seat(seat_id),
  UNIQUE (flight_id, seat_id)
);

CREATE TABLE OrderItem (
  item_id INT NOT NULL AUTO_INCREMENT,
  order_id INT NOT NULL,
  flight_seat_id INT NOT NULL,
  PRIMARY KEY (item_id),
  FOREIGN KEY (order_id) REFERENCES FlightOrder(order_id),
  FOREIGN KEY (flight_seat_id) REFERENCES FlightSeat(flight_seat_id),
  UNIQUE (order_id, flight_seat_id)
);

CREATE TABLE FlightCrewPlacement (
  flight_id INT NOT NULL,
  id INT NOT NULL,
  PRIMARY KEY (flight_id, id),
  FOREIGN KEY (flight_id) REFERENCES Flight(flight_id),
  FOREIGN KEY (id) REFERENCES AirCrew(id)
);
