"""
Run directly:   python create_db.py
Or as module:   python -m arcane_armory.create_db

sys.path manipulation lets the relative-style imports work in both cases.
"""
import sys
from pathlib import Path

# Allow running as a top-level script (python create_db.py)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from arcane_armory.app import create_app, db
from arcane_armory.models import Character, SpellSlot, InitiativeEntry

def seed():
    chars = [
        Character(name="Fighter", current_hp=24, max_hp=24, notes="Frontline"),
        Character(name="Wizard", current_hp=14, max_hp=18, notes="Caster"),
        Character(name="Cleric", current_hp=20, max_hp=20, notes="Healer"),
    ]
    db.session.add_all(chars)
    db.session.commit()

    # Spell slots for Wizard (id = chars[1]) and Cleric (id = chars[2])
    wizard = chars[1]
    cleric = chars[2]

    for lvl, (cur, mx) in {1: (4, 4), 2: (3, 3), 3: (2, 2)}.items():
        db.session.add(SpellSlot(character_id=wizard.id, slot_level=lvl, current_slots=cur, max_slots=mx))

    for lvl, (cur, mx) in {1: (4, 4), 2: (3, 3)}.items():
        db.session.add(SpellSlot(character_id=cleric.id, slot_level=lvl, current_slots=cur, max_slots=mx))

    # Initiative rows for all characters
    for c in chars:
        db.session.add(InitiativeEntry(character_id=c.id, initiative_value=0, is_current_turn=False))

    db.session.commit()

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        if Character.query.count() == 0:
            seed()
            print("Database created and seeded.")
        else:
            print("Database already has data; skipped seeding.")