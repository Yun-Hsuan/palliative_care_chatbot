import uuid
from typing import Optional

from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from .enums import UserRole

# Base Healthcare Member Model
class HealthcareMemberBase(SQLModel):
    """Base model with common fields for all healthcare system members."""
    email: EmailStr = Field(unique=True, index=True)
    full_name: str | None
    is_active: bool = True
    is_superuser: bool = False
    role: UserRole

class HealthcareMember(HealthcareMemberBase, table=True):
    """Main healthcare member model for database storage."""
    __tablename__ = "healthcare_members"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str

# Caregiver Model
class CaregiverBase(SQLModel):
    """Base model for caregiver-specific information."""
    institution: str = Field(max_length=100)  # Institution or organization name
    position: str = Field(max_length=50)      # Job position
    license_number: str = Field(max_length=50) # Professional license number
    specialization: str = Field(max_length=100) # Area of specialization

class Caregiver(CaregiverBase, table=True):
    """Caregiver model for database storage."""
    __tablename__ = "caregivers"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    member_id: uuid.UUID = Field(foreign_key="healthcare_members.id")

# Family Model
class FamilyBase(SQLModel):
    """Base model for family member-specific information."""
    relationship: str = Field(max_length=50)  # Relationship to the patient

class Family(FamilyBase, table=True):
    """Family member model for database storage."""
    __tablename__ = "family_members"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    member_id: uuid.UUID = Field(foreign_key="healthcare_members.id")

# Medical Team Member Model
class MedicalTeamMemberBase(SQLModel):
    """Base model for medical team member-specific information."""
    department: str = Field(max_length=100)  # Medical department
    position: str = Field(max_length=50)     # Position in medical team
    specialty: str = Field(max_length=100)   # Medical specialty
    license_number: str = Field(max_length=50) # Medical license number

class MedicalTeamMember(MedicalTeamMemberBase, table=True):
    """Medical team member model for database storage."""
    __tablename__ = "medical_team_members"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    member_id: uuid.UUID = Field(foreign_key="healthcare_members.id")

# API Models for Create/Update Operations
class HealthcareMemberCreate(HealthcareMemberBase):
    """Model for creating a new healthcare member."""
    password: str = Field(min_length=8)

class HealthcareMemberUpdate(SQLModel):
    """Model for updating healthcare member information."""
    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = None

class CaregiverCreate(CaregiverBase):
    """Model for creating a new caregiver."""
    member: HealthcareMemberCreate

class FamilyCreate(FamilyBase):
    """Model for creating a new family member."""
    member: HealthcareMemberCreate

class MedicalTeamMemberCreate(MedicalTeamMemberBase):
    """Model for creating a new medical team member."""
    member: HealthcareMemberCreate 