from datetime import date, timedelta


def iso_week_string(d: date) -> str:
    iso = d.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def current_iso_week_plus(offset_weeks: int) -> str:
    return iso_week_string(date.today() + timedelta(weeks=offset_weeks))
