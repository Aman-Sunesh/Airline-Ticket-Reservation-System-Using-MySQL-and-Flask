-- Airlines
INSERT INTO Airline VALUES ('Jet Blue');
INSERT INTO Airline VALUES ('Etihad Airways');
INSERT INTO Airline VALUES ('Emirates');
INSERT INTO Airline VALUES ('United Airlines');
INSERT INTO Airline VALUES ('American Airlines');
INSERT INTO Airline VALUES ('British Airways');



-- Airports
INSERT INTO Airport VALUES ('JFK', 'New York City', 'USA', 'international');
INSERT INTO Airport VALUES ('PVG', 'Shanghai', 'China', 'international');
INSERT INTO Airport VALUES ('DXB', 'Dubai', 'UAE', 'international');
INSERT INTO Airport VALUES ('AUH', 'Abu Dhabi', 'UAE', 'international');
INSERT INTO Airport VALUES ('SYD', 'Sydney', 'Australia', 'international');
INSERT INTO Airport VALUES ('LHR', 'London Heathrow', 'UK', 'international');


-- Airplane
INSERT INTO Airplane VALUES ('A321-JB1', 'Jet Blue', 200, 'Airbus', 4);
INSERT INTO Airplane VALUES ('A350-BA1', 'British Airways', 350, 'Airbus', 1);
INSERT INTO Airplane VALUES ('E190-JB1', 'Jet Blue', 100, 'Embraer', 7);
INSERT INTO Airplane VALUES ('A320-JB2', 'Jet Blue', 180, 'Airbus', 6);
INSERT INTO Airplane VALUES ('A380-EY1', 'Etihad Airways', 489, 'Airbus', 6);
INSERT INTO Airplane VALUES ('B789-EY2', 'Etihad Airways', 299, 'Boeing', 4);
INSERT INTO Airplane VALUES ('A380-EK1', 'Emirates', 517, 'Airbus', 5);
INSERT INTO Airplane VALUES ('B77W-EK2', 'Emirates', 360, 'Boeing', 8);
INSERT INTO Airplane VALUES ('B738-UA1', 'United Airlines', 160, 'Boeing', 9);
INSERT INTO Airplane VALUES ('A321-AA1', 'American Airlines', 190, 'Airbus', 7);


-- AirlineStaff
INSERT INTO AirlineStaff VALUES ('j.rivera', MD5('JB-Admin#2025'), 'Jet Blue', 'Jordan', 'Rivera', '1990-01-01', 'j.rivera@jetblue.com');
INSERT INTO AirlineStaff VALUES ('a.alnuaimi', MD5('EY-Admin#2025'), 'Etihad Airways', 'Amina', 'Al Nuaimi', '1988-06-15','a.alnuaimi@etihad.ae');
INSERT INTO AirlineStaff VALUES ('o.alhassan', MD5('EK-Admin#2025'), 'Emirates', 'Omar', 'Al Hasan', '1985-03-22', 'o.alhassan@emirates.com');
INSERT INTO AirlineStaff VALUES ('s.hughes', MD5('UA-Admin#2025'), 'United Airlines', 'Sarah', 'Hughes', '1986-11-09', 's.hughes@united.com');
INSERT INTO AirlineStaff VALUES ('d.nguyen', MD5('AA-Admin#2025'), 'American Airlines', 'David', 'Nguyen', '1988-05-30', 'd.nguyen@aa.com');
INSERT INTO AirlineStaff VALUES ('l.perera', MD5('EK-OPS#2025'), 'Emirates', 'Lakshmi', 'Perera', '1991-02-14', 'l.perera@emirates.com');
INSERT INTO AirlineStaff VALUES ('h.alhammadi', MD5('EY-OPS#2025'), 'Etihad Airways', 'Huda','Al Hammadi', '1993-07-19', 'h.alhammadi@etihad.ae');


-- StaffPhoneNo
INSERT INTO StaffPhoneNo VALUES ('j.rivera', '+1-718-555-1212');
INSERT INTO StaffPhoneNo VALUES ('j.rivera', '+1-718-555-3434');
INSERT INTO StaffPhoneNo VALUES ('a.alnuaimi', '+971-2-555-0101');
INSERT INTO StaffPhoneNo VALUES ('o.alhassan', '+971-4-555-0202');
INSERT INTO StaffPhoneNo VALUES ('s.hughes', '+1-312-555-0303');
INSERT INTO StaffPhoneNo VALUES ('d.nguyen', '+1-817-555-0404');
INSERT INTO StaffPhoneNo VALUES ('l.perera', '+971-4-555-0606');
INSERT INTO StaffPhoneNo VALUES ('h.alhammadi', '+971-2-555-0707');


-- Flight
INSERT INTO Flight VALUES ('B61220', '2025-10-10 07:00:00', 'Jet Blue', 'E190-JB1', 'JFK', 'PVG', '2025-10-11 00:10:00', 'delayed', 650.00);
INSERT INTO Flight VALUES ('BA676', '2025-12-25 20:15:00', 'British Airways', 'A350-BA1', 'JFK', 'LHR', '2025-12-26 08:10:00', 'on-time', 650.00);
INSERT INTO Flight VALUES ('EK303',  '2025-10-15 23:15:00', 'Emirates', 'B77W-EK2', 'DXB', 'JFK', '2025-10-16 07:30:00', 'on-time', 920.00);
INSERT INTO Flight VALUES ('B61234', '2025-11-10 09:00:00', 'Jet Blue', 'A321-JB1', 'JFK', 'PVG', '2025-11-11 01:10:00', 'on-time', 750.00);
INSERT INTO Flight VALUES ('B61235', '2025-11-15 13:30:00', 'Jet Blue', 'A320-JB2', 'PVG', 'JFK', '2025-11-15 20:10:00', 'delayed', 730.00);
INSERT INTO Flight VALUES ('EY101',  '2025-11-20 02:00:00', 'Etihad Airways', 'B789-EY2', 'AUH', 'JFK', '2025-11-20 09:30:00', 'delayed', 820.00);
INSERT INTO Flight VALUES ('EK202',  '2025-12-05 22:30:00', 'Emirates', 'A380-EK1',  'DXB', 'SYD', '2025-12-06 17:30:00', 'on-time', 980.00);
INSERT INTO Flight VALUES ('UA089',  '2025-12-03 12:00:00', 'United Airlines', 'B738-UA1',  'JFK', 'PVG', '2025-12-04 16:00:00', 'on-time', 765.00);
INSERT INTO Flight VALUES ('AA100',  '2025-11-25 18:00:00', 'American Airlines', 'A321-AA1', 'JFK','DXB', '2025-11-26 15:00:00', 'on-time', 840.00);
INSERT INTO Flight VALUES ('EY202',  '2025-12-10 01:30:00', 'Etihad Airways', 'A380-EY1',   'AUH', 'SYD', '2025-12-10 18:45:00', 'on-time', 995.00);
INSERT INTO Flight VALUES ('UA123',  '2025-11-28 10:00:00', 'United Airlines', 'B738-UA1',  'PVG', 'JFK', '2025-11-28 23:40:00', 'on-time', 770.00);



-- Customer
INSERT INTO Customer VALUES ('as18181@nyu.edu', 'Aman Sunesh', MD5('pw-aman'), '1', 'Saadiyat St', 'Abu Dhabi', 'AD', '+971-50-000-0001', 'IN9A12345', '2030-05-31', 'India', '2005-04-17');
INSERT INTO Customer VALUES ('alice.lee@gmail.com', 'Alice Lee', MD5('pw-alice'), '100', 'Main St', 'New York', 'NY', '+1-212-555-0103', 'USL777777', '2029-12-31', 'USA', '1999-04-12');
INSERT INTO Customer VALUES ('noah.patel@gmail.com', 'Noah Patel', MD5('pw-noah'), '221', 'Park Ave', 'New York', 'NY', '+1-917-555-0155', 'IN8B98765', '2031-07-31', 'India', '1997-02-14');
INSERT INTO Customer VALUES ('bob.chen@gmail.com', 'Bob Chen', MD5('pw-bob'), '55', 'Broadway', 'New York', 'NY', '+1-212-555-0104','CN88AB234', '2032-01-31', 'China', '1998-11-03');
INSERT INTO Customer VALUES ('maria.garcia@yahoo.com', 'Maria Garcia', MD5('pw-maria'), '12', 'Queens Blvd', 'New York', 'NY', '+1-929-555-0111', 'ESZ123456', '2031-09-30', 'Spain', '1997-08-21');
INSERT INTO Customer VALUES ('sofia.rodriguez@gmail.com','Sofia Rodriguez', MD5('pw-sofia'),'18', 'Gran Via', 'Madrid', 'MD', '+34-91-555-0303', 'ESY890123', '2033-02-28', 'Spain', '1995-09-05');
INSERT INTO Customer VALUES ('li.wei@outlook.com', 'Li Wei', MD5('pw-liwei'),'88', 'Century Ave', 'Shanghai', 'SH', '+86-21-555-0202', 'CN99XZ321', '2030-04-30', 'China', '1996-05-11');
INSERT INTO Customer VALUES ('fatima.tamimi@outlook.com', 'Fatima Al Tamimi', MD5('pw-fatima'), '7', 'Corniche Rd', 'Abu Dhabi', 'AD', '+971-50-000-0023', 'AE12345PQ', '2032-06-30', 'UAE', '1998-02-10');
INSERT INTO Customer VALUES ('ahmed.khan@gmail.com', 'Ahmed Khan', MD5('pw-ahmed'), '9', 'Ittihad St', 'Abu Dhabi', 'AD', '+971-50-000-0042','PKP556677', '2031-10-31', 'UAE', '1994-12-01');
INSERT INTO Customer VALUES ('ad6647@nyu.edu', 'Anish Deshpande', MD5('pw-anish'), '101', 'Johnson St', 'Brooklyn', 'NY', '+1-978-995-3171', 'USL758367', '2029-02-27', 'USA', '2005-02-17');


   
-- Ticket
INSERT INTO Ticket
   (flight_no, dep_datetime, airline_name, customer_email,
   card_type, card_num, card_name, exp_date, purchase_datetime)
VALUES ('B61234', '2025-11-10 09:00:00', 'Jet Blue', 'as18181@nyu.edu', 'credit', '4111111111111111', 'Aman Sunesh', '2029-12-31', '2025-10-26 10:00:00'),
       ('EK202',  '2025-12-05 22:30:00', 'Emirates', 'as18181@nyu.edu', 'debit',  '5105105105105100', 'Aman Sunesh', '2030-03-31', '2025-10-27 09:00:00'),
       ('BA676',  '2025-12-25 20:15:00', 'British Airways', 'ad6647@nyu.edu', 'debit',  '7165706165206100', 'Anish Deshpande', '2030-06-10', '2025-09-25 12:00:00'),
       ('B61220', '2025-10-10 07:00:00', 'Jet Blue', 'noah.patel@gmail.com', 'credit', '4111111111111113', 'Noah Patel', '2031-09-30', '2025-09-20 12:00:00'),
       ('UA089',  '2025-12-03 12:00:00', 'United Airlines', 'alice.lee@gmail.com', 'credit', '6011000990139424', 'Alice Lee', '2029-11-30', '2025-10-28 16:05:00'),
       ('B61235', '2025-11-15 13:30:00', 'Jet Blue', 'bob.chen@gmail.com', 'credit', '4000000000000002', 'Bob Chen', '2027-05-31', '2025-10-29 14:15:00'),
       ('EK303',  '2025-10-15 23:15:00', 'Emirates', 'sofia.rodriguez@gmail.com', 'credit', '4000000000000009', 'Sofia Rodriguez',  '2029-05-31', '2025-09-25 10:05:00'),
       ('AA100',  '2025-11-25 18:00:00', 'American Airlines', 'bob.chen@gmail.com', 'debit',  '3530111333300000', 'Bob Chen', '2028-01-31', '2025-10-31 12:20:00'),
       ('EY101',  '2025-11-20 02:00:00', 'Etihad Airways', 'maria.garcia@yahoo.com', 'credit', '5200828282828210', 'Maria Garcia', '2031-09-30', '2025-10-30 09:00:00'),
       ('EY202',  '2025-12-10 01:30:00', 'Etihad Airways', 'ahmed.khan@gmail.com', 'debit',  '5105105105105106', 'Ahmed Khan', '2032-10-31', '2025-11-01 14:00:00'),
       ('EK202',  '2025-12-05 22:30:00', 'Emirates', 'li.wei@outlook.com', 'credit', '4007000000027', 'Li Wei', '2030-04-30', '2025-10-31 11:30:00'),
       ('AA100',  '2025-11-25 18:00:00', 'American Airlines', 'fatima.tamimi@outlook.com', 'debit',  '3566002020360505', 'Fatima Al Tamimi', '2032-06-30', '2025-10-27 13:40:00'),
       ('UA123',  '2025-11-28 10:00:00', 'United Airlines', 'li.wei@outlook.com', 'credit', '6011111111111117', 'Li Wei', '2030-06-30', '2025-11-05 09:30:00');


-- FlightRating
INSERT INTO FlightRating VALUES ('as18181@nyu.edu', 'EK202',  '2025-12-05 22:30:00', 'Emirates', 5, 'Smooth flight and friendly crew.');
INSERT INTO FlightRating VALUES ('as18181@nyu.edu', 'B61234', '2025-11-10 09:00:00', 'Jet Blue', 2, 'Seats were cramped and power outlets didn''t work.');
INSERT INTO FlightRating VALUES ('alice.lee@gmail.com', 'UA089', '2025-12-03 12:00:00', 'United Airlines', 1, 'Boarding was chaotic and luggage was delayed.');
INSERT INTO FlightRating VALUES ('bob.chen@gmail.com', 'B61235', '2025-11-15 13:30:00', 'Jet Blue', 3, 'Late departure but comfortable overall.');
INSERT INTO FlightRating VALUES ('bob.chen@gmail.com', 'AA100',  '2025-11-25 18:00:00', 'American Airlines', 5, 'Great service and on-time arrival.');
INSERT INTO FlightRating VALUES ('maria.garcia@yahoo.com', 'EY101', '2025-11-20 02:00:00', 'Etihad Airways', 4, 'Good food and entertainment.');
INSERT INTO FlightRating VALUES ('li.wei@outlook.com', 'EK202', '2025-12-05 22:30:00', 'Emirates', 5, 'Excellent A380 experience.');
INSERT INTO FlightRating VALUES ('fatima.tamimi@outlook.com', 'AA100', '2025-11-25 18:00:00', 'American Airlines', 4, 'Comfortable seats and helpful crew.');
INSERT INTO FlightRating VALUES ('ad6647@nyu.edu', 'BA676', '2025-12-25 20:15:00', 'British Airways', 5, 'Great food, cabin, and special crew.');

