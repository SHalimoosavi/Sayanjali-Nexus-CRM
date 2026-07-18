"""
Reusable FastAPI dependencies: current-user resolution from JWT, and a
`require_permission` factory for granular RBAC checks on any endpoint.

Usage in a router:
    @router.post("/leads", dependencies=[Depends(require_permission("leads.create"))])
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.identity import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id, User.is_deleted.is_(False)).first()
    if not user or not user.is_active:
        raise credentials_exception
    return user


def require_permission(permission_code: str):
    def checker(current_user: User = Depends(get_current_user)) -> User:
        # Founder/Director-tier system roles bypass granular checks.
        if current_user.role and current_user.role.name in ("Founder", "Director"):
            return current_user

        role_codes = {p.code for p in current_user.role.permissions} if current_user.role else set()
        extra_codes = {p.code for p in current_user.extra_permissions}
        if permission_code not in role_codes | extra_codes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission_code}",
            )
        return current_user

    return checker
