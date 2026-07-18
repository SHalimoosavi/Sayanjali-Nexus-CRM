"""
Identity & RBAC: Users, Roles, Permissions, Departments, Teams.

Granular RBAC: a Role is a named bundle of Permissions (many-to-many),
a User has exactly one primary Role but can also get extra ad-hoc
Permissions directly (user_permissions) for edge cases like "give Aisha
temporary access to Finance reports without making her a Finance role".
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship

from app.db.base_class import Base, BaseModel, UUIDMixin, TimestampMixin

# --- Association tables ---

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", String(36), ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", String(36), ForeignKey("permissions.id"), primary_key=True),
)

user_permissions = Table(
    "user_permissions",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id"), primary_key=True),
    Column("permission_id", String(36), ForeignKey("permissions.id"), primary_key=True),
)

team_members = Table(
    "team_members",
    Base.metadata,
    Column("team_id", String(36), ForeignKey("teams.id"), primary_key=True),
    Column("user_id", String(36), ForeignKey("users.id"), primary_key=True),
)


class Department(BaseModel):
    __tablename__ = "departments"
    name = Column(String(120), nullable=False, unique=True)
    description = Column(String(500))

    employees = relationship("Employee", back_populates="department")


class Team(BaseModel):
    __tablename__ = "teams"
    name = Column(String(120), nullable=False)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True)

    members = relationship("User", secondary=team_members, back_populates="teams")


class Permission(BaseModel):
    __tablename__ = "permissions"
    code = Column(String(100), nullable=False, unique=True)  # e.g. "leads.create"
    module = Column(String(80), nullable=False)              # e.g. "leads"
    description = Column(String(255))


class Role(BaseModel):
    __tablename__ = "roles"
    name = Column(String(80), nullable=False, unique=True)  # Founder, Director, Manager, Sales...
    description = Column(String(255))
    is_system_role = Column(Boolean, default=False)  # prevents deletion of built-in roles

    permissions = relationship("Permission", secondary=role_permissions)
    users = relationship("User", back_populates="role", foreign_keys="User.role_id")


class User(BaseModel):
    __tablename__ = "users"
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    phone = Column(String(30))
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime)

    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False)
    role = relationship("Role", back_populates="users", foreign_keys=[role_id])

    extra_permissions = relationship("Permission", secondary=user_permissions)
    teams = relationship("Team", secondary=team_members, back_populates="members")

    employee = relationship("Employee", back_populates="user", uselist=False, foreign_keys="Employee.user_id")


class Employee(BaseModel):
    """HR-facing profile, separate from User (login/auth) so someone can
    exist as an employee record before they ever get system access."""
    __tablename__ = "employees"
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, unique=True)
    employee_code = Column(String(40), unique=True, nullable=False)
    designation = Column(String(120))
    department_id = Column(String(36), ForeignKey("departments.id"))
    date_joined = Column(DateTime)
    employment_status = Column(String(30), default="active")  # active, on_leave, exited

    user = relationship("User", back_populates="employee", foreign_keys=[user_id])
    department = relationship("Department", back_populates="employees")
