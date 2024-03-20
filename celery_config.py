import os
from celery import Celery
from celery.schedules import crontab
from datetime import datetime, timezone
from flask import Flask
from dotenv import load_dotenv
from extensions import db
from models import Challenge, PersonalChallengeParticipant, CommunityChallengeParticipant

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config.update(
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URI'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

# Initialize Flask extensions
db.init_app(app)


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['result_backend'],
        broker=app.config['broker_url']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    return celery


celery = make_celery(app)


@celery.task
def complete_challenges_automatically():
    now = datetime.now(timezone.utc)
    print("Running automatic challenge completion...")

    # Complete personal challenges
    personal_challenges = PersonalChallengeParticipant.query.filter(
        PersonalChallengeParticipant.end_date == None,
        PersonalChallengeParticipant.challenge.has(Challenge.end_date <= now)
    ).all()

    for participant in personal_challenges:
        participant.end_date = now

    # Complete community challenges
    community_challenges = CommunityChallengeParticipant.query.filter(
        CommunityChallengeParticipant.end_date == None,
        CommunityChallengeParticipant.community_challenge.has(Challenge.end_date <= now)
    ).all()

    for participant in community_challenges:
        participant.end_date = now
        participant.status = "completed"

    db.session.commit()
    print("Challenges updated successfully.")


celery.conf.beat_schedule = {
    'complete-challenges-every-midnight': {
        'task': 'celery_config.complete_challenges_automatically',
        'schedule': crontab(hour=0, minute=0),  # Executes daily at midnight
    },
}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure your database is ready and tables are created

# just execute the task like: celery -A celery_config.celery worker --loglevel=info --beat
