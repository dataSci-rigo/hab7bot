from pydantic import BaseModel

from app.ai.schemas import BreakdownTask, ProjectSuggestion


class BreakdownAcceptRequest(BaseModel):
    selected: list[BreakdownTask]


class SuggestionAcceptRequest(BaseModel):
    suggestion: ProjectSuggestion
