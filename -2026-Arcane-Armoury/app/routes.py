from flask import render_template, request, jsonify
from .app import socketio
from flask_socketio import emit

# Server-side state cache so new connections immediately get the latest state
_last_state = None


def register_routes(app):
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
            return jsonify({"success": False, "error": f"Invalid payload: {e}"}), 400

        payload = {"player": player, "delta": delta}
        socketio.emit("hp_delta", payload)
        return jsonify({"success": True, "sent": payload})

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
        # Push cached state to newly connected client so it is immediately in sync
        if _last_state is not None:
            emit("state_updated", _last_state)

    @socketio.on("disconnect")
    def on_disconnect():
        print("Socket client disconnected")

    @socketio.on("request_state")
    def on_request_state():
        """Client asks for latest state on page load."""
        if _last_state is not None:
            emit("state_updated", _last_state)

    @socketio.on("state_set")
    def on_state_set(state):
        """
        DM sends full state snapshot.
        Broadcast to ALL clients including sender — the DM tab handles
        deduplication itself in JS using the 'dm_ack' flag.
        """
        global _last_state
        _last_state = state
        socketio.emit("state_updated", state)
