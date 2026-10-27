"""Weeks, fiscal periods (variant V9: Oct-Sep, FY named by end year) and US public holidays."""
import datetime as dt

import numpy as np
import pandas as pd

WINDOW_START = dt.date(2021, 10, 1)
WINDOW_END = dt.date(2026, 9, 30)
FORWARD_END = dt.date(2027, 3, 31)
AS_OF = dt.date(2026, 10, 1)


def fiscal_year(d) -> int:
    return d.year + 1 if d.month >= 10 else d.year


def fiscal_period(d) -> int:
    return (d.month - 10) % 12 + 1


def _nth_weekday(year, month, weekday, n):
    d = dt.date(year, month, 1)
    d += dt.timedelta(days=(weekday - d.weekday()) % 7)
    return d + dt.timedelta(weeks=n - 1)


def _last_weekday(year, month, weekday):
    d = dt.date(year, month + 1, 1) - dt.timedelta(days=1) if month < 12 else dt.date(year, 12, 31)
    return d - dt.timedelta(days=(d.weekday() - weekday) % 7)


def holidays(years) -> set:
    out = set()
    for y in years:
        out |= {dt.date(y, 1, 1), _last_weekday(y, 5, 0), dt.date(y, 7, 4), _nth_weekday(y, 9, 0, 1),
                _nth_weekday(y, 11, 3, 4), dt.date(y, 12, 25)}
    return out


HOLIDAYS = holidays(range(2021, 2028))


def workdays(start=WINDOW_START, end=FORWARD_END) -> pd.DataFrame:
    days = pd.date_range(start, end, freq="D")
    df = pd.DataFrame({"date": days.date})
    df["weekday"] = [d.weekday() for d in df["date"]]
    df = df[df["weekday"] < 5].copy()
    df["is_holiday"] = df["date"].isin(HOLIDAYS)
    return df.reset_index(drop=True)


def weeks() -> pd.DataFrame:
    """Monday-based weeks covering the window to the forward end; workday count inside the window per week."""
    wd = workdays()
    wd["week_start"] = [d - dt.timedelta(days=d.weekday()) for d in wd["date"]]
    g = wd.groupby("week_start").agg(workdays=("date", "size"), holidays=("is_holiday", "sum")).reset_index()
    g["week_idx"] = np.arange(len(g))
    g["fiscal_year"] = [fiscal_year(d) for d in g["week_start"]]
    g["month_start"] = [dt.date(d.year, d.month, 1) for d in g["week_start"]]
    g["work_hours"] = (g["workdays"] - g["holidays"]) * 8.0
    return g
