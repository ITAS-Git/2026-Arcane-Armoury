from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from pathlib import Path

db = SQLAlchemy()

# Force threading mode (works on Windows + Python 3.13)
socketio = SocketIO(async_mode="threading", cors_allowed_origins="*")


def create_app() -> Flask:
    app = Flask(__name__)

    # Ensure instance folder exists (where sqlite DB will live)
    instance_path = Path(app.instance_path)
    instance_path.mkdir(parents=True, exist_ok=True)

    db_path = instance_path / "arcane_armory.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    socketio.init_app(app)

    from . import models  # noqa: F401
    from .routes import register_routes
    register_routes(app)

    return app


if __name__ == "__main__":
    app = create_app()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)