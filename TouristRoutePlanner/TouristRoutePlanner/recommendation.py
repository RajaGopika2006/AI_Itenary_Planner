"""Preference-based tourist-place recommendations."""
from __future__ import annotations
import re
import pandas as pd


def parse_visit_duration(duration_text) -> int:
    """Convert a visit-duration label such as '1-2 hours' to minutes."""
    text = str(duration_text).lower().strip()
    if "full day" in text:
        return 480
    numbers = re.findall(r"\d+(?:\.\d+)?", text)
    if not numbers:
        return 120
    values = [float(value) for value in numbers]
    if "minute" in text or "min" in text:
        value = sum(values[:2]) / min(len(values), 2) if len(values) > 1 else values[0]
        return max(1, int(value))
    value = sum(values[:2]) / min(len(values), 2) if len(values) > 1 else values[0]
    return max(1, int(value * 60))


def calculate_recommendation_score(row, interests, budget, available_time):
    category = str(row.get("category", ""))
    interest_score = 1.0 if not interests or category in interests else 0.0
    rating_score = max(0.0, min(float(row.get("rating", 0)) / 5.0, 1.0))
    fee = float(row.get("entry_fee", 0) or 0)
    budget_score = 1.0 if fee <= budget else (0.5 if fee <= budget * 1.5 else 0.0)
    visit_minutes = parse_visit_duration(row.get("visit_duration", "2 hours"))
    available_minutes = max(1, float(available_time) * 60)
    time_score = 1.0 if visit_minutes <= available_minutes else (0.5 if visit_minutes <= available_minutes * 1.5 else 0.0)
    return round((0.40 * interest_score + 0.20 * rating_score + 0.20 * budget_score + 0.20 * time_score) * 100, 2)


def recommend_places(csv_file, start_area, interests, budget, available_time, max_places, candidate_pool_size=None):
    df = pd.read_csv(csv_file)
    if start_area and start_area != "All Areas":
        df = df[df["area"].astype(str) == start_area].copy()
    else:
        df = df.copy()
    if df.empty:
        df["recommendation_score"] = pd.Series(dtype=float)
        return df
    df["recommendation_score"] = df.apply(
        lambda row: calculate_recommendation_score(row, interests or [], budget, available_time), axis=1
    )
    df = df.sort_values(["recommendation_score", "rating"], ascending=[False, False])
    limit = candidate_pool_size if candidate_pool_size is not None else max_places
    return df.head(max(1, int(limit))).reset_index(drop=True)
