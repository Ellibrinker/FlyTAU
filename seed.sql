USE flytau;

-- =========================
-- 1) Customers: 2 registered + 2 guests
-- =========================
INSERT INTO Customer (email, first_name, last_name) VALUES
('eli1@example.com', 'Eli', 'Levi'),
('eli2@example.com', 'Dana', 'Cohen'),
('guest1@example.com', 'Guest', 'One'),
('guest2@example.com', 'Guest', 'Two');

INSERT INTO RegisteredCustomer (email, passport_number, date_of_birth, registration_date, password) VALUES
('eli1@example.com', 'P1234567', '2003-01-01', CURDATE(), 'pass123'),
('eli2@example.com', 'P7654321', '2002-05-12', CURDATE(), 'pass123');

INSERT INTO CustomerPhone (email, phone_number) VALUES
('eli1@example.com', '050-1111111'),
('eli1@example.com', '052-2222222'),
('eli2@example.com', '054-3333333');

-- =========================
-- 2) Workers: 2 managers + 10 pilots + 20 flight attendants
-- =========================
-- Managers (also Workers)
INSERT INTO Worker (id, first_name, last_name, phone_number, city, street, house_num, start_date) VALUES
(1, 'Noa', 'Manager', '050-0000001', 'Tel Aviv', 'Herzl', 1, '2020-01-01'),
(2, 'Stav', 'Manager', '050-0000002', 'Tel Aviv', 'Dizengoff', 10, '2021-01-01');

INSERT INTO Manager (id, password) VALUES
(1, 'admin123'),
(2, 'admin123');

-- Pilots (Workers -> AirCrew -> Pilot)
-- 10 pilots: ids 101-110
INSERT INTO Worker (id, first_name, last_name, phone_number, city, street, house_num, start_date) VALUES
(101,'Pilot','P1','050-101','Tel Aviv','A',1,'2019-01-01'),
(102,'Pilot','P2','050-102','Tel Aviv','A',2,'2019-01-01'),
(103,'Pilot','P3','050-103','Tel Aviv','A',3,'2019-01-01'),
(104,'Pilot','P4','050-104','Tel Aviv','A',4,'2019-01-01'),
(105,'Pilot','P5','050-105','Tel Aviv','A',5,'2019-01-01'),
(106,'Pilot','P6','050-106','Tel Aviv','A',6,'2019-01-01'),
(107,'Pilot','P7','050-107','Tel Aviv','A',7,'2019-01-01'),
(108,'Pilot','P8','050-108','Tel Aviv','A',8,'2019-01-01'),
(109,'Pilot','P9','050-109','Tel Aviv','A',9,'2019-01-01'),
(110,'Pilot','P10','050-110','Tel Aviv','A',10,'2019-01-01');

INSERT INTO AirCrew (id, long_flight_training) VALUES
(101, TRUE),(102, TRUE),(103, TRUE),(104, TRUE),(105, TRUE),
(106, FALSE),(107, FALSE),(108, FALSE),(109, FALSE),(110, FALSE);

INSERT INTO Pilot (id) VALUES
(101),(102),(103),(104),(105),(106),(107),(108),(109),(110);

-- Flight attendants (Workers -> AirCrew -> FlightAttendant)
-- 20 attendants: ids 201-220
INSERT INTO Worker (id, first_name, last_name, phone_number, city, street, house_num, start_date) VALUES
(201,'FA','F1','050-201','Tel Aviv','B',1,'2022-01-01'),
(202,'FA','F2','050-202','Tel Aviv','B',2,'2022-01-01'),
(203,'FA','F3','050-203','Tel Aviv','B',3,'2022-01-01'),
(204,'FA','F4','050-204','Tel Aviv','B',4,'2022-01-01'),
(205,'FA','F5','050-205','Tel Aviv','B',5,'2022-01-01'),
(206,'FA','F6','050-206','Tel Aviv','B',6,'2022-01-01'),
(207,'FA','F7','050-207','Tel Aviv','B',7,'2022-01-01'),
(208,'FA','F8','050-208','Tel Aviv','B',8,'2022-01-01'),
(209,'FA','F9','050-209','Tel Aviv','B',9,'2022-01-01'),
(210,'FA','F10','050-210','Tel Aviv','B',10,'2022-01-01'),
(211,'FA','F11','050-211','Tel Aviv','B',11,'2022-01-01'),
(212,'FA','F12','050-212','Tel Aviv','B',12,'2022-01-01'),
(213,'FA','F13','050-213','Tel Aviv','B',13,'2022-01-01'),
(214,'FA','F14','050-214','Tel Aviv','B',14,'2022-01-01'),
(215,'FA','F15','050-215','Tel Aviv','B',15,'2022-01-01'),
(216,'FA','F16','050-216','Tel Aviv','B',16,'2022-01-01'),
(217,'FA','F17','050-217','Tel Aviv','B',17,'2022-01-01'),
(218,'FA','F18','050-218','Tel Aviv','B',18,'2022-01-01'),
(219,'FA','F19','050-219','Tel Aviv','B',19,'2022-01-01'),
(220,'FA','F20','050-220','Tel Aviv','B',20,'2022-01-01');

INSERT INTO AirCrew (id, long_flight_training) VALUES
(201, TRUE),(202, TRUE),(203, TRUE),(204, TRUE),(205, TRUE),
(206, FALSE),(207, FALSE),(208, FALSE),(209, FALSE),(210, FALSE),
(211, TRUE),(212, TRUE),(213, FALSE),(214, FALSE),(215, TRUE),
(216, FALSE),(217, TRUE),(218, FALSE),(219, TRUE),(220, FALSE);

INSERT INTO FlightAttendant (id) VALUES
(201),(202),(203),(204),(205),(206),(207),(208),(209),(210),
(211),(212),(213),(214),(215),(216),(217),(218),(219),(220);

-- =========================
-- 3) Planes + classes + seats (minimal)
-- =========================
INSERT INTO Plane (plane_id, manufacturer, purchase_date) VALUES
(1,'Boeing','2018-01-01'),
(2,'Airbus','2019-01-01'),
(3,'Boeing','2020-01-01'),
(4,'Airbus','2021-01-01'),
(5,'Embraer','2022-01-01'),
(6,'Embraer','2023-01-01');

-- mark some as big/small (optional ISA)
INSERT INTO BigPlane (plane_id) VALUES (1),(2),(3);
INSERT INTO SmallPlane (plane_id) VALUES (4),(5),(6);

-- Classes: for big planes include Regular + Business, for small only Regular
INSERT INTO Class (plane_id, class_type, rows_number, columns_number) VALUES
(1,'Regular',20,6),(1,'Business',5,4),
(2,'Regular',22,6),(2,'Business',6,4),
(3,'Regular',18,6),(3,'Business',4,4),
(4,'Regular',15,4),
(5,'Regular',12,4),
(6,'Regular',10,4);

-- Seats: minimal seats per plane (רק כמה כדי שיהיה אפשר FlightSeat)
-- plane 1 Regular seats: row 1 col 1..3
INSERT INTO Seat (seat_id, row_num, column_number, plane_id, class_type) VALUES
(1001,1,1,1,'Regular'),
(1002,1,2,1,'Regular'),
(1003,1,3,1,'Regular');

-- plane 2 Regular seats
INSERT INTO Seat (seat_id, row_num, column_number, plane_id, class_type) VALUES
(2001,1,1,2,'Regular'),
(2002,1,2,2,'Regular'),
(2003,1,3,2,'Regular');

-- =========================
-- 4) Airway + Flights (4 open flights)
-- =========================
INSERT INTO Airway (origin_airport, destination_airport, duration) VALUES
('TLV','ATH',120),
('TLV','ROM',180),
('TLV','PAR',300),
('TLV','LON',330);

INSERT INTO Flight (flight_id, plane_id, origin_airport, destination_airport, departure_date, departure_time, status) VALUES
(501,1,'TLV','ATH','2026-01-10','10:00:00','open'),
(502,2,'TLV','ROM','2026-01-11','12:30:00','open'),
(503,3,'TLV','PAR','2026-01-12','09:15:00','open'),
(504,4,'TLV','LON','2026-01-13','14:45:00','open');

-- FlightPricing: set at least Regular (and Business where exists)
INSERT INTO FlightPricing (flight_id, class_type, price) VALUES
(501,'Regular',500.00),(501,'Business',900.00),
(502,'Regular',600.00),(502,'Business',1100.00),
(503,'Regular',750.00),(503,'Business',1400.00),
(504,'Regular',800.00); -- plane 4 has only Regular

-- =========================
-- 5) FlightSeat + Orders + OrderItems (4 orders)
-- =========================
-- Create flight seats for some flights using the seats we inserted
INSERT INTO FlightSeat (flight_seat_id, flight_id, seat_id, status) VALUES
(9001,501,1001,'available'),
(9002,501,1002,'available'),
(9003,502,2001,'available'),
(9004,502,2002,'available');

-- 4 orders (2 registered + 2 guests)
INSERT INTO FlightOrder (order_id, flight_id, email, execution_date, status, total_payment) VALUES
(7001,501,'eli1@example.com',CURDATE(),'paid',500.00),
(7002,501,'guest1@example.com',CURDATE(),'paid',500.00),
(7003,502,'eli2@example.com',CURDATE(),'paid',600.00),
(7004,502,'guest2@example.com',CURDATE(),'paid',600.00);

-- link each order to a seat
INSERT INTO OrderItem (item_id, order_id, flight_seat_id) VALUES
(8001,7001,9001),
(8002,7002,9002),
(8003,7003,9003),
(8004,7004,9004);

-- mark those seats as booked (optional but logical)
UPDATE FlightSeat SET status='booked' WHERE flight_seat_id IN (9001,9002,9003,9004);

-- =========================
-- 6) Crew placements (optional but makes sense)
-- =========================
INSERT INTO FlightCrewPlacement (flight_id, id) VALUES
(501,101),(501,201),(501,202),
(502,102),(502,203),(502,204);
