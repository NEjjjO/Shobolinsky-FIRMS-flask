from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import folium
import requests
from datetime import datetime, timedelta
import logging
import ssl

app = Flask(__name__)
app.config['SECRET_KEY'] = "your_secret_key_here"

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# MongoDB connection setup
try:
    client = MongoClient("mongodb+srv://NEjjjO:fuckyou69@shoby0.bcrmqu3.mongodb.net/?retryWrites=true&w=majority",
                         ssl=True)
    db = client['FIRMS-recent']
    fire_data_collection = db['NASA']
    users_collection = db['users']
    logger.info("MongoDB connected successfully")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")

# Login Manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# NASA API Configuration
API_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
API_KEY = "0766fdd69804e90e9724d59ac79a6bf8"  # Change this to your NASA API key


# User class for Flask Login
class User(UserMixin):
    def __init__(self, username):
        self.id = username


@login_manager.user_loader
def load_user(username):
    user = users_collection.find_one({"username": username})
    if user:
        return User(username=user['username'])
    return None


# Login Form
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=128)])
    submit = SubmitField('Login')


# Register Form
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField('Password',
                             validators=[InputRequired(), EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Confirm Password')
    submit = SubmitField('Register')


# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            hashed_password = generate_password_hash(form.password.data)
            users_collection.insert_one({'username': form.username.data, 'password': hashed_password})
            flash('User registered successfully.')
            logger.info(f"User {form.username.data} registered successfully.")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'An error occurred while registering: {e}', 'error')
            logger.error(f"Error during registration: {e}")
            return redirect(url_for('register'))
    return render_template('register.html', form=form)


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = users_collection.find_one({'username': form.username.data})
            if user and check_password_hash(user['password'], form.password.data):
                user_obj = User(username=user['username'])
                login_user(user_obj)
                logger.info(f"User {form.username.data} logged in successfully.")
                return redirect(url_for('home'))
            else:
                flash('Invalid username or password!')
                logger.warning(f"Invalid login attempt for username {form.username.data}.")
        except Exception as e:
            flash(f'An error occurred while logging in: {e}', 'error')
            logger.error(f"Error during login: {e}")
    return render_template('login.html', form=form)


# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# Function to fetch data from NASA API and update MongoDB
@app.route('/fetch_data')
def fetch_data():
    params = {
        'product': 'MODIS_C6',
        'version': 'v1',
        'date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
        'geo': 'bbox',
        'bbox': '-180,-90,180,90',
        'key': API_KEY
    }
    response = requests.get(API_URL, params=params)
    if response.status_code == 200:
        try:
            data = response.json()
            # Ensure data is a list of dictionaries
            if isinstance(data, list) and all(isinstance(fire, dict) for fire in data):
                fire_data_collection.delete_many({})
                fire_data_collection.insert_many(data)
                logger.info("Data fetched and stored successfully")
                return {'message': 'Data fetched and stored successfully'}, 200
            else:
                logger.error("Data format is incorrect")
                return {'message': 'Data format is incorrect'}, 500
        except ValueError as e:
            logger.error("Failed to decode JSON:", e)
            return {'message': f"Failed to decode JSON: {e}"}, 500
    else:
        logger.error(f"Failed to fetch data: {response.status_code} {response.text}")
        return {'message': f"Failed to fetch data: {response.status_code}"}, 500


# Homepage route
@app.route('/')
def home():
    try:
        fire_data = list(fire_data_collection.find())
        logger.info(f"Fetched {len(fire_data)} records from the database.")
    except Exception as e:
        logger.error(f"Error fetching fire data: {e}")
        fire_data = []

    if fire_data:
        logger.debug(f"Sample records: {fire_data[:5]}")
        total_incidents = len(fire_data)
        most_affected_region = "North America"
        latest_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        fire_data_europe = [
            {"latitude": fire['latitude'], "longitude": fire['longitude']}
            for fire in fire_data
            if -10 <= fire['longitude'] <= 40 and 35 <= fire['latitude'] <= 70
        ]
        logger.info(f"Filtered {len(fire_data_europe)} fire records for Europe.")

        map_center = [54.5260, 15.2551]  # Center of Europe
        fire_map = folium.Map(location=map_center, zoom_start=4)
        for fire in fire_data_europe:
            folium.Marker(
                location=[fire['latitude'], fire['longitude']],
                popup=f"Fire detected at {fire['latitude']}, {fire['longitude']}"
            ).add_to(fire_map)

        # Save the map to static directory
        fire_map.save('static/fire_map.html')
    else:
        total_incidents = 0
        most_affected_region = "North America"
        latest_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return render_template(
        'home.html',
        total_incidents=total_incidents,
        most_affected_region=most_affected_region,
        latest_update=latest_update,
        fire_data=fire_data
    )


# Reporting guidelines page route
@app.route('/reporting_guidelines')
def reporting_guidelines():
    return render_template('reporting_guidelines.html')


# Safety guidelines page route
@app.route('/safety_guidelines')
def safety_guidelines():
    return render_template('safety_guidelines.html')


# FAQ page route
@app.route('/faq')
def faq():
    return render_template('faq.html')


# Sitemap page route
@app.route('/sitemap')
def sitemap():
    return render_template('sitemap.html')


# Report fire page route
@app.route('/report_fire', methods=['POST'])
@login_required
def report_fire():
    try:
        data = request.get_json()
        latitude = data['latitude']
        longitude = data['longitude']
        fire_data_collection.insert_one({'latitude': latitude, 'longitude': longitude, 'reported_by': current_user.id})
        return jsonify({'message': 'Fire reported successfully'}), 200
    except Exception as e:
        logger.error(f"Error reporting fire: {e}")
        return jsonify({'message': 'Failed to report fire'}), 500


if __name__ == '__main__':
    app.run(debug=True)