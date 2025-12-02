import re
from flask import *
import pymysql.cursors
from datetime import datetime, timedelta   
from zoneinfo import ZoneInfo
from types import SimpleNamespace
from calendar import monthrange


# Initialize the app from Flask
app = Flask(__name__)

# Configure MySQL
conn = pymysql.connect(host='127.0.0.1',
                       user='root',
                       password='',
                       db='airline_reservation',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

# Mapping of airport IATA codes to their respective IANA timezone names.
# This is used to assign the correct timezone to departure and arrival datetimes.
AIRPORT_TZ = {
    'JFK': 'America/New_York',
    'BOS': 'America/New_York',
    'ORD': 'America/Chicago',
    'LAX': 'America/Los_Angeles',
    'LHR': 'Europe/London',
    'PVG': 'Asia/Shanghai',
    'DXB': 'Asia/Dubai',
    'AUH': 'Asia/Dubai',
    'SYD': 'Australia/Sydney',
}

def _recompute_durations(rows):
    """
    Post-processes flight data rows by recomputing flight durations across time zones.
    This ensures accurate and consistent durations for routes crossing time zones,
    instead of relying on DB-stored duration strings (which may be incorrect).
	"""
    if not rows:
        return

    for r in rows:
        try:
            # Create departure datetime with timezone
            dep_date_str = r['d_date'] + " " + r['d_time']
            dep_dt = datetime.strptime(dep_date_str, "%B %d, %Y %I:%M %p")
            dep_tz = AIRPORT_TZ.get(r['dep_airport_code'], 'UTC')
            dep_dt = dep_dt.replace(tzinfo=ZoneInfo(dep_tz))

            # Create arrival datetime with timezone
            arr_date_str = r['a_date'] + " " + r['a_time']
            arr_dt = datetime.strptime(arr_date_str, "%B %d, %Y %I:%M %p")
            arr_tz = AIRPORT_TZ.get(r['arr_airport_code'], 'UTC')
            arr_dt = arr_dt.replace(tzinfo=ZoneInfo(arr_tz))

            # Convert both datetimes to UTC
            dep_utc = dep_dt.astimezone(ZoneInfo('UTC'))
            arr_utc = arr_dt.astimezone(ZoneInfo('UTC'))

            # Calculate difference in minutes
            total_seconds = (arr_utc - dep_utc).total_seconds()
            minutes = int(total_seconds // 60)

            # Format as "HHh MMm"
            hours = minutes // 60
            mins = minutes % 60
            r['flight_duration'] = f"{hours:02d}h {mins:02d}m"

        except Exception:
            # If anything goes wrong, skip and keep existing value
            continue

def _normalize_staff_phone(raw: str) -> str:
    """
    Normalize a staff phone number so formatting is consistent.
    Assumes US-style numbers when there are 10 or 11 digits.
    Examples:
      '19175550221'    -> '+1-917-555-0221'
      '9175550221'     -> '+1-917-555-0221'
      '+1-718-555-1212' (already formatted) -> unchanged
    """
    raw = raw.strip()
    digits = ''.join(c for c in raw if c.isdigit())

    # If already contains '+' or '-' we assume user formatted it;
    # we only auto-format plain digit strings.
    if ('+' in raw or '-' in raw) or len(digits) not in (10, 11):
        return raw

    # 10-digit (US local) number -> assume +1
    if len(digits) == 10:
        return f"+1-{digits[0:3]}-{digits[3:6]}-{digits[6:]}"

    # 11-digit starting with '1' -> treat first digit as country code
    if len(digits) == 11 and digits[0] == '1':
        return f"+1-{digits[1:4]}-{digits[4:7]}-{digits[7:]}"

    # Fallback – shouldn't hit because of len check above
    return raw

#Define route for login
@app.route('/login')
def login():
	return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
	return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    # if someone hits /loginAuth directly via GET, show the form instead of KeyError
    if request.method == 'GET':
        return render_template('login.html')

    #grabs information from the forms
    email = request.form['email'].lower()
    password = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()

    # Check if user exists in either customer or airline staff tab
    query = """SELECT role, airline_name, display_name 
            FROM (
                SELECT 'customer' AS role, NULL AS airline_name, name AS display_name 
                FROM Customer 
                WHERE email = %s AND password = MD5(%s)
                UNION ALL
                SELECT 'staff' AS role, airline_name, CONCAT(first_name, ' ', last_name) AS display_name
                FROM AirlineStaff 
                WHERE email = %s AND password = MD5(%s)
            ) AS t
            LIMIT 1
        """
    cursor.execute(query, (email, password, email, password))

    # stores the results
    data = cursor.fetchone()
    cursor.close()

    error = None

    if (data):
        # creates a session for the user
        session['email'] = email                
        session['role'] = data['role']   # 'customer' or 'staff'
        session['display_name'] = data.get('display_name')
        
        if data['role'] == 'staff':
            session['airline_name'] = data['airline_name']
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM AirlineStaff WHERE email = %s", (email,))
            row = cursor.fetchone()
            cursor.close()
        
            if row:
                session['staff_username'] = row['username']
                
            return redirect(url_for('staff_home'))
        else:
            return redirect(url_for('customer_home')) 
    else:
        # Check separately if user even exists
        cursor = conn.cursor()
        query2 = """SELECT 1 FROM Customer WHERE email=%s
                    UNION SELECT 1 FROM AirlineStaff WHERE email=%s
                    LIMIT 1
                    """
        
        cursor.execute(query2, (email, email))
        exists = cursor.fetchone()
        cursor.close()

        if (exists):
            error = "Incorrect password. Please try again."
        else:
            error = "User does not exist. Please register first."

        flash(error, "error")
        return redirect(url_for('login'))

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
	# If someone hits the URL directly, just show the form
	if request.method == 'GET':
		return render_template('register.html')
	
	error = None

	# Grabs information from the forms
	email = request.form['email'].lower().strip()
	password = request.form['password']
	name = request.form['name'].strip()
	phone_number       = request.form['phone_number'].strip()
	passport_number    = request.form['passport_number'].strip()
	passport_country   = request.form['passport_country'].strip()
	date_of_birth      = request.form['date_of_birth']  # 'YYYY-MM-DD'
	passport_expiration= request.form['passport_expiration']  # 'YYYY-MM-DD'

	building_no = request.form.get('building_no')
	if building_no:
		building_no = building_no.strip()
	else:
		building_no = None

	street = request.form.get('street')
	if street:
		street = street.strip()
	else:
		street = None

	city = request.form.get('city')
	if city:
		city = city.strip()
	else:
		city = None

	state = request.form.get('state')
	if state:
		state = state.strip()
	else:
		state = None

	# Required fields (to ensure all the NOT NULL fields are filled by the user)
	required = [
		('email', email, 'Email'),
		('name', name, 'Name'),
		('password', password, 'Password'),
		('phone_number', phone_number, 'Phone number'),
		('passport_number', passport_number, 'Passport number'),
		('passport_expiration', passport_expiration, 'Passport expiration'),
		('passport_country', passport_country, 'Passport country'),
		('date_of_birth', date_of_birth, 'Date of birth'),
	]

	for key, value, label in required:
		if not value or not value.strip():
			flash(f'{label} is required.', 'error')
			return redirect(url_for('register'))

	if (len(password) < 8 or not any(c.isupper() for c in password) or not any(c.isdigit() for c in password)):
		flash("Password must be at least 8 characters, include one uppercase letter and one number.", "error")
		return redirect(url_for('register'))
	
	email_regex = r"[^@]+@[^@]+\.[^@]+"
	if not re.match(email_regex, email):
		flash("Please enter a valid email address.", "error")
		return redirect(url_for('register'))
	
	# Minial check for phone numbers
	digits_only = ''
	for c in phone_number:
		if c.isdigit():
			digits_only += c

	if len(digits_only) < 7:
		flash("Phone number seems too short — include at least 7 digits.", "error")
		return redirect(url_for('register'))
	if len(phone_number) > 20:
		flash("Phone number must be 20 characters or fewer.", "error")
		return redirect(url_for('register'))

	if not re.match(r'^[A-Z0-9]{5,20}$', passport_number, re.IGNORECASE):
		flash("Please enter a valid passport number (5–20 alphanumeric characters).", "error")
		return redirect(url_for('register'))	

	try:
		dob = datetime.strptime(date_of_birth, '%Y-%m-%d')
		exp = datetime.strptime(passport_expiration, '%Y-%m-%d')
		if dob >= exp:
			flash("Passport expiration must be after date of birth.", "error")
			return redirect(url_for('register'))
	except ValueError:
		flash("Invalid date format. Please use YYYY-MM-DD.", "error")
		return redirect(url_for('register'))

	#cursor used to send queries
	cursor = conn.cursor()

	#executes query
	query = """SELECT 1 FROM Customer WHERE email = %s
			UNION
			SELECT 1 FROM AirlineStaff WHERE email = %s
			LIMIT 1
			"""
	cursor.execute(query, (email, email))

	#stores the results in a variable
	data = cursor.fetchone()
	cursor.close()

	if(data):
		#If the previous query returns data, then user exists
		flash("This user already exists", "error")
		return redirect(url_for('register'))
	
	else:
		ins_query = """INSERT INTO Customer 
				 (email, name, password, building_no, street, city, state,
				  phone_number, passport_number, passport_expiration, 
				  passport_country, date_of_birth)
				 VALUES (%s, %s, MD5(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s)
			  """
		
		cursor = conn.cursor()
		cursor.execute(ins_query, (email, name, password, building_no, street, city, state,
				       phone_number, passport_number, passport_expiration, 
				       passport_country, date_of_birth))
		conn.commit()
		cursor.close()

	return redirect(url_for('home'))


@app.route('/search_flights', methods=['GET'])
def search_flights():
    # Grabs information from the forms
    trip_type = request.args.get('trip', 'oneway')
    source = request.args.get('source', '').strip().upper()
    destination = request.args.get('destination', '').strip().upper()
    depart_date = request.args.get('depart_date')
    return_date = request.args.get('return_date')

    # If a customer is logged in, keep them on their dashboard template
    # otherwise use the public home page template.
    if session.get('role') == 'customer':
        template = 'customer_home.html'
    else:
        template = 'home.html'      

    # basic validation
    if not (source and destination and depart_date):
        airports = get_airport_codes()
        return render_template(template, error="Please fill all required fields.", airports=airports)

    # disallow same-airport searches
    if source == destination:
        airports = get_airport_codes()
        return render_template(template, error="From and To cannot be the same airport.", airports=airports)

    if (trip_type == "oneway"):
        query =  """SELECT flight_no, airline_name, dep_airport_code, arr_airport_code, 
                            DATE_FORMAT(dep_datetime, '%%M %%e, %%Y') AS d_date,
                            DATE_FORMAT(dep_datetime, '%%l:%%i %%p') AS d_time,
                            DATE_FORMAT(arr_datetime, '%%M %%e, %%Y') AS a_date,
                            DATE_FORMAT(arr_datetime, '%%l:%%i %%p') AS a_time,
                            TIME_FORMAT(TIMEDIFF(arr_datetime, dep_datetime), '%%Hh %%im') AS flight_duration,
                            base_price
                    FROM Flight
                    WHERE dep_airport_code = %s AND arr_airport_code = %s AND 
                            DATE(dep_datetime) = %s AND dep_datetime > NOW()
                    ORDER BY dep_datetime ASC; 
                """
        # cursor used to send queries
        cursor = conn.cursor()
        cursor.execute(query, (source, destination, depart_date))

        #stores the results in a variable
        data = cursor.fetchall()
        _recompute_durations(data)
        airports = get_airport_codes()
        cursor.close()


        return render_template(
            template,
            outbound=data,          
            trip=trip_type,
            source=source,
            destination=destination,
            depart_date=depart_date,
            airports=airports,
        )

    elif (trip_type == "round"):
        if not return_date:
            airports = get_airport_codes()
            return render_template(template, error="Please pick a return date for round trips.", airports=airports)
        
        # ensure chronological round-trip dates
        if return_date < depart_date:
            airports = get_airport_codes()
            return render_template(template, error="Return date must be on or after the departure date.", airports=airports)

        query =  """SELECT flight_no, airline_name, dep_airport_code, arr_airport_code, 
                            DATE_FORMAT(dep_datetime, '%%M %%e, %%Y') AS d_date,
                            DATE_FORMAT(dep_datetime, '%%l:%%i %%p') AS d_time,
                            DATE_FORMAT(arr_datetime, '%%M %%e, %%Y') AS a_date,
                            DATE_FORMAT(arr_datetime, '%%l:%%i %%p') AS a_time,
                            TIME_FORMAT(TIMEDIFF(arr_datetime, dep_datetime), '%%Hh %%im') AS flight_duration,
                            base_price
                    FROM Flight
                    WHERE dep_airport_code = %s AND arr_airport_code = %s AND 
                            DATE(dep_datetime) = %s AND dep_datetime > NOW()
                    ORDER BY dep_datetime ASC; 
                """
        
        cursor = conn.cursor()

        # source -> destination flights on depart_date
        cursor.execute(query, (source, destination, depart_date))
        outbound = cursor.fetchall()

        # destination -> source flights on return_date
        cursor.execute(query, (destination, source, return_date))
        inbound = cursor.fetchall()
        cursor.close()

        _recompute_durations(outbound)
        _recompute_durations(inbound)

        airports = get_airport_codes()

        return render_template(
            template,
            trip=trip_type,
            source=source,
            destination=destination,
            depart_date=depart_date,
            return_date=return_date,
            outbound=outbound,
            inbound=inbound,
            airports=airports,
        )

def get_airport_codes():
	cursor = conn.cursor()
	cursor.execute("SELECT code FROM airport ORDER BY code")
	rows = cursor.fetchall()
	cursor.close()
	return [row["code"] for row in rows]

def _require_staff():
    """Redirect to login unless the session is a staff user with an airline."""
    if session.get('role') != 'staff' or not session.get('airline_name'):
        return redirect(url_for('login'))
    return None

def _require_customer():
    """Redirect to login unless the session is a logged-in customer."""
    if session.get("role") != "customer" or not session.get("email"):
        return redirect(url_for("login"))
    return None

def _parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None
# ============================================================================


# Landing page: main public search view
@app.route("/")
@app.route("/home")
def home():
    airports = get_airport_codes()
    return render_template(
        "home.html",
        username=session.get("email"),
        role=session.get("role"),
        airports=airports,
    )

@app.route('/customer_home')
def customer_home():
    guard = _require_customer()
    if guard:
        return guard

    airports = get_airport_codes()
    return render_template('customer_home.html', airports=airports)

@app.route('/staff_home')
def staff_home():
    # protect staff dashboard; bounce non-staff to login
    guard = _require_staff()
    if guard:
        return guard

    airline = session.get('airline_name')
    c = conn.cursor()
    c.execute("""
        SELECT
            flight_no,
            dep_airport_code AS src,
            arr_airport_code AS dst,
            DATE_FORMAT(dep_datetime, '%%Y-%%m-%%d %%H:%%i') AS dep_datetime,
            status
        FROM Flight
        WHERE airline_name = %s
          AND dep_datetime >= NOW()
          AND dep_datetime < DATE_ADD(NOW(), INTERVAL 30 DAY)
        ORDER BY dep_datetime ASC
        LIMIT 50
    """, (airline,))
    flights = c.fetchall()
    c.close()

    return render_template('staff_home.html', flights=flights)



@app.get("/customer/upcoming_flights")
def customer_view_upcoming_flights():
    guard = _require_customer()
    if guard:
        return guard

    email = session.get('email')

    query = """SELECT T.ticket_id, T.flight_no, T.airline_name,
                    DATE_FORMAT(T.dep_datetime,'%%M %%e, %%Y %%l:%%i %%p') AS dep_disp,
                    DATE_FORMAT(T.purchase_datetime,'%%M %%e, %%Y %%l:%%i %%p') AS purchase_disp,
                    F.dep_airport_code AS src,
                    F.arr_airport_code AS dst,
                    F.status
               FROM Ticket T
               JOIN Flight F
                    ON F.flight_no = T.flight_no
                    AND F.dep_datetime = T.dep_datetime
                    AND F.airline_name = T.airline_name
               WHERE T.dep_datetime >= NOW() AND T.customer_email = %s
               ORDER BY T.dep_datetime
            """

    # cursor used to send queries
    cursor = conn.cursor()
    cursor.execute(query, (email, ))

    # stores the result in a variable
    tickets = cursor.fetchall()
    cursor.close()

    return render_template(
        "customer_upcoming_flights.html",
        tickets=tickets,     
    )

@app.get("/customer/past_flights")
def customer_view_past_flights():
    guard = _require_customer()
    if guard:
        return guard

    email = session.get('email')

    query = """SELECT T.ticket_id, T.flight_no, T.airline_name,
                    DATE_FORMAT(T.dep_datetime,'%%M %%e, %%Y %%l:%%i %%p') AS dep_disp,
                    DATE_FORMAT(T.purchase_datetime,'%%M %%e, %%Y %%l:%%i %%p') AS purchase_disp,
                    F.dep_airport_code AS src,
                    F.arr_airport_code AS dst,
                    F.status
               FROM Ticket T
               JOIN Flight F
                    ON F.flight_no = T.flight_no
                    AND F.dep_datetime = T.dep_datetime
                    AND F.airline_name = T.airline_name
               WHERE T.dep_datetime < NOW() AND T.customer_email = %s
               ORDER BY T.dep_datetime DESC
            """

    # cursor used to send queries
    cursor = conn.cursor()
    cursor.execute(query, (email, ))

    # stores the result in a variable
    tickets = cursor.fetchall()
    cursor.close()

    return render_template(
        "customer_past_flights.html",
        tickets=tickets,     
    )


@app.get("/customer/rate_flight")
def customer_rate_flights_page():
    """Show all past, unrated flights for this customer so they can rate them."""
    guard = _require_customer()
    if guard:
        return guard

    email = session.get("email")

    # Fetch past flights this customer took but has NOT rated yet
    query = """
        SELECT T.flight_no, T.airline_name,
            DATE_FORMAT(T.dep_datetime,'%%Y-%%m-%%d %%H:%%i:%%s') AS dep_dt_key,
            DATE_FORMAT(T.dep_datetime,'%%M %%e, %%Y %%l:%%i %%p') AS dep_disp,
            F.dep_airport_code AS src, F.arr_airport_code AS dst
        FROM Ticket T
        JOIN Flight F
          ON F.flight_no = T.flight_no
          AND F.dep_datetime  = T.dep_datetime
          AND F.airline_name  = T.airline_name
        LEFT JOIN FlightRating FR
          ON FR.customer_email = T.customer_email
          AND FR.flight_no = T.flight_no
          AND FR.dep_datetime = T.dep_datetime
          AND FR.airline_name = T.airline_name
        WHERE T.customer_email = %s AND T.dep_datetime < NOW()
          AND FR.customer_email IS NULL
        ORDER BY T.dep_datetime DESC
    """

    cursor = conn.cursor()
    cursor.execute(query, (email,))
    flights = cursor.fetchall()
    cursor.close()

    return render_template("customer_rate_flight.html", flights=flights)

@app.post("/customer/rate_flight")
def customer_rate_flights():
    guard = _require_customer()
    if guard:
        return guard
    
    # Grabs information from the forms
    rating_raw = request.form['rating'].strip()
    comment = request.form['comment'].strip()
    flight_no = request.form['flight_no'].strip().upper()
    dep_datetime = request.form['dep_datetime'].strip()
    airline_name = request.form['airline_name'].strip()

    email = session.get('email')

    try:
        rating = int(rating_raw)
    except ValueError:
        flash("Rating must be an integer between 1 and 5.", "error")
        return redirect(url_for("customer_rate_flights_page"))

    if rating < 1 or rating > 5:
        flash("Rating must be between 1 and 5.", "error")
        return redirect(url_for("customer_rate_flights_page"))

    # comment is optional; store NULL if empty
    if not comment:
        comment = None

    # cursor used to send queries
    cursor = conn.cursor()

    # check that this exact flight exists, is in the past,
    # and is actually booked by this customer
    query_flight = """SELECT 1 
                      FROM Ticket T 
                      JOIN Flight F
                        ON F.flight_no     = T.flight_no
                        AND F.dep_datetime  = T.dep_datetime
                        AND F.airline_name  = T.airline_name
                      WHERE T.customer_email = %s AND T.flight_no      = %s
                        AND T.dep_datetime   = %s AND T.airline_name   = %s
                        AND T.dep_datetime   < NOW()
                      LIMIT 1
                   """

    cursor.execute(query_flight, (email, flight_no, dep_datetime, airline_name))

    valid_flight = cursor.fetchone()
    if not valid_flight:
        cursor.close()
        flash("You can only rate flights you have already taken.", "error")
        return redirect(url_for("customer_rate_flights_page"))

    
    # ensure this customer hasn't already rated this flight
    query_check = """SELECT 1 
                     FROM FlightRating
                     WHERE customer_email=%s AND flight_no=%s
                           AND dep_datetime=%s AND airline_name=%s
                    LIMIT 1
                  """


    cursor.execute(query_check, (email, flight_no, dep_datetime, airline_name))
    exists = cursor.fetchone()
    
    if exists:
        cursor.close()
        flash("You have already rated this flight.", "info")
        return redirect(url_for("customer_rate_flights_page"))

    # insert rating
    query_insert = """INSERT INTO FlightRating
                      (customer_email, flight_no, dep_datetime, airline_name, rating, comment) 
                      VALUES (%s, %s, %s, %s, %s, %s)
                    """

    cursor.execute(query_insert, (email, flight_no, dep_datetime, airline_name, rating, comment))
    conn.commit()
    cursor.close()

    flash("Thank you for rating this flight!", "success")
    return redirect(url_for("customer_rate_flights_page"))

@app.route("/customer/purchase_review", methods=["GET", "POST"])
def customer_purchase_review():
    guard = _require_customer()
    if guard:
        return guard
    
    # If redirected here after confirm_purchase, rebuild from session
    if request.method == "GET":
        ctx = session.get("purchase_context")
        if not ctx:
            flash("No purchase in progress.", "error")
            return redirect(url_for("customer_home"))

        trip = ctx.get("trip", "oneway")

        if trip == "oneway":
            flight = SimpleNamespace(**ctx["flight"])
            return render_template(
                "customer_purchase.html",
                trip="oneway",
                flight=flight,
                total_price=ctx["total_price"],
            )
        
        elif trip == "round":
            outbound = SimpleNamespace(**ctx["outbound"])
            inbound  = SimpleNamespace(**ctx["inbound"])
            return render_template(
                "customer_purchase.html",
                trip="round",
                outbound=outbound,
                inbound=inbound,
                total_price=ctx["total_price"],
            )
        
        else:
            flash("Unknown trip type.", "error")
            return redirect(url_for("customer_home"))
    
    # POST: coming from search_flights page after choosing flights
    trip = request.form.get("trip", "oneway")

    if trip == "oneway":
        # Extract flight details from the form
        flight_no = request.form["flight_no"]
        airline_name = request.form["airline_name"]
        dep_airport_code = request.form["dep_airport_code"]
        arr_airport_code = request.form["arr_airport_code"]
        d_date = request.form["depart_date"]
        d_time = request.form["dep_time"]
        a_date = request.form["arrival_date"]
        a_time = request.form["arrival_time"]
        base_price = float(request.form["base_price"])
        flight_duration = request.form.get("flight_duration", "")

        # Store context in session so confirm_purchase can redirect back
        session["purchase_context"] = {
            "trip": "oneway",
            "flight": {
                "flight_no": flight_no,
                "airline_name": airline_name,
                "dep_airport_code": dep_airport_code,
                "arr_airport_code": arr_airport_code,
                "d_date": d_date,
                "d_time": d_time,
                "a_date": a_date,
                "a_time": a_time,
                "base_price": base_price,
                "flight_duration": flight_duration,
            },
            "total_price": base_price,
        }

        flight = SimpleNamespace(**session["purchase_context"]["flight"])
        total_price = base_price

        # Render the purchase review page with flight info
        return render_template(
            "customer_purchase.html",
            trip="oneway",
            flight=flight,
            total_price=total_price,
        )

    elif trip == "round":
        outbound_raw = request.form.get("outbound_choice")
        return_raw = request.form.get("return_choice")

        if not outbound_raw or not return_raw:
            flash("Please select one outbound and one return flight.", "error")
            return redirect(url_for("customer_home"))
        
        def parse_choice(raw):
            """Helper function to parse pipe-separated flight data."""
            (
                flight_no,
                airline_name,
                dep_airport_code,
                arr_airport_code,
                d_date,
                d_time,
                a_date,
                a_time,
                base_price,
                flight_duration,
            ) = raw.split("|")

            return {
                "flight_no": flight_no,
                "airline_name": airline_name,
                "dep_airport_code": dep_airport_code,
                "arr_airport_code": arr_airport_code,
                "d_date": d_date,
                "d_time": d_time,
                "a_date": a_date,
                "a_time": a_time,
                "base_price": float(base_price),
                "flight_duration": flight_duration,
            }
        
        # Parse and store as dicts
        outbound_dict = parse_choice(outbound_raw)
        inbound_dict  = parse_choice(return_raw)

        # Calculate total price
        total_price = outbound_dict["base_price"] + inbound_dict["base_price"]

        # Save in session for later GET reload
        session["purchase_context"] = {
            "trip": "round",
            "outbound": outbound_dict,
            "inbound": inbound_dict,
            "total_price": total_price,
        }

        outbound = SimpleNamespace(**outbound_dict)
        inbound  = SimpleNamespace(**inbound_dict)
        
        return render_template(
            "customer_purchase.html",
            trip="round",
            outbound=outbound,
            inbound=inbound,
            total_price=total_price,
        )
         
    # Fallback – should never hit if trip is valid
    flash("Unknown trip type.", "error")

    return redirect(url_for("customer_home"))
    

@app.route("/customer/confirm_purchase", methods=["POST"])
def customer_confirm_purchase():
    guard = _require_customer()
    if guard:
        return guard

    trip = request.form.get("trip", "oneway")
    email = session.get("email")
    
    # ---- card details ----
    card_type = request.form["card_type"].lower()
    card_num_raw = request.form["card_num"].strip()
    card_name = request.form["card_name"].strip()
    exp_date_raw = request.form["exp_date"].strip() 
    cvc_raw = request.form.get("cvc", "").strip()

    if not card_num_raw.isdigit():
        flash("Card number must contain only digits.", "error")
        return redirect(url_for("customer_purchase_review"))

    if len(card_num_raw) < 13 or len(card_num_raw) > 19:
        flash("Card number must be between 13 and 19 digits long.", "error")
        return redirect(url_for("customer_purchase_review"))

    card_num = card_num_raw

    if not cvc_raw.isdigit():
        flash("CVC must contain only digits.", "error")
        return redirect(url_for("customer_purchase_review"))

    if len(cvc_raw) not in (3, 4):
        flash("CVC must be 3 or 4 digits long.", "error")
        return redirect(url_for("customer_purchase_review"))

    cvc = cvc_raw

    # Parse MM/YY and treat the card as valid through the end of that month
    try:
        month_str, year_str = exp_date_raw.split("/")
        month = int(month_str)
        year = 2000 + int(year_str)
        # Compare by (year, month) only
        today = datetime.today().date()
        this_ym = (today.year, today.month)
        exp_ym  = (year, month)
        last_day = monthrange(year, month)[1]
        exp_date = datetime(year, month, last_day).date()
    except Exception:
        flash("Invalid expiration date format. Please use MM/YY.", "error")
        return redirect(url_for("customer_purchase_review"))

    # Reject if expired by year+month
    if exp_ym < this_ym:
        flash("This card is expired. Please use a valid, non-expired card.", "error")
        return redirect(url_for("customer_purchase_review"))
    
    cursor = conn.cursor()

    def _insert_ticket_for_flight(flight_no, airline_name, dep_date_str, dep_time_str):
        # Get canonical dep_datetime from Flight using same format as search_flights
        lookup_sql = """SELECT dep_datetime
                        FROM Flight
                        WHERE flight_no = %s AND airline_name = %s
                            AND DATE(dep_datetime) = %s
                            AND DATE_FORMAT(dep_datetime,'%%l:%%i %%p') = %s
                        LIMIT 1
                     """
    
        # dep_date_str is like "November 21, 2025" (same as r.d_date),
        # so parse it back to a real date before passing to MySQL.
        try:
            dep_date_obj = datetime.strptime(dep_date_str, "%B %d, %Y").date()
        except ValueError:
            flash("Could not parse departure date.", "error")
            return False

        cursor.execute(lookup_sql, (flight_no, airline_name, dep_date_obj, dep_time_str))
        row = cursor.fetchone()

        if not row:
            # Should be impossible in normal use, but avoids a crash if
            # something gets out of sync.
            flash("Could not locate the selected flight in the database.", "error")
            return False

        dep_datetime = row["dep_datetime"]

        # Check for duplicate ticket
        check_query = """SELECT 1 FROM Ticket
                         WHERE flight_no = %s AND dep_datetime = %s 
                               AND airline_name = %s AND customer_email = %s
                         LIMIT 1
                      """
        
        cursor.execute(check_query, (flight_no, dep_datetime, airline_name, email))
        exists = cursor.fetchone()

        if exists:
            flash(f"You’ve already purchased a ticket for flight {flight_no} that departs on {dep_datetime}.", "error")
            return False

		# Capacity Check: Block if sold >= seat_capacity
		cap_query = """SELECT a.seat_capacity AS capacity, COUNT(t.ticket_id) AS sold
			           FROM Flight f
			           JOIN Airplane a
			           ON a.airplane_id = f.airplane_id
			               AND a.airline_name = f.airline_name
			           LEFT JOIN Ticket t
			           ON t.flight_no = f.flight_no
			               AND t.dep_datetime = f.dep_datetime
			               AND t.airline_name = f.airline_name
			           WHERE f.flight_no = %s
			               AND f.dep_datetime = %s
			               AND f.airline_name = %s
			           GROUP BY a.seat_capacity
        			"""
        cursor.execute(cap_query, (flight_no, dep_datetime, airline_name))
        cap_row = cursor.fetchone()
		
        if not cap_row:
            flash("Could not verify seat capacity for this flight.", "error")
            return False
			
        if cap_row["sold"] >= cap_row["capacity"]:
            flash("Sorry, this flight is fully booked.", "error")
            return False
					   
        # Insert ticket
        insert_query = """INSERT INTO Ticket 
                          (flight_no, dep_datetime, airline_name, customer_email,
                          card_type, card_num, card_name, exp_date) 
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                       """
        
        cursor.execute(insert_query, (flight_no, dep_datetime, airline_name, email,
                       card_type, card_num, card_name, exp_date))

        return True

    if trip == "oneway":
        ok = _insert_ticket_for_flight(request.form["flight_no"], request.form["airline_name"],
                                       request.form["dep_date"], request.form["dep_time"])
        if not ok:
            conn.rollback()
            cursor.close()
            return redirect(url_for("customer_purchase_review"))

    elif trip == "round":
        ok_out = _insert_ticket_for_flight(request.form["out_flight_no"], request.form["out_airline_name"],
                                           request.form["out_dep_date"], request.form["out_dep_time"])
        
        ok_ret = _insert_ticket_for_flight(request.form["ret_flight_no"], request.form["ret_airline_name"],
                                           request.form["ret_dep_date"], request.form["ret_dep_time"])
        
        if not (ok_out and ok_ret):
            conn.rollback()
            cursor.close()
            return redirect(url_for("customer_purchase_review"))

    else:
        flash("Invalid trip type.", "error")
        return redirect(url_for("customer_purchase_review"))

    conn.commit()
    cursor.close()
    flash("Thank you, your purchase has been recorded.", "success")
    return redirect(url_for("customer_purchase_review"))

# 1) View flights (filters; default next 30 days)
@app.get("/staff/view_flights")
def staff_view_flights():
    guard = _require_staff()
    if guard: return guard
    airline = session['airline_name']

    from_date = request.args.get('from_date')
    to_date   = request.args.get('to_date')
    dep_code  = (request.args.get('dep_code') or '').upper().strip()
    arr_code  = (request.args.get('arr_code') or '').upper().strip()

    today = datetime.now().date()
    fd = _parse_date(from_date) or today
    td = _parse_date(to_date) or (today + timedelta(days=30))

    conds = ["airline_name=%s", "DATE(dep_datetime) BETWEEN %s AND %s"]
    params = [airline, fd, td]
    if dep_code:
        conds.append("dep_airport_code=%s"); params.append(dep_code)
    if arr_code:
        conds.append("arr_airport_code=%s"); params.append(arr_code)

    sql = f"""
        SELECT flight_no, airline_name,
               dep_airport_code, arr_airport_code,
               DATE_FORMAT(dep_datetime,'%%Y-%%m-%%d %%H:%%i:%%s') AS dep_key,
               DATE_FORMAT(dep_datetime,'%%M %%e, %%Y %%l:%%i %%p') AS dep_disp,
               DATE_FORMAT(arr_datetime,'%%M %%e, %%Y %%l:%%i %%p') AS arr_disp,
               status, base_price
        FROM Flight
        WHERE {' AND '.join(conds)}
        ORDER BY dep_datetime ASC
        LIMIT 500
    """
    c = conn.cursor(); c.execute(sql, params); flights = c.fetchall(); c.close()
    airports = get_airport_codes()
    return render_template("staff_view_flights.html",
        flights=flights, airports=airports,
        current_filters={'from_date':fd.isoformat(),'to_date':td.isoformat(),
                         'dep_code':dep_code,'arr_code':arr_code})

# 1b) View customers of a flight (read-only)
@app.get("/staff/flight_customers")
def staff_flight_customers():
    guard = _require_staff()
    if guard: return guard
    airline = session['airline_name']
    flight_no = request.args['flight_no']
    dep_dt_key = request.args['dep_dt_key']  # 'YYYY-MM-DD HH:MM:SS'
    dep_dt = datetime.strptime(dep_dt_key, "%Y-%m-%d %H:%M:%S")

    c = conn.cursor()
    # safety: verify the flight belongs to this airline
    c.execute("""SELECT 1 FROM Flight
                 WHERE flight_no=%s AND dep_datetime=%s AND airline_name=%s""",
              (flight_no, dep_dt, airline))
    if not c.fetchone():
        c.close(); flash("Flight not found for your airline.", "error")
        return redirect(url_for("staff_view_flights"))

    c.execute("""
      SELECT c.name, c.email, t.purchase_datetime
      FROM Ticket t JOIN Customer c ON c.email=t.customer_email
      WHERE t.flight_no=%s AND t.dep_datetime=%s AND t.airline_name=%s
      ORDER BY t.purchase_datetime
    """, (flight_no, dep_dt, airline))
    rows = c.fetchall(); c.close()
    return render_template("staff_flight_customers.html",
                           customers=rows, flight_no=flight_no, dep_dt_key=dep_dt_key)
                           

# 2) Create new flight (form + submit)
@app.get("/create_flight")
def create_flight_form():
    guard = _require_staff()
    if guard: return guard
    # Show only airplanes owned by this airline
    c = conn.cursor()
    c.execute("SELECT airplane_id FROM airplane WHERE airline_name=%s ORDER BY airplane_id",
              (session['airline_name'],))
    planes = [r['airplane_id'] for r in c.fetchall()]
    c.close()
    airports = get_airport_codes()  # returns list of Airport.code
    return render_template("create_flight.html", airports=airports, planes=planes)

@app.post("/create_flight")
def create_flight_submit():
    guard = _require_staff()
    if guard: return guard

    fno = request.form['flight_no'].strip().upper()
    a = session['airline_name']

    # New: separate date + time fields from the form
    dep_date = request.form['dep_date'].strip()
    dep_time = request.form['dep_time'].strip()
    arr_date = request.form['arr_date'].strip()
    arr_time = request.form['arr_time'].strip()

    dep = request.form['dep_airport_code'].strip().upper()
    arr = request.form['arr_airport_code'].strip().upper()
    plane = request.form['airplane_id'].strip()
    price = request.form['base_price'].strip()

    # Combine into full datetimes and validate
    try:
        dep_dt_obj = datetime.strptime(f"{dep_date} {dep_time}", "%Y-%m-%d %H:%M")
        arr_dt_obj = datetime.strptime(f"{arr_date} {arr_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        flash("Invalid departure or arrival date/time.", "error")
        return redirect(url_for("create_flight_form"))
    
    if dep == arr:
        flash("Departure and arrival airports must differ.", "error")
        return redirect(url_for("create_flight_form"))
    
    if arr_dt_obj <= dep_dt_obj:
        flash("Arrival time must be after departure time.", "error")
        return redirect(url_for("create_flight_form"))

    # Store as 'YYYY-MM-DD HH:MM:SS' for MySQL
    depdt = dep_dt_obj.strftime("%Y-%m-%d %H:%M:%S")
    arrdt = arr_dt_obj.strftime("%Y-%m-%d %H:%M:%S")


    c = conn.cursor()
    # airplane must be owned by this airline
    c.execute("SELECT 1 FROM airplane WHERE airplane_id=%s AND airline_name=%s", (plane, a))
    if not c.fetchone():
        c.close(); flash("Airplane not owned by your airline.","error")
        return redirect(url_for('create_flight_form'))
    try:
        c.execute("""
          INSERT INTO flight
            (flight_no,dep_datetime,airline_name,airplane_id,
             dep_airport_code,arr_airport_code,arr_datetime,status,base_price)
          VALUES (%s,%s,%s,%s,%s,%s,%s,'on-time',%s)
        """, (fno, depdt, a, plane, dep, arr, arrdt, price))
        conn.commit(); flash("Flight created.","success")
    except Exception:
        conn.rollback(); flash("Error creating flight.","error")
    finally:
        c.close()
    return redirect(url_for("staff_view_flights"))

# 3) Manage (change) status
@app.get("/staff/manage_status")
def staff_manage_status():
    guard = _require_staff()
    if guard: return guard
    airline = session['airline_name']

    from_date = request.args.get('from_date')
    to_date   = request.args.get('to_date')
    dep_code  = (request.args.get('dep_code') or '').strip().upper()
    arr_code  = (request.args.get('arr_code') or '').strip().upper()

    today = datetime.now().date()
    fd = _parse_date(from_date) or today
    td = _parse_date(to_date) or (today + timedelta(days=30))

    conditions = ["airline_name=%s", "DATE(dep_datetime) BETWEEN %s AND %s"]
    params = [airline, fd, td]
    if dep_code:
        conditions.append("dep_airport_code=%s"); params.append(dep_code)
    if arr_code:
        conditions.append("arr_airport_code=%s"); params.append(arr_code)

    query = f"""
        SELECT flight_no, airline_name,
               dep_airport_code, arr_airport_code,
               DATE_FORMAT(dep_datetime,'%%Y-%%m-%%d %%H:%%i:%%s') AS dep_dt_key,
               DATE_FORMAT(dep_datetime,'%%M %%e, %%Y %%l:%%i %%p') AS dep_dt_disp,
               DATE_FORMAT(arr_datetime,'%%M %%e, %%Y %%l:%%i %%p') AS arr_dt_disp,
               status, base_price
        FROM Flight
        WHERE {' AND '.join(conditions)}
        ORDER BY dep_datetime ASC
        LIMIT 500
    """
    c = conn.cursor(); c.execute(query, params); flights = c.fetchall(); c.close()
    airports = get_airport_codes()
    return render_template("staff_manage_status.html",
                           flights=flights, airports=airports,
                           current_filters={'from_date':fd.isoformat(),'to_date':td.isoformat(),
                                            'dep_code':dep_code,'arr_code':arr_code})

@app.post("/staff/update_status")
def staff_update_status():
    guard = _require_staff()
    if guard: return guard
    airline = session['airline_name']

    flight_no  = request.form.get('flight_no','').strip()
    dep_dt_key = request.form.get('dep_dt_key','').strip()  # 'YYYY-MM-DD HH:MM:SS'
    new_status = request.form.get('status','').strip()

    if new_status not in ('on-time','delayed'):
        flash('Invalid status.','error'); return redirect(url_for('staff_manage_status'))
    try:
        dep_dt = datetime.strptime(dep_dt_key, "%Y-%m-%d %H:%M:%S")
    except Exception:
        flash('Invalid departure datetime.','error'); return redirect(url_for('staff_manage_status'))

    c = conn.cursor()
    # make sure it belongs to this airline
    c.execute("""SELECT 1 FROM Flight
                 WHERE flight_no=%s AND dep_datetime=%s AND airline_name=%s""",
              (flight_no, dep_dt, airline))
    if not c.fetchone():
        c.close(); flash('Cannot update: flight not found for your airline.','error')
        return redirect(url_for('staff_manage_status'))

    c.execute("""UPDATE flight SET status=%s
                 WHERE flight_no=%s AND dep_datetime=%s AND airline_name=%s
                 LIMIT 1""",
              (new_status, flight_no, dep_dt, airline))
    conn.commit(); c.close()
    flash(f'Updated {flight_no} @ {dep_dt_key} to "{new_status}".','success')
    return redirect(url_for('staff_manage_status'))

# 4) Add airplane + list my airplanes
@app.get("/staff/add_airplane")
def add_airplane_form():
    guard = _require_staff()
    if guard:
        return guard

    # Map full airline name -> code used in airplane_id
    airline_name = session.get("airline_name")
    airline_code_map = {
        "Jet Blue": "JB",
        "British Airways": "BA",
        "Etihad Airways": "EY",
        "Emirates": "EK",
        "United Airlines": "UA",
        "Delta Air Lines": "DL",
        "Air Canada": "AC",
        "American Airlines": "AA",
    }

    # Fallback: first two letters uppercased if not in the map
    airline_code = airline_code_map.get(
        airline_name,
        (airline_name or "XX")[:2].upper()
    )

    return render_template(
        "add_airplane.html",
        airline_code=airline_code
    )


@app.post("/staff/add_airplane")
def add_airplane_submit():
    guard = _require_staff()
    if guard:
        return guard

    a = session["airline_name"]

    # ---- read form fields ----
    prefix       = request.form.get("prefix", "").strip().upper()
    airline_code = request.form.get("airline_code", "").strip().upper()
    model_number = request.form.get("model_number", "").strip()
    seats_raw    = request.form.get("seats", "").strip()
    age_raw      = request.form.get("age", "").strip()

    # manufacturer must be A / B / E
    manufacturer_map = {
        "A": "Airbus",
        "B": "Boeing",
        "E": "Embraer",
    }
    manufacturer = manufacturer_map.get(prefix)
    if not manufacturer:
        flash("Please choose a valid manufacturer prefix (A/B/E).", "error")
        return redirect(url_for("add_airplane_form"))

    if not model_number.isdigit():
        flash("Model number must be digits only.", "error")
        return redirect(url_for("add_airplane_form"))

    try:
        seats = int(seats_raw)
        age   = int(age_raw)
    except ValueError:
        flash("Seats and age must be valid numbers.", "error")
        return redirect(url_for("add_airplane_form"))

    airplane_id = f"{prefix}{model_number}-{airline_code}"

    c = conn.cursor()
    try:
        c.execute(
            """
            INSERT INTO airplane (airplane_id, airline_name, seat_capacity, manufacturer, age)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (airplane_id, a, seats, manufacturer, age),
        )
        conn.commit()
        flash(f"Airplane {airplane_id} added.", "success")
    except Exception:
        conn.rollback()
        flash("Error adding airplane.", "error")
    finally:
        c.close()

    return redirect(url_for("list_my_airplanes"))


@app.get("/staff/airplanes")
def list_my_airplanes():
    guard = _require_staff()
    if guard: return guard
    c = conn.cursor()
    c.execute("""SELECT airplane_id, seat_capacity, manufacturer, age
                 FROM airplane WHERE airline_name=%s ORDER BY airplane_id""",
              (session['airline_name'],))
    rows = c.fetchall(); c.close()
    return render_template("list_airplanes.html", airplanes=rows)

# 5) View flight ratings (avg + comments)
@app.get("/staff/ratings")
def staff_ratings():
    guard = _require_staff()
    if guard: return guard
    a = session['airline_name']
    c = conn.cursor()
    c.execute("""
      SELECT f.flight_no,
             DATE_FORMAT(f.dep_datetime,'%%Y-%%m-%%d %%H:%%i:%%s') AS dep_key,
             DATE_FORMAT(f.dep_datetime,'%%M %%e, %%Y %%l:%%i %%p') AS dep_disp,
             f.dep_airport_code, f.arr_airport_code,
             ROUND(AVG(fr.rating),2) AS avg_rating, COUNT(fr.rating) AS num_reviews
      FROM Flight f
      LEFT JOIN FlightRating fr
        ON fr.flight_no=f.flight_no AND fr.dep_datetime=f.dep_datetime AND fr.airline_name=f.airline_name
      WHERE f.airline_name=%s
      GROUP BY f.flight_no, f.dep_datetime, f.dep_airport_code, f.arr_airport_code
      ORDER BY f.dep_datetime DESC
      LIMIT 300
    """,(a,))
    flights = c.fetchall(); c.close()
    return render_template("staff_ratings.html", flights=flights)

@app.get("/staff/ratings/detail")
def staff_ratings_detail():
    guard = _require_staff()
    if guard: return guard
    a = session['airline_name']
    flight_no = request.args['flight_no']
    dep_dt_key= request.args['dep_dt_key']
    dep_dt    = datetime.strptime(dep_dt_key,"%Y-%m-%d %H:%M:%S")
    c = conn.cursor()
    c.execute("""
      SELECT fr.rating, fr.comment, fr.customer_email, c.name AS customer_name
      FROM FlightRating fr JOIN Customer c ON c.email=fr.customer_email
      WHERE fr.flight_no=%s AND fr.dep_datetime=%s AND fr.airline_name=%s
      ORDER BY fr.rating DESC, c.name
    """,(flight_no, dep_dt, a))

    rows = c.fetchall()
    c.close()

    return render_template("staff_ratings_detail.html",
                           reviews=rows, flight_no=flight_no, dep_dt_key=dep_dt_key)

# 6) Reports (total sold + month-wise)
@app.get("/staff/reports")
def staff_reports():
    guard = _require_staff()
    if guard: return guard
    a = session['airline_name']
    from_date = request.args.get('from_date')
    to_date   = request.args.get('to_date')

    clauses = ["t.airline_name=%s"]; params=[a]
    if from_date:
        clauses.append("DATE(t.purchase_datetime) >= %s"); params.append(from_date)
    if to_date:
        clauses.append("DATE(t.purchase_datetime) <= %s"); params.append(to_date)
    where = " AND ".join(clauses)

    c = conn.cursor()
    c.execute(f"SELECT COUNT(*) AS total_tickets FROM Ticket t WHERE {where}", params)
    totals = c.fetchone()
    c.execute(f"""
      SELECT DATE_FORMAT(t.purchase_datetime,'%%Y-%%m') AS ym, COUNT(*) AS cnt
      FROM Ticket t
      WHERE {where}
      GROUP BY ym ORDER BY ym
    """, params)
    monthly = c.fetchall(); c.close()

    return render_template("staff_reports.html",
                           totals=totals, monthly=monthly,
                           from_date=from_date or "", to_date=to_date or "")

# 7) Manage staff phone numbers
@app.get("/staff/phones")
def staff_manage_phones():
    guard = _require_staff()
    if guard:
        return guard

    username = session.get("staff_username")
    if not username:
        flash("Unable to load staff username for phone numbers.", "error")
        return redirect(url_for("staff_home"))

    c = conn.cursor()
    c.execute("SELECT phone_number FROM StaffPhoneNo WHERE username = %s", (username,))
    phones = c.fetchall()
    c.close()

    return render_template("staff_manage_phones.html", phones=phones)

@app.post("/staff/phones/add")
def staff_add_phone():
    guard = _require_staff()
    if guard:
        return guard

    username = session.get("staff_username")
    if not username:
        flash("Unable to load staff username for phone numbers.", "error")
        return redirect(url_for("staff_manage_phones"))
    raw_phone = request.form.get("phone_number", "").strip()

    if not raw_phone:
        flash("Please enter a phone number.", "error")
        return redirect(url_for("staff_manage_phones"))

    digits_only = ""
    for c in raw_phone:
        if c.isdigit():
            digits_only += c

    if len(digits_only) < 7:
        flash("Phone number seems too short — include at least 7 digits.", "error")
        return redirect(url_for("staff_manage_phones"))

    if len(raw_phone) > 20:
        flash("Phone number must be 20 characters or fewer.", "error")
        return redirect(url_for("staff_manage_phones"))
    
    # Normalize so formatting is consistent (e.g. +1-718-555-1212)
    phone_number = _normalize_staff_phone(raw_phone)

    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO StaffPhoneNo (username, phone_number) VALUES (%s, %s)",
            (username, phone_number),
        )
        conn.commit()
        flash("Phone number added.", "success")
    except Exception:
        conn.rollback()
        flash("Error adding phone number (it may already exist).", "error")
    finally:
        c.close()

    return redirect(url_for("staff_manage_phones"))


@app.post("/staff/phones/delete")
def staff_delete_phone():
    guard = _require_staff()
    if guard:
        return guard

    username = session.get("staff_username")
    if not username:
        flash("Unable to load staff username for phone numbers.", "error")
        return redirect(url_for("staff_manage_phones"))

    phone_number = request.form.get("phone_number", "").strip()

    c = conn.cursor()
    c.execute(
        "DELETE FROM StaffPhoneNo WHERE username=%s AND phone_number=%s",
        (username, phone_number),
    )
    conn.commit()
    c.close()

    flash("Phone number deleted.", "success")
    return redirect(url_for("staff_manage_phones"))

# ================= End Staff Features =======================================

@app.route('/logout')
def logout():
	session.clear()
	return redirect(url_for('login'))
		
app.secret_key = 'some key that you will never guess'

#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)
