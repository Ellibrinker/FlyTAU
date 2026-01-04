USE `ellibrinker$flytau`;

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
--    Worker.id הוא AUTO_INCREMENT => חייבים לתפוס LAST_INSERT_ID
-- =========================

-- ---- Managers (Workers -> Manager)
INSERT INTO Worker (first_name, last_name, phone_number, city, street, house_num, start_date) VALUES
('Noa', 'Meyron', '050-0000001', 'Tel Aviv', 'Herzl', 1, '2020-01-01');
SET @noa_id = LAST_INSERT_ID();

INSERT INTO Worker (first_name, last_name, phone_number, city, street, house_num, start_date) VALUES
('Stav', 'Abraham', '050-0000002', 'Tel Aviv', 'Dizengoff', 10, '2021-01-01');
SET @stav_id = LAST_INSERT_ID();

INSERT INTO Worker (first_name, last_name, phone_number, city, street, house_num, start_date) VALUES
('Elli', 'Brinker', '050-0000003', 'Tel Aviv', 'Ibn Gabirol', 25, '2022-01-01');
SET @elli_worker_id = LAST_INSERT_ID();

-- בוחרים לשים רק 2 מנהלים (כמו הדרישה), אז נכניס מנהלים ל-Noa ול-Stav
INSERT INTO Manager (id, password) VALUES
(@noa_id, 'admin123'),
(@stav_id, 'admin123');

-- ---- 10 Pilots (Workers -> AirCrew -> Pilot)
-- נשמור את ה-IDs במשתנים @p1..@p10
INSERT INTO Worker (first_name, last_name, phone_number, city, street, house_num, start_date)
VALUES ('Pilot','P1','050-101','Tel Aviv','A',1,'2019-01-01'); SET @p1 = LAST_INSERT_ID();
INSERT INTO Worker (first_name, last_name, phone_number, city, street, house_num, start_date)
VALUES ('Pilot','P2','050-102','Tel Aviv','A',2,'2019-01-01'); SET @p2 = LAST_INSERT_ID();
INSERT INTO Worker (first_name, last_name, phone_number, city, street, house_num, start_date)
VALUES ('Pilot','P3','050-103','Tel Aviv','A',3,'2019-01-01'); SET @p3 = LAST_INSERT_ID();
INSERT INTO Worker (first_name, last_name, phone_number, city, street, house_num, start_date)
VALUES ('Pilot','P4','050-104','Tel Aviv','A',4,'2019-01-01'); SET @p4 = LAST_INSERT_ID();
INSERT INTO Worker (first_name, last_name, phone_number, city, street, house_num, start_date)
VALUES ('Pilot','P5','050-105','Tel Aviv','A',5,'2019-01-01'); SET @p5 = LAST_INSERT_ID();
INSERT INTO Worker (first_name, last_name, phone_number, city, street, house_num, start_date)
VALUES ('Pilot','P6','050-106','Tel Aviv','A',6,'2019-01-01'); SET @p6 = LAST_INSERT_ID();
INSERT INTO Worker (first_name, last_name, phone_number, city, street, house_num, start_date)
VALUES ('Pilot','P7','050-107','Tel Aviv','A',7,'2019-01-01'); SET @p7 = LAST_INSERT_ID();
INSERT INTO Worker (first_name, last_name, phone_number, city, street, house_num, start_date)
VALUES ('Pilot','P8','050-108','Tel Aviv','A',8,'2019-01-01'); SET @p8 = LAST_INSERT_ID();
INSERT INTO Worker (first_name, last_name, phone_number, city, street, house_num, start_date)
VALUES ('Pilot','P9','050-109','Tel Aviv','A',9,'2019-01-01'); SET @p9 = LAST_INSERT_ID();
INSERT INTO Worker (first_name, last_name, phone_number, city, street, house_num, start_date)
VALUES ('Pilot','P10','050-110','Tel Aviv','A',10,'2019-01-01'); SET @p10 = LAST_INSERT_ID();

INSERT INTO AirCrew (id, long_flight_training) VALUES
(@p1, TRUE),(@p2, TRUE),(@p3, TRUE),(@p4, TRUE),(@p5, TRUE),
(@p6, FALSE),(@p7, FALSE),(@p8, FALSE),(@p9, FALSE),(@p10, FALSE);

INSERT INTO Pilot (id) VALUES
(@p1),(@p2),(@p3),(@p4),(@p5),(@p6),(@p7),(@p8),(@p9),(@p10);

-- ---- 20 Flight Attendants (Workers -> AirCrew -> FlightAttendant)
-- נשמור @fa1..@fa20
INSERT INTO Worker (first_name,last_name,phone_number,city,street,house_num,start_date)
VALUES ('FA','F1','050-201','Tel Aviv','B',1,'2022-01-01'); SET @fa1 = LAST_INSERT_ID();
INSERT INTO Worker (first_name,last_name,phone_number,city,street,house_num,start_date)
VALUES ('FA','F2','050-202','Tel Aviv','B',2,'2022-01-01'); SET @fa2 = LAST_INSERT_ID();
INSERT INTO Worker (first_name,last_name,phone_number,city,street,house_num,start_date)
VALUES ('FA','F3','050-203','Tel Aviv','B',3,'2022-01-01'); SET @fa3 = LAST_INSERT_ID();
INSERT INTO Worker (first_name,last_name,phone_number,city,street,house_num,start_date)
VALUES ('FA','F4','050-204','Tel Aviv','B',4,'2022-01-01'); SET @fa4 = LAST_INSERT_ID();
INSERT INTO Worker (first_name,last_name,phone_number,city,street,house_num,start_date)
VALUES ('FA','F5','050-205','Tel Aviv','B',5,'2022-01-01'); SET @fa5 = LAST_INSERT_ID();
INSERT INTO Worker (first_name,last_name,phone_number,city,street,house_num,start_date)
VALUES ('FA','F6','050-206','Tel Aviv','B',6,'2022-01-01'); SET @fa6 = LAST_INSERT_ID();
INSERT INTO Worker (first_name,last_name,phone_number,city,street,house_num,start_date)
VALUES ('FA','F7','050-207','Tel Aviv','B',7,'2022-01-01'); SET @fa7 = LAST_INSERT_ID();
INSERT INTO Worker (first_name,last_name,phone_number,city,street,house_num,start_date)
VALUES ('FA','F8','050-208','Tel Aviv','B',8,'2022-01-01'); SET @fa8 = LAST_INSERT_ID();
INSERT INTO Worker (first_name,last_name,phone_number,city,street,house_num,start_date)
VALUES ('FA','F9','050-209','Tel Aviv','B',9,'2022-01-01'); SET @fa9 = LAST_INSERT_ID();
INSERT INTO Worker (first_name,last_name,phone_number,city,street,house_num,start_date)
VALUES ('FA','F10','050-210','Tel Aviv','B',10,'2022-01-01'); SET @fa10 = LAST_INSERT_ID();
INSERT INTO Worker (first_name,last_name,phone_number,city,street,house_num,start_date)
VALUES ('FA','F11','050-211','Tel Aviv','B',11,'2022-01-01'); SET @fa11 = LAST_INSERT_ID();
INSERT INTO Worker (first_name,last_name,phone_number,city,street,house_num,start_date)
VALUES ('FA','F12','050-212','Tel Aviv','B',12,'2022-01-01'); SET @fa12 = LAST_INSERT_ID();
INSERT INTO Worker (first_name,last_name,phone_number,city,street,house_num,start_date)
VALUES ('FA','F13','050-213','Tel Aviv','B',13,'2022-01-01'); SET @fa13 = LAST_INSERT_ID();
INSERT INTO Worker (first_name,last_name,phone_number,city,street,house_num,start_date)
VALUES ('FA','F14','050-214','Tel Aviv','B',14,'2022-01-01'); SET @fa14 = LAST_INSERT_ID();
INSERT INTO Worker (first_name,last_name,phone_number,city,street,house_num,start_date)
VALUES ('FA','F15','050-215','Tel Aviv','B',15,'2022-01-01'); SET @fa15 = LAST_INSERT_ID();
INSERT INTO Worker (first_name,last_name,phone_number,city,street,house_num,start_date)
VALUES ('FA','F16','050-216','Tel Aviv','B',16,'2022-01-01'); SET @fa16 = LAST_INSERT_ID();
INSERT INTO Worker (first_name,last_name,phone_number,city,street,house_num,start_date)
VALUES ('FA','F17','050-217','Tel Aviv','B',17,'2022-01-01'); SET @fa17 = LAST_INSERT_ID();
INSERT INTO Worker (first_name,last_name,phone_number,city,street,house_num,start_date)
VALUES ('FA','F18','050-218','Tel Aviv','B',18,'2022-01-01'); SET @fa18 = LAST_INSERT_ID();
INSERT INTO Worker (first_name,last_name,phone_number,city,street,house_num,start_date)
VALUES ('FA','F19','050-219','Tel Aviv','B',19,'2022-01-01'); SET @fa19 = LAST_INSERT_ID();
INSERT INTO Worker (first_name,last_name,phone_number,city,street,house_num,start_date)
VALUES ('FA','F20','050-220','Tel Aviv','B',20,'2022-01-01'); SET @fa20 = LAST_INSERT_ID();

INSERT INTO AirCrew (id, long_flight_training) VALUES
(@fa1, TRUE),(@fa2, TRUE),(@fa3, TRUE),(@fa4, TRUE),(@fa5, TRUE),
(@fa6, FALSE),(@fa7, FALSE),(@fa8, FALSE),(@fa9, FALSE),(@fa10, FALSE),
(@fa11, TRUE),(@fa12, TRUE),(@fa13, FALSE),(@fa14, FALSE),(@fa15, TRUE),
(@fa16, FALSE),(@fa17, TRUE),(@fa18, FALSE),(@fa19, TRUE),(@fa20, FALSE);

INSERT INTO FlightAttendant (id) VALUES
(@fa1),(@fa2),(@fa3),(@fa4),(@fa5),(@fa6),(@fa7),(@fa8),(@fa9),(@fa10),
(@fa11),(@fa12),(@fa13),(@fa14),(@fa15),(@fa16),(@fa17),(@fa18),(@fa19),(@fa20);

-- =========================
-- 3) Planes + classes + seats (minimal)
--    Plane.plane_id AUTO_INCREMENT => נשמור משתנים @pl1..@pl6
-- =========================
INSERT INTO Plane (manufacturer, purchase_date) VALUES ('Boeing','2018-01-01'); SET @pl1 = LAST_INSERT_ID();
INSERT INTO Plane (manufacturer, purchase_date) VALUES ('Airbus','2019-01-01'); SET @pl2 = LAST_INSERT_ID();
INSERT INTO Plane (manufacturer, purchase_date) VALUES ('Boeing','2020-01-01'); SET @pl3 = LAST_INSERT_ID();
INSERT INTO Plane (manufacturer, purchase_date) VALUES ('Airbus','2021-01-01'); SET @pl4 = LAST_INSERT_ID();
INSERT INTO Plane (manufacturer, purchase_date) VALUES ('Embraer','2022-01-01'); SET @pl5 = LAST_INSERT_ID();
INSERT INTO Plane (manufacturer, purchase_date) VALUES ('Embraer','2023-01-01'); SET @pl6 = LAST_INSERT_ID();

INSERT INTO BigPlane (plane_id) VALUES (@pl1),(@pl2),(@pl3);
INSERT INTO SmallPlane (plane_id) VALUES (@pl4),(@pl5),(@pl6);

INSERT INTO Class (plane_id, class_type, rows_number, columns_number) VALUES
(@pl1,'Regular',20,6),(@pl1,'Business',5,4),
(@pl2,'Regular',22,6),(@pl2,'Business',6,4),
(@pl3,'Regular',18,6),(@pl3,'Business',4,4),
(@pl4,'Regular',15,4),
(@pl5,'Regular',12,4),
(@pl6,'Regular',10,4);

-- Seats (כמה מושבים מינימליים) - Seat.seat_id AUTO_INCREMENT => לא שמים seat_id
INSERT INTO Seat (row_num, column_number, plane_id, class_type) VALUES
(1,1,@pl1,'Regular'),
(1,2,@pl1,'Regular'),
(1,3,@pl1,'Regular');
SET @s1 = LAST_INSERT_ID();  -- זה יהיה המושב השלישי (האחרון) שנכנס

-- כדי לתפוס גם את שני המושבים הראשונים, נשלוף לפי (plane,row,col):
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
--    Flight.flight_id AUTO_INCREMENT => נשמור @f1..@f4
-- =========================
INSERT INTO Airway (origin_airport, destination_airport, duration) VALUES
('TLV','ATH',120),
('TLV','ROM',180),
('TLV','PAR',300),
('TLV','LON',330);

INSERT INTO Flight (plane_id, origin_airport, destination_airport, departure_date, departure_time, status)
VALUES (@pl1,'TLV','ATH','2026-01-10','10:00:00','open');
SET @f1 = LAST_INSERT_ID();

INSERT INTO Flight (plane_id, origin_airport, destination_airport, departure_date, departure_time, status)
VALUES (@pl2,'TLV','ROM','2026-01-11','12:30:00','open');
SET @f2 = LAST_INSERT_ID();

INSERT INTO Flight (plane_id, origin_airport, destination_airport, departure_date, departure_time, status)
VALUES (@pl3,'TLV','PAR','2026-01-12','09:15:00','open');
SET @f3 = LAST_INSERT_ID();

INSERT INTO Flight (plane_id, origin_airport, destination_airport, departure_date, departure_time, status)
VALUES (@pl4,'TLV','LON','2026-01-13','14:45:00','open');
SET @f4 = LAST_INSERT_ID();

INSERT INTO FlightPricing (flight_id, class_type, price) VALUES
(@f1,'Regular',500.00),(@f1,'Business',900.00),
(@f2,'Regular',600.00),(@f2,'Business',1100.00),
(@f3,'Regular',750.00),(@f3,'Business',1400.00),
(@f4,'Regular',800.00);

-- =========================
-- 5) FlightSeat + Orders + OrderItems (4 orders)
--    FlightSeat.flight_seat_id, FlightOrder.order_id, OrderItem.item_id = AUTO_INCREMENT
-- =========================
INSERT INTO FlightSeat (flight_id, seat_id, status) VALUES
(@f1, @s_pl1_1_1, 'available'),
(@f1, @s_pl1_1_2, 'available'),
(@f2, @s_pl2_1_1, 'available'),
(@f2, @s_pl2_1_2, 'available');

-- תופסים את ה-flight_seat_id שנוצר לכל אחד לפי (flight_id, seat_id)
SELECT flight_seat_id INTO @fs1 FROM FlightSeat WHERE flight_id=@f1 AND seat_id=@s_pl1_1_1;
SELECT flight_seat_id INTO @fs2 FROM FlightSeat WHERE flight_id=@f1 AND seat_id=@s_pl1_1_2;
SELECT flight_seat_id INTO @fs3 FROM FlightSeat WHERE flight_id=@f2 AND seat_id=@s_pl2_1_1;
SELECT flight_seat_id INTO @fs4 FROM FlightSeat WHERE flight_id=@f2 AND seat_id=@s_pl2_1_2;

INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment) VALUES
(@f1,'eli1@example.com',CURDATE(),'paid',500.00);
SET @o1 = LAST_INSERT_ID();

INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment) VALUES
(@f1,'guest1@example.com',CURDATE(),'paid',500.00);
SET @o2 = LAST_INSERT_ID();

INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment) VALUES
(@f2,'eli2@example.com',CURDATE(),'paid',600.00);
SET @o3 = LAST_INSERT_ID();

INSERT INTO FlightOrder (flight_id, email, execution_date, status, total_payment) VALUES
(@f2,'guest2@example.com',CURDATE(),'paid',600.00);
SET @o4 = LAST_INSERT_ID();

INSERT INTO OrderItem (order_id, flight_seat_id) VALUES
(@o1, @fs1),
(@o2, @fs2),
(@o3, @fs3),
(@o4, @fs4);

UPDATE FlightSeat SET status='booked' WHERE flight_seat_id IN (@fs1,@fs2,@fs3,@fs4);

-- =========================
-- 6) Crew placements (optional)
--    משתמשים במשתנים של הטייסים/דיילים שיצרנו
-- =========================
INSERT INTO FlightCrewPlacement (flight_id, id) VALUES
(@f1, @p1),(@f1, @fa1),(@f1, @fa2),
(@f2, @p2),(@f2, @fa3),(@f2, @fa4);
