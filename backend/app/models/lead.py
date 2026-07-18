"""
Lead-to-deal pipeline. One `leads` table serves every vertical; the funnel
stage a lead is in is validated against that vertical's
`BusinessVertical.pipeline_stages` at the service layer (not the DB layer,
to keep the schema stable as verticals evolve their funnels).
"""
from sqlalchemy import Column, String, ForeignKey, Text, Numeric, Integer, DateTime, Boolean
from sqlalchemy.orm import relationship

from app.db.base_class import BaseModel


class LeadSource(BaseModel):
    __tablename__ = "lead_sources"
    name = Column(String(100), nullable=False, unique=True)  # Website, Referral, WhatsApp, Cold Call...
    is_active = Column(Boolean, default=True)


class Lead(BaseModel):
    __tablename__ = "leads"
    vertical_id = Column(String(36), ForeignKey("business_verticals.id"), nullable=False)
    source_id = Column(String(36), ForeignKey("lead_sources.id"))
    owner_id = Column(String(36), ForeignKey("users.id"))  # lead owner / assigned sales rep

    full_name = Column(String(200), nullable=False)
    company_name = Column(String(200))
    email = Column(String(255))
    phone = Column(String(30))
    whatsapp_number = Column(String(30))

    stage = Column(String(80), nullable=False, default="New")  # validated against vertical.pipeline_stages
    priority = Column(String(20), default="medium")            # low, medium, high, urgent
    score = Column(Integer, default=0)                         # lead scoring, AI-assisted later

    expected_value = Column(Numeric(14, 2))
    expected_close_date = Column(DateTime)

    converted_client_id = Column(String(36), ForeignKey("clients.id"), nullable=True)
    is_converted = Column(Boolean, default=False)

    custom_fields = Column(Text)  # JSON blob matching vertical.custom_fields_schema

    notes = relationship("LeadNote", back_populates="lead")
    activities = relationship("LeadActivity", back_populates="lead")


class LeadNote(BaseModel):
    __tablename__ = "lead_notes"
    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=False)
    note = Column(Text, nullable=False)

    lead = relationship("Lead", back_populates="notes")


class LeadActivity(BaseModel):
    """Timeline of everything that happened to a lead: stage changes,
    calls, follow-ups, emails — feeds the Activity Timeline module."""
    __tablename__ = "lead_activities"
    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=False)
    activity_type = Column(String(50), nullable=False)  # stage_change, call, email, followup, note
    description = Column(Text)
    follow_up_date = Column(DateTime, nullable=True)

    lead = relationship("Lead", back_populates="activities")


class SalesOpportunity(BaseModel):
    """A qualified Lead becomes an Opportunity/Deal once serious commercial
    discussion starts. Kept separate from Lead so top-of-funnel noise
    doesn't pollute deal-value reporting."""
    __tablename__ = "sales_opportunities"
    vertical_id = Column(String(36), ForeignKey("business_verticals.id"), nullable=False)
    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=True)
    client_id = Column(String(36), ForeignKey("clients.id"), nullable=True)
    owner_id = Column(String(36), ForeignKey("users.id"))

    title = Column(String(200), nullable=False)
    stage = Column(String(80), nullable=False, default="Qualification")
    value = Column(Numeric(14, 2))
    probability_percent = Column(Integer, default=10)
    expected_close_date = Column(DateTime)
    is_won = Column(Boolean, nullable=True)  # None = open, True = won, False = lost
    lost_reason = Column(String(255))
