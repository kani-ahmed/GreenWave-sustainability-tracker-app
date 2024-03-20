import os
import logging
from flask import Flask
from extensions import db
from sqlalchemy import text
from seed import seed_challenges

# Initialize logging
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')

# Determine if the app is running on Heroku
IS_HEROKU = 'DYNO' in os.environ

# Load environment variables only if not on Heroku
if not IS_HEROKU:
    from dotenv import load_dotenv

    load_dotenv()

# Import the create_app function from your views package
from views import create_app

# Call create_app to initialize your Flask application and register routes
app = create_app()

# Configure the SQLAlchemy database URI
if IS_HEROKU:
    # Parse the ClearDB URL and use it for SQLAlchemy
    cleardb_url = os.environ['CLEARDB_DATABASE_URL']
    # Remove the reconnect=true query from the URL if present
    if '?reconnect=true' in cleardb_url:
        cleardb_url = cleardb_url.split('?')[0]  # Alternatively, cleardb_url.replace('?reconnect=true', '')
    cleardb_url = cleardb_url.replace('mysql://', 'mysql+pymysql://')
    app.config['SQLALCHEMY_DATABASE_URI'] = cleardb_url
else:
    # When running locally, take the database URI from the .env file
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')

# Prevent SQLAlchemy from tracking modifications
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the SQLAlchemy app
db.init_app(app)


# Function to test database connection
def test_db_connection():
    try:
        with app.app_context():
            with db.engine.connect() as connection:
                # Using the text() construct to execute a simple query
                result = connection.execute(text("SELECT 1"))
                for row in result:
                    logging.info("Database connection test was successful. Result: {}".format(row))
    except Exception as e:
        logging.error(f"Database connection test failed: {e}")


if __name__ == '__main__':
    with app.app_context():
        if not IS_HEROKU:
            # Create database tables and seed only if not on Heroku
            db.create_all()
            seed_challenges(app)
            logging.info("Database tables created successfully.")
            test_db_connection()  # Test database connection only if not on Heroku
    # Run the Flask app
    # The host must be set to '0.0.0.0' to be accessible within the Heroku dyno
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
