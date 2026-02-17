# Arcane Armoury
Repository: 2026-Arcane Armoury
Organization: ITAS-Git
Course: ITAS Project Management (2026)

## Project Overview

The Arcane Armoury is a Raspberry Pi–based dual-screen encounter management tool designed to improve tabletop gameplay interaction and reduce paper dependency during sessions.

The system separates player-facing information from Dungeon Master controls using a two-display architecture:

- Player Screen (Public View): Displays HP, initiative order, and spell slots.
- DM Screen (Control Interface): Allows manual entry and editing of HP, initiative, and spell slots using mouse and keyboard.

Physical push buttons connected to Raspberry Pi GPIO allow players to increment or decrement HP without interrupting gameplay.

## Project Purpose

The purpose of this project is to:

- Increase player interaction by centralizing visible game data
- Provide a clean and readable interface for HP, initiative, and spell slot tracking
- Separate player and DM responsibilities through controlled interfaces
- Demonstrate integration of hardware (GPIO), backend software (Flask/SQLite), and frontend UI
- Apply Agile project management practices using GitHub Issues and Kanban

## Team Members
- Alexander Preston
- Brayden Burton
- Carter Ottenbreit

## System Architecture

Hardware:
- Raspberry Pi (dual HDMI output)
- 10-inch player-facing display
- Secondary DM display
- Momentary push buttons (HP increment/decrement)
- Supporting wiring and breadboard

Software:
- Python
- Flask (backend API)
- SQLite (database)
- HTML/CSS/JavaScript (frontend)
- Raspberry Pi OS

## Core Features

1. Dual-Screen Architecture
   - Public read-only player display
   - Interactive DM dashboard

2. HP Tracking
   - Player-controlled via physical buttons
   - DM manual override via dashboard

3. Initiative Tracking
   - DM-managed ordering
   - Real-time update to player screen

4. Spell Slot Tracking
   - Per-character slot levels
   - Spend and restore controls
   - Automatic validation (no negative or overflow values)

## Folder Structure

The repository follows this structure:

/app
    /static
        /css
        /js
    /templates
    app.py
    models.py
    routes.py

/documentation
    Project_Charter.pdf
    Scope_Statement.pdf
    WBS.xlsx
    Risk_Register.xlsx
    Meeting_Notes/
    Diagrams/

/hardware
    Wiring_Diagram.png
    GPIO_Map.pdf
    Parts_List.xlsx

/tests
    test_api.py

README.md

All documentation artifacts will be stored in the documentation folder and updated throughout the semester.


## Development Process

The team follows an iterative Agile workflow:

1. Issues created for each user story
2. Tasks broken into actionable checklist items
3. Priorities and size estimates assigned
4. Issues added to Kanban board
5. Work selected for 3-week sprint
6. Artifacts committed continuously to repository

## Repository Rules

- Every artifact (code, documentation, diagrams) must be committed.
- Clear commit messages are required.
- All team members have full privileges.

## License

Academic project for ITAS coursework.
