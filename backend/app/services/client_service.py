"""
Client service layer.

Owns the one piece of real business logic outside plain CRUD: converting a
qualified Lead into a Client (Section 5 of the SDD — the Lead record is
never deleted, only marked converted, preserving its activity history).

Also logs a ClientActivity row on creation, status changes, and contact
additions, and exposes ClientNote CRUD -- the same timeline/notes pattern
already proven on Leads.
"""
import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.client import Client, Contact, ClientNote, ClientActivity
from app.models.vertical import BusinessVertical
from app.models.lead import Lead
from app.repositories.base import BaseRepository


class ClientService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BaseRepository(Client, db)

    # --- CRUD ---

    def create_client(self, data: dict, created_by: str) -> Client:
        vertical_ids = data.pop("vertical_ids", [])
        if not data.get("client_code"):
            data["client_code"] = f"CLI-{uuid.uuid4().hex[:8].upper()}"
        data["created_by"] = created_by
        client = self.repo.create(data)
        self._set_verticals(client, vertical_ids)
        self._log_activity(client.id, "created", f"Client created: {client.display_name}")
        return client

    def list_clients(self, page: int, page_size: int, status_filter: Optional[str] = None,
                      account_owner_id: Optional[str] = None):
        skip = (page - 1) * page_size
        items = self.repo.list(skip=skip, limit=page_size, status=status_filter, account_owner_id=account_owner_id)
        total = self.repo.count(status=status_filter, account_owner_id=account_owner_id)
        return items, total

    def get_client(self, client_id: str) -> Client:
        client = self.repo.get(client_id)
        if not client:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Client not found")
        return client

    def update_client(self, client_id: str, updates: dict, updated_by: str) -> Client:
        vertical_ids = updates.pop("vertical_ids", None)
        client = self.get_client(client_id)
        old_status = client.status
        updates["updated_by"] = updated_by
        client = self.repo.update(client, updates)
        if vertical_ids is not None:
            self._set_verticals(client, vertical_ids)
        if updates.get("status") and updates["status"] != old_status:
            self._log_activity(client.id, "status_change", f"Status changed: {old_status} -> {client.status}")
        return client

    def delete_client(self, client_id: str) -> None:
        client = self.get_client(client_id)
        self.repo.soft_delete(client)

    # --- Contacts ---

    def add_contact(self, client_id: str, data: dict, created_by: str) -> Contact:
        self.get_client(client_id)  # 404 if missing
        data["client_id"] = client_id
        data["created_by"] = created_by
        contact = Contact(**data)
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        self._log_activity(client_id, "contact_added", f"Contact added: {contact.first_name} {contact.last_name or ''}".strip())
        return contact

    def update_contact(self, client_id: str, contact_id: str, updates: dict, updated_by: str) -> Contact:
        contact = (
            self.db.query(Contact)
            .filter(Contact.id == contact_id, Contact.client_id == client_id, Contact.is_deleted.is_(False))
            .first()
        )
        if not contact:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Contact not found")
        for field, value in updates.items():
            if value is not None:
                setattr(contact, field, value)
        contact.updated_by = updated_by
        self.db.commit()
        self.db.refresh(contact)
        return contact

    # --- Notes & timeline (mirrors LeadService) ---

    def list_notes(self, client_id: str) -> list[ClientNote]:
        self.get_client(client_id)
        return (
            self.db.query(ClientNote)
            .filter(ClientNote.client_id == client_id, ClientNote.is_deleted.is_(False))
            .order_by(ClientNote.created_at.desc())
            .all()
        )

    def add_note(self, client_id: str, note: str, created_by: str) -> ClientNote:
        self.get_client(client_id)
        note_obj = ClientNote(client_id=client_id, note=note, created_by=created_by)
        self.db.add(note_obj)
        self.db.commit()
        self.db.refresh(note_obj)
        return note_obj

    def list_timeline(self, client_id: str) -> list[ClientActivity]:
        self.get_client(client_id)
        return (
            self.db.query(ClientActivity)
            .filter(ClientActivity.client_id == client_id)
            .order_by(ClientActivity.created_at.desc())
            .all()
        )

    # --- Lead -> Client conversion ---

    def convert_lead(self, lead_id: str, created_by: str) -> Client:
        lead = self.db.query(Lead).filter(Lead.id == lead_id, Lead.is_deleted.is_(False)).first()
        if not lead:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
        if lead.is_converted:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Lead has already been converted")

        client = self.create_client(
            {
                "display_name": lead.company_name or lead.full_name,
                "account_owner_id": lead.owner_id,
                "notes": f"Converted from lead '{lead.full_name}'.",
                "vertical_ids": [lead.vertical_id],
            },
            created_by=created_by,
        )
        self._log_activity(client.id, "converted_from_lead", f"Converted from lead '{lead.full_name}'")

        # Carry the lead's primary contact across so the relationship isn't lost.
        self.add_contact(
            client.id,
            {
                "first_name": lead.full_name.split(" ")[0],
                "last_name": " ".join(lead.full_name.split(" ")[1:]) or None,
                "email": lead.email,
                "phone": lead.phone,
                "whatsapp_number": lead.whatsapp_number,
                "is_primary": True,
            },
            created_by=created_by,
        )

        lead.is_converted = True
        lead.converted_client_id = client.id
        lead.updated_by = created_by
        self.db.commit()

        from app.models.lead import LeadActivity
        self.db.add(LeadActivity(
            lead_id=lead.id, activity_type="converted",
            description=f"Converted to client '{client.display_name}'",
        ))
        self.db.commit()

        return client

    # --- internal ---

    def _set_verticals(self, client: Client, vertical_ids: list[str]) -> None:
        if not vertical_ids:
            return
        verticals = self.db.query(BusinessVertical).filter(BusinessVertical.id.in_(vertical_ids)).all()
        client.verticals = verticals
        self.db.commit()
        self.db.refresh(client)

    def _log_activity(self, client_id: str, activity_type: str, description: str) -> None:
        self.db.add(ClientActivity(client_id=client_id, activity_type=activity_type, description=description))
        self.db.commit()
