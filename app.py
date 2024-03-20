# app.py

from flask import Flask
from dotenv import load_dotenv
from extensions import db
import os
import logging
from sqlalchemy import text
from seed import seed_challenges

# Initialize logging
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')

# Load environment variables
load_dotenv()

# Import the create_app function from your views package
from views import create_app

# Call create_app to initialize your Flask application and register routes
app = create_app()

# Configure the SQLAlchemy database URI
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
        try:
            # Create database tables
            db.create_all()
            logging.info("Database tables created successfully.")

            # Seed the database with challenge data
            seed_challenges(app)

            # Test database connection
            test_db_connection()
        except Exception as e:
            logging.error(f"Error during startup: {e}")

    # Run the Flask app
    app.run(debug=True)
