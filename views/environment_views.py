# environment_views.py

from flask import request, jsonify
from models import EnvironmentalImpact, UserAction, User
from extensions import db


def register_environment_routes(app):
    @app.route('/log_action', methods=['POST'])
    def log_action():
        data = request.get_json()
        user_id = data['user_id']
        action_type = data['action_type']
        details = data.get('details', {})

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        new_action = UserAction(user_id=user_id, action_type=action_type, details=details)
        db.session.add(new_action)

        # Assuming details contain environmental impact metrics
        impact_score = details.get('impact_score', 0)
        user.eco_points += impact_score  # Update user's eco points based on the action
        db.session.commit()

        return jsonify({"message": "Action logged successfully", "eco_points": user.eco_points}), 200

    @app.route('/get_impact/<int:user_id>', methods=['GET'])
    def get_impact(user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        impacts = EnvironmentalImpact.query.filter_by(user_id=user_id).all()

        impact_details = [
            {
                "id": impact.id,
                "user_id": impact.user_id,
                "impact_score": impact.impact_score,
                "water_saved": impact.water_saved,
                "plastic_waste_reduced": impact.plastic_waste_reduced,
                "co2_emissions_prevented": impact.co2_emissions_prevented,
                "money_saved": impact.money_saved,
                "recycled_bottles": impact.recycled_bottles,
                "single_use_bottles": impact.single_use_bottles,
                "refillable_bottles": impact.refillable_bottles,
            } for impact in impacts
        ]

        return jsonify(impact_details), 200

    @app.route('/get_eco_points/<int:user_id>', methods=['GET'])
    def get_eco_points(user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"eco_points": user.eco_points}), 200

    @app.route('/update_user_impact_score/<int:user_id>', methods=['PUT'])
    def update_user_impact_score(user_id):
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json()
        new_score = data.get('new_score')
        if new_score is None:
            return jsonify({"error": "New score is required"}), 400

        user.eco_points = new_score  # Assuming we're updating eco points as the impact score
        db.session.commit()

        return jsonify({"message": "User impact score updated successfully", "eco_points": user.eco_points}), 200

    def get_baseline_values():
        """Calculates and returns baseline values for each environmental metric."""
        co2_saved_per_year = 156  # kg CO2 savings per person per year using a reusable bottle
        plastic_saved_per_year = 1.5  # kg plastic waste saved per person per year
        money_saved_per_year = 308.88  # dollars saved per person per year
        water_saved_per_use = 0.83  # liters of water saved per use

        # Calculate baseline values based on daily usage
        baseline_co2_saved_per_action = co2_saved_per_year / 365
        baseline_plastic_saved_per_action = plastic_saved_per_year / 365
        baseline_money_saved_per_action = money_saved_per_year / 365
        baseline_water_saved_per_action = water_saved_per_use

        return {
            'co2_saved_per_action': baseline_co2_saved_per_action,
            'plastic_saved_per_action': baseline_plastic_saved_per_action,
            'money_saved_per_action': baseline_money_saved_per_action,
            'water_saved_per_action': baseline_water_saved_per_action,
        }

    def calculate_impact_score(baseline_values, co2_saved, water_saved, plastic_waste_reduced, money_saved):
        """Calculates the overall impact score based on normalized and weighted contributions of different
        environmental savings."""
        weights = {'co2_saved': 0.25, 'water_saved': 0.25, 'plastic_waste_reduced': 0.25, 'money_saved': 0.25}

        normalized_co2_saved = co2_saved / baseline_values['co2_saved_per_action']
        normalized_water_saved = water_saved / baseline_values['water_saved_per_action']
        normalized_plastic_waste_reduced = plastic_waste_reduced / baseline_values['plastic_saved_per_action']
        normalized_money_saved = money_saved / baseline_values['money_saved_per_action']

        impact_score = (
                normalized_co2_saved * weights['co2_saved'] +
                normalized_water_saved * weights['water_saved'] +
                normalized_plastic_waste_reduced * weights['plastic_waste_reduced'] +
                normalized_money_saved * weights['money_saved']
        )
        return impact_score

    @app.route('/log_water_usage', methods=['POST'])
    def log_water_usage():
        data = request.get_json()
        user_id = data['user_id']
        bottle_type = data['bottle_type']  # Expect 'recycled', 'single-use', 'refillable'
        count = data.get('count', 1)

        # Retrieve or create EnvironmentalImpact record for user
        impact_record = EnvironmentalImpact.query.filter_by(user_id=user_id).first()
        if not impact_record:
            impact_record = EnvironmentalImpact(
                user_id=user_id,
                impact_score=0  # Initialize impact_score to 0
            )
            db.session.add(impact_record)

        # Update environmental impact based on bottle type and count
        update_environmental_impact(impact_record, bottle_type, count)
        db.session.commit()

        return jsonify({"message": "Water usage logged successfully"}), 200

    def update_environmental_impact(impact_record, bottle_type, count):
        baseline_values = get_baseline_values()

        # Initialize impact record fields if they are None
        impact_record.co2_emissions_prevented = impact_record.co2_emissions_prevented or 0
        impact_record.water_saved = impact_record.water_saved or 0
        impact_record.plastic_waste_reduced = impact_record.plastic_waste_reduced or 0
        impact_record.money_saved = impact_record.money_saved or 0

        # Define the impact of each bottle type on environmental savings
        CO2_SAVINGS_FACTOR = {
            'recycled': 0.1,  # Example factor: Recycled bottles save 10% of baseline CO2 savings per use
            'single-use': 0,  # Single-use bottles do not save CO2
            'refillable': 0.3,  # Refillable bottles save 30% of baseline CO2 savings per use
        }
        WATER_SAVINGS_FACTOR = 1  # Assuming using a refillable bottle saves all the baseline water per use
        PLASTIC_WASTE_FACTOR = {
            'recycled': 0.02,  # Recycled bottles reduce 2% of baseline plastic waste per use
            'single-use': -0.03,  # Single-use bottles add 3% of baseline plastic waste per use
            'refillable': 0,  # Refillable bottles do not directly reduce additional plastic waste per use
        }
        MONEY_SAVINGS_FACTOR = 0.15  # Assuming using a refillable bottle saves 15% of baseline money savings per use

        # Calculate the environmental impact based on the type of bottle and count
        co2_emissions_saved = CO2_SAVINGS_FACTOR.get(bottle_type, 0) * baseline_values['co2_saved_per_action'] * count
        water_saved = WATER_SAVINGS_FACTOR * baseline_values[
            'water_saved_per_action'] * count if bottle_type == 'refillable' else 0
        plastic_waste_reduced = PLASTIC_WASTE_FACTOR.get(bottle_type, 0) * baseline_values[
            'plastic_saved_per_action'] * count
        money_saved = MONEY_SAVINGS_FACTOR * baseline_values[
            'money_saved_per_action'] * count if bottle_type == 'refillable' else 0

        # Update the environmental impact record
        impact_record.co2_emissions_prevented += co2_emissions_saved
        impact_record.water_saved += water_saved
        impact_record.plastic_waste_reduced += plastic_waste_reduced
        impact_record.money_saved += money_saved

        # Recalculate the impact score with updated values
        new_impact_score = calculate_impact_score(
            baseline_values,
            impact_record.co2_emissions_prevented,
            impact_record.water_saved,
            impact_record.plastic_waste_reduced,
            impact_record.money_saved
        )
        impact_record.impact_score = new_impact_score

