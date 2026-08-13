from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.settings import AppSettings
from app.schemas.settings import AppSettingsUpdate


def get_settings(db: Session) -> AppSettings:
    settings_row = db.scalar(select(AppSettings).limit(1))
    if settings_row is None:
        settings_row = AppSettings()
        db.add(settings_row)
        db.commit()
        db.refresh(settings_row)
    return settings_row


def update_settings(db: Session, data: AppSettingsUpdate) -> AppSettings:
    settings_row = get_settings(db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(settings_row, field, value)
    db.commit()
    db.refresh(settings_row)
    return settings_row
