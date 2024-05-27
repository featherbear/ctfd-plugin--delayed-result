from flask import Blueprint

from CTFd.models import Challenges, db
from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.challenges import CHALLENGE_CLASSES, BaseChallenge
from CTFd.plugins.delayed_result.decay import DECAY_FUNCTIONS, logarithmic
from CTFd.plugins.migrations import upgrade
from datetime import datetime

class DelayedResult(Challenges):
    __mapper_args__ = {"polymorphic_identity": "delayed"}
    id = db.Column(
        None, db.ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True
    )
    expiry = db.Column(db.Integer)

    def isExpired(self):
        # return False
        return datetime.now() > self.getExpiry()

    def getExpiry(self):
        return datetime.fromtimestamp(self.expiry)
    
    def getNow(self):
        return datetime.now()


class DelayedResultChallenge(BaseChallenge):
    id = "delayed"  # Unique identifier used to register challenges
    name = "delayed"  # Name of a challenge type
    templates = (
        {  # Handlebars templates used for each aspect of challenge editing & viewing
            "create": "/plugins/delayed_result/assets/create.html",
            "update": "/plugins/delayed_result/assets/update.html",
            "view": "/plugins/delayed_result/assets/view.html",
        }
    )
    scripts = {  # Scripts that are loaded when a template is loaded
        "create": "/plugins/delayed_result/assets/create.js",
        "update": "/plugins/delayed_result/assets/update.js",
        "view": "/plugins/delayed_result/assets/view.js",
    }
    # Route at which files are accessible. This must be registered using register_plugin_assets_directory()
    route = "/plugins/delayed_result/assets/"
    # Blueprint used to access the static_folder directory.
    blueprint = Blueprint(
        "delayed_result",
        __name__,
        template_folder="templates",
        static_folder="assets",
    )
    challenge_model = DelayedResult

    @classmethod
    def read(cls, challenge):
        """
        This method is in used to access the data of a challenge in a format processable by the front end.

        :param challenge:
        :return: Challenge object, data dictionary to be returned to the user
        """
        challenge = DelayedResult.query.filter_by(id=challenge.id).first()
        data = {
            "id": challenge.id,
            "name": challenge.name,
            "value": challenge.value,
            "expiry": datetime.fromtimestamp(challenge.expiry).strftime("%Y-%m-%dT%H:%M:%S"),
            "description": challenge.description,
            "connection_info": challenge.connection_info,
            "next_id": challenge.next_id,
            "category": challenge.category,
            "state": challenge.state,
            "max_attempts": challenge.max_attempts,
            "type": challenge.type,
            "type_data": {
                "id": cls.id,
                "name": cls.name,
                "templates": cls.templates,
                "scripts": cls.scripts,
            },
        }
        return data

    @classmethod
    def update(cls, challenge, request):
        """
        This method is used to update the information associated with a challenge. This should be kept strictly to the
        Challenges table and any child tables.

        :param challenge:
        :param request:
        :return:
        """
        data = request.form or request.get_json()

        for attr, value in data.items():
            # # We need to set these to floats so that the next operations don't operate on strings
            # if attr in ("expiry"):
            #     # TODO: Change to date
            #     value = datetime.strptime("%Y-%m-%dT%H:%M")
            setattr(challenge, attr, value)

        db.session.commit()
        # return DelayedResultChallenge.calculate_value(challenge)
        return challenge

    # Visibly the user gets $.attempts to see if they've submitted, so we can add a change to the theme

    '''
    https://github.com/CTFd/CTFd/blob/69dc0a799ace1596d5a5f079db92684907b63882/CTFd/plugins/challenges/__init__.py#L110
    '''
    @classmethod
    def attempt(cls, challenge, request):
        if datetime.now().timestamp() > challenge.expiry:
            return super().attempt(challenge, request)

        return False, "Your submission has been taken"

    '''
    Adds to solve
    '''
    @classmethod
    def solve(cls, user, team, challenge, request):
        # Revert to usual flag behaviour if there is no more delay
        if datetime.now().timestamp() > challenge.expiry:
            return super().solve(user, team, challenge, request)
        
        # Add submission to the "fail" pile, so it doesn't appear as solved
        # We should add some sort of timer to check
        return super().fail(user, team, challenge, request)

def transition_solves_from_fail_pile():
    print(DelayedResult.query)
    # Get challenges
    # Check
    # Move
    '''

       all_challenge_ids = {
            c.id for c in Challenges.query.with_entities(Challenges.id).all()
        }
        get_all_challenges 
    '''
    pass

'''
on load
  Check for all existing challenges with unprocessed solves

on schedule
  same thing!
'''

class Scheduler:
    pass

def load(app):
    app.db.create_all()
    CHALLENGE_CLASSES["delayed"] = DelayedResultChallenge
    transition_solves_from_fail_pile()
    
    register_plugin_assets_directory(
        app, base_path="/plugins/delayed_result/assets/"
    )
