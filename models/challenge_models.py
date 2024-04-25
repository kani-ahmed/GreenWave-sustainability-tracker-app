# challenge_models.py

from datetime import datetime, timezone

from extensions import db


class EnvironmentalImpact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recycled_bottles = db.Column(db.Integer, default=0)
    single_use_bottles = db.Column(db.Integer, default=0)
    refillable_bottles = db.Column(db.Integer, default=0)
    impact_score = db.Column(db.Float, nullable=False)
    water_saved = db.Column(db.Float, default=0)  # Liters of water saved
    plastic_waste_reduced = db.Column(db.Float, default=0)  # Kilograms of plastic waste reduced
    co2_emissions_prevented = db.Column(db.Float, default=0)  # Kilograms of CO2 emissions prevented
    money_saved = db.Column(db.Float, default=0)  # Money saved in currency unit
    user = db.relationship('User', backref=db.backref('impacts', lazy=True))
    personal_challenge_id = db.Column(db.Integer, db.ForeignKey('personal_challenge_participant.id'), nullable=True)
    community_challenge_id = db.Column(db.Integer,
                                       db.ForeignKey('community_challenge_participant.community_challenge_id'),
                                       nullable=True)


class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    eco_points = db.Column(db.Integer, nullable=False)
    # duration = db.Column(db.Integer, nullable=False)  # the unit (days, weeks, etc.)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    end_date = db.Column(db.DateTime, nullable=False)


class PersonalChallengeParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)
    challenge = db.relationship('Challenge', backref=db.backref('user_challenges', lazy=True))
    user = db.relationship('User', backref=db.backref('challenges', lazy='dynamic'))
    environmental_impacts = db.relationship('EnvironmentalImpact', backref='personal_challenge', lazy='dynamic')


# Association table for the many-to-many relationship between Badge and User
user_badges = db.Table('user_badges',
                       db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
                       db.Column('badge_id', db.Integer, db.ForeignKey('badge.id'), primary_key=True),
                       db.Column('earned_on', db.DateTime, default=datetime.now(timezone.utc))
                       # TO be added: Track when the badge was earned
                       )


class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    eco_points_required = db.Column(db.Integer, nullable=False)
    earners = db.relationship('User', secondary=user_badges, backref=db.backref('badges', lazy='dynamic'))


class CommunityChallenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'),
                           nullable=False)  # User who created the community challenge
    participants = db.relationship('CommunityChallengeParticipant', back_populates='community_challenge', overlaps="community_participations,community_challenges")


class CommunityChallengeParticipant(db.Model):
    __tablename__ = 'community_challenge_participant'
    community_challenge_id = db.Column(db.Integer, db.ForeignKey('community_challenge.id'), primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    status = db.Column(db.String(50))  # e.g., "active", "completed"
    progress = db.Column(db.Integer)  # Arbitrary progress metric, could be points, percentage, etc.
    start_date = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    end_date = db.Column(db.DateTime)  # Can be null until challenge is completed
    environmental_impacts = db.relationship('EnvironmentalImpact', backref='community_challenge', lazy='dynamic')

    # Relationships - these might already be implicitly defined by backrefs from User and CommunityChallenge
    # participant = db.relationship('User', backref='community_participations')
    # community_challenge = db.relationship('CommunityChallenge', backref='participants')

    participant = db.relationship('User', back_populates='community_participations',
                                  overlaps="participating_challenges,participants")
    community_challenge = db.relationship('CommunityChallenge', back_populates='participants',
                                          overlaps="community_participations,community_challenges")

