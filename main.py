import re
from flask import *
import pymysql.cursors
from datetime import datetime
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
	cursor.execute("SELECT code FROM Airport ORDER BY code")
	rows = cursor.fetchall()
	cursor.close()
	return [row["code"] for row in rows]


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
	return render_template('staff_home.html')

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
