"""
Client-side entities: Company -> Client -> Contact, all vertical-aware.

One Company (legal entity) can have multiple Client records if they engage
SAYANJALI across multiple verticals (e.g. same company is both a
"Custom Software Development" client and a "Digital Marketing" client) —
modeled as a many-to-many via `client_verticals` so reporting per vertical
stays clean, while `Company` remains the single source of truth for the org.
"""
from sqlalchemy import Column, String, ForeignKey, Table, Text, Boolean
from sqlalchemy.orm import relationship

from app.db.base_class import Base, BaseModel

client_verticals = Table(
    "client_verticals",
    Base.metadata,
    Column("client_id", String(36), ForeignKey("clients.id"), primary_key=True),
    Column("vertical_id", String(36), ForeignKey("business_verticals.id"), primary_key=True),
)


class Company(BaseModel):
    __tablename__ = "companies"
    name = Column(String(200), nullable=False)
    website = Column(String(255))
    industry = Column(String(120))
    gst_number = Column(String(40))
    billing_address = Column(Text)
    notes = Column(Text)

    branches = relationship("CompanyBranch", back_populates="company")
    clients = relationship("Client", back_populates="company")


class CompanyBranch(BaseModel):
    __tablename__ = "company_branches"
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    branch_name = Column(String(150))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100), default="India")

    company = relationship("Company", back_populates="branches")


class Client(BaseModel):
    __tablename__ = "clients"
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=True)
    display_name = Column(String(200), nullable=False)
    client_code = Column(String(40), unique=True)
    status = Column(String(30), default="active")  # active, inactive, churned
    account_owner_id = Column(String(36), ForeignKey("users.id"))
    notes = Column(Text)

    company = relationship("Company", back_populates="clients")
    contacts = relationship("Contact", back_populates="client")
    verticals = relationship("BusinessVertical", secondary=client_verticals)
    projects = relationship("Project", back_populates="client")
    client_notes = relationship("ClientNote", back_populates="client")
    activities = relationship("ClientActivity", back_populates="client")


class Contact(BaseModel):
    __tablename__ = "contacts"
    client_id = Column(String(36), ForeignKey("clients.id"), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100))
    designation = Column(String(120))
    email = Column(String(255))
    phone = Column(String(30))
    whatsapp_number = Column(String(30))
    is_primary = Column(Boolean, default=False)
    notes = Column(Text)

    client = relationship("Client", back_populates="contacts")


class ClientNote(BaseModel):
    __tablename__ = "client_notes"
    client_id = Column(String(36), ForeignKey("clients.id"), nullable=False)
    note = Column(Text, nullable=False)

    client = relationship("Client", back_populates="client_notes")


class ClientActivity(BaseModel):
    """Timeline of everything that happened to a client: status changes,
    contacts added, conversion-from-lead, etc. -- mirrors LeadActivity."""
    __tablename__ = "client_activities"
    client_id = Column(String(36), ForeignKey("clients.id"), nullable=False)
    activity_type = Column(String(50), nullable=False)  # created, status_change, contact_added, note
    description = Column(Text)

    client = relationship("Client", back_populates="activities")
