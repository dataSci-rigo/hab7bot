from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.daily_log import DailyLog


def get_or_create_log(db: Session, log_date: date) -> DailyLog:
    log = db.scalar(select(DailyLog).where(DailyLog.log_date == log_date))
    if log is None:
        log = DailyLog(log_date=log_date)
        db.add(log)
        db.commit()
        db.refresh(log)
    return log


def mark_morning_brief_sent(db: Session, log: DailyLog) -> DailyLog:
    log.morning_brief_sent = True
    db.commit()
    db.refresh(log)
    return log


def mark_evening_checkin_sent(db: Session, log: DailyLog) -> DailyLog:
    log.evening_checkin_sent = True
    db.commit()
    db.refresh(log)
    return log


def set_note(db: Session, log_date: date, note: str) -> DailyLog:
    log = get_or_create_log(db, log_date)
    log.note = note
    db.commit()
    db.refresh(log)
    return log
