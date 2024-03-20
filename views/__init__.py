# __init__.py in the views package

from flask import Flask


def create_app():
    app = Flask(__name__)

    # Register environment routes
    from .environment_views import register_environment_routes
    register_environment_routes(app)

    # Register challenge routes
    from .challenge_views import register_challenge_routes
    register_challenge_routes(app)

    # Register social routes
    from .social_views import register_social_routes
    register_social_routes(app)

    # Register user routes
    from .user_views import register_user_routes
    register_user_routes(app)

    # Register utility routes
    from .utility_views import register_utility_routes
    register_utility_routes(app)

    return app
