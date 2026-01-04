USE `ellibrinker$flytau`;

-- =========================
-- 1) Customers: 2 registered + 2 guests
-- =========================
INSERT INTO Customer (email, first_name, last_name) VALUES
('elli.brinker@example.com', 'Elli', 'Brinker'),
('stav.abraham@example.com', 'Stav', 'Abraham'),
('guest1@example.com', 'Guest', 'One'),
('guest2@example.com', 'Guest', 'Two');

INSERT INTO RegisteredCustomer (email, passport_number, date_of_birth, registration_date, password) VALUES
('elli.brinker@example.com', 'P1234567', '2003-01-01', CURDATE(), 'pass123'),
('stav.abraham@example.com', 'P7654321', '2002-05-12', CURDATE(), 'pass123');

INSERT INTO CustomerPhone (email, phone_number) VALUES
('elli.brinker@example.com', '050-1111111'),
('elli.brinker@example.com', '052-2222222'),
('stav.abraham@example.com', '054-3333333');

-- =========================
-- 2) Workers: 2 managers + 10 pilots + 20 flight attendants
--    ✅ Worker.id = ת"ז INT אמיתי => מכניסים ידנית
-- =========================

-- ---- Managers (Workers -> Manager)
INSERT INTO Worker (id, first_name, last_name, phone_number, city, street, house_num, start_date) VALUES
(318274615, 'Noa', 'Meyron',   '050-0000001', 'Tel Aviv', 'Herzl',      1,  '2020-01-01'),
(317555222, 'Stav', 'Abraham', '050-0000002', 'Tel Aviv', 'Dizengoff',  10, '2021-01-01');

INSERT INTO Manager (id, password) VALUES
(318274615, 'admin123'),
(317555222, 'admin123');

-- ---- 10 Pilots: ids 300000001-300000010
INSERT INTO Worker (id, first_name, last_name, phone_number, city, street, house_num, start_date) VALUES
(300000001,'Pilot','P1','050-101','Tel Aviv','A',1,'2019-01-01'),
(300000002,'Pilot','P2','050-102','Tel Aviv','A',2,'2019-01-01'),
(300000003,'Pilot','P3','050-103','Tel Aviv','A',3,'2019-01-01'),
(300000004,'Pilot','P4','050-104','Tel Aviv','A',4,'2019-01-01'),
(300000005,'Pilot','P5','050-105','Tel Aviv','A',5,'2019-01-01'),
(300000006,'Pilot','P6','050-106','Tel Aviv','A',6,'2019-01-01'),
(300000007,'Pilot','P7','050-107','Tel Aviv','A',7,'2019-01-01'),
(300000008,'Pilot','P8','050-108','Tel Aviv','A',8,'2019-01-01'),
(300000009,'Pilot','P9','050-109','Tel Aviv','A',9,'2019-01-01'),
(300000010,'Pilot','P10','050-110','Tel Aviv','A',10,'2019-01-01');

INSERT INTO AirCrew (id, long_flight_training) VALUES
(300000001, TRUE),(300000002, TRUE),(300000003, TRUE),(300000004, TRUE),(300000005, TRUE),
(300000006, FALSE),(300000007, FALSE),(300000008, FALSE),(300000009, FALSE),(300000010, FALSE);

INSERT INTO Pilot (id) VALUES
(300000001),(300000002),(300000003),(300000004),(300000005),
(300000006),(300000007),(300000008),(300000009),(300000010);

-- ---- 20 Flight Attendants: ids 400000001-400000020
INSERT INTO Worker (id, first_name, last_name, phone_number, city, street, house_num, start_date) VALUES
(400000001,'FA','F1','050-201','Tel Aviv','B',1,'2022-01-01'),
(400000002,'FA','F2','050-202','Tel Aviv','B',2,'2022-01-01'),
(400000003,'FA','F3','050-203','Tel Aviv','B',3,'2022-01-01'),
(400000004,'FA','F4','050-204','Tel Aviv','B',4,'2022-01-01'),
(400000005,'FA','F5','050-205','Tel Aviv','B',5,'2022-01-01'),
(400000006,'FA','F6','050-206','Tel Aviv','B',6,'2022-01-01'),
(400000007,'FA','F7','050-207','Tel Aviv','B',7,'2022-01-01'),
(400000008,'FA','F8','050-208','Tel Aviv','B',8,'2022-01-01'),
(400000009,'FA','F9','050-209','Tel Aviv','B',9,'2022-01-01'),
(400000010,'FA','F10','050-210','Tel Aviv','B',10,'2022-01-01'),
(400000011,'FA','F11','050-211','Tel Aviv','B',11,'2022-01-01'),
(400000012,'FA','F12','050-212','Tel Aviv','B',12,'2022-01-01'),
(400000013,'FA','F13','050-213','Tel Aviv','B',13,'2022-01-01'),
(400000014,'FA','F14','050-214','Tel Aviv','B',14,'2022-01-01'),
(400000015,'FA','F15','050-215','Tel Aviv','B',15,'2022-01-01'),
(400000016,'FA','F16','050-216','Tel Aviv','B',16,'2022-01-01'),
(400000017,'FA','F17','050-217','Tel Aviv','B',17,'2022-01-01'),
(400000018,'FA','F18','050-218','Tel Aviv','B',18,'2022-01-01'),
(400000019,'FA','F19','050-219','Tel Aviv','B',19,'2022-01-01'),
(400000020,'FA','F20','050-220','Tel Aviv','B',20,'2022-01-01');

INSERT INTO AirCrew (id, long_flight_training) VALUES
(400000001, TRUE),(400000002, TRUE),(400000003, TRUE),(400000004, TRUE),(400000005, TRUE),
(400000006, FALSE),(400000007, FALSE),(400000008, FALSE),(400000009, FALSE),(400000010, FALSE),
(400000011, TRUE),(400000012, TRUE),(400000013, FALSE),(400000014, FALSE),(400000015, TRUE),
(400000016, FALSE),(400000017, TRUE),(400000018, FALSE),(400000019, TRUE),(400000020, FALSE);

INSERT INTO FlightAttendant (id) VALUES
(400000001),(400000002),(400000003),(400000004),(400000005),
(400000006),(400000007),(400000008),(400000009),(400000010),
(400000011),(400000012),(400000013),(400000014),(400000015),
(400000016),(400000017),(400000018),(400000019),(400000020);

-- =========================
-- 3) Planes + classes + seats (minimal)
--    plane_id AUTO_INCREMENT => שומרים משתנים
-- =========================
INSERT INTO Plane (manufacturer, purchase_date) VALUES ('Boeing','2018-01-01');  SET @pl1 = LAST_INSERT_ID();
INSERT INTO Plane (manufacturer, purchase_date) VALUES ('Airbus','2019-01-01');  SET @pl2 = LAST_INSERT_ID();
INSERT INTO Plane (manufacturer, purchase_date) VALUES ('Boeing','2020-01-01');  SET @pl3 = LAST_INSERT_ID();
INSERT INTO Plane (manufacturer, purchase_date) VALUES ('Airbus','2021-01-01');  SET @pl4 = LAST_INSERT_ID();
INSERT INTO Plane (manufacturer, purchase_date) VALUES ('Dassault','2022-01-01');SET @pl5 = LAST_INSERT_ID();
INSERT INTO Plane (manufacturer, purchase_date) VALUES ('Dassault','2023-01-01');SET @pl6 = LAST_INSERT_ID();

INSERT INTO BigPlane (plane_id) VALUES (@pl1),(@pl2),(@pl3);
INSERT INTO SmallPlane (plane_id) VALUES (@pl4),(@pl5),(@pl6);

INSERT INTO Class (plane_id, class_type, rows_number, columns_number) VALUES
(@pl1,'Regular',20,6),(@pl1,'Business',5,4),
(@pl2,'Regular',22,6),(@pl2,'Business',6,4),
(@pl3,'Regular',18,6),(@pl3,'Business',4,4),
(@pl4,'Regular',15,4),
(@pl5,'Regular',12,4),
(@pl6,'Regular',10,4);

-- Seats: seat_id AUTO_INCREMENT => לא מציינים seat_id
INSERT INTO Seat (row_num, column_number, plane_id, class_type) VALUES
(1,1,@pl1,'Regular'),
(1,2,@pl1,'Regular'),
(1,3,@pl1,'Regular');

SELECT seat_id INTO @s_pl1_1_1 FROM Seat WHERE plane_id=@pl1 AND row_num=1 AND column_number=1;
SELECT seat_id INTO @s_pl1_1_2 FROM Seat WHERE plane_id=@pl1 AND row_num=1 AND column_number=2;
SELECT seat_id INTO @s_pl1_1_3 FROM Seat WHERE plane_id=@pl1 AND row_num=1 AND column_number=3;

INSERT INTO Seat (row_num, column_number, plane_id, class_type) VALUES
(1,1,@pl2,'Regular'),
(1,2,@pl2,'Regular'),
(1,3,@pl2,'Regular');

SELECT seat_id INTO @s_pl2_1_1 FROM Seat WHERE plane_id=@pl2 AND row_num=1 AND column_number=1;
SELECT seat_id INTO @s_pl2_1_2 FROM Seat WHERE plane_id=@pl2 AND row_num=1 AND column_number=2;
SELECT seat_id INTO @s_pl2_1_3 FROM Seat WHERE plane_id=@pl2 AND row_num=1 AND column_number=3;

-- =========================
-- 4) Airway + Flights (4 open flights)
--    flight_id AUTO_INCREMENT => שומרים @f1..@f4
-- =========================
INSERT INTO Airway (origin_airport, destination_airport, duration) VALUES
('TLV','ATH',120),
('TLV','ROM',180),
('TLV','PAR',300),
('TLV','LON',330);

INSERT INTO Flight (plane_id, origin_airport, destination_airport, departure_date, departure_time, status)
VALUES (@pl1,'TLV','ATH','2026-01-10','10:00:00','open'); SET @f1 = LAST_INSERT_ID();

INSERT INTO Flight (plane_id, origin_airport, destination_airport, departure_date, departure_time, status)
VALUES (@pl2,'TLV','ROM','2026-01-11','12:30:00','open'); SET @f2 = LAST_INSERT_ID();

INSERT INTO Flight (plane_id, origin_airport, destination_airport, departure_date, departure_time, status)
VALUES (@pl3,'TLV','PAR','2026-01-12','09:15:00','open'); SET @f3 = LAST_INSERT_ID();

INSERT INTO Flight (plane_id, origin_airport, destination_airport, departure_date, departure_time, status)
VALUES (@pl4,'TLV','LON','2026-01-13','14:45:00','open'); SET @f4 = LAST_INSERT_ID();

INSERT INTO FlightPricing (flight_id, class_type, price) VALUES
(@f1,'Regular',500.00),(@f1,'Business',900.00),
(@f2,'Regular',600.00),(@f2,'Business',1100.00),
(@f3,'Regular',750.00),(@f3,'Business',1400.00),
(@f4,'Regular',800.00);

-- =========================
-- 5) FlightSeat + Orders + OrderItems (4 orders)
-- =========================
INSERT INTO FlightSeat (flight_id, seat_id, status) VALUES
(@f1, @s_pl1_1_1, 'available'),
(@f1, @s_pl1_1_2, 'available'),
(@f2, @s_pl2_1_1, 'available'),
(@f2, @s_pl2_1_2, 'available');

SELECT flight_seat_id INTO @fs1 FROM FlightSeat WHERE flight_id=@f1 AND seat_id=@s_pl1_1_1;
SELECT flight_seat_id INTO @fs2 FROM FlightSeat WHERE flight_id=@f1 AND seat_id=@s_pl1_1_2;
SELECT flight_seat_id INTO @fs3 FROM FlightSeat WHERE flight_id=@f2 AND seat_id=@s_pl2_1_1;
SELECT flight_seat_id INTO @fs4 FROM FlightSeat WHERE flight_id=@f2 AND seat_id=@s_pl2_1_2;

INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment) VALUES
(@f1,'elli.brinker@example.com',CURDATE(),'paid',500.00); SET @o1 = LAST_INSERT_ID();

INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment) VALUES
(@f1,'guest1@example.com',CURDATE(),'paid',500.00); SET @o2 = LAST_INSERT_ID();

INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment) VALUES
(@f2,'stav.abraham@example.com',CURDATE(),'paid',600.00); SET @o3 = LAST_INSERT_ID();

INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment) VALUES
(@f2,'guest2@example.com',CURDATE(),'paid',600.00); SET @o4 = LAST_INSERT_ID();

INSERT INTO OrderItem (order_id, flight_seat_id) VALUES
(@o1, @fs1),
(@o2, @fs2),
(@o3, @fs3),
(@o4, @fs4);

UPDATE FlightSeat SET status='booked' WHERE flight_seat_id IN (@fs1,@fs2,@fs3,@fs4);

-- =========================
-- 6) Crew placements (optional)
-- =========================
INSERT INTO FlightCrewPlacement (flight_id, id) VALUES
(@f1, 300000001),(@f1, 400000001),(@f1, 400000002),
(@f2, 300000002),(@f2, 400000003),(@f2, 400000004);
