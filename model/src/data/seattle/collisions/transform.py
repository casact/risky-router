import json

import joblib
import pandas as pd
import pytz
from loguru import logger

from src import CONFIG, DATA_SCHEMA, MODELS_DIR, PROC_DATA_DIR, RAW_DATA_DIR
from src.data import encode_categories  # bin_hour_of_data,


def reduce_weather(col: pd.Series) -> pd.Series:
    out_col = col.copy()

    out_col[out_col == "Raining"] = "RAIN"
    out_col[out_col == "Fog/Smog/Smoke"] = "OTHER"
    out_col[out_col == "Overcast"] = "OVERCAST"
    out_col[out_col == "Sleet/Hail/Freezing Rain"] = "RAIN"
    out_col[out_col == "Unknown"] = "CLEAR"
    out_col[out_col == "Snowing"] = "SNOW"
    out_col[out_col == "Severe Crosswind"] = "OTHER"
    out_col[out_col == "Blowing Sand/Dirt"] = "OTHER"
    out_col[out_col == "Partly Cloudy"] = "CLEAR"
    out_col[out_col == "Blowing Snow"] = "SNOW"

    out_col = out_col.str.upper().copy()

    out_col = out_col.astype("category")

    return out_col


def reduce_light_condition(col: pd.Series) -> pd.Series:
    out_col = col.copy()

    out_col[out_col == "Dark - Street Lights On"] = "DARK"
    out_col[out_col == "Dawn"] = "DARK"
    out_col[out_col == "Dark - No Street Lights"] = "DARK"
    out_col[out_col == "Dark - Street Lights Off"] = "DARK"
    out_col[out_col == "Dusk"] = "DARK"
    out_col[out_col == "Dark - Unknown Lighting"] = "DARK"
    out_col[out_col == "Other"] = "DAYLIGHT"
    out_col[out_col == "Unknown"] = "DAYLIGHT"

    out_col = out_col.str.upper().copy()

    out_col = out_col.astype("category")

    return out_col


def transform_seattle_collision_data() -> pd.DataFrame:
    logger.info("Transforming collision data")

    schema = DATA_SCHEMA["seattle"]["collisions"]

    with open(RAW_DATA_DIR / "seattle" / "collisions" / "collisions.geojson", "r") as f:
        collision_json = dict(json.load(f))

    collisions = pd.DataFrame([row["properties"] for row in collision_json["features"]])
    collisions = collisions[collisions.STATUS == "Matched"]

    # Get coords
    coords = pd.DataFrame(
        [
            row["geometry"]["coordinates"]
            for row in collision_json["features"]
            if row["geometry"]
        ],
        columns=["LONGITUDE", "LATITUDE"],
    )
    ids = pd.DataFrame(
        [
            row["properties"]["OBJECTID"]
            for row in collision_json["features"]
            if row["geometry"]
        ],
        columns=["OBJECTID"],
    )
    coords = coords.join(ids)

    # Merge in coords
    df = collisions.merge(coords, on=["OBJECTID"])

    # Rename
    df = df.rename(columns=schema["columns"])

    # Drop unnecessary columns
    df = df[list(schema["columns"].values())]

    # Convert to appropriate data types
    df.ObjectId = pd.to_numeric(df.ObjectId, downcast="integer")
    df.IncidentId = pd.to_numeric(df.IncidentId, downcast="integer")
    df.CollisionId = pd.to_numeric(df.CollisionId, downcast="integer")
    df.NumFatalities = pd.to_numeric(df.NumFatalities, downcast="integer")
    df.NumInjuries = pd.to_numeric(df.NumInjuries, downcast="integer")
    df.IntersectionId = pd.to_numeric(df.IntersectionId, downcast="integer")
    df.NumPedestrians = pd.to_numeric(df.NumPedestrians, downcast="integer")
    df.NumCyclists = pd.to_numeric(df.NumCyclists, downcast="integer")
    df.NumPersons = pd.to_numeric(df.NumPersons, downcast="integer")
    df.NumSeriousInjuries = pd.to_numeric(df.NumSeriousInjuries, downcast="integer")
    df.NumVehicles = pd.to_numeric(df.NumVehicles, downcast="integer")
    df.Longitude = pd.to_numeric(df.Longitude, downcast="float")
    df.Latitude = pd.to_numeric(df.Latitude, downcast="float")

    df.Time = pd.to_datetime(df.Time, format="%m/%d/%Y %I:%M:%S %p", errors="coerce")
    pacific_time = pytz.timezone("America/Los_Angeles")
    df.Time = df.Time.dt.tz_localize(
        pacific_time, ambiguous=True, nonexistent="shift_forward"
    )

    # Remove NA
    for col in df.columns:
        if col in ["IntersectionId"]:
            continue
        if df[col].isna().any():
            logger.warning(
                f"{col} has {df[col].isna().sum()} NA values that will be dropped."
            )
            df = df.dropna(subset=[col])

    # Category mappings
    df["WeekdayofData"] = df.Time.dt.weekday.map(
        encode_categories(encoding=schema["weekday_of_data"], reverse=True)
    ).astype("category")
    df.SeverityCode = df.SeverityCode.map(
        encode_categories(encoding=schema["severity_code"], reverse=True)
    )

    # Add intersection col
    df["StreetType"] = "STREET"
    df.loc[~df.IntersectionId.isna(), "StreetType"] = "INTERSECTION"
    df.StreetType = df.StreetType.astype("category")

    # Reduce categories
    df.LightCondition = reduce_light_condition(df.LightCondition)
    df.Weather = reduce_weather(df.Weather)
    df = df.loc[df.Weather != "OTHER"]
    df.Weather = df.Weather.cat.remove_categories(removals=["OTHER"])

    # Remove extra columns
    df = df.drop(columns=["MatchingStatus"])

    # Rename columns, filter, aggregate, and save
    df = df[
        (df.Time.dt.date >= CONFIG["start_date"])
        & (df.Time.dt.date <= CONFIG["end_date"])
    ]
    df = df.reset_index(drop=True)

    df.to_feather(PROC_DATA_DIR / "collisions.f")
    logger.success(f"Saved {PROC_DATA_DIR / 'collisions.f'}")

    return df


def save_seattle_risk_data(collision: pd.DataFrame) -> pd.DataFrame:
    logger.info("Adding StationId to risk data")

    # Add StationId
    with open(MODELS_DIR / "station_id_classifier.joblib", "rb") as f:
        station_classifier = joblib.load(f)

    collision["StationId"] = station_classifier.predict(
        collision[["Latitude", "Longitude"]]
    )
    collision.StationId = pd.to_numeric(collision.StationId, downcast="integer")

    # Remove columns
    risk = collision.drop(
        columns=[
            "ObjectId",
            "IncidentId",
            "CollisionId",
            "IntersectionId",
            "Longitude",
            "Latitude",
        ]
    ).copy()

    # Aggregate
    risk.Time = risk.Time.dt.round("H", ambiguous=True, nonexistent="shift_forward")
    risk = (
        risk.groupby(
            [
                "Time",
                "LightCondition",
                "Weather",
                "WeekdayofData",
                "StreetType",
                "StationId",
            ],
            observed=True,
        )
        .sum()
        .reset_index()
        .dropna()
    )
    risk["HourofData"] = risk.Time.dt.hour
    risk.HourofData = pd.to_numeric(risk.HourofData, downcast="integer")

    # Save
    risk = risk.reset_index(drop=True).copy()

    risk.to_feather(PROC_DATA_DIR / "risk.f")
    logger.success(f"Saved {PROC_DATA_DIR / 'risk.f'}")
