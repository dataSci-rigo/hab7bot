from fastapi import APIRouter

from app.api.v1 import auth, goals, mission, projects, roles, settings, tasks, weeks

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(roles.router)
router.include_router(goals.router)
router.include_router(projects.router)
router.include_router(tasks.router)
router.include_router(weeks.router)
router.include_router(mission.router)
router.include_router(settings.router)
