from flask import render_template, request, jsonify
from . import socketio
from flask_socketio import emit
import os


# Server-side state cache so new connections immediately get the latest state
_last_state = None


def register_routes(app):

    @app.get("/api/portraits")
    def get_portraits():
        static_folder = os.path.join(app.root_path, "static")
        exts = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
        files = [
            f for f in os.listdir(static_folder)
            if os.path.splitext(f)[1].lower() in exts
        ]
        return jsonify(sorted(files))
    
    # ----------------------------
    # PAGE ROUTES (HTML)
    # ----------------------------

    @app.get("/")
    def home():
        return render_template("player.html")

    @app.get("/dm")
    def dm_page():
        return render_template("dm.html")

    @app.get("/player")
    def player_page():
        return render_template("player.html")

    # ----------------------------
    # API ROUTES
    # ----------------------------

    @app.post("/api/hp_delta")
    def hp_delta():
        data = request.get_json(force=True)
        try:
            player = int(data["player"])
            delta = int(data["delta"])
        except (KeyError, TypeError, ValueError) as e:
            return jsonify({"success": False, "error": f"Invalid : {e}"}), 400

        payload = {"player": player, "delta": delta}
        socketio.emit("hp_delta", payload)
        return jsonify({"success": True, "sent": payload})

    @app.post("/api/hp_delta_current_turn")
    def hp_delta_current_turn():
        global _last_state

        data = request.get_json(force=True)
        try:
            delta = int(data["delta"])
        except (KeyError, TypeError, ValueError) as e:
            return jsonify({"success": False, "error": f"Invalid payload: {e}"}), 400

        if _last_state is None:
            return jsonify({"success": False, "error": "No active state on server yet"}), 400

        players = _last_state.get("players", [])
        if not players:
            return jsonify({"success": False, "error": "No players in current state"}), 400

        try:
            turn_index = int(_last_state.get("turnIndex", 0))
        except (TypeError, ValueError):
            turn_index = 0

        turn_index = max(0, min(turn_index, len(players) - 1))

        player = players[turn_index]

        try:
            max_hp = int(player.get("maxHp", 1))
        except (TypeError, ValueError):
            max_hp = 1

        try:
            current_hp = int(player.get("hp", 0))
        except (TypeError, ValueError):
            current_hp = 0

        new_hp = max(0, min(current_hp + delta, max_hp))
        player["hp"] = new_hp

        socketio.emit("state_updated", _last_state)

        return jsonify({
            "success": True,
            "turnIndex": turn_index,
            "player": turn_index + 1,
            "playerName": player.get("name", f"Player {turn_index + 1}"),
            "hp": new_hp,
            "maxHp": max_hp,
            "delta": delta
        })

    @app.post("/api/slot_delta")
    def slot_delta():
        data = request.get_json(force=True)
        try:
            player = int(data["player"])
            level = int(data["level"])
            delta = int(data["delta"])
        except (KeyError, TypeError, ValueError) as e:
            return jsonify({"success": False, "error": f"Invalid payload: {e}"}), 400

        payload = {"player": player, "level": level, "delta": delta}
        socketio.emit("slot_delta", payload)
        return jsonify({"success": True, "sent": payload})

    # ----------------------------
    # SOCKET EVENTS
    # ----------------------------

    @socketio.on("connect")
    def on_connect():
        print("Socket client connected:", request.sid)
        if _last_state is not None:
            emit("state_updated", _last_state)

    @socketio.on("disconnect")
    def on_disconnect():
        print("Socket client disconnected")

    @socketio.on("request_state")
    def on_request_state():
        if _last_state is not None:
            emit("state_updated", _last_state)

    @socketio.on("state_set")
    def on_state_set(state):
        global _last_state
        _last_state = state
        socketio.emit("state_updated", state)
