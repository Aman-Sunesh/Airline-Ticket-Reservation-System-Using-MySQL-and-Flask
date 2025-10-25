CREATE TABLE Airline(
  airline_name VARCHAR (50),
  PRIMARY KEY (airline_name)
  );


CREATE TABLE Airplane(
  airplane_id VARCHAR(20),
  airline_name VARCHAR(50),
  seat_capacity INT,
  manufacturer VARCHAR(100),
  age INT,
  PRIMARY KEY (airplane_id, airline_name),
  FOREIGN KEY (airline_name) REFERENCES Airline(airline_name)
  );


CREATE TABLE AirlineStaff(
  username VARCHAR(50),
  password VARCHAR(255),
  airline_name VARCHAR(50),
  first_name VARCHAR(50),
  last_name VARCHAR(50),
  date_of_birth DATE,
  email VARCHAR(255),
  PRIMARY KEY (username),
  FOREIGN KEY (airline_name) REFERENCES Airline(airline_name)
);


CREATE TABLE StaffPhoneNo(
  username VARCHAR(50),
  phone_number VARCHAR(25),
  PRIMARY KEY (username, phone_number),
  FOREIGN KEY (username) REFERENCES AirlineStaff(username)
);


CREATE TABLE Airport(
  code CHAR(3),
  city VARCHAR(200),
  country VARCHAR(60),
  airport_type ENUM('domestic','international','both'),
  PRIMARY KEY (code)
);


CREATE TABLE Flight(
  flight_no VARCHAR(10),
  dep_datetime DATETIME,
  airplane_id VARCHAR(20),
  airline_name VARCHAR(50),
  dep_airport_code CHAR(3),
  arr_airport_code CHAR(3),
  arr_datetime DATETIME,
  status ENUM('on-time','delayed') NOT NULL DEFAULT 'on-time',
  base_price DECIMAL(10,2) CHECK (base_price >= 0),
  PRIMARY KEY (flight_no, dep_datetime, airplane_id, airline_name),
  FOREIGN KEY (airline_name) REFERENCES Airline(airline_name),
  FOREIGN KEY (dep_airport_code) REFERENCES Airport(code),
  FOREIGN KEY (arr_airport_code) REFERENCES Airport(code),
  FOREIGN KEY (airplane_id, airline_name)          
    REFERENCES Airplane(airplane_id, airline_name)
);


CREATE TABLE Customer(
  email VARCHAR(255),
  name VARCHAR(100),
  password VARCHAR(255),
  building_no VARCHAR(20),
  street VARCHAR(200),
  city VARCHAR(200),
  state VARCHAR(200),
  phone_number VARCHAR(25),
  passport_number VARCHAR(20),
  passport_expiration DATE,
  passport_country VARCHAR(60),
  date_of_birth DATE,
  PRIMARY KEY (email)
);


CREATE TABLE Ticket(
  ticket_id BIGINT AUTO_INCREMENT,
  flight_no VARCHAR(10),
  dep_datetime DATETIME,
  airplane_id VARCHAR(20),
  airline_name VARCHAR (50),
  customer_email VARCHAR(255),
  card_type ENUM('credit','debit'),
  card_num VARCHAR(20),
  card_name VARCHAR(100),
  exp_date DATE,
  purchase_datetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (ticket_id),
  FOREIGN KEY (flight_no, dep_datetime, airplane_id, airline_name)
    REFERENCES Flight(flight_no, dep_datetime, airplane_id, airline_name),
  FOREIGN KEY (customer_email) REFERENCES Customer(email)
);


CREATE TABLE FlightRating(
  customer_email VARCHAR(255),
  flight_no VARCHAR(10),
  dep_datetime DATETIME,
  airplane_id VARCHAR(20),
  airline_name VARCHAR (50),
  rating INT CHECK (rating BETWEEN 1 AND 5),
  comment TEXT,
  PRIMARY KEY (customer_email, flight_no, dep_datetime, airplane_id, airline_name),
  FOREIGN KEY (flight_no, dep_datetime, airplane_id, airline_name)
  REFERENCES Flight(flight_no, dep_datetime, airplane_id, airline_name),
  FOREIGN KEY (customer_email) REFERENCES Customer(email)
);
