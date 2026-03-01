from flask import render_template, request, jsonify
from .app import socketio
from flask_socketio import emit

def register_routes(app):
    # ----------------------------
    # PAGE ROUTES (HTML)
    # ----------------------------

    @app.get("/")
    def home():
        # Optional convenience redirect page
        return render_template("player.html")

    @app.get("/dm")
    def dm_page():
        return render_template("dm.html")

    @app.get("/player")
    def player_page():
        return render_template("player.html")

    # ----------------------------
    # API ROUTES (Fix 1: delta broadcast)
    # ----------------------------

    @app.post("/api/hp_delta")
    def hp_delta():
        data = request.get_json(force=True)
        player = int(data["player"])
        delta = int(data["delta"])

        payload = {"player": player, "delta": delta}
        socketio.emit("hp_delta", payload)
        return jsonify({"success": True, "sent": payload})

    @app.post("/api/slot_delta")
    def slot_delta():
        data = request.get_json(force=True)
        player = int(data["player"])
        level = int(data["level"])
        delta = int(data["delta"])

        payload = {"player": player, "level": level, "delta": delta}
        socketio.emit("slot_delta", payload)
        return jsonify({"success": True, "sent": payload})
    
    @socketio.on("connect")
    def on_connect():
    # Optional: helps debugging
        print("Socket client connected")

    @socketio.on("disconnect")
    def on_disconnect():
        print("Socket client disconnected")

    @socketio.on("state_set")
    def on_state_set(state):
        """
        DM sends full state snapshot.
        Server re-broadcasts to everyone (DM + Player screens).
        """
        # Broadcast to all clients
        socketio.emit("state_updated", state)