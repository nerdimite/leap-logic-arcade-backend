import os
import sqlite3
from pathlib import Path

CURRENT_DIR = Path(__file__).parent


def seed_db():
    """Create a SQLite database with ship systems and protocols data."""
    db_path = CURRENT_DIR / "ship_database.sqlite"

    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)

    # Connect to the database (this will create it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create ship_systems table
    cursor.execute(
        """
    CREATE TABLE ship_systems (
        system_id INTEGER PRIMARY KEY,
        system_name TEXT,
        status TEXT,
        location TEXT,
        power_consumption REAL,
        last_maintenance DATE
    )
    """
    )

    # Create system_protocols table
    cursor.execute(
        """
    CREATE TABLE system_protocols (
        protocol_id INTEGER PRIMARY KEY,
        protocol_name TEXT,
        system_id INTEGER,
        file_location TEXT,
        last_updated DATE,
        checksum TEXT,
        FOREIGN KEY (system_id) REFERENCES ship_systems (system_id)
    )
    """
    )

    # Insert data into ship_systems
    ship_systems_data = [
        (1, "Life Support", "operational", "Deck 2, Section A", 45.7, "2186-04-10"),
        (2, "Main Engines", "warning", "Deck 5, Section C", 120.3, "2186-03-22"),
        (3, "Navigation", "error", "Deck 1, Bridge", 15.2, "2186-05-01"),
        (4, "Communications", "operational", "Deck 1, Section B", 10.5, "2186-04-15"),
        (5, "Weapons Systems", "offline", "Deck 3, Section D", 0.0, "2186-02-28"),
        (6, "Shield Generators", "error", "Deck 4, Section A", 35.8, "2186-04-30"),
        (7, "Sensor Array", "operational", "Deck 1, Section C", 22.4, "2186-05-02"),
        (8, "Artificial Gravity", "operational", "All Decks", 50.0, "2186-03-15"),
        (9, "Emergency Thrusters", "warning", "Deck 5, Section D", 18.7, "2186-04-05"),
        (10, "Quantum Stabilizers", "error", "Deck 7, Section A", 42.1, "2186-05-03"),
    ]

    cursor.executemany(
        """
    INSERT INTO ship_systems 
    (system_id, system_name, status, location, power_consumption, last_maintenance)
    VALUES (?, ?, ?, ?, ?, ?)
    """,
        ship_systems_data,
    )

    # Insert data into system_protocols
    system_protocols_data = [
        (
            101,
            "Life Support Maintenance",
            1,
            "/protocols/life/maintenance.dat",
            "2186-04-10",
            "a7f9e32d1c",
        ),
        (
            102,
            "Engine Ignition Sequence",
            2,
            "/protocols/engine/ignition.dat",
            "2186-03-20",
            "b8e7d21f3a",
        ),
        (
            103,
            "Standard Navigation Protocol",
            3,
            "/protocols/nav/standard.dat",
            "2186-04-20",
            "d4c3a52b1e",
        ),
        (
            104,
            "Communications Encryption",
            4,
            "/protocols/comm/encrypt.dat",
            "2186-04-15",
            "e2b1c30d9f",
        ),
        (
            105,
            "Weapons Targeting System",
            5,
            "/protocols/weapons/targeting.dat",
            "2186-02-25",
            "f0a9b87c6d",
        ),
        (
            106,
            "Shield Modulation Protocol",
            6,
            "/protocols/shield/modulate.dat",
            "2186-04-28",
            "a8b7c65d4e",
        ),
        (
            107,
            "Sensor Calibration Protocol",
            7,
            "/protocols/sensor/calibrate.dat",
            "2186-05-01",
            "b6c5d43e2f",
        ),
        (
            108,
            "Gravity Control Protocol",
            8,
            "/protocols/gravity/control.dat",
            "2186-03-10",
            "c4d3e21f0a",
        ),
        (
            109,
            "Emergency Course Correction",
            3,
            "/protocols/nav/course_correct.dat",
            "2186-05-02",
            "d2e1f09b8a",
        ),
    ]

    cursor.executemany(
        """
    INSERT INTO system_protocols
    (protocol_id, protocol_name, system_id, file_location, last_updated, checksum)
    VALUES (?, ?, ?, ?, ?, ?)
    """,
        system_protocols_data,
    )

    # Commit changes and close connection
    conn.commit()
    conn.close()

    print(f"Database created successfully at {db_path}")


if __name__ == "__main__":
    seed_db()
