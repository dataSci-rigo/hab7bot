import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate


def create_role(db: Session, data: RoleCreate) -> Role:
    role = Role(**data.model_dump())
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def get_role(db: Session, role_id: uuid.UUID) -> Role | None:
    return db.get(Role, role_id)


def list_roles(db: Session, active_only: bool = False) -> list[Role]:
    stmt = select(Role)
    if active_only:
        stmt = stmt.where(Role.is_active.is_(True))
    return list(db.scalars(stmt.order_by(Role.created_at)))


def update_role(db: Session, role_id: uuid.UUID, data: RoleUpdate) -> Role | None:
    role = get_role(db, role_id)
    if role is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(role, field, value)
    db.commit()
    db.refresh(role)
    return role


def delete_role(db: Session, role_id: uuid.UUID) -> bool:
    role = get_role(db, role_id)
    if role is None:
        return False
    db.delete(role)
    db.commit()
    return True
