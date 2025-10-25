-- Show all the future flights in the system.
SELECT * FROM Flight 
WHERE dep_datetime > NOW()
ORDER BY dep_datetime;

-- Show all of the delayed flights in the system.
SELECT * FROM Flight 
WHERE status = 'delayed'
ORDER BY dep_datetime;

--  Show the customer names who bought the tickets.
SELECT DISTINCT c.name 
FROM Customer AS c 
JOIN Ticket AS t 
ON c.email = t.customer_email
ORDER BY c.name;

-- Show all the airplanes owned by the airline Jet Blue.
SELECT * FROM Airplane 
WHERE airline_name = 'Jet Blue'
ORDER BY airplane_id;
