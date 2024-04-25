# challenge_views.py

from flask import request, jsonify
from models import Challenge, PersonalChallengeParticipant, User, CommunityChallenge, Badge, \
    CommunityChallengeParticipant, ChallengesInbox, EnvironmentalImpact
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

    # added views:

    @app.route('/get_personal_challenges/<int:user_id>', methods=['GET'])
    def get_personal_challenges(user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        personal_challenges = PersonalChallengeParticipant.query.filter_by(user_id=user_id).all()
        if not personal_challenges:
            return jsonify({"message": "No personal challenges found for this user"}), 200

        challenge_details = []
        for part in personal_challenges:
            challenge = Challenge.query.get(part.challenge_id)
            if not challenge:
                continue

            # Retrieve the environmental impact for the current personal challenge
            environmental_impact = EnvironmentalImpact.query.filter_by(
                user_id=user_id,
                personal_challenge_id=part.id
            ).first()

            impact_score = environmental_impact.impact_score if environmental_impact else 0

            challenge_details.append({
                'challenge_id': challenge.id,
                'name': challenge.name,
                'description': challenge.description,
                'start_date': part.start_date.isoformat(),
                'end_date': part.end_date.isoformat() if part.end_date else None,
                'status': 'Completed' if part.end_date else 'In Progress',
                'impact_score': impact_score,
                'total_impact_score_all_personal_challenges': user.eco_points
            })

        return jsonify(challenge_details), 200

    @app.route('/award_badge', methods=['POST'])
    def award_badge():
        user_id = request.json.get('user_id')
        badge_type = request.json.get('badge_type')

        # Retrieve user from database
        user = User.query.get(user_id)
        if not user:
            return 'User not found', 404

        # Check if the badge type exists and can be awarded
        badge = Badge.query.filter_by(name=badge_type).first()
        if not badge:
            return 'Badge type not found', 404

        # Check if the user already has this badge
        if badge in user.badges:
            return 'Badge already awarded', 409

        # Award the badge to the user
        user.badges.append(badge)
        db.session.commit()

        return '', 204  # No Content response, indicating success

    @app.route('/create_badge', methods=['POST'])
    def create_badge():
        # Extract badge details from the request's JSON body
        badge_data = request.get_json()
        name = badge_data.get('name')
        eco_points_required = badge_data.get('eco_points_required')

        if not name or not eco_points_required:
            return jsonify({'error': 'Missing badge name or eco points required'}), 400

        # Check if the badge already exists
        if Badge.query.filter_by(name=name).first():
            return jsonify({'error': 'Badge already exists'}), 409

        # Create a new badge instance
        new_badge = Badge(name=name, eco_points_required=eco_points_required)

        # Add the new badge to the database
        db.session.add(new_badge)
        db.session.commit()

        return jsonify({'message': 'Badge created successfully', 'badge_id': new_badge.id}), 201

    # create a new route to get all community challenges
    @app.route('/get_community_challenges', methods=['GET'])
    def get_community_challenges():
        community_challenges = CommunityChallenge.query.all()

        challenges_data = []
        for community_challenge in community_challenges:
            challenge = Challenge.query.get(community_challenge.challenge_id)
            challenge_data = {
                "id": community_challenge.id,
                "name": challenge.name,
                "description": challenge.description,
                "eco_points": challenge.eco_points,
                "start_date": challenge.start_date.isoformat(),
                "end_date": challenge.end_date.isoformat(),
                "created_by": community_challenge.created_by
            }
            challenges_data.append(challenge_data)

        return jsonify(challenges_data)

    @app.route('/get_sent_personal_challenges/<int:user_id>', methods=['GET'])
    def get_sent_personal_challenges(user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        sent_challenges = [challenge for challenge in user.sent_challenges if challenge.challenge_id is not None]
        if not sent_challenges:
            return jsonify({"error": "No sent personal challenges found for this user"}), 404

        challenge_details = [{
            'id': challenge.id,
            'recipient_id': challenge.user_id,
            'recipient_username': challenge.user.username,
            'challenge_id': challenge.challenge_id,
            'challenge_name': challenge.challenge.name,
            'timestamp': challenge.timestamp.isoformat(),
            'status': challenge.status
        } for challenge in sent_challenges]

        return jsonify(challenge_details), 200

    @app.route('/get_sent_community_challenges/<int:user_id>', methods=['GET'])
    def get_sent_community_challenges(user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        sent_challenges = [challenge for challenge in user.sent_challenges if
                           challenge.community_challenge_id is not None]
        if not sent_challenges:
            return jsonify({"error": "No sent community challenges found for this user"}), 404

        challenge_details = [{
            'id': challenge.id,
            'recipient_id': challenge.user_id,
            'recipient_username': challenge.user.username,
            'community_challenge_id': challenge.community_challenge_id,
            'community_challenge_name': Challenge.query.get(challenge.community_challenge.challenge_id).name,
            'timestamp': challenge.timestamp.isoformat(),
            'status': challenge.status
        } for challenge in sent_challenges]

        return jsonify(challenge_details), 200

    @app.route('/get_received_personal_challenges/<int:user_id>', methods=['GET'])
    def get_received_personal_challenges(user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        received_challenges = [challenge for challenge in user.received_challenges if
                               challenge.challenge_id is not None]
        if not received_challenges:
            return jsonify({"error": "No received personal challenges found for this user"}), 404

        challenge_details = [{
            'id': challenge.id,
            'sender_id': challenge.sender_id,
            'sender_username': challenge.sender.username,
            'challenge_id': challenge.challenge_id,
            'challenge_name': challenge.challenge.name,
            'timestamp': challenge.timestamp.isoformat(),
            'status': challenge.status
        } for challenge in received_challenges]

        return jsonify(challenge_details), 200

    @app.route('/get_received_community_challenges/<int:user_id>', methods=['GET'])
    def get_received_community_challenges(user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        received_challenges = [challenge for challenge in user.received_challenges if
                               challenge.community_challenge_id is not None]
        if not received_challenges:
            return jsonify({"error": "No received community challenges found for this user"}), 404

        challenge_details = [{
            'id': challenge.id,
            'sender_id': challenge.sender_id,
            'sender_username': challenge.sender.username,
            'community_challenge_id': challenge.community_challenge_id,
            'community_challenge_name': Challenge.query.get(
                CommunityChallenge.query.get(challenge.community_challenge_id).challenge_id).name,
            'timestamp': challenge.timestamp.isoformat(),
            'status': challenge.status
        } for challenge in received_challenges]

        return jsonify(challenge_details), 200

    @app.route('/send_personal_challenge', methods=['POST'])
    def send_personal_challenge():
        data = request.get_json()
        sender_id = data.get('sender_id')
        recipient_id = data.get('recipient_id')
        challenge_id = data.get('challenge_id')

        sender = User.query.get(sender_id)
        recipient = User.query.get(recipient_id)
        challenge = Challenge.query.get(challenge_id)

        if not sender or not recipient or not challenge:
            return jsonify({"error": "Invalid sender, recipient, or challenge"}), 400

        new_challenge = ChallengesInbox(
            user_id=recipient_id,
            sender_id=sender_id,
            challenge_id=challenge_id,
            status="pending"
        )

        db.session.add(new_challenge)
        db.session.commit()

        return jsonify({"message": "Personal challenge sent successfully"}), 200

    @app.route('/send_community_challenge', methods=['POST'])
    def send_community_challenge():
        data = request.get_json()
        sender_id = data.get('sender_id')
        recipient_id = data.get('recipient_id')
        community_challenge_id = data.get('community_challenge_id')

        sender = User.query.get(sender_id)
        recipient = User.query.get(recipient_id)
        community_challenge = CommunityChallenge.query.get(community_challenge_id)

        if not sender or not recipient or not community_challenge:
            return jsonify({"error": "Invalid sender, recipient, or community challenge"}), 400

        new_challenge = ChallengesInbox(
            user_id=recipient_id,
            sender_id=sender_id,
            community_challenge_id=community_challenge_id,
            status="pending"
        )

        db.session.add(new_challenge)
        db.session.commit()

        return jsonify({"message": "Community challenge sent successfully"}), 200

    @app.route('/accept_challenge', methods=['PUT'])
    def accept_challenge():
        data = request.get_json()
        challenge_id = data.get('challenge_id')
        user_id = data.get('user_id')
        challenge_type = data.get('challenge_type')  # 'personal' or 'community'

        if not user_id or not challenge_id:
            return jsonify({"error": "Missing user ID or challenge ID"}), 400

        challenge_inbox = ChallengesInbox.query.filter_by(id=challenge_id, user_id=user_id).first()
        if not challenge_inbox:
            return jsonify({"error": "Challenge not found"}), 404

        if challenge_inbox.status != "pending":
            return jsonify({"error": "Challenge is not in a pending state"}), 400

        if challenge_type == 'community':
            community_challenge_id = challenge_inbox.community_challenge_id
            if not community_challenge_id:
                return jsonify({"error": "No community challenge associated"}), 400

            new_participant = CommunityChallengeParticipant(
                community_challenge_id=community_challenge_id,
                participant_id=user_id,
                status="active",
                progress=0,
                start_date=datetime.now(timezone.utc)
            )
            db.session.add(new_participant)

        elif challenge_type == 'personal':
            personal_challenge_id = challenge_inbox.challenge_id
            if not personal_challenge_id:
                return jsonify({"error": "No personal challenge associated"}), 400

            new_participant = PersonalChallengeParticipant(
                user_id=user_id,
                challenge_id=personal_challenge_id,
                start_date=datetime.now(timezone.utc)
            )
            db.session.add(new_participant)

        else:
            return jsonify({"error": "Invalid challenge type"}), 400

        challenge_inbox.status = "accepted"
        db.session.commit()

        return jsonify({"message": "Challenge accepted successfully"}), 200

    @app.route('/reject_challenge', methods=['PUT'])
    def reject_challenge():
        data = request.get_json()
        challenge_id = data.get('challenge_id')
        user_id = data.get('user_id')
        challenge_type = data.get('challenge_type')  # 'personal' or 'community'

        if not challenge_id or not user_id or not challenge_type:
            return jsonify({"error": "Challenge ID, User ID, and challenge type are required"}), 400

        challenge_inbox = ChallengesInbox.query.filter_by(id=challenge_id, user_id=user_id).first()
        if not challenge_inbox:
            return jsonify({"error": "Challenge not found"}), 404

        if challenge_inbox.status != "pending":
            return jsonify({"error": "Challenge is not in a pending state"}), 400

        if challenge_type == 'community' and not challenge_inbox.community_challenge_id:
            return jsonify({"error": "No community challenge associated"}), 400
        elif challenge_type == 'personal' and not challenge_inbox.challenge_id:
            return jsonify({"error": "No personal challenge associated"}), 400
        elif challenge_type not in ['personal', 'community']:
            return jsonify({"error": "Invalid challenge type"}), 400

        challenge_inbox.status = "rejected"
        db.session.commit()

        return jsonify({"message": f"Challenge rejected successfully. Type: {challenge_type}"}), 200
