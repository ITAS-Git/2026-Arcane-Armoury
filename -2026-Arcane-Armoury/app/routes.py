from flask import jsonify, request
from .app import db, socketio
from .models import Character

def register_routes(app):

    @app.post("/api/update_hp")
    def update_hp():
        """
        Called by:
        - GPIO script (physical buttons)
        - DM dashboard (manual change)
        """
        data = request.get_json(force=True)
        character_id = int(data["character_id"])
        delta = int(data["delta"])

        c = Character.query.get(character_id)
        if not c:
            return jsonify({"error": "Character not found"}), 404

        # Update + validate
        c.current_hp = max(0, min(c.max_hp, c.current_hp + delta))
        db.session.commit()

        payload = {
            "character_id": c.id,
            "current_hp": c.current_hp,
            "max_hp": c.max_hp,
        }

        # Broadcast to ALL connected screens
        socketio.emit("hp_updated", payload)

        return jsonify({"success": True, **payload})