import re
from flask import *
import pymysql.cursors
from datetime import datetime, timedelta   
from zoneinfo import ZoneInfo

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
    'AUH': 'Asia/Abu Dhabi',
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
            dep_dt = dep_dt.replace(tzinfo=ZoneInfo(AIRPORT_TZ[r['dep_airport_code']]))

            # Create arrival datetime with timezone
            arr_date_str = r['a_date'] + " " + r['a_time']
            arr_dt = datetime.strptime(arr_date_str, "%B %d, %Y %I:%M %p")
            arr_dt = arr_dt.replace(tzinfo=ZoneInfo(AIRPORT_TZ[r['arr_airport_code']]))

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

		return render_template('login.html', error=error)

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
			return render_template('register.html', error=f'{label} is required.')

	if (len(password) < 8 or not any(c.isupper() for c in password) or not any(c.isdigit() for c in password)):
		error = "Password must be at least 8 characters, include one uppercase letter and one number."
		return render_template('register.html', error = error)
	
	email_regex = r"[^@]+@[^@]+\.[^@]+"
	if not re.match(email_regex, email):
		error = "Please enter a valid email address."
		return render_template('register.html', error=error)
	
	# Minial check for phone numbers
	digits_only = ''
	for c in phone_number:
		if c.isdigit():
			digits_only += c

	if len(digits_only) < 7:
		return render_template('register.html', error="Phone number seems too short — include at least 7 digits.")
	if len(phone_number) > 20:
		return render_template('register.html', error="Phone number must be 20 characters or fewer.")

	if not re.match(r'^[A-Z0-9]{5,20}$', passport_number, re.IGNORECASE):
		error = "Please enter a valid passport number (5–20 alphanumeric characters)."
		return render_template('register.html', error=error)	

	try:
		dob = datetime.strptime(date_of_birth, '%Y-%m-%d')
		exp = datetime.strptime(passport_expiration, '%Y-%m-%d')
		if dob >= exp:
			error = "Passport expiration must be after date of birth."
			return render_template('register.html', error=error)
	except ValueError:
		error = "Invalid date format. Please use YYYY-MM-DD."
		return render_template('register.html', error=error)

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
		error = "This user already exists"
		return render_template('register.html', error = error)
	
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

	# basic validation
	if not (source and destination and depart_date):
		airports = get_airport_codes()
		return render_template('home.html', error="Please fill all required fields.", airports=airports)

	# disallow same-airport searches
	if source == destination:
		airports = get_airport_codes()
		return render_template('home.html', error="From and To cannot be the same airport.", airports=airports)
 
	if (trip_type == "oneway"):
		query =  """SELECT flight_no, airline_name, dep_airport_code, arr_airport_code, 
						   DATE_FORMAT(dep_datetime, '%%M %%e, %%Y') AS d_date,
				           DATE_FORMAT(dep_datetime, '%%l:%%i %%p') AS d_time,
						   DATE_FORMAT(arr_datetime, '%%M %%e, %%Y') AS a_date,
				           DATE_FORMAT(arr_datetime, '%%l:%%i %%p') AS a_time,
						   TIME_FORMAT(TIMEDIFF(arr_datetime, dep_datetime), '%%Hh %%im') AS flight_duration,
						   base_price
				    FROM flight
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
			'home.html',
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
			return render_template('home.html', error="Please pick a return date for round trips.", airports=airports)
		
		# ensure chronological round-trip dates
		if return_date < depart_date:
			airports = get_airport_codes()
			return render_template('home.html', error="Return date must be on or after the departure date.", airports=airports)

		query =  """SELECT flight_no, airline_name, dep_airport_code, arr_airport_code, 
						   DATE_FORMAT(dep_datetime, '%%M %%e, %%Y') AS d_date,
				           DATE_FORMAT(dep_datetime, '%%l:%%i %%p') AS d_time,
						   DATE_FORMAT(arr_datetime, '%%M %%e, %%Y') AS a_date,
				           DATE_FORMAT(arr_datetime, '%%l:%%i %%p') AS a_time,
						   TIME_FORMAT(TIMEDIFF(arr_datetime, dep_datetime), '%%Hh %%im') AS flight_duration,
						   base_price
				    FROM flight
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
			'home.html',
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

# ===== Helpers for staff features (ADD) =====================================
def _require_staff():
    """Redirect to login unless the session is a staff user with an airline."""
    if session.get('role') != 'staff' or not session.get('airline_name'):
        return redirect(url_for('login'))
    return None

def _parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None
# ============================================================================



@app.get("/")
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
    return redirect(url_for('home'))

@app.route('/staff_home')
def staff_home():
    # protect staff dashboard; bounce non-staff to login
    if session.get('role') != 'staff':
        return redirect(url_for('login'))

    airline = session.get('airline_name')
    c = conn.cursor()
    c.execute("""
        SELECT
            flight_no,
            dep_airport_code AS src,
            arr_airport_code AS dst,
            DATE_FORMAT(dep_datetime, '%%Y-%%m-%%d %%H:%%i') AS dep_datetime,
            status
        FROM flight
        WHERE airline_name = %s
          AND dep_datetime >= NOW()
          AND dep_datetime < DATE_ADD(NOW(), INTERVAL 30 DAY)
        ORDER BY dep_datetime ASC
        LIMIT 50
    """, (airline,))
    flights = c.fetchall()
    c.close()

    return render_template('staff_home.html', flights=flights)

# ================= Staff Features — Use Cases 1–6 (ADD) =====================

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
               DATE_FORMAT(dep_datetime,'%Y-%m-%d %H:%i:%s') AS dep_key,
               DATE_FORMAT(dep_datetime,'%M %e, %Y %l:%i %p') AS dep_disp,
               DATE_FORMAT(arr_datetime,'%M %e, %Y %l:%i %p') AS arr_disp,
               status, base_price
        FROM flight
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
    c.execute("""SELECT 1 FROM flight
                 WHERE flight_no=%s AND dep_datetime=%s AND airline_name=%s""",
              (flight_no, dep_dt, airline))
    if not c.fetchone():
        c.close(); flash("Flight not found for your airline.", "error")
        return redirect(url_for("staff_view_flights"))

    c.execute("""
      SELECT c.name, c.email, t.purchase_datetime
      FROM ticket t JOIN customer c ON c.email=t.customer_email
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
    a = session['airline_name']

    fno   = request.form['flight_no'].strip()
    depdt = request.form['dep_datetime'].strip()    # 'YYYY-MM-DD HH:MM'
    arrdt = request.form['arr_datetime'].strip()
    dep   = request.form['dep_airport_code'].strip().upper()
    arr   = request.form['arr_airport_code'].strip().upper()
    plane = request.form['airplane_id'].strip()
    price = request.form['base_price'].strip()

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
               DATE_FORMAT(dep_datetime,'%Y-%m-%d %H:%i:%s') AS dep_dt_key,
               DATE_FORMAT(dep_datetime,'%M %e, %Y %l:%i %p') AS dep_dt_disp,
               DATE_FORMAT(arr_datetime,'%M %e, %Y %l:%i %p') AS arr_dt_disp,
               status, base_price
        FROM flight
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
    c.execute("""SELECT 1 FROM flight
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
    if guard: return guard
    return render_template("add_airplane.html")

@app.post("/staff/add_airplane")
def add_airplane_submit():
    guard = _require_staff()
    if guard: return guard
    a = session['airline_name']
    plane_id = request.form['airplane_id'].strip()
    seats    = int(request.form['seat_capacity'])
    make     = request.form['manufacturer'].strip()
    age      = int(request.form['age'])

    c = conn.cursor()
    try:
        c.execute("""
          INSERT INTO airplane(airplane_id, airline_name, seat_capacity, manufacturer, age)
          VALUES (%s,%s,%s,%s,%s)
        """,(plane_id,a,seats,make,age))
        conn.commit(); flash("Airplane added.","success")
    except Exception:
        conn.rollback(); flash("Error adding airplane.","error")
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
             DATE_FORMAT(f.dep_datetime,'%Y-%m-%d %H:%i:%s') AS dep_key,
             DATE_FORMAT(f.dep_datetime,'%M %e, %Y %l:%i %p') AS dep_disp,
             f.dep_airport_code, f.arr_airport_code,
             ROUND(AVG(fr.rating),2) AS avg_rating, COUNT(fr.rating) AS num_reviews
      FROM flight f
      LEFT JOIN flightrating fr
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
      SELECT fr.rating, fr.comment, c.name AS customer_name
      FROM flightrating fr JOIN customer c ON c.email=fr.customer_email
      WHERE fr.flight_no=%s AND fr.dep_datetime=%s AND fr.airline_name=%s
      ORDER BY fr.rating DESC, c.name
    """,(flight_no, dep_dt, a))
    rows = c.fetchall(); c.close()
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
    c.execute(f"SELECT COUNT(*) AS total_tickets FROM ticket t WHERE {where}", params)
    totals = c.fetchone()
    c.execute(f"""
      SELECT DATE_FORMAT(t.purchase_datetime,'%Y-%m') AS ym, COUNT(*) AS cnt
      FROM ticket t
      WHERE {where}
      GROUP BY ym ORDER BY ym
    """, params)
    monthly = c.fetchall(); c.close()

    return render_template("staff_reports.html",
                           totals=totals, monthly=monthly,
                           from_date=from_date or "", to_date=to_date or "")
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
