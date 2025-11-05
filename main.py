import re
from flask import *
import pymysql.cursors
from datetime import datetime

# Initialize the app from Flask
app = Flask(__name__)

# Configure MySQL
conn = pymysql.connect(host='127.0.0.1',
                       user='root',
                       password='',
                       db='airline_reservation',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
	return render_template('index.html')

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
	query = """SELECT role, airline_name 
			FROM (
				SELECT 'customer' AS role, NULL AS airline_name
				FROM Customer WHERE email = %s AND password = MD5(%s)
				UNION ALL
				SELECT 'staff' AS role, airline_name
				FROM AirlineStaff WHERE email = %s AND password = MD5(%s)
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

	username = session.get('email')
	return render_template('index.html', username=username)

@app.route('/home')
def home():
    username = session.get('email')  # None if not logged in
    return render_template('home.html', username=username, role=session.get('role'))

@app.route('/customer_home')
def customer_home():
    return redirect(url_for('home'))

@app.route('/staff_home')
def staff_home():
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
	session.pop('email')
	return redirect('/')
		
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)
