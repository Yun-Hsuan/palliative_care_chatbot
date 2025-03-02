from enum import IntEnum

class UserRole(IntEnum):
    ADMIN = 1
    CAREGIVER = 2
    FAMILY = 3
    MEDICAL_TEAM = 4

class PatientStatus(IntEnum):
    ACTIVE = 1          # Currently under care
    HOSPITALIZED = 2    # Admitted to hospital
    DISCHARGED = 3      # Discharged from care
    DECEASED = 4        # Deceased

class ConversationType(IntEnum):
    GENERAL = 1         # General conversation
    SYMPTOM_COLLECTION = 2  # Symptom collection session

class ConversationStatus(IntEnum):
    IN_PROGRESS = 1     # Conversation ongoing
    COMPLETED = 2       # Conversation completed
    INTERRUPTED = 3     # Conversation interrupted

class MessageType(IntEnum):
    USER_TEXT = 1       # User message
    SYSTEM_MESSAGE = 2  # System message
    AI_RESPONSE = 3     # AI response

class DiagnosisStatus(IntEnum):
    PENDING = 1         # Waiting for review
    IN_REVIEW = 2       # Under medical team review
    COMPLETED = 3       # Review completed
    ARCHIVED = 4        # Archived

class SymptomSeverity(IntEnum):
    NONE = 1           # No symptoms
    MILD = 2           # Mild symptoms
    MODERATE = 3       # Moderate symptoms
    SEVERE = 4         # Severe symptoms
    CRITICAL = 5       # Critical symptoms 