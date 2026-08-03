from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.mission import MissionStatement


def get_mission(db: Session) -> MissionStatement:
    mission = db.scalar(select(MissionStatement).limit(1))
    if mission is None:
        mission = MissionStatement(content="")
        db.add(mission)
        db.commit()
        db.refresh(mission)
    return mission


def update_mission(db: Session, content: str) -> MissionStatement:
    mission = get_mission(db)
    mission.content = content
    db.commit()
    db.refresh(mission)
    return mission
