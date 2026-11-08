"""
Seed a fresh local CTFd for trying the plugin (run by docker-compose.yml).

Skips the setup wizard and creates an admin, a student and one delayed
challenge whose results are released SEED_DELAY_MINUTES from now. Does nothing
if CTFd is already set up.
"""

import os
import time

from CTFd import create_app
from CTFd.models import Admins, Flags, Users, db
from CTFd.utils import set_config
from CTFd.utils.config import is_setup

FLAG = "flag{delayed}"
PASSWORD = "password"

app = create_app()
with app.app_context():
    if is_setup():
        print("CTFd is already set up; skipping seed")
        raise SystemExit(0)

    from CTFd.plugins.delayed_result import DelayedResult

    set_config("ctf_name", "Delayed Result Sandbox")
    set_config("ctf_theme", "core")
    set_config("user_mode", "users")
    set_config("challenge_visibility", "private")
    set_config("registration_visibility", "public")
    set_config("score_visibility", "public")
    set_config("account_visibility", "public")

    db.session.add(Admins(name="admin", email="admin@example.com", password=PASSWORD, verified=True))
    db.session.add(Users(name="student", email="student@example.com", password=PASSWORD, verified=True))

    delay = int(os.environ.get("SEED_DELAY_MINUTES", "3"))
    challenge = DelayedResult(
        name="Delayed challenge",
        category="sample",
        description=f"Submit `{FLAG}`.",
        value=100,
        state="visible",
        type="delayed",
        expiry=int(time.time()) + delay * 60,
    )
    db.session.add(challenge)
    db.session.flush()
    db.session.add(Flags(challenge_id=challenge.id, type="static", content=FLAG))

    set_config("setup", True)
    db.session.commit()
    print(f"Seeded: log in as student/{PASSWORD} or admin/{PASSWORD}; results release in {delay} minutes")
