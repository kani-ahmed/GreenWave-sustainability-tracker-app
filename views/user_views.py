# user_views.py
from flask import request, jsonify
from werkzeug.security import generate_password_hash

from models import UserPreference, Notification, User
from extensions import db


def register_user_routes(app):
    @app.route('/register', methods=['POST'])
    def register_user():
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')  # Assuming the front end sends this

        if User.query.filter((User.username == username) | (User.email == email)).first():
            # User already exists
            return jsonify({"error": "Username or email already in use"}), 409

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password_hash=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "Registration successful"}), 201

    @app.route('/update_preferences/<int:user_id>', methods=['PUT'])
    def update_preferences(user_id):
        data = request.json
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Update user preferences
        preferences = UserPreference.query.filter_by(user_id=user_id).first()
        if not preferences:
            preferences = UserPreference(user_id=user_id)
            db.session.add(preferences)

        preferences.receive_notifications = data.get('receive_notifications', preferences.receive_notifications)
        preferences.privacy_settings = data.get('privacy_settings', preferences.privacy_settings)
        db.session.commit()

        return jsonify({"message": "Preferences updated successfully"}), 200

    @app.route('/get_notifications/<int:user_id>', methods=['GET'])
    def get_notifications(user_id):
        notifications = Notification.query.filter_by(user_id=user_id).all()
        notifications_data = [{"id": n.id, "content": n.content, "is_read": n.is_read,
                               "timestamp": n.timestamp.strftime('%Y-%m-%d %H:%M:%S')} for n in notifications]
        return jsonify(notifications_data), 200

    @app.route('/view_profile/<int:user_id>', methods=['GET'])
    def view_profile(user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        profile_data = {
            "username": user.username,
            "email": user.email,
            "profile_picture": user.profile_picture,
            "eco_points": user.eco_points
        }

        # Optional: include additional user data, like preferences
        preferences = UserPreference.query.filter_by(user_id=user_id).first()
        if preferences:
            profile_data["preferences"] = {
                "receive_notifications": preferences.receive_notifications,
                "privacy_settings": preferences.privacy_settings
            }

        return jsonify(profile_data), 200

    @app.route('/update_user_profile/<int:user_id>', methods=['PUT'])
    def update_user_profile(user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.json
        user.profile_picture = data.get('profile_picture', user.profile_picture)
        # Update additional fields as needed

        db.session.commit()

        return jsonify({"message": "User profile updated successfully"}), 200
