import os
import sys
from pathlib import Path

# Ensure backend package is importable
BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND.parent / "database" / "seeds"))

from app import create_app
from app.extensions import db
from seed_data import seed_all

app = create_app(os.getenv("FLASK_ENV", "development"))


@app.cli.command("seed")
def seed_cmd():
    db.create_all()
    ok = seed_all(app)
    print("Seeds cargados." if ok else "Ya existían datos.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_all(app)
        from seed_data import sync_profile_visibility_perms

        sync_profile_visibility_perms(db)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
