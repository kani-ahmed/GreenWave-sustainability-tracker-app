# challenge_views.py

from flask import request, jsonify
from models import Challenge, PersonalChallengeParticipant, User, CommunityChallenge, Badge, \
    CommunityChallengeParticipant
from extensions import db
from datetime import datetime, timezone


def register_challenge_routes(app):
    @app.route('/create_personal_challenge', methods=['POST'])
    def create_personal_challenge():
        data = request.get_json()

        name = data.get('name')
        description = data.get('description')
        eco_points = data.get('eco_points')
        start_date = data.get('start_date')  # Expecting ISO 8601 format (e.g., "2020-01-01T00:00:00")
        end_date = data.get('end_date')  # Same format as start_date

        if not all([name, description, eco_points, start_date, end_date]):
            return jsonify({"error": "Missing required challenge information"}), 400

        if Challenge.query.filter_by(name=name).first():
            return jsonify({"error": "Challenge with this name already exists"}), 409

        new_challenge = Challenge(
            name=name,
            description=description,
            eco_points=eco_points,
            start_date=datetime.fromisoformat(start_date),
            end_date=datetime.fromisoformat(end_date)
        )

        db.session.add(new_challenge)
        db.session.commit()

        return jsonify({"message": "Challenge created successfully", "challenge_id": new_challenge.id}), 201

    @app.route('/join_personal_challenge', methods=['POST'])
    def join_personal_challenge():
        data = request.get_json()
        user_id = data.get('user_id')
        challenge_id = data.get('challenge_id')

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        challenge = Challenge.query.get(challenge_id)
        if not challenge:
            return jsonify({"error": "Challenge not found"}), 404

        new_user_challenge = PersonalChallengeParticipant(user_id=user_id, challenge_id=challenge_id,
                                                          start_date=datetime.now(timezone.utc))
        db.session.add(new_user_challenge)
        db.session.commit()

        return jsonify({"message": "Challenge started successfully"}), 200

    @app.route('/edit_personal_challenge/<int:participant_id>', methods=['PUT'])
    def edit_personal_challenge(participant_id):
        personal_challenge_participant = PersonalChallengeParticipant.query.get(participant_id)

        if not personal_challenge_participant:
            return jsonify({"error": "Personal challenge participation not found"}), 404

        user_id = request.json.get('user_id')
        if personal_challenge_participant.user_id != user_id:
            return jsonify({"error": "Unauthorized edit attempt"}), 403

        new_start_date = request.json.get('start_date')
        new_end_date = request.json.get('end_date')

        if new_start_date and datetime.fromisoformat(new_start_date) < datetime.now(timezone.utc):
            return jsonify({"error": "Start date cannot be in the past"}), 400

        if new_start_date:
            personal_challenge_participant.start_date = datetime.fromisoformat(new_start_date)

        if new_end_date:
            personal_challenge_participant.end_date = datetime.fromisoformat(new_end_date)

        db.session.commit()
        return jsonify({"message": "Personal challenge participation updated successfully"}), 200

    @app.route('/complete_personal_challenge/<int:user_id>/<int:challenge_id>', methods=['POST'])
    def complete_personal_challenge(user_id, challenge_id):
        user_challenge = PersonalChallengeParticipant.query.filter_by(user_id=user_id, challenge_id=challenge_id,
                                                                      end_date=None).first()
        if not user_challenge:
            return jsonify({"error": "Challenge not started or already completed"}), 404

        now = datetime.now(timezone.utc)
        user_challenge.end_date = now
        db.session.commit()

        # Deduct 15% from user's accumulated eco-points
        challenge = Challenge.query.get(challenge_id)
        user = User.query.get(user_id)
        penalty_points = challenge.eco_points * 0.15
        user.eco_points = max(user.eco_points - penalty_points, 0)  # Ensure eco_points do not go below 0
        db.session.commit()

        # Check and award new badges based on updated eco-points
        awarded_badges = []
        eligible_badges = Badge.query.filter(Badge.eco_points_required <= user.eco_points).all()
        for badge in eligible_badges:
            if badge not in user.badges:
                user.badges.append(badge)
                awarded_badges.append(badge.name)

        db.session.commit()

        return jsonify({
            "message": "Challenge ended prematurely. Eco-points deducted.",
            "eco_points": user.eco_points,
            "awarded_badges": awarded_badges
        }), 200

    @app.route('/delete_personal_challenge/<int:user_id>/<int:challenge_id>', methods=['DELETE'])
    def delete_personal_challenge(user_id, challenge_id):
        personal_challenge = PersonalChallengeParticipant.query.filter_by(user_id=user_id,
                                                                          challenge_id=challenge_id).first()
        if not personal_challenge:
            return jsonify({"error": "Personal challenge not found or not participated by the user"}), 404

        # Apply penalty if user accumulated points
        if personal_challenge.end_date:
            user = User.query.get(user_id)
            challenge = personal_challenge.challenge
            penalty_points = challenge.eco_points * 0.10  # 10% penalty
            user.eco_points = max(user.eco_points - penalty_points, 0)  # Ensure eco_points do not go below 0
            db.session.commit()

        db.session.delete(personal_challenge)
        db.session.commit()

        return jsonify({"message": "Personal challenge deleted successfully. Points penalized if accumulated."}), 200

    @app.route('/create_community_challenge', methods=['POST'])
    def create_community_challenge():
        data = request.get_json()
        challenge_id = data.get('challenge_id')
        created_by = data.get('created_by')

        if not Challenge.query.get(challenge_id):
            return jsonify({"error": "Challenge not found"}), 404

        new_community_challenge = CommunityChallenge(challenge_id=challenge_id, created_by=created_by)
        db.session.add(new_community_challenge)
        db.session.commit()

        return jsonify({"message": "Community challenge created successfully",
                        "community_challenge_id": new_community_challenge.id}), 200

    @app.route('/join_community_challenge', methods=['POST'])
    def join_community_challenge():
        data = request.get_json()
        user_id = data.get('user_id')
        community_challenge_id = data.get('community_challenge_id')

        # Ensure user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Ensure community challenge exists
        community_challenge = CommunityChallenge.query.get(community_challenge_id)
        if not community_challenge:
            return jsonify({"error": "Community challenge not found"}), 404

        # Check if user already joined the challenge
        participant = CommunityChallengeParticipant.query.filter_by(participant_id=user_id,
                                                                    community_challenge_id=community_challenge_id).first()
        if participant:
            return jsonify({"error": "User already joined this community challenge"}), 409

        # Add user to community challenge
        new_participant = CommunityChallengeParticipant(
            community_challenge_id=community_challenge_id,
            participant_id=user_id,
            status="active",
            progress=0,  # Initial progress
            start_date=datetime.now(timezone.utc),  # Start now
            end_date=None  # End date is unknown at this point
        )
        db.session.add(new_participant)
        db.session.commit()

        return jsonify({"message": "Successfully joined the community challenge"}), 200

    @app.route('/complete_community_challenge/<int:user_id>/<int:community_challenge_id>', methods=['POST'])
    def complete_community_challenge(user_id, community_challenge_id):
        participant = CommunityChallengeParticipant.query.filter_by(participant_id=user_id,
                                                                    community_challenge_id=community_challenge_id,
                                                                    end_date=None).first()
        if not participant:
            return jsonify({"error": "Not part of this community challenge or already completed"}), 404

        now = datetime.now(timezone.utc)
        participant.end_date = now
        participant.status = "completed prematurely"

        db.session.commit()

        # Retrieve the associated challenge to calculate the penalty
        community_challenge = CommunityChallenge.query.get(participant.community_challenge_id)
        challenge = community_challenge.challenge

        # Deduct 15% from user's accumulated eco-points as a penalty
        user = User.query.get(user_id)
        penalty_points = challenge.eco_points * 0.15
        user.eco_points = max(user.eco_points - penalty_points, 0)  # Ensure eco_points do not go below 0
        db.session.commit()

        # Check and award new badges based on updated eco-points
        awarded_badges = []
        eligible_badges = Badge.query.filter(Badge.eco_points_required <= user.eco_points).all()
        for badge in eligible_badges:
            if badge not in user.badges:
                user.badges.append(badge)
                awarded_badges.append(badge.name)

        db.session.commit()

        return jsonify({
            "message": "Community challenge ended prematurely. Eco-points deducted.",
            "eco_points": user.eco_points,
            "awarded_badges": awarded_badges
        }), 200

    @app.route('/delete_community_challenge/<int:user_id>/<int:community_challenge_id>', methods=['DELETE'])
    def delete_community_challenge(user_id, community_challenge_id):
        community_challenge = CommunityChallenge.query.get(community_challenge_id)
        if not community_challenge:
            return jsonify({"error": "Community challenge not found"}), 404

        # Check if the user is the creator
        if community_challenge.created_by != user_id:
            return jsonify({"error": "User is not the creator of the community challenge"}), 403

        # Check if there are other participants
        if community_challenge.participants.count() > 1:  # Count includes the creator as a participant
            return jsonify({"error": "Community challenge has other participants"}), 403

        db.session.delete(community_challenge)
        db.session.commit()

        return jsonify({"message": "Community challenge deleted successfully"}), 200

    @app.route('/edit_community_challenge/<int:user_id>/<int:community_challenge_id>', methods=['PUT'])
    def edit_community_challenge(user_id, community_challenge_id):
        community_challenge = CommunityChallenge.query.get(community_challenge_id)
        if not community_challenge:
            return jsonify({"error": "Community challenge not found"}), 404

        if community_challenge.created_by != user_id:
            return jsonify({"error": "User is not the creator of the community challenge"}), 403

        data = request.get_json()
        challenge = community_challenge.challenge
        new_start_date = datetime.fromisoformat(data.get('start_date'))
        new_end_date = datetime.fromisoformat(data.get('end_date'))

        if new_start_date < datetime.now(timezone.utc):
            return jsonify({"error": "Start date cannot be in the past"}), 400

        challenge.name = data.get('name', challenge.name)
        challenge.description = data.get('description', challenge.description)
        challenge.eco_points = data.get('eco_points', challenge.eco_points)
        challenge.start_date = new_start_date
        challenge.end_date = new_end_date

        db.session.commit()
        return jsonify({"message": "Community challenge updated successfully"}), 200

    @app.route('/get_badges/<int:user_id>', methods=['GET'])
    def get_badges(user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        badges = [badge.name for badge in user.badges]
        return jsonify({"badges": badges}), 200

