"""
Initial data seed: system roles, core permissions, the Founder user
(Syed Ali Hasan Moosavi), and the starting set of business verticals.

Run with:  python scripts/seed.py   (from backend/ with venv active)
Works on Windows/macOS/Linux without needing PYTHONPATH set manually --
the sys.path fix below mirrors the same pattern already used in
tests/conftest.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.base_class import Base
from app.db.session import engine, SessionLocal
from app.core.security import hash_password
from app.models.identity import Role, Permission, User
from app.models.vertical import BusinessVertical

VERTICALS = [
    "AI Solutions", "AI Consulting", "AI Automation", "Custom Software Development",
    "SaaS Products", "Web Development", "Mobile Applications", "Digital Marketing",
    "SEO Services", "Branding", "Business Consulting", "Cloud Kitchen", "Hotels",
    "Hospitality", "Real Estate", "Construction", "Education", "Training",
    "Online Courses", "Farming", "Agriculture", "Import & Export", "Frozen Foods",
    "Jewellery", "E-Commerce", "Corporate Transportation", "Dealership Management",
    "Government Projects", "Enterprise Solutions",
]

ROLES = ["Founder", "Director", "Manager", "Sales", "Marketing", "Developer",
          "Support", "Finance", "HR", "Operations", "Guest"]

MODULES = ["leads", "clients", "projects", "tasks", "invoices", "reports", "settings", "users",
           "opportunities", "documents"]
ACTIONS = ["create", "read", "update", "delete"]


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Permissions
        perms = {}
        for module in MODULES:
            for action in ACTIONS:
                code = f"{module}.{action}"
                perm = db.query(Permission).filter_by(code=code).first()
                if not perm:
                    perm = Permission(code=code, module=module, description=f"{action} {module}")
                    db.add(perm)
                perms[code] = perm
        db.commit()

        # Roles
        role_objs = {}
        for name in ROLES:
            role = db.query(Role).filter_by(name=name).first()
            if not role:
                role = Role(name=name, is_system_role=True, description=f"{name} role")
                db.add(role)
                db.commit()
                db.refresh(role)
            role_objs[name] = role

        # Founder & Director get everything; every other role gets a
        # deliberate, module-scoped slice reflecting how that role actually
        # works day to day (Section 5 / 11 of the SDD). Nothing is implicit --
        # a role with no entry here genuinely has zero access, by design.
        for name in ("Founder", "Director"):
            role_objs[name].permissions = list(perms.values())

        def grant(role_name: str, codes: list[str]) -> None:
            role_objs[role_name].permissions = [perms[c] for c in codes if c in perms]

        grant("Manager", [f"{m}.{a}" for m in ("leads", "clients", "projects", "tasks", "opportunities")
                           for a in ("create", "read", "update")] + ["reports.read", "users.read"])
        grant("Sales", [f"{m}.{a}" for m in ("leads", "clients", "opportunities") for a in ACTIONS]
              + ["projects.read", "tasks.read", "tasks.create"])
        grant("Marketing", ["leads.create", "leads.read", "leads.update", "reports.read", "clients.read"])
        grant("Developer", [f"tasks.{a}" for a in ACTIONS] + ["projects.read", "projects.update", "documents.read"])
        grant("Support", [f"tasks.{a}" for a in ACTIONS] + ["clients.read", "documents.read", "documents.create"])
        grant("Finance", [f"invoices.{a}" for a in ACTIONS] + ["reports.read", "clients.read"])
        grant("HR", ["users.read", "users.update", "settings.read"])
        grant("Operations", ["projects.read", "tasks.read", "reports.read", "documents.read"])
        # Guest: intentionally zero permissions -- true guest access must be
        # granted per-user via `extra_permissions`, never inherited by default.
        db.commit()

        # Founder user
        founder = db.query(User).filter_by(email="syed@sayanjalinexus.com").first()
        if not founder:
            founder = User(
                email="syed@sayanjalinexus.com",
                hashed_password=hash_password("ChangeMe123!"),
                full_name="Syed Ali Hasan Moosavi",
                role_id=role_objs["Founder"].id,
                is_active=True,
            )
            db.add(founder)
            db.commit()
            print("Created Founder login -> syed@sayanjalinexus.com / ChangeMe123!  (CHANGE THIS PASSWORD)")

        # Verticals
        for i, name in enumerate(VERTICALS):
            slug = name.lower().replace(" & ", "-").replace(" ", "-")
            existing = db.query(BusinessVertical).filter_by(slug=slug).first()
            if not existing:
                db.add(BusinessVertical(
                    name=name, slug=slug, display_order=i,
                    pipeline_stages=["New", "Contacted", "Qualified", "Proposal Sent",
                                       "Negotiation", "Won", "Lost"],
                ))
        db.commit()
        print(f"Seeded {len(VERTICALS)} business verticals, {len(ROLES)} roles, {len(perms)} permissions.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
