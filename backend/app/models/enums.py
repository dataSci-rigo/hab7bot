import enum


class Quadrant(enum.StrEnum):
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"


class TaskStatus(enum.StrEnum):
    inbox = "inbox"
    planned = "planned"
    in_progress = "in_progress"
    done = "done"
    dropped = "dropped"


class TaskOrigin(enum.StrEnum):
    user = "user"
    ai = "ai"
    telegram = "telegram"
    web = "web"
    google = "google"  # pulled in via Google Tasks/Calendar sync — see SPEC §5


class ProjectStatus(enum.StrEnum):
    idea = "idea"
    active = "active"
    paused = "paused"
    done = "done"
    abandoned = "abandoned"


class ProjectOrigin(enum.StrEnum):
    user = "user"
    ai = "ai"
