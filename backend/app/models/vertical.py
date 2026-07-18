"""
Business Verticals — the single table that makes this a true multi-vertical
platform without needing per-vertical schema changes.

Every pipeline-bearing entity (Lead, Client, Deal, Project, ServiceRequest)
carries a `vertical_id` FK here. To onboard a brand-new business line
(say, tomorrow SAYANJALI enters "Solar Energy Installations"), an admin
inserts one row — no migration, no downtime, no code deploy.

`pipeline_stages` (JSON) lets each vertical define its own custom lead/deal
funnel (e.g. Real Estate: Enquiry -> Site Visit -> Booking -> Registration,
vs. SaaS: Trial -> Demo -> Proposal -> Won) while reusing the same
`leads` / `sales_opportunities` tables.
"""
from sqlalchemy import Column, String, Boolean, JSON, Integer

from app.db.base_class import BaseModel


class BusinessVertical(BaseModel):
    __tablename__ = "business_verticals"

    name = Column(String(120), nullable=False, unique=True)
    slug = Column(String(120), nullable=False, unique=True)
    description = Column(String(500))
    icon = Column(String(80))          # icon key for UI (lucide-react name)
    color = Column(String(20))         # hex, used for dashboard/pipeline theming
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)

    # Custom funnel per vertical, e.g.:
    # ["New", "Qualified", "Proposal Sent", "Negotiation", "Won", "Lost"]
    pipeline_stages = Column(JSON, default=list)

    # Vertical-specific custom field definitions, rendered dynamically
    # by the frontend's DynamicForm component. e.g.:
    # [{"key": "plot_size", "label": "Plot Size (sqft)", "type": "number"}]
    custom_fields_schema = Column(JSON, default=list)
