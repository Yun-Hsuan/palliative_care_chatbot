import uuid
from datetime import date
from typing import Optional, List

from sqlmodel import Field, SQLModel, Relationship

from .enums import PatientStatus
from .healthcare_member import Caregiver, Family

# Base Patient Model
class PatientBase(SQLModel):
    """Base patient model with common fields."""
    full_name: str = Field(max_length=100)
    birth_date: date
    gender: str = Field(max_length=10)
    national_id: Optional[str] = Field(default=None, max_length=20)
    phone: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=200)
    status: PatientStatus = Field(default=PatientStatus.ACTIVE)
    medical_history: Optional[str] = Field(default=None)
    allergies: Optional[str] = Field(default=None)
    current_medications: Optional[str] = Field(default=None)

class Patient(PatientBase, table=True):
    """Patient model for database storage."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    caregivers: List["PatientCaregiver"] = Relationship(back_populates="patient")
    family_members: List["PatientFamily"] = Relationship(back_populates="patient")

# Patient-Caregiver Relationship
class PatientCaregiver(SQLModel, table=True):
    """Relationship model between patients and caregivers."""
    __tablename__ = "patient_caregivers"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    patient_id: uuid.UUID = Field(foreign_key="patient.id")
    caregiver_id: uuid.UUID = Field(foreign_key="caregivers.id")
    start_date: date = Field(default_factory=date.today)
    end_date: Optional[date] = Field(default=None)
    is_primary: bool = Field(default=False)
    notes: Optional[str] = Field(default=None)
    
    patient: Patient = Relationship(back_populates="caregivers")
    caregiver: Caregiver = Relationship()

# Patient-Family Relationship
class PatientFamily(SQLModel, table=True):
    """Relationship model between patients and family members."""
    __tablename__ = "patient_family_members"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    patient_id: uuid.UUID = Field(foreign_key="patient.id")
    family_id: uuid.UUID = Field(foreign_key="family_members.id")
    is_primary_contact: bool = Field(default=False)
    notes: Optional[str] = Field(default=None)
    
    patient: Patient = Relationship(back_populates="family_members")
    family: Family = Relationship()

# API Models
class PatientCreate(PatientBase):
    """Model for creating a new patient."""
    pass

class PatientUpdate(SQLModel):
    """Model for updating patient information."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    status: Optional[PatientStatus] = None
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    current_medications: Optional[str] = None

class PatientCaregiverCreate(SQLModel):
    """Model for creating a patient-caregiver relationship."""
    caregiver_id: uuid.UUID
    is_primary: bool = False
    notes: Optional[str] = None

class PatientFamilyCreate(SQLModel):
    """Model for creating a patient-family relationship."""
    family_id: uuid.UUID
    is_primary_contact: bool = False
    notes: Optional[str] = None 