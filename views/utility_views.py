# utility_views.py

from flask import request, jsonify
from models import User, CommunityChallenge, Challenge, PersonalChallengeParticipant, CommunityChallengeParticipant
from extensions import db
from sqlalchemy import desc


def register_utility_routes(app):
    @app.route('/leaderboards', methods=['GET'])
    def get_leaderboards():
        top_users = User.query.order_by(desc(User.eco_points)).limit(10).all()
        leaderboard = [{"username": user.username, "eco_points": user.eco_points} for user in top_users]
        return jsonify(leaderboard=leaderboard)

    @app.route('/search', methods=['GET'])
    def search():
        query = request.args.get('query', '')
        users = User.query.filter(User.username.ilike('%{}%'.format(query))).all()
        challenges = CommunityChallenge.query.filter(CommunityChallenge.name.ilike('%{}%'.format(query))).all()

        users_result = [{"id": user.id, "username": user.username} for user in users]
        challenges_result = [{"id": challenge.id, "name": challenge.name} for challenge in challenges]

        return jsonify({"users": users_result, "challenges": challenges_result})

    @app.route('/report', methods=['POST'])
    def report():
        # Here you'd handle user reports, maybe saving them to a database or sending them to admins
        report_data = request.json
        # Placeholder for report handling logic
        return jsonify({"status": "success", "message": "Report submitted successfully"})

    @app.route('/user_insights/<int:user_id>', methods=['GET'])
    def get_user_insights(user_id):
        user = User.query.get_or_404(user_id)
        # Placeholder for generating insights based on user's activity
        insights = {
            "eco_points": user.eco_points,
            # Additional insights can be added here
        }
        return jsonify(insights=insights)

    @app.route('/customize_profile/<int:user_id>', methods=['PUT'])
    def customize_profile(user_id):
        user = User.query.get_or_404(user_id)
        updates = request.json
        # Example of updating the profile picture
        if 'profile_picture' in updates:
            user.profile_picture = updates['profile_picture']
        # Other profile customizations can be handled here
        db.session.commit()
        return jsonify({"status": "success", "message": "Profile updated successfully"})

    @app.route('/community_challenge_details/<int:community_challenge_id>', methods=['GET'])
    def get_community_challenge_details(community_challenge_id):
        community_challenge = CommunityChallenge.query.get_or_404(community_challenge_id)
        challenge = Challenge.query.get(community_challenge.challenge_id)
        details = {
            "name": challenge.name,
            "description": challenge.description,
            "eco_points": challenge.eco_points,
            "start_date": challenge.start_date.isoformat(),
            "end_date": challenge.end_date.isoformat(),
            "created_by": community_challenge.created_by
            # Other details can be included here
        }
        return jsonify(details)

    @app.route('/user_challenge_status/<int:user_id>', methods=['GET'])
    def get_user_challenge_status(user_id):
        personal_challenges = PersonalChallengeParticipant.query.filter_by(user_id=user_id).all()
        community_challenges = CommunityChallengeParticipant.query.filter_by(participant_id=user_id).all()

        personal_challenge_status = [{
            "challenge_id": pc.challenge.id,
            "name": pc.challenge.name,
            "status": "Participating",
            "type": "Personal",
            "start_date": pc.start_date.isoformat(),
            "end_date": pc.end_date.isoformat() if pc.end_date else None
        } for pc in personal_challenges]

        community_challenge_status = [{
            "community_challenge_id": cc.community_challenge_id,
            "challenge_id": cc.community_challenge.challenge_id,
            "name": cc.community_challenge.challenge.name,
            "status": cc.status,
            "type": "Community",
            "start_date": cc.start_date.isoformat(),
            "end_date": cc.end_date.isoformat() if cc.end_date else None
        } for cc in community_challenges]

        challenges_status = personal_challenge_status + community_challenge_status
        return jsonify(challenges_status)

