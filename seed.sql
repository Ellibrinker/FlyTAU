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
-- 3) Planes + classes + seats
--    plane_id AUTO_INCREMENT => שומרים משתנים
-- =========================
INSERT INTO Plane (manufacturer, purchase_date) VALUES ('Boeing','2018-01-01');   SET @pl1 = LAST_INSERT_ID();
INSERT INTO Plane (manufacturer, purchase_date) VALUES ('Airbus','2019-01-01');   SET @pl2 = LAST_INSERT_ID();
INSERT INTO Plane (manufacturer, purchase_date) VALUES ('Boeing','2020-01-01');   SET @pl3 = LAST_INSERT_ID();
INSERT INTO Plane (manufacturer, purchase_date) VALUES ('Airbus','2021-01-01');   SET @pl4 = LAST_INSERT_ID();
INSERT INTO Plane (manufacturer, purchase_date) VALUES ('Dassault','2022-01-01'); SET @pl5 = LAST_INSERT_ID();
INSERT INTO Plane (manufacturer, purchase_date) VALUES ('Dassault','2023-01-01'); SET @pl6 = LAST_INSERT_ID();

-- NEW planes (extra)
INSERT INTO Plane (manufacturer, purchase_date) VALUES ('Boeing','2020-06-01');   SET @pl7 = LAST_INSERT_ID();
INSERT INTO Plane (manufacturer, purchase_date) VALUES ('Airbus','2021-06-01');   SET @pl8 = LAST_INSERT_ID();
INSERT INTO Plane (manufacturer, purchase_date) VALUES ('Dassault','2024-01-01'); SET @pl9 = LAST_INSERT_ID();

INSERT INTO BigPlane (plane_id) VALUES (@pl1),(@pl2),(@pl3),(@pl7),(@pl8);
INSERT INTO SmallPlane (plane_id) VALUES (@pl4),(@pl5),(@pl6),(@pl9);

INSERT INTO Class (plane_id, class_type, rows_number, columns_number) VALUES
(@pl1,'Regular',20,6),(@pl1,'Business',5,4),
(@pl2,'Regular',22,6),(@pl2,'Business',6,4),
(@pl3,'Regular',18,6),(@pl3,'Business',4,4),
(@pl4,'Regular',15,4),
(@pl5,'Regular',12,4),
(@pl6,'Regular',10,4),

-- NEW classes
(@pl7,'Regular',20,6),(@pl7,'Business',5,4),
(@pl8,'Regular',22,6),(@pl8,'Business',6,4),
(@pl9,'Regular',12,4);

-- Seats (sample seats – enough to show the structure clearly)
-- plane 1: 6 seats
INSERT INTO Seat (row_num, column_number, plane_id, class_type) VALUES
(1,1,@pl1,'Regular'), (1,2,@pl1,'Regular'), (1,3,@pl1,'Regular'),
(2,1,@pl1,'Regular'), (2,2,@pl1,'Regular'), (2,3,@pl1,'Regular');

SELECT seat_id INTO @s_pl1_1_1 FROM Seat WHERE plane_id=@pl1 AND row_num=1 AND column_number=1;
SELECT seat_id INTO @s_pl1_1_2 FROM Seat WHERE plane_id=@pl1 AND row_num=1 AND column_number=2;
SELECT seat_id INTO @s_pl1_2_1 FROM Seat WHERE plane_id=@pl1 AND row_num=2 AND column_number=1;
SELECT seat_id INTO @s_pl1_2_2 FROM Seat WHERE plane_id=@pl1 AND row_num=2 AND column_number=2;

-- plane 2: 6 seats
INSERT INTO Seat (row_num, column_number, plane_id, class_type) VALUES
(1,1,@pl2,'Regular'), (1,2,@pl2,'Regular'), (1,3,@pl2,'Regular'),
(2,1,@pl2,'Regular'), (2,2,@pl2,'Regular'), (2,3,@pl2,'Regular');

SELECT seat_id INTO @s_pl2_1_1 FROM Seat WHERE plane_id=@pl2 AND row_num=1 AND column_number=1;
SELECT seat_id INTO @s_pl2_1_2 FROM Seat WHERE plane_id=@pl2 AND row_num=1 AND column_number=2;
SELECT seat_id INTO @s_pl2_2_1 FROM Seat WHERE plane_id=@pl2 AND row_num=2 AND column_number=1;
SELECT seat_id INTO @s_pl2_2_2 FROM Seat WHERE plane_id=@pl2 AND row_num=2 AND column_number=2;

-- NEW plane 7: 4 seats
INSERT INTO Seat (row_num, column_number, plane_id, class_type) VALUES
(1,1,@pl7,'Regular'), (1,2,@pl7,'Regular'),
(2,1,@pl7,'Regular'), (2,2,@pl7,'Regular');

SELECT seat_id INTO @s_pl7_1_1 FROM Seat WHERE plane_id=@pl7 AND row_num=1 AND column_number=1;
SELECT seat_id INTO @s_pl7_1_2 FROM Seat WHERE plane_id=@pl7 AND row_num=1 AND column_number=2;

-- =========================
-- 4) Airway + Flights
-- =========================
INSERT INTO Airway (origin_airport, destination_airport, duration) VALUES
-- original
('TLV','ATH',120),
('TLV','ROM',180),
('TLV','PAR',300),
('TLV','LON',330),

-- added (full list)
('TLV','LCA',60),  ('LCA','TLV',60),
('TLV','IST',150), ('IST','TLV',150),
('TLV','FCO',210), ('FCO','TLV',210),
('TLV','MXP',240), ('MXP','TLV',240),
('TLV','CDG',300), ('CDG','TLV',300),
('TLV','AMS',315), ('AMS','TLV',315),
('TLV','FRA',285), ('FRA','TLV',285),
('TLV','MUC',270), ('MUC','TLV',270),
('TLV','VIE',240), ('VIE','TLV',240),
('TLV','ZRH',255), ('ZRH','TLV',255),
('TLV','BCN',270), ('BCN','TLV',270),
('TLV','MAD',300), ('MAD','TLV',300),
('TLV','LIS',330), ('LIS','TLV',330),
('TLV','LHR',330), ('LHR','TLV',330),
('TLV','BRU',315), ('BRU','TLV',315),
('TLV','CPH',270), ('CPH','TLV',270),
('TLV','ARN',300), ('ARN','TLV',300),
('TLV','OSL',330), ('OSL','TLV',330),
('TLV','HEL',330), ('HEL','TLV',330),
('TLV','WAW',240), ('WAW','TLV',240),
('TLV','PRG',255), ('PRG','TLV',255),
('TLV','BUD',240), ('BUD','TLV',240),
('TLV','OTP',180), ('OTP','TLV',180),
('TLV','SOF',165), ('SOF','TLV',165),
('TLV','BEG',150), ('BEG','TLV',150),
('TLV','SKG',120), ('SKG','TLV',120),
('CDG','AMS',75), ('AMS','CDG',75),
('CDG','FRA',80), ('FRA','CDG',80),
('AMS','FRA',70), ('FRA','AMS',70),
('FRA','VIE',80), ('VIE','FRA',80),
('VIE','ZRH',85), ('ZRH','VIE',85),
('BCN','MAD',75), ('MAD','BCN',75),
('LHR','CDG',75), ('CDG','LHR',75),
('FCO','MXP',70), ('MXP','FCO',70),
('PRG','WAW',75), ('WAW','PRG',75),
('BUD','VIE',45), ('VIE','BUD',45),
('CPH','ARN',60), ('ARN','CPH',60),
('ARN','OSL',55), ('OSL','ARN',55),
('HEL','ARN',60), ('ARN','HEL',60);

-- Flights (original 4)
INSERT INTO Flight (plane_id, origin_airport, destination_airport, departure_date, departure_time, status)
VALUES (@pl1,'TLV','ATH','2026-01-10','10:00:00','open'); SET @f1 = LAST_INSERT_ID();

INSERT INTO Flight (plane_id, origin_airport, destination_airport, departure_date, departure_time, status)
VALUES (@pl2,'TLV','ROM','2026-01-11','12:30:00','open'); SET @f2 = LAST_INSERT_ID();

INSERT INTO Flight (plane_id, origin_airport, destination_airport, departure_date, departure_time, status)
VALUES (@pl3,'TLV','PAR','2026-01-12','09:15:00','open'); SET @f3 = LAST_INSERT_ID();

INSERT INTO Flight (plane_id, origin_airport, destination_airport, departure_date, departure_time, status)
VALUES (@pl4,'TLV','LON','2026-01-13','14:45:00','open'); SET @f4 = LAST_INSERT_ID();

-- NEW Flights (extra)
INSERT INTO Flight (plane_id, origin_airport, destination_airport, departure_date, departure_time, status)
VALUES (@pl7,'TLV','LCA','2026-01-14','08:00:00','open'); SET @f5 = LAST_INSERT_ID();

INSERT INTO Flight (plane_id, origin_airport, destination_airport, departure_date, departure_time, status)
VALUES (@pl8,'TLV','FCO','2026-01-15','16:15:00','open'); SET @f6 = LAST_INSERT_ID();

INSERT INTO FlightPricing (flight_id, class_type, price) VALUES
(@f1,'Regular',500.00),(@f1,'Business',900.00),
(@f2,'Regular',600.00),(@f2,'Business',1100.00),
(@f3,'Regular',750.00),(@f3,'Business',1400.00),
(@f4,'Regular',800.00),
(@f5,'Regular',350.00),(@f5,'Business',650.00),
(@f6,'Regular',900.00),(@f6,'Business',1600.00);

-- =========================
-- 5) FlightSeat + Orders + OrderItems
-- =========================
-- original flight seats
INSERT INTO FlightSeat (flight_id, seat_id, status) VALUES
(@f1, @s_pl1_1_1, 'available'),
(@f1, @s_pl1_1_2, 'available'),
(@f2, @s_pl2_1_1, 'available'),
(@f2, @s_pl2_1_2, 'available');

-- NEW flight seats for new flights (using plane 1/2/7 sample seats)
INSERT INTO FlightSeat (flight_id, seat_id, status) VALUES
(@f5, @s_pl7_1_1, 'available'),
(@f5, @s_pl7_1_2, 'available'),
(@f6, @s_pl2_2_1, 'available'),
(@f6, @s_pl2_2_2, 'available');

-- fetch flight_seat_ids for orders
SELECT flight_seat_id INTO @fs1 FROM FlightSeat WHERE flight_id=@f1 AND seat_id=@s_pl1_1_1;
SELECT flight_seat_id INTO @fs2 FROM FlightSeat WHERE flight_id=@f1 AND seat_id=@s_pl1_1_2;
SELECT flight_seat_id INTO @fs3 FROM FlightSeat WHERE flight_id=@f2 AND seat_id=@s_pl2_1_1;
SELECT flight_seat_id INTO @fs4 FROM FlightSeat WHERE flight_id=@f2 AND seat_id=@s_pl2_1_2;

SELECT flight_seat_id INTO @fs5 FROM FlightSeat WHERE flight_id=@f5 AND seat_id=@s_pl7_1_1;
SELECT flight_seat_id INTO @fs6 FROM FlightSeat WHERE flight_id=@f6 AND seat_id=@s_pl2_2_1;

-- Orders (original 4 + 2 new)
INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment) VALUES
(@f1,'elli.brinker@example.com',CURDATE(),'paid',500.00); SET @o1 = LAST_INSERT_ID();

INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment) VALUES
(@f1,'guest1@example.com',CURDATE(),'paid',500.00); SET @o2 = LAST_INSERT_ID();

INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment) VALUES
(@f2,'stav.abraham@example.com',CURDATE(),'paid',600.00); SET @o3 = LAST_INSERT_ID();

INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment) VALUES
(@f2,'guest2@example.com',CURDATE(),'paid',600.00); SET @o4 = LAST_INSERT_ID();

-- NEW orders
INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment) VALUES
(@f5,'elli.brinker@example.com',CURDATE(),'paid',350.00); SET @o5 = LAST_INSERT_ID();

INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment) VALUES
(@f6,'guest1@example.com',CURDATE(),'paid',900.00); SET @o6 = LAST_INSERT_ID();

INSERT INTO OrderItem (order_id, flight_seat_id) VALUES
(@o1, @fs1),
(@o2, @fs2),
(@o3, @fs3),
(@o4, @fs4),
(@o5, @fs5),
(@o6, @fs6);

UPDATE FlightSeat
SET status='booked'
WHERE flight_seat_id IN (@fs1,@fs2,@fs3,@fs4,@fs5,@fs6);

-- =========================
-- 6) Crew placements (optional)
-- =========================
INSERT INTO FlightCrewPlacement (flight_id, id) VALUES
(@f1, 300000001),(@f1, 400000001),(@f1, 400000002),
(@f2, 300000002),(@f2, 400000003),(@f2, 400000004),
(@f5, 300000003),(@f5, 400000005),(@f5, 400000006);



USE `ellibrinker$flytau`;

-- A) Boeing Business seat on @pl1 (choose a free coord)
INSERT INTO Seat (row_num, column_number, plane_id, class_type)
VALUES (3, 1, @pl1, 'Business');

SELECT seat_id INTO @s_pl1_b_3_1
FROM Seat
WHERE plane_id = @pl1 AND row_num = 3 AND column_number = 1 AND class_type = 'Business'
ORDER BY seat_id DESC
LIMIT 1;

INSERT INTO FlightSeat (flight_id, seat_id, status)
VALUES (@f1, @s_pl1_b_3_1, 'available');

SELECT flight_seat_id INTO @fs7
FROM FlightSeat
WHERE flight_id = @f1 AND seat_id = @s_pl1_b_3_1
ORDER BY flight_seat_id DESC
LIMIT 1;

INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment)
VALUES (@f1, 'guest2@example.com', CURDATE(), 'paid', 900.00);
SET @o7 = LAST_INSERT_ID();

INSERT INTO OrderItem (order_id, flight_seat_id)
VALUES (@o7, @fs7);

UPDATE FlightSeat
SET status = 'booked'
WHERE flight_seat_id = @fs7;


-- B) Airbus Business seat on @pl2 (choose a free coord)
INSERT INTO Seat (row_num, column_number, plane_id, class_type)
VALUES (3, 1, @pl2, 'Business');

SELECT seat_id INTO @s_pl2_b_3_1
FROM Seat
WHERE plane_id = @pl2 AND row_num = 3 AND column_number = 1 AND class_type = 'Business'
ORDER BY seat_id DESC
LIMIT 1;

INSERT INTO FlightSeat (flight_id, seat_id, status)
VALUES (@f2, @s_pl2_b_3_1, 'available');

SELECT flight_seat_id INTO @fs8
FROM FlightSeat
WHERE flight_id = @f2 AND seat_id = @s_pl2_b_3_1
ORDER BY flight_seat_id DESC
LIMIT 1;

INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment)
VALUES (@f2, 'guest1@example.com', CURDATE(), 'paid', 1100.00);
SET @o8 = LAST_INSERT_ID();

INSERT INTO OrderItem (order_id, flight_seat_id)
VALUES (@o8, @fs8);

UPDATE FlightSeat
SET status = 'booked'
WHERE flight_seat_id = @fs8;


USE `ellibrinker$flytau`;

-- 1) Add a seat to Dassault plane @pl5 (Small)
INSERT INTO Seat (row_num, column_number, plane_id, class_type)
VALUES (99, 99, @pl5, 'Regular');

SELECT seat_id INTO @s_pl5_r_99_99
FROM Seat
WHERE plane_id = @pl5 AND row_num = 99 AND column_number = 99 AND class_type = 'Regular'
ORDER BY seat_id DESC
LIMIT 1;

-- 2) Create a flight on Dassault plane @pl5
INSERT INTO Flight (plane_id, origin_airport, destination_airport, departure_date, departure_time, status)
VALUES (@pl5, 'TLV', 'ATH', '2026-01-16', '11:00:00', 'open');
SET @f7 = LAST_INSERT_ID();

-- 3) Pricing (Regular)
INSERT INTO FlightPricing (flight_id, class_type, price)
VALUES (@f7, 'Regular', 400.00);

-- 4) FlightSeat
INSERT INTO FlightSeat (flight_id, seat_id, status)
VALUES (@f7, @s_pl5_r_99_99, 'available');

SELECT flight_seat_id INTO @fs9
FROM FlightSeat
WHERE flight_id = @f7 AND seat_id = @s_pl5_r_99_99
ORDER BY flight_seat_id DESC
LIMIT 1;

-- 5) Order + item
INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment)
VALUES (@f7, 'stav.abraham@example.com', CURDATE(), 'paid', 400.00);
SET @o9 = LAST_INSERT_ID();

INSERT INTO OrderItem (order_id, flight_seat_id)
VALUES (@o9, @fs9);

UPDATE FlightSeat
SET status = 'booked'
WHERE flight_seat_id = @fs9;


USE `ellibrinker$flytau`;

-- =========================================================
-- ADD MORE ORDERS ACROSS MONTHS (to get 5+ monthly rows)
-- Months added: 2025-09, 2025-10, 2025-11, 2025-12
-- Existing orders already create 2026-01 (via CURDATE in your seed)
-- =========================================================

/* -----------------------------
   2025-09 (customer cancelled)
   Add a NEW Regular seat on plane @pl1, attach it to flight @f1
------------------------------ */
INSERT INTO Seat (row_num, column_number, plane_id, class_type)
VALUES (4, 1, @pl1, 'Regular');

SELECT seat_id INTO @s_pl1_r_4_1
FROM Seat
WHERE plane_id = @pl1 AND row_num = 4 AND column_number = 1 AND class_type = 'Regular'
ORDER BY seat_id DESC
LIMIT 1;

INSERT INTO FlightSeat (flight_id, seat_id, status)
VALUES (@f1, @s_pl1_r_4_1, 'available');

SELECT flight_seat_id INTO @fs10
FROM FlightSeat
WHERE flight_id = @f1 AND seat_id = @s_pl1_r_4_1
ORDER BY flight_seat_id DESC
LIMIT 1;

INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment)
VALUES (@f1, 'guest1@example.com', '2025-09-05', 'customer cancelled', 25.00);
SET @o10 = LAST_INSERT_ID();

INSERT INTO OrderItem (order_id, flight_seat_id)
VALUES (@o10, @fs10);

UPDATE FlightSeat
SET status = 'booked'
WHERE flight_seat_id = @fs10;


/* -----------------------------
   2025-10 (paid)
   Add a NEW Regular seat on plane @pl2, attach it to flight @f2
------------------------------ */
INSERT INTO Seat (row_num, column_number, plane_id, class_type)
VALUES (4, 1, @pl2, 'Regular');

SELECT seat_id INTO @s_pl2_r_4_1
FROM Seat
WHERE plane_id = @pl2 AND row_num = 4 AND column_number = 1 AND class_type = 'Regular'
ORDER BY seat_id DESC
LIMIT 1;

INSERT INTO FlightSeat (flight_id, seat_id, status)
VALUES (@f2, @s_pl2_r_4_1, 'available');

SELECT flight_seat_id INTO @fs11
FROM FlightSeat
WHERE flight_id = @f2 AND seat_id = @s_pl2_r_4_1
ORDER BY flight_seat_id DESC
LIMIT 1;

INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment)
VALUES (@f2, 'guest2@example.com', '2025-10-10', 'paid', 600.00);
SET @o11 = LAST_INSERT_ID();

INSERT INTO OrderItem (order_id, flight_seat_id)
VALUES (@o11, @fs11);

UPDATE FlightSeat
SET status = 'booked'
WHERE flight_seat_id = @fs11;


/* -----------------------------
   2025-11 (system_cancelled)
   Add a NEW Regular seat on plane @pl7, attach it to flight @f5
------------------------------ */
INSERT INTO Seat (row_num, column_number, plane_id, class_type)
VALUES (3, 1, @pl7, 'Regular');

SELECT seat_id INTO @s_pl7_r_3_1
FROM Seat
WHERE plane_id = @pl7 AND row_num = 3 AND column_number = 1 AND class_type = 'Regular'
ORDER BY seat_id DESC
LIMIT 1;

INSERT INTO FlightSeat (flight_id, seat_id, status)
VALUES (@f5, @s_pl7_r_3_1, 'available');

SELECT flight_seat_id INTO @fs12
FROM FlightSeat
WHERE flight_id = @f5 AND seat_id = @s_pl7_r_3_1
ORDER BY flight_seat_id DESC
LIMIT 1;

INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment)
VALUES (@f5, 'elli.brinker@example.com', '2025-11-12', 'system_cancelled', 0.00);
SET @o12 = LAST_INSERT_ID();

INSERT INTO OrderItem (order_id, flight_seat_id)
VALUES (@o12, @fs12);

UPDATE FlightSeat
SET status = 'booked'
WHERE flight_seat_id = @fs12;


/* -----------------------------
   2025-12 (paid)
   Add a NEW Regular seat on plane @pl8 (flight @f6 uses @pl8), attach it to flight @f6
------------------------------ */
INSERT INTO Seat (row_num, column_number, plane_id, class_type)
VALUES (3, 1, @pl8, 'Regular');

SELECT seat_id INTO @s_pl8_r_3_1
FROM Seat
WHERE plane_id = @pl8 AND row_num = 3 AND column_number = 1 AND class_type = 'Regular'
ORDER BY seat_id DESC
LIMIT 1;

INSERT INTO FlightSeat (flight_id, seat_id, status)
VALUES (@f6, @s_pl8_r_3_1, 'available');

SELECT flight_seat_id INTO @fs13
FROM FlightSeat
WHERE flight_id = @f6 AND seat_id = @s_pl8_r_3_1
ORDER BY flight_seat_id DESC
LIMIT 1;

INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment)
VALUES (@f6, 'stav.abraham@example.com', '2025-12-20', 'paid', 900.00);
SET @o13 = LAST_INSERT_ID();

INSERT INTO OrderItem (order_id, flight_seat_id)
VALUES (@o13, @fs13);

UPDATE FlightSeat
SET status = 'booked'
WHERE flight_seat_id = @fs13;
