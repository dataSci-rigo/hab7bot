from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.settings import AppSettings


def get_settings(db: Session) -> AppSettings:
    settings_row = db.scalar(select(AppSettings).limit(1))
    if settings_row is None:
        settings_row = AppSettings()
        db.add(settings_row)
        db.commit()
        db.refresh(settings_row)
    return settings_row


def update_settings(db: Session, week_start_day: str) -> AppSettings:
    settings_row = get_settings(db)
    settings_row.week_start_day = week_start_day
    db.commit()
    db.refresh(settings_row)
    return settings_row
