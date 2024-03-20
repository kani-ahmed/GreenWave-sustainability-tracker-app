# seed.py
from datetime import datetime, timezone, timedelta

from models import Challenge
from extensions import db


def seed_challenges(app):
    """Seed or update the database with challenge data."""
    challenge_data = [
        {
            "name": "Daily Quick Wins",
            "description": "Refuse a plastic straw",
            "eco_points": 5,
            "start_date": datetime.now(timezone.utc),
            "end_date": datetime.now(timezone.utc) + timedelta(days=1)
        },
        {
            "name": "Weekly Warriors",
            "description": "Use a refillable water bottle for a week",
            "eco_points": 50,
            "start_date": datetime.now(timezone.utc),
            "end_date": datetime.now(timezone.utc) + timedelta(days=7)
        },
        {
            "name": "Monthly Masters",
            "description": "Avoid all single-use plastics for a month",
            "eco_points": 200,
            "start_date": datetime.now(timezone.utc),
            "end_date": datetime.now(timezone.utc) + timedelta(days=30)
        },
        {
            "name": "Yearly Heroes",
            "description": "Reduce personal waste by 50%",
            "eco_points": 1000,
            "start_date": datetime.now(timezone.utc),
            "end_date": datetime.now(timezone.utc) + timedelta(days=365)
        }
    ]

    with app.app_context():
        for challenge_info in challenge_data:
            challenge = Challenge.query.filter_by(name=challenge_info["name"]).first()
            if challenge:
                # Update existing challenge
                challenge.description = challenge_info["description"]
                challenge.eco_points = challenge_info["eco_points"]
                challenge.start_date = challenge_info["start_date"]
                challenge.end_date = challenge_info["end_date"]
                print(f"Updated challenge: {challenge.name}")
            else:
                # Add new challenge
                new_challenge = Challenge(**challenge_info)
                db.session.add(new_challenge)
                print(f"Added new challenge: {new_challenge.name}")

        db.session.commit()