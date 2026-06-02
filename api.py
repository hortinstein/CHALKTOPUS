import json
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Chalktopus Climbing API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

GRADES = ["vb", "v0", "v1", "v2", "v3", "v4", "v5", "v6"]

SCORING_METHODS = {
    "original_exponential": {"vb": 0.5, "v0": 1, "v1": 2, "v2": 4, "v3": 8, "v4": 12},
    "extended_exponential": {"vb": 0.5, "v0": 1, "v1": 2, "v2": 4, "v3": 8, "v4": 12, "v5": 20, "v6": 32},
    "fibonacci": {"vb": 1, "v0": 1, "v1": 2, "v2": 3, "v3": 5, "v4": 8, "v5": 13, "v6": 21},
    "power_scaling": {
        "vb": round(0.5 ** 1.5, 1),
        "v0": round(1 ** 1.5, 1),
        "v1": round(2 ** 1.5, 1),
        "v2": round(3 ** 1.5, 1),
        "v3": round(4 ** 1.5, 1),
        "v4": round(5 ** 1.5, 1),
        "v5": round(6 ** 1.5, 1),
        "v6": round(7 ** 1.5, 1),
    },
    "difficulty_curve": {"vb": 1, "v0": 2, "v1": 3, "v2": 5, "v3": 7, "v4": 11, "v5": 16, "v6": 24},
}

LOCATION_ALIASES = {
    "VERTICALVENTURES": "VERTICAL VENTURES",
    "VERTICAL VENTURES": "VERTICAL VENTURES",
    "CENTRAL ROCK": "CENTRAL ROCK",
    "MOVEMENT, VA": "MOVEMENT, VA",
    "MOVEMENT, MD": "MOVEMENT, MD",
    "UPLIFT, WA": "UPLIFT",
    "UPLIFT": "UPLIFT",
    "EDINBURGH INTERNATIONAL CLIMBING ARENA": "EDINBURGH INTERNATIONAL CLIMBING ARENA",
}

SHEET_ID = "15r0qE2WNQYk2CLqxnI7b5r9_OWyaOMFAtb_4t8_ylnA"
SHEET_EXPORT_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
LOCAL_CSV = "20250212_rockclimbing.csv"


def normalize_location(loc: str) -> str:
    if pd.isna(loc):
        return loc
    loc = str(loc).upper().strip()
    loc = " ".join(loc.split())
    loc = loc.replace(" ,", ",").replace(", ", ",")
    loc = loc.replace(",", ", ")
    loc = loc.strip()
    return LOCATION_ALIASES.get(loc, loc)


def parse_grade_value(value) -> tuple[int, int]:
    """Return (completed, tried) counts from a raw cell value."""
    if pd.isna(value):
        return 0, 0
    if isinstance(value, str):
        parts = value.split()
        if "tried" in parts:
            idx = parts.index("tried")
            completed = int(parts[idx - 1]) if idx > 0 and parts[idx - 1].isdigit() else 0
            tried = int(parts[idx + 1]) if idx + 1 < len(parts) and parts[idx + 1].isdigit() else 0
            return completed, tried
        if value.strip().isdigit():
            return int(value.strip()), 0
        return 0, 0
    try:
        return int(value), 0
    except (ValueError, TypeError):
        return 0, 0


def load_raw_data() -> pd.DataFrame:
    try:
        df = pd.read_csv(SHEET_EXPORT_URL)
    except Exception:
        try:
            df = pd.read_csv(LOCAL_CSV)
        except Exception as e:
            raise RuntimeError(f"Failed to load climbing data: {e}")
    return df


def build_clean_dataframe() -> pd.DataFrame:
    df = load_raw_data()

    df["Location"] = df["Location"].apply(normalize_location)
    df["Dates"] = pd.to_datetime(df["Dates"], errors="coerce")
    df = df.sort_values("Dates")

    present_grades = [g for g in GRADES if g in df.columns]
    for grade in present_grades:
        df[[f"{grade}_completed", f"{grade}_tried"]] = df[grade].apply(
            lambda v: pd.Series(parse_grade_value(v))
        )

    return df, present_grades


def calculate_score(row: pd.Series, weights: dict, present_grades: list) -> float:
    return sum(
        row.get(f"{g}_completed", 0) * weights.get(g, 0)
        for g in present_grades
        if pd.notna(row.get(f"{g}_completed", 0))
    )


@app.get("/api/climbing-data")
def get_climbing_data(
    scoring: Optional[str] = Query(
        default="original_exponential",
        description="Scoring method key. One of: " + ", ".join(SCORING_METHODS.keys()),
    )
):
    """Return all cleaned climbing sessions with parsed grade counts and daily score."""
    if scoring not in SCORING_METHODS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scoring method '{scoring}'. Valid options: {list(SCORING_METHODS.keys())}",
        )

    try:
        df, present_grades = build_clean_dataframe()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    weights = SCORING_METHODS[scoring]
    df["daily_score"] = df.apply(lambda r: calculate_score(r, weights, present_grades), axis=1)

    grade_cols = [f"{g}_{suffix}" for g in present_grades for suffix in ("completed", "tried")]
    output_cols = ["Location", "Dates", "daily_score"] + grade_cols
    if "Comments" in df.columns:
        output_cols.append("Comments")

    result_df = df[output_cols].copy()
    result_df["Dates"] = result_df["Dates"].dt.strftime("%Y-%m-%d")
    result_df = result_df.fillna(0)

    sessions = result_df.to_dict(orient="records")

    return {
        "scoring_method": scoring,
        "weights": weights,
        "total_sessions": len(sessions),
        "sessions": sessions,
    }


@app.get("/api/scoring-methods")
def get_scoring_methods():
    """Return all available scoring methods and their grade weights."""
    return SCORING_METHODS


@app.get("/api/locations")
def get_locations():
    """Return gym location metadata."""
    try:
        with open("locations.json") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Could not load locations: {e}")


@app.get("/health")
def health():
    return {"status": "ok"}
