# Data Model Design Document

## Enums and Constants

```python
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
```

## User Related Models

### 1. Base User Model (User) - Existing
```python
class User(UserBase, table=True):
    id: uuid.UUID
    email: EmailStr
    hashed_password: str
    is_active: bool
    is_superuser: bool
    full_name: str | None
    role: UserRole  # Changed from str to UserRole enum
```

### 2. Caregiver Model
```python
class Caregiver(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    institution: str  # Institution or organization name
    position: str    # Job position
    license_number: str  # Professional license number
    specialization: str  # Area of specialization
```

### 3. Family Model
```python
class Family(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    relationship: str  # Relationship to the patient
```

### 4. Medical Team Member Model
```python
class MedicalTeamMember(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    department: str  # Medical department
    position: str    # Position in medical team
    specialty: str   # Medical specialty
    license_number: str  # Medical license number
```

## Patient Related Models

### 1. Patient Model
```python
class Patient(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    medical_record_number: str = Field(unique=True, index=True)
    full_name: str
    birth_date: date
    gender: str
    primary_diagnosis: str
    admission_date: datetime
    status: PatientStatus  # Changed from str to PatientStatus enum
    primary_caregiver_id: uuid.UUID = Field(foreign_key="caregiver.id")
    family_contact_id: uuid.UUID = Field(foreign_key="family.id")
```

### 2. Symptom Record Model
```python
class SymptomRecord(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    patient_id: uuid.UUID = Field(foreign_key="patient.id")
    conversation_id: uuid.UUID = Field(foreign_key="conversation.id")
    recorded_by_id: uuid.UUID = Field(foreign_key="user.id")
    recorded_at: datetime
    assessment_datetime: datetime
    note: str | None
    collection_order: int  # 1-4 for tracking order in conversation
    collection_complete: bool = False
```

### 3. Symptom Detail Model
```python
class SymptomDetail(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    symptom_record_id: uuid.UUID = Field(foreign_key="symptomrecord.id")
    category: str  # e.g., "respiratory", "digestive", "pain"
    primary_symptom: str  # e.g., "cough", "nausea", "headache"
    severity: SymptomSeverity  # Changed from int to SymptomSeverity enum
    duration: str  # e.g., "3 days", "1 week"
    frequency: str  # e.g., "continuous", "intermittent"
    characteristics: dict  # Detailed characteristics in JSON format
    related_symptoms: list[str]
    impact_on_daily_life: int  # 1-5 scale
```

### 4. Symptom Characteristic Model
```python
class SymptomCharacteristic(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    symptom_category: str  # Symptom category
    characteristic_key: str  # Characteristic key (e.g., color, consistency, location)
    name: str  # Display name of the characteristic
    type: str  # Data type (text, number, select, multiple)
    options: list[str] | None  # Options for select and multiple types
    required: bool  # Whether this characteristic is required
    follow_up_questions: list[str] | None  # Follow-up questions to ask
```

### 5. Related Symptom Rule Model
```python
class RelatedSymptomRule(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    primary_symptom: str  # Primary symptom that triggers the rule
    related_symptoms: list[str]  # List of potentially related symptoms
    condition: dict  # Trigger conditions in JSON format
    priority: int  # Priority for asking follow-up questions
```

### 6. Conversation Model
```python
class Conversation(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    patient_id: uuid.UUID = Field(foreign_key="patient.id", nullable=False)
    initiator_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    start_time: datetime = Field(nullable=False)
    end_time: datetime | None = Field(default=None)
    status: ConversationStatus = Field(nullable=False)
    conversation_type: ConversationType = Field(nullable=False)
    symptoms_collected_count: int = Field(default=0, nullable=False)
    target_symptoms_count: int = Field(default=4, nullable=False)
    current_symptom_focus: str | None = Field(default=None)
    collection_complete: bool = Field(default=False, nullable=False)

    # Relationships
    patient: "Patient" = Relationship(back_populates="conversations")
    initiator: "User" = Relationship(back_populates="initiated_conversations")
    messages: list["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    symptom_records: list["SymptomRecord"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
```

### 7. Message Model
```python
class Message(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(foreign_key="conversation.id", nullable=False)
    sender_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    content: str = Field(nullable=False)
    timestamp: datetime = Field(nullable=False)
    message_type: MessageType = Field(nullable=False)

    # Relationships
    conversation: Conversation = Relationship(back_populates="messages")
    sender: "User" = Relationship(back_populates="messages")
```

### 8. Diagnosis Model
```python
class Diagnosis(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    patient_id: uuid.UUID = Field(foreign_key="patient.id", nullable=False)
    created_by_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(nullable=False)
    symptoms_summary: str = Field(nullable=False)
    ai_suggestion: str = Field(nullable=False)
    medical_team_notes: str | None = Field(default=None)
    priority_level: int = Field(ge=1, le=5, nullable=False)  # 1-5 scale
    status: DiagnosisStatus = Field(nullable=False)

    # Relationships
    patient: "Patient" = Relationship(back_populates="diagnoses")
    created_by: "User" = Relationship(back_populates="created_diagnoses")
```

### API Models for Conversation Related Operations

```python
class ConversationCreate(SQLModel):
    patient_id: uuid.UUID
    conversation_type: ConversationType
    target_symptoms_count: int = Field(default=4, ge=1)

class MessageCreate(SQLModel):
    conversation_id: uuid.UUID
    content: str = Field(min_length=1)
    message_type: MessageType

class DiagnosisCreate(SQLModel):
    patient_id: uuid.UUID
    symptoms_summary: str = Field(min_length=1)
    ai_suggestion: str = Field(min_length=1)
    medical_team_notes: str | None = None
    priority_level: int = Field(ge=1, le=5)
```

### Schema Changes and Constraints

The following important constraints and relationships have been added to ensure data integrity:

1. **Nullable Constraints**:
   - All critical fields are marked as `nullable=False`
   - Optional fields like `end_time`, `current_symptom_focus`, and `medical_team_notes` allow NULL values

2. **Field Validations**:
   - String content fields have `min_length=1` validation
   - Priority levels are constrained between 1 and 5 (`ge=1, le=5`)
   - Target symptoms count must be at least 1 (`ge=1`)

3. **Relationship Configurations**:
   - Added cascade delete for messages and symptom records (`cascade="all, delete-orphan"`)
   - Proper back-population of relationships for all models

4. **Default Values**:
   - `symptoms_collected_count` defaults to 0
   - `target_symptoms_count` defaults to 4
   - `collection_complete` defaults to False

These changes ensure:
- Data integrity through proper constraints
- Consistent relationship handling
- Automatic cleanup of related records
- Valid input data through field validation

## Example JSON Response Format

```json
{
    "conversation_id": "uuid-1",
    "status": 1,  // ConversationStatus.IN_PROGRESS
    "symptoms_collected_count": 2,
    "target_symptoms_count": 4,
    "current_symptom_focus": "breathing_difficulty",
    "collected_symptoms": [
        {
            "order": 1,
            "symptom": "sputum",
            "complete": true
        },
        {
            "order": 2,
            "symptom": "breathing_difficulty",
            "complete": false
        }
    ]
}
```

## Implementation Plan

### 0. Refactoring Strategy

To safely implement our new data models while preserving existing authentication functionality, we'll adopt a gradual refactoring approach:

#### Current Structure
```
backend/app/
└── models.py  # Contains existing user authentication models
```

#### Target Structure
```
backend/app/models/
├── __init__.py      # Export all models
├── auth/            # Authentication related models
│   ├── __init__.py
│   └── user.py      # Moved from existing models.py
├── enums.py         # New enum types
├── patient.py       # Patient related models
├── symptom.py       # Symptom related models
└── conversation.py  # Conversation related models
```

#### Refactoring Steps

1. **Create New Directory Structure**
   - Create `models/` directory and subdirectories
   - Set up `__init__.py` files for proper module imports

2. **Move Authentication Models**
   - Move existing user models to `models/auth/user.py`
   - Maintain backward compatibility through imports

3. **Setup Import Redirections**
   Example `models/__init__.py`:
   ```python
   from .auth.user import User, UserBase, UserCreate
   from .enums import UserRole, PatientStatus
   from .patient import Patient
   from .symptom import SymptomRecord
   from .conversation import Conversation
   
   # For backward compatibility
   __all__ = [
       'User', 'UserBase', 'UserCreate',  # Existing models
       'UserRole', 'PatientStatus',       # New enums
       'Patient', 'SymptomRecord', 'Conversation'  # New models
   ]
   ```

4. **Bridge Transition**
   Update existing `models.py`:
   ```python
   # models.py
   from .models.auth.user import *  # Import all user related models
   ```

#### Benefits
- Maintains existing authentication system
- Ensures backward compatibility
- Allows gradual migration
- Achieves modular structure

### 1. Project Structure Setup
```
backend/app/
├── models/
│   ├── __init__.py
│   ├── enums.py        # Step 1: Implement enums
│   ├── user.py         # Step 2: User-related models
│   ├── patient.py      # Step 3: Patient model
│   ├── symptom.py      # Step 4: Symptom-related models
│   └── conversation.py # Step 5: Conversation and message models
```

### 2. Implementation Steps

#### Phase 1: Basic Models and Database Setup
1. **Create Enum Classes** (enums.py)
   - [ ] UserRole
   - [ ] PatientStatus
   - [ ] ConversationType
   - [ ] ConversationStatus
   - [ ] MessageType
   - [ ] DiagnosisStatus
   - [ ] SymptomSeverity

2. **Implement User-Related Models** (user.py)
   - [ ] Base User Model
   - [ ] Caregiver Model
   - [ ] Family Model
   - [ ] Medical Team Member Model

3. **Implement Patient Model** (patient.py)
   - [ ] Patient Base Model
     - Basic Information
       - full_name (str, max_length=100)
       - birth_date (date)
       - gender (str, max_length=10)
       - national_id (Optional[str], max_length=20)
       - phone (Optional[str], max_length=20)
       - address (Optional[str], max_length=200)
     - Medical Information
       - status (PatientStatus enum)
       - medical_history (Optional[str])
       - allergies (Optional[str])
       - current_medications (Optional[str])

   - [ ] Patient-Caregiver Relationship
     - Relationship Fields
       - patient_id (UUID, foreign key)
       - caregiver_id (UUID, foreign key)
       - start_date (date, defaults to today)
       - end_date (Optional[date])
       - is_primary (bool, defaults to False)
       - notes (Optional[str])

   - [ ] Patient-Family Relationship
     - Relationship Fields
       - patient_id (UUID, foreign key)
       - family_id (UUID, foreign key)
       - is_primary_contact (bool, defaults to False)
       - notes (Optional[str])

   - [ ] API Models
     - PatientCreate (extends PatientBase)
     - PatientUpdate (optional fields for updates)
     - PatientCaregiverCreate (for relationship creation)
     - PatientFamilyCreate (for relationship creation)

4. **Implement Symptom Models** (symptom.py)
   - [ ] Symptom Record Model
     - Base Fields
       - id: UUID (primary key)
       - patient_id: UUID (foreign key to patient)
       - conversation_id: UUID (foreign key to conversation)
       - recorded_by_id: UUID (foreign key to user)
       - recorded_at: datetime (auto-set to UTC now)
       - assessment_datetime: datetime
       - note: Optional[str]
       - collection_order: int (1-4 for tracking order)
       - collection_complete: bool (default False)
     - Relationships
       - patient: Patient (back_populates="symptom_records")
       - recorded_by: User
       - conversation: Conversation (back_populates="symptom_records")
       - details: List[SymptomDetail] (back_populates="symptom_record")

   - [ ] Symptom Detail Model
     - Base Fields
       - id: UUID (primary key)
       - symptom_record_id: UUID (foreign key to symptom record)
       - category: str (max_length=50)
       - primary_symptom: str (max_length=100)
       - severity: SymptomSeverity (enum)
       - duration: str (max_length=50)
       - frequency: str (max_length=50)
       - characteristics: Dict (JSON format)
       - related_symptoms: List[str]
       - impact_on_daily_life: int (1-5 scale)
     - Relationships
       - symptom_record: SymptomRecord (back_populates="details")

   - [ ] Symptom Characteristic Model
     - Base Fields
       - id: UUID (primary key)
       - symptom_category: str (max_length=50)
       - characteristic_key: str (max_length=50)
       - name: str (max_length=100)
       - type: str (max_length=20)
       - options: Optional[List[str]]
       - required: bool (default False)
       - follow_up_questions: Optional[List[str]]

   - [ ] Related Symptom Rule Model
     - Base Fields
       - id: UUID (primary key)
       - primary_symptom: str (max_length=100)
       - related_symptoms: List[str]
       - condition: Dict (JSON format)
       - priority: int (1-5 scale)

   - [ ] API Models
     - SymptomRecordCreate
       - patient_id: UUID
       - conversation_id: UUID
       - assessment_datetime: datetime
       - note: Optional[str]
       - collection_order: int
     - SymptomDetailCreate
       - symptom_record_id: UUID
       - category: str
       - primary_symptom: str
       - severity: SymptomSeverity
       - duration: str
       - frequency: str
       - characteristics: Dict
       - related_symptoms: List[str]
       - impact_on_daily_life: int
     - SymptomCharacteristicCreate
       - symptom_category: str
       - characteristic_key: str
       - name: str
       - type: str
       - options: Optional[List[str]]
       - required: bool
       - follow_up_questions: Optional[List[str]]
     - RelatedSymptomRuleCreate
       - primary_symptom: str
       - related_symptoms: List[str]
       - condition: Dict
       - priority: int

5. **Implement Conversation Models** (conversation.py)
   - [ ] Conversation Model
   - [ ] Message Model
   - [ ] Diagnosis Model

#### Phase 2: Database Migration
1. **Setup Database Configuration**
   - [ ] Configure database connection
   - [ ] Setup SQLAlchemy engine
   - [ ] Configure Alembic

2. **Create Migration Scripts**
   - [ ] Initial database schema
   - [ ] Create indexes
   - [ ] Add constraints

#### Phase 3: API Development
1. **Authentication and Authorization**
   - [ ] User registration
   - [ ] User login
   - [ ] Role-based access control

2. **Patient Management**
   - [ ] CRUD operations for patients
   - [ ] Patient-caregiver association
   - [ ] Patient-family association

3. **Symptom Recording**
   - [ ] Symptom creation and update
   - [ ] Symptom characteristic management
   - [ ] Related symptom rules

4. **Conversation Management**
   - [ ] Conversation flow control
   - [ ] Message handling
   - [ ] Diagnosis generation

### Development Progress Tracking

#### Current Status
- [ ] Project structure setup
- [ ] Basic models implementation
- [ ] Database migration
- [ ] API development

#### Next Steps
1. Create project directory structure
2. Implement enums.py
3. Setup database configuration

#### Notes
- Follow Python best practices and PEP 8 style guide
- Implement comprehensive unit tests for each model
- Document all API endpoints
- Maintain consistent error handling 