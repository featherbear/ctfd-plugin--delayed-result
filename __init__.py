from flask import Blueprint

from CTFd.models import Challenges, db
from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.challenges import CHALLENGE_CLASSES, BaseChallenge
from CTFd.plugins.delayed_result.decay import DECAY_FUNCTIONS, logarithmic


class DelayedResult(Challenges):
    __mapper_args__ = {"polymorphic_identity": "delayed"}
    id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True
    )
    initial = db.Column(db.Integer, default=0)
    minimum = db.Column(db.Integer, default=0)
    decay = db.Column(db.Integer, default=0)
    function = db.Column(db.String(32), default="logarithmic")

    def __init__(self, *args, **kwargs):
        super(DelayedResult, self).__init__(**kwargs)
        self.value = kwargs["initial"]


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
    def calculate_value(cls, challenge):
        f = DECAY_FUNCTIONS.get(challenge.function, logarithmic)
        value = f(challenge)

        challenge.value = value
        db.session.commit()
        return challenge

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
            "initial": challenge.initial,
            "decay": challenge.decay,
            "minimum": challenge.minimum,
            "function": challenge.function,
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
            # We need to set these to floats so that the next operations don't operate on strings
            if attr in ("initial", "minimum", "decay"):
                value = float(value)
            setattr(challenge, attr, value)

        return DelayedResultChallenge
    .calculate_value(challenge)

    @classmethod
    def solve(cls, user, team, challenge, request):
        super().solve(user, team, challenge, request)

        DelayedResultChallenge
    .calculate_value(challenge)


def load(app):
    CHALLENGE_CLASSES["dynamic"] = DelayedResultChallenge

    register_plugin_assets_directory(
        app, base_path="/plugins/delayed_result/assets/"
    )
