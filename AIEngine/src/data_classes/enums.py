from enum import Enum

class ConversationStage(Enum):
    INITIAL_HANDSHAKE = 1
    MOOD_ANALYSIS = 2
    UNDERSTANDING_ISSUE = 3
    EMPATHETIC_CONVERSATION = 4
    TOOL_SUGGESTION = 5
    PLAN_OF_ACTION = 6
    CLOSING = 7

class Mood(Enum):
    HAPPY = "happy"
    STRESSED = "stressed"
    ANXIOUS = "anxious"
    ANGRY = "angry"
    SAD = "sad"
    NEUTRAL = "neutral"
    TIRED = "tired"
    OVERWHELMED = "overwhelmed"

class Issue(Enum):
    WORK_STRESS = "work_stress"
    WORK_LIFE_BALANCE = "work_life_balance"
    COLLEAGUE_CONFLICT = "colleague_conflict"
    BURNOUT = "burnout"
    CAREER_UNCERTAINTY = "career_uncertainty"
    TIME_MANAGEMENT = "time_management"
    PERFECTIONISM = "perfectionism"
    IMPOSTER_SYNDROME = "imposter_syndrome"
    WORKPLACE_ANXIETY = "workplace_anxiety"
    OTHER = "other"