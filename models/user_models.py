# user_models.py

from datetime import datetime, timezone

from extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)  # Indexed for faster lookups
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)  # For notifications, also indexed
    profile_picture = db.Column(db.String(255))  # URL to profile picture
    eco_points = db.Column(db.Integer, default=0)  # Tracks eco-points directly on the user
    password_hash = db.Column(db.String(128))  # Add this line for storing hashed passwords
    # Additional fields as needed

    # Define the relationship to CommunityChallengeParticipant
    community_participations = db.relationship('CommunityChallengeParticipant', back_populates='participant',
                                               overlaps="participating_challenges,participants")


class UserAction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    user = db.relationship('User', backref=db.backref('actions', lazy=True))


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))


class UserPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receive_notifications = db.Column(db.Boolean, default=True)
    privacy_settings = db.Column(db.String(50))  # Example: "Public", "Friends Only", "Private"

    user = db.relationship('User', backref='preferences')
