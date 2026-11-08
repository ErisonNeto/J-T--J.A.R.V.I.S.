from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def today():
    return datetime.now(ZoneInfo("America/Sao_Paulo")).date()


def default_period(kind, day=None):
    day = day or today()
    if kind in {"avaria", "extravio", "pnr"}:
        monday = day - timedelta(days=day.weekday())
        return monday, monday + timedelta(days=6)
    ref = day - timedelta(days=2 if kind in {"1bd", "5cd", "csat"} else 1)
    return ref, ref


def comparisons(start, end):
    monday = end - timedelta(days=end.weekday())
    return {
        "same_weekdays": (start - timedelta(days=7), end - timedelta(days=7)),
        "previous_week": (monday - timedelta(days=7), monday - timedelta(days=1)),
    }
