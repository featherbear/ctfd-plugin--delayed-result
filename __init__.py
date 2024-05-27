from flask import Blueprint, jsonify

from CTFd.models import Challenges, Solves, Fails, Flags, db
from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.flags import get_flag_class
from CTFd.plugins.challenges import CHALLENGE_CLASSES, BaseChallenge
from CTFd.cache import clear_challenges, clear_standings

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
            "expiry": datetime.fromtimestamp(challenge.expiry).strftime(
                "%Y-%m-%dT%H:%M:%S"
            ),
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
            setattr(challenge, attr, value)

        db.session.commit()
        return challenge

    # Visibly the user gets $.attempts to see if they've submitted, so we can add a change to the theme
    @classmethod
    def attempt(cls, challenge, request):
        if datetime.now().timestamp() > challenge.expiry:
            return super().attempt(challenge, request)

        return False, "Your submission has been taken"

    """
    Adds to solve
    """
    @classmethod
    def solve(cls, user, team, challenge, request):
        # Revert to usual flag behaviour if there is no more delay
        if datetime.now().timestamp() > challenge.expiry:
            return super().solve(user, team, challenge, request)

        # Add submission to the "fail" pile, so it doesn't appear as solved
        # We should add some sort of timer to check
        return super().fail(user, team, challenge, request)


def transition_solves_from_fail_pile():
    isModificationMade = False
    
    print("Searching for candidate delayed result challenges")
    results = []
    for challenge in DelayedResult.query.all():
        if not challenge.isExpired():
            continue

        # Find submissions marked as "failed" that were submitted before the challenge expired
        fails = (
            Fails.query.filter(
                Fails.challenge_id == challenge.id, Fails.date < challenge.getExpiry()
            )
            .order_by(Fails.date.desc())
            .distinct(Fails.user_id)
            .all()
        )

        # Someone with better SQL skill please make my code better
        solves = [
            (result.user_id, result.team_id)
            for result in Solves.query.filter_by(challenge_id=challenge.id).all()
        ]

        flags = Flags.query.filter_by(challenge_id=challenge.id).all()
        for fail in fails:
            if (fail.user_id, fail.team_id) in solves:
                continue
            for flag in flags:
                try:
                    if get_flag_class(flag.type).compare(flag, fail.provided):
                        solve = Solves(
                            # id=fail.id,
                            challenge_id=fail.challenge_id,
                            user_id=fail.user_id,
                            team_id=fail.team_id,
                            ip=fail.ip,
                            provided=fail.provided,
                            date=fail.date,
                        )
                        isModificationMade = True
                        db.session.delete(fail)
                        db.session.add(solve)
                        solves.append((fail.user_id, fail.team_id))
                        results.append(solve)
                        print(f"Transitioned held attempt {solve=} for {challenge=}")
                        break
                except Exception:
                    pass

    if isModificationMade:
        db.session.commit()
        clear_standings()
        clear_challenges()
    
    return results

def load(app):
    app.db.create_all()
    CHALLENGE_CLASSES["delayed"] = DelayedResultChallenge
    transition_solves_from_fail_pile()
    register_plugin_assets_directory(app, base_path="/plugins/delayed_result/assets/")

    @app.route('/plugin/do_update_delayed_result', methods=['GET'])
    def update():
        return jsonify(transition_solves_from_fail_pile())