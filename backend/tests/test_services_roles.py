from sqlalchemy.orm import Session

from app.schemas.role import RoleCreate, RoleUpdate
from app.services import roles as roles_service


def test_create_and_get_role(db_session: Session) -> None:
    role = roles_service.create_role(db_session, RoleCreate(name="Parent"))
    fetched = roles_service.get_role(db_session, role.id)
    assert fetched is not None
    assert fetched.name == "Parent"
    assert fetched.is_active is True


def test_list_roles_active_only(db_session: Session) -> None:
    roles_service.create_role(db_session, RoleCreate(name="Active", is_active=True))
    roles_service.create_role(db_session, RoleCreate(name="Inactive", is_active=False))

    all_roles = roles_service.list_roles(db_session)
    active_roles = roles_service.list_roles(db_session, active_only=True)

    assert len(all_roles) == 2
    assert len(active_roles) == 1
    assert active_roles[0].name == "Active"


def test_update_role(db_session: Session) -> None:
    role = roles_service.create_role(db_session, RoleCreate(name="Old name"))
    updated = roles_service.update_role(db_session, role.id, RoleUpdate(name="New name"))
    assert updated is not None
    assert updated.name == "New name"


def test_update_missing_role_returns_none(db_session: Session) -> None:
    import uuid

    assert roles_service.update_role(db_session, uuid.uuid4(), RoleUpdate(name="x")) is None


def test_delete_role(db_session: Session) -> None:
    role = roles_service.create_role(db_session, RoleCreate(name="Temp"))
    assert roles_service.delete_role(db_session, role.id) is True
    assert roles_service.get_role(db_session, role.id) is None
