from enum import Enum


class ChallengeState(Enum):
    LOCKED = "locked"  # Challenge is locked and not available
    SUBMISSION = "submission"  # Teams can submit entries
    VOTING = "voting"  # Teams can vote on entries
    SCORING = "scoring"  # Scores are being calculated
    COMPLETE = "complete"  # Challenge is completed
