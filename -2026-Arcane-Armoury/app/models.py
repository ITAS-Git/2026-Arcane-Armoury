from .app import db

class Character(db.Model):
    __tablename__ = "characters"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)

    current_hp = db.Column(db.Integer, nullable=False, default=0)
    max_hp = db.Column(db.Integer, nullable=False, default=0)

    # Optional: for display (Wizard, Fighter, etc.)
    notes = db.Column(db.String(128), nullable=True)

    # Relationships
    spell_slots = db.relationship("SpellSlot", backref="character", cascade="all, delete-orphan")
    initiative_entry = db.relationship("InitiativeEntry", backref="character", uselist=False, cascade="all, delete-orphan")

class SpellSlot(db.Model):
    __tablename__ = "spell_slots"

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("characters.id"), nullable=False)

    # 1..9
    slot_level = db.Column(db.Integer, nullable=False)
    current_slots = db.Column(db.Integer, nullable=False, default=0)
    max_slots = db.Column(db.Integer, nullable=False, default=0)

    __table_args__ = (
        db.UniqueConstraint("character_id", "slot_level", name="uq_character_slotlevel"),
    )

class InitiativeEntry(db.Model):
    __tablename__ = "initiative"

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("characters.id"), nullable=False, unique=True)

    initiative_value = db.Column(db.Integer, nullable=False, default=0)
    is_current_turn = db.Column(db.Boolean, nullable=False, default=False)