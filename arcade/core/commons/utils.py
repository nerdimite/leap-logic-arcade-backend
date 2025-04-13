from hashlib import sha256


def hash_team_name(team_name: str) -> str:
    """Hash a team name using SHA-256."""
    return sha256(team_name.encode()).hexdigest()


def is_hashed_team_name(team_name: str) -> bool:
    """Check if a team name is hashed."""
    return len(team_name) == 64
