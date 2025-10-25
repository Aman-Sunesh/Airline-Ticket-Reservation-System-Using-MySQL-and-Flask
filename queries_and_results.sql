-- Show all the future flights in the system.
SELECT * FROM Flight 
WHERE dep_datetime > NOW()
ORDER BY dep_datetime;

/*
Result (9 rows):

+-----------+---------------------+-------------+--------------------+-------------------+-------------------+-----------------------+---------+------------+
| flight_no | dep_datetime        | airplane_id | airline_name       | dep_airport_code  | arr_airport_code  | arr_datetime          | status  | base_price |
+-----------+---------------------+---------- --+--------------------+-------------------+-------------------+-----------------------+---------+------------+
| B61234    | 2025-11-10 09:00:00 | A321-JB1    | Jet Blue           | JFK               | PVG               | 2025-11-11 01:10:00   | on-time |    750.00  |
| B61235    | 2025-11-15 13:30:00 | A320-JB2    | Jet Blue           | PVG               | JFK               | 2025-11-15 20:10:00   | delayed |    730.00  |
| EY101     | 2025-11-20 02:00:00 | B789-EY2    | Etihad Airways     | AUH               | JFK               | 2025-11-20 09:30:00   | delayed |    820.00  |
| AA100     | 2025-11-25 18:00:00 | A321-AA1    | American Airlines  | JFK               | DXB               | 2025-11-26 15:00:00   | on-time |    840.00  |
| UA123     | 2025-11-28 10:00:00 | B738-UA1    | United Airlines    | PVG               | JFK               | 2025-11-28 23:40:00   | on-time |    770.00  |
| UA089     | 2025-12-03 12:00:00 | B738-UA1    | United Airlines    | JFK               | PVG               | 2025-12-04 16:00:00   | on-time |    765.00  |
| EK202     | 2025-12-05 22:30:00 | A380-EK1    | Emirates           | DXB               | SYD               | 2025-12-06 17:30:00   | on-time |    980.00  |
| EY202     | 2025-12-10 01:30:00 | A380-EY1    | Etihad Airways     | AUH               | SYD               | 2025-12-10 18:45:00   | on-time |    995.00  |
| BA676     | 2025-12-25 20:15:00 | A350-BA1    | British Airways    | JFK               | LHR               | 2025-12-26 08:10:00   | on-time |    650.00  |
+-----------+---------------------+-------------+--------------------+-------------------+-------------------+-----------------------+---------+------------+
*/



-- Show all of the delayed flights in the system.
SELECT * FROM Flight 
WHERE status = 'delayed'
ORDER BY dep_datetime;

/*
Result (3 rows):

+-----------+---------------------+-------------+-----------------+------------------+-------------------+-----------------------+---------+------------+
| flight_no | dep_datetime        | airplane_id | airline_name    | dep_airport_code | arr_airport_code  | arr_datetime          | status  | base_price |
+-----------+---------------------+-------------+-----------------+------------------+-------------------+-----------------------+---------+------------+
| B61220    | 2025-10-10 07:00:00 | E190-JB1    | Jet Blue        | JFK              | PVG               | 2025-10-11 00:10:00   | delayed |    650.00  |
| B61235    | 2025-11-15 13:30:00 | A320-JB2    | Jet Blue        | PVG              | JFK               | 2025-11-15 20:10:00   | delayed |    730.00  |
| EY101     | 2025-11-20 02:00:00 | B789-EY2    | Etihad Airways  | AUH              | JFK               | 2025-11-20 09:30:00   | delayed |    820.00  |
+-----------+---------------------+-------------+-----------------+------------------+-------------------+-----------------------+---------+------------+
*/


--  Show the customer names who bought the tickets.
SELECT DISTINCT c.name 
FROM Customer AS c 
JOIN Ticket AS t 
ON c.email = t.customer_email
ORDER BY c.name;

/*
Result (10 rows):

+---------------------+
| name                |
+---------------------+
| Ahmed Khan          |
| Alice Lee           |
| Aman Sunesh         |
| Anish Deshpande     |
| Bob Chen            |
| Fatima Al Tamimi    |
| Li Wei              |
| Maria Garcia        |
| Noah Patel          |
| Sofia Rodriguez     |
+---------------------+
*/

-- Show all the airplanes owned by the airline Jet Blue.
SELECT * FROM Airplane 
WHERE airline_name = 'Jet Blue'
ORDER BY airplane_id;

/*
Result (3 rows):

+-------------+--------------+---------------+--------------+-----+
| airplane_id | airline_name | seat_capacity | manufacturer | age |
+-------------+--------------+---------------+--------------+-----+
| A320-JB2    | Jet Blue     | 180           | Airbus       | 6   |
| A321-JB1    | Jet Blue     | 200           | Airbus       | 4   |
| E190-JB1    | Jet Blue     | 100           | Embraer      | 7   |
+-------------+--------------+---------------+--------------+-----+
*/
