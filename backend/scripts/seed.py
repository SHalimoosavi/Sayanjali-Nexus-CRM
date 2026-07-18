"""
Initial data seed: system roles, core permissions, the Founder user
(Syed Ali Hasan Moosavi), and the starting set of business verticals.

Run with:  python scripts_seed.py   (from backend/ with venv active)
"""
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

MODULES = ["leads", "clients", "projects", "tasks", "invoices", "reports", "settings", "users"]
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

        # Founder & Director get everything; Sales gets leads/clients/projects
        for name in ("Founder", "Director"):
            role_objs[name].permissions = list(perms.values())
        role_objs["Sales"].permissions = [p for c, p in perms.items()
                                            if c.startswith(("leads.", "clients.", "projects.read"))]
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
