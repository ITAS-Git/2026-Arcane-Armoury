from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from pathlib import Path

db = SQLAlchemy()

# SocketIO is the WebSocket layer (Socket.IO protocol)
# eventlet is a lightweight async server that supports websockets well
socketio = SocketIO(cors_allowed_origins="*")  # ok for local LAN project

def create_app() -> Flask:
    app = Flask(__name__)

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
    # IMPORTANT: run with socketio.run, not app.run
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)