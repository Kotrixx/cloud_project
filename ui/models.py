from typing import Optional, List

from beanie import Document, Indexed, Link
from pydantic import Field, EmailStr
from datetime import datetime

from schemas import Preferences, ContactInfo, Location, PhotoEvidence, IncidentLocation, \
    AccessControlEmbedded


class Role(Document):
    description: str
    access_control: List[AccessControlEmbedded] = []

    class Settings:
        name = "roles"


class Resource(Document):
    resource_name: str  # Unique identifier (e.g., "users")
    description: str  # Description of what this resource represents

    class Settings:
        name = "resources"


class Permission(Document):
    permission_name: str  # Unique identifier for the permission (e.g., "create")
    description: str  # Description of the permission

    class Settings:
        name = "permissions"


class User(Document):
    first_name: str
    last_name: str
    email: EmailStr = Field(unique=True)
    password: str
    status: str = "active"
    date_created: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    class Settings:
        name = "users"


class ActivityLog(Document):
    user_id: str  # Foreign key to User
    action: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    location: Optional[Location]
    report_id: Optional[str]  # To reference a report if needed

    class Settings:
        name = "activity_logs"


class Incident(Document):
    user_id: str  # Reference to the User responsible for the incident
    incident_id: str  # Unique identifier for the incident
    description: str  # Details about the unsafe condition or incident
    location_area: str  # Location area of the incident
    observation_date: datetime  # Date when the incident was observed
    action_plan: Optional[str]  # Plan to resolve the incident
    resolution_deadline: Optional[datetime]  # Deadline for incident resolution
    status: str = "Pending"  # Status of the incident
    photo_evidence: List[PhotoEvidence] = []  # List of photos related to the incident
    locations: List[IncidentLocation] = []  # Locations related to the incident

    class Settings:
        name = "incidents"
