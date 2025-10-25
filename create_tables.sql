CREATE TABLE Airline(
  airline_name VARCHAR (50) NOT NULL,
  PRIMARY KEY (airline_name)
  );

CREATE TABLE Airport(
  code CHAR(3) NOT NULL,
  city VARCHAR(200) NOT NULL,
  country VARCHAR(60) NOT NULL,
  airport_type ENUM('domestic','international','both') NOT NULL,
  PRIMARY KEY (code)
);

CREATE TABLE Airplane(
  airplane_id VARCHAR(20) NOT NULL,
  airline_name VARCHAR(50) NOT NULL,
  seat_capacity INT NOT NULL CHECK (seat_capacity > 0),
  manufacturer VARCHAR(100) NOT NULL,
  age INT NOT NULL CHECK (age >= 0),
  PRIMARY KEY (airplane_id, airline_name),
  FOREIGN KEY (airline_name) 
    REFERENCES Airline(airline_name)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
  );


CREATE TABLE AirlineStaff(
  username VARCHAR(50) NOT NULL,
  password VARCHAR(255) NOT NULL,
  airline_name VARCHAR(50) NOT NULL,
  first_name VARCHAR(50) NOT NULL,
  last_name VARCHAR(50) NOT NULL,
  date_of_birth DATE NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  PRIMARY KEY (username),
  FOREIGN KEY (airline_name) 
    REFERENCES Airline(airline_name)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);


CREATE TABLE StaffPhoneNo(
  username VARCHAR(50) NOT NULL,
  phone_number VARCHAR(20) NOT NULL,
  PRIMARY KEY (username, phone_number),
  FOREIGN KEY (username) 
    REFERENCES AirlineStaff(username)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);


CREATE TABLE Flight(
  flight_no VARCHAR(10) NOT NULL,
  dep_datetime DATETIME NOT NULL,
  airplane_id VARCHAR(20) NOT NULL,
  airline_name VARCHAR(50) NOT NULL,
  dep_airport_code CHAR(3) NOT NULL,
  arr_airport_code CHAR(3) NOT NULL,
  arr_datetime DATETIME NOT NULL,
  status ENUM('on-time','delayed') NOT NULL DEFAULT 'on-time',
  base_price DECIMAL(10,2) NOT NULL CHECK (base_price >= 0),
  CONSTRAINT chk_times_order CHECK (arr_datetime > dep_datetime),
  CONSTRAINT chk_airports_diff CHECK (dep_airport_code <> arr_airport_code),
  PRIMARY KEY (flight_no, dep_datetime, airplane_id, airline_name),
  FOREIGN KEY (airline_name)  
    REFERENCES Airline(airline_name)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  FOREIGN KEY (dep_airport_code) 
    REFERENCES Airport(code)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  FOREIGN KEY (arr_airport_code) 
    REFERENCES Airport(code)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  FOREIGN KEY (airplane_id, airline_name)          
    REFERENCES Airplane(airplane_id, airline_name)
    ON UPDATE CASCADE
    ON DELETE RESTRICT
);


CREATE TABLE Customer(
  email VARCHAR(255) NOT NULL,
  name VARCHAR(100) NOT NULL,
  password VARCHAR(255) NOT NULL,
  building_no VARCHAR(20),
  street VARCHAR(200),
  city VARCHAR(200),
  state VARCHAR(200),
  phone_number VARCHAR(20) NOT NULL,
  passport_number VARCHAR(20) NOT NULL,
  passport_expiration DATE NOT NULL,
  passport_country VARCHAR(60) NOT NULL,
  date_of_birth DATE NOT NULL,
  CONSTRAINT chk_passport_date_order CHECK (passport_expiration > date_of_birth),
  CONSTRAINT chk_dob CHECK (date_of_birth <= CURDATE()),
  CONSTRAINT chk_passport_not_expired CHECK (passport_expiration > CURRENT_DATE),
  PRIMARY KEY (email),
  UNIQUE KEY uq_passport (passport_country, passport_number)
);


CREATE TABLE Ticket(
  ticket_id BIGINT AUTO_INCREMENT,
  flight_no VARCHAR(10) NOT NULL,
  dep_datetime DATETIME NOT NULL,
  airplane_id VARCHAR(20) NOT NULL,
  airline_name VARCHAR (50) NOT NULL,
  customer_email VARCHAR(255) NOT NULL,
  card_type ENUM('credit','debit') NOT NULL,
  card_num VARCHAR(20) NOT NULL CHECK (CHAR_LENGTH(card_num) BETWEEN 13 AND 19),
  card_name VARCHAR(100) NOT NULL,
  exp_date DATE NOT NULL,
  purchase_datetime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT chk_card_not_expired CHECK (exp_date >= DATE(purchase_datetime)),
  CONSTRAINT chk_purchase_before_dep CHECK (purchase_datetime <= dep_datetime),
  PRIMARY KEY (ticket_id),
  FOREIGN KEY (flight_no, dep_datetime, airplane_id, airline_name)
    REFERENCES Flight(flight_no, dep_datetime, airplane_id, airline_name)
    ON UPDATE CASCADE
    ON DELETE RESTRICT,
  FOREIGN KEY (customer_email) 
    REFERENCES Customer(email)
      ON UPDATE CASCADE
      ON DELETE RESTRICT
);


CREATE TABLE FlightRating(
  customer_email VARCHAR(255) NOT NULL,
  flight_no VARCHAR(10) NOT NULL,
  dep_datetime DATETIME NOT NULL,
  airplane_id VARCHAR(20) NOT NULL,
  airline_name VARCHAR (50) NOT NULL,
  rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment TEXT,
  PRIMARY KEY (customer_email, flight_no, dep_datetime, airplane_id, airline_name),
  FOREIGN KEY (flight_no, dep_datetime, airplane_id, airline_name)
    REFERENCES Flight(flight_no, dep_datetime, airplane_id, airline_name)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  FOREIGN KEY (customer_email) 
    REFERENCES Customer(email)
    ON UPDATE CASCADE
    ON DELETE CASCADE
);
