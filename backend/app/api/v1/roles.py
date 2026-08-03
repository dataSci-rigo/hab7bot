import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import require_session
from app.db import get_db
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate
from app.services import roles as roles_service

router = APIRouter(prefix="/roles", tags=["roles"], dependencies=[Depends(require_session)])


@router.get("", response_model=list[RoleRead])
def list_roles(active_only: bool = False, db: Session = Depends(get_db)) -> list[RoleRead]:
    return roles_service.list_roles(db, active_only=active_only)


@router.post("", response_model=RoleRead, status_code=201)
def create_role(data: RoleCreate, db: Session = Depends(get_db)) -> RoleRead:
    return roles_service.create_role(db, data)


@router.get("/{role_id}", response_model=RoleRead)
def get_role(role_id: uuid.UUID, db: Session = Depends(get_db)) -> RoleRead:
    role = roles_service.get_role(db, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.put("/{role_id}", response_model=RoleRead)
def update_role(role_id: uuid.UUID, data: RoleUpdate, db: Session = Depends(get_db)) -> RoleRead:
    role = roles_service.update_role(db, role_id, data)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.delete("/{role_id}", status_code=204)
def delete_role(role_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    if not roles_service.delete_role(db, role_id):
        raise HTTPException(status_code=404, detail="Role not found")
