import json

import joblib
import pandas as pd
import pytz
from loguru import logger
from sklearn.neighbors import KNeighborsClassifier

from src import (
    CONFIG,
    DATA_SCHEMA,
    INTERVALS_PER_HOUR,
    MODELS_DIR,
    PROC_DATA_DIR,
    RAW_DATA_DIR,
)
from src.data import encode_categories


def transform_seattle_streets_data() -> pd.DataFrame:
    logger.info("Transforming Seattle streets data")
    schema = DATA_SCHEMA["seattle"]["streets"]

    with open(RAW_DATA_DIR / "seattle" / "streets" / "streets.geojson", "r") as f:
        street_json = dict(json.load(f))

    streets = pd.DataFrame([row["properties"] for row in street_json["features"]])

    coords = pd.DataFrame(
        [row["geometry"]["coordinates"][0] for row in street_json["features"]]
    )
    coords.columns = [f"coord_{col}" for col in coords]
    coords = streets[["OBJECTID"]].join(coords)
    coords = coords.melt(id_vars="OBJECTID", value_vars=coords.columns).dropna(
        subset="value"
    )
    coords["PointId"] = coords.variable.str.split("_").str[-1]
    coords["Latitude"], coords["Longitude"] = coords.value.str[1], coords.value.str[0]
    coords = coords.drop(columns=["variable", "value"])

    df = streets.merge(coords, on="OBJECTID")

    # Rename
    df = df.rename(columns=schema["columns"])

    # Drop unnecessary columns
    df = df[list(schema["columns"].values()) + ["PointId", "Longitude", "Latitude"]]

    # Convert to appropriate data types
    df.ObjectId = pd.to_numeric(df.ObjectId, downcast="integer")
    df.PointId = pd.to_numeric(df.PointId, downcast="integer")
    df.ArterialCode = pd.to_numeric(df.ArterialCode, downcast="integer")
    df.SpeedLimitMPH = pd.to_numeric(df.SpeedLimitMPH, downcast="float")
    df.Length = pd.to_numeric(df.Length, downcast="float")
    df.Longitude = pd.to_numeric(df.Longitude, downcast="float")
    df.Latitude = pd.to_numeric(df.Latitude, downcast="float")

    # Remove NA
    for col in df.columns:
        if df[col].isna().any():
            logger.warning(
                f"{col} has {df[col].isna().sum()} NA values that will be dropped."
            )
            df = df.dropna(subset=[col])

    # Category mappings
    df.ArterialCode = df.ArterialCode.map(
        encode_categories(encoding=schema["arterial_code"], reverse=True)
    ).astype("category")

    # Rename columns, filter, and save
    df = df.reset_index(drop=True)

    df.to_feather(PROC_DATA_DIR / "streets.f")
    logger.success(f"Saved {PROC_DATA_DIR / 'streets.f'}")

    return df


def transform_seattle_intersection_data() -> pd.DataFrame:
    logger.info("Transforming Seattle intersection data")
    schema = DATA_SCHEMA["seattle"]["intersections"]

    with open(
        RAW_DATA_DIR / "seattle" / "intersections" / "intersections.geojson", "r"
    ) as f:
        street_json = dict(json.load(f))

    df = pd.DataFrame([row["properties"] for row in street_json["features"]])

    # Rename
    df = df.rename(columns=schema["columns"])

    # Drop unnecessary columns
    df = df[list(schema["columns"].values())]

    # Convert to appropriate data types
    df.IntersectionId = pd.to_numeric(df.IntersectionId, downcast="integer")
    df.Longitude = pd.to_numeric(df.Longitude, downcast="float")
    df.Latitude = pd.to_numeric(df.Latitude, downcast="float")

    # Remove NA
    for col in df.columns:
        if df[col].isna().any():
            logger.warning(
                f"{col} has {df[col].isna().sum()} NA values that will be dropped."
            )
            df = df.dropna(subset=[col])

    # Rename columns, filter, and save
    df = df.reset_index(drop=True)

    df.to_feather(PROC_DATA_DIR / "intersections.f")
    logger.success(f"Saved {PROC_DATA_DIR / 'intersections.f'}")

    return df


def transform_seattle_volume_data(weather: pd.DataFrame) -> pd.DataFrame:
    logger.info("Transforming Seattle volume data")
    schema = DATA_SCHEMA["seattle"]["volume"]

    vol = pd.read_csv(
        RAW_DATA_DIR / "seattle" / "volume" / "volume.csv",
        usecols=[0, 1, 2, 4],
    )
    vol.Time = pd.to_datetime(
        vol.Time.str.replace(" P[D,S]T", "", regex=True), format="%m/%d/%Y %H:%M:%S"
    )
    pacific_time = pytz.timezone("America/Los_Angeles")
    vol.Time = vol.Time.dt.tz_localize(
        pacific_time, ambiguous=True, nonexistent="shift_forward"
    )

    # Round to hours so can join with weather
    vol.Time = vol.Time.dt.round("H", ambiguous=True, nonexistent="shift_forward")
    vol = vol.groupby(["APEG", "Time"]).sum().reset_index()

    # Merge in weather data
    df = vol.merge(weather, on=["Time"], how="inner")

    df = df.groupby(["APEG", "Time"], observed=True).sum().reset_index().dropna()
    df["Intervals"] = INTERVALS_PER_HOUR  # Need intervals for accurate exposure

    # Add weather
    weather_map = CONFIG["weather"]["classification"]

    df["Weather"] = "CLEAR"
    df.loc[df.Cloudcover >= weather_map["cloudcover"], "Weather"] = "OVERCAST"
    df.loc[df.Rainfall >= weather_map["rainfall"], "Weather"] = "RAIN"
    df.loc[df.Snowfall >= weather_map["snowfall"], "Weather"] = "SNOW"
    df.Weather = df.Weather.astype("category")

    # Finalise
    df["WeekdayofData"] = pd.to_datetime(df.Time).dt.weekday
    df.WeekdayofData = df.WeekdayofData.map(
        encode_categories(encoding=schema["weekday_of_data"], reverse=True)
    ).astype("category")
    df = df.drop(
        columns=[
            "Rainfall",
            "Snowfall",
            "Cloudcover",
        ]
    )

    # Aggregate
    df = (
        df.groupby(["APEG", "Time", "WeekdayofData", "Weather"], observed=True)
        .sum()
        .reset_index()
    )
    df["HourofData"] = df.Time.dt.hour

    # Coordinates
    latlng = pd.read_excel(
        RAW_DATA_DIR / "seattle" / "volume" / "latlong.xlsx",
        usecols=["APEG", "Latitude", "Longitude"],
    )

    # Rename
    df = df.rename(columns={"APEG": "StationId", "Vol": "TotalVolume"})
    latlng = latlng.rename(columns={"APEG": "StationId"})

    # Merge
    df = df.merge(latlng, on=["StationId"])

    # Map StationId
    station_id_map = {station: i for i, station in enumerate(df.StationId.unique())}
    df.StationId = df.StationId.map(encode_categories(encoding=station_id_map)).astype(
        "int8"
    )

    # Convert to appropriate data types
    df.HourofData = pd.to_numeric(df.HourofData, downcast="integer")
    df.TotalVolume = pd.to_numeric(df.TotalVolume, downcast="float")
    df.Intervals = pd.to_numeric(df.Intervals, downcast="integer")
    df.Longitude = pd.to_numeric(df.Longitude, downcast="float")
    df.Latitude = pd.to_numeric(df.Latitude, downcast="float")

    # Remove NA
    for col in df.columns:
        if df[col].isna().any():
            logger.warning(
                f"{col} has {df[col].isna().sum()} NA values that will be dropped."
            )
            df = df.dropna(subset=[col])

    # Rename columns, filter, and save
    df = df.reset_index(drop=True)

    df.to_feather(PROC_DATA_DIR / "volume.f")
    logger.success(f"Saved {PROC_DATA_DIR / 'volume.f'}")

    return df


def transform_seattle_weather_data():
    logger.info("Transforming Seattle weather data")
    schema = DATA_SCHEMA["seattle"]["weather"]

    with open(RAW_DATA_DIR / "seattle" / "weather" / "weather.json", "r") as f:
        weather_json = json.load(f)

    df = pd.DataFrame(dict(weather_json)["hourly"])

    pacific_time = pytz.timezone("America/Los_Angeles")
    df.time = (
        pd.to_datetime(df.time).dt.tz_localize(pytz.utc).dt.tz_convert(pacific_time)
    )

    # Rename
    df = df.rename(columns=schema["columns"]).reset_index(drop=True)

    # Dtypes
    df.Rainfall = pd.to_numeric(df.Rainfall, downcast="float")
    df.Snowfall = pd.to_numeric(
        df.Snowfall * 10, downcast="float"
    )  # Raw data is in cm, conver to mm
    df.Cloudcover = pd.to_numeric(df.Cloudcover / 100, downcast="float")
    df.CloudcoverLow = pd.to_numeric(df.CloudcoverLow / 100, downcast="float")
    df.RelativeHumidity = pd.to_numeric(df.RelativeHumidity / 100, downcast="float")

    # Save
    df.to_feather(PROC_DATA_DIR / "weather.f")
    logger.success(f"Saved {PROC_DATA_DIR / 'weather.f'}")

    return df


def save_exposure_data(
    street: pd.DataFrame,
    intersection: pd.DataFrame,
    volume: pd.DataFrame,
) -> pd.DataFrame:
    logger.info("Merging street and intersection data")
    df = street.merge(intersection, on=["Longitude", "Latitude"], how="left")

    df["StreetType"] = "STREET"
    df.loc[~df.IntersectionId.isna(), "StreetType"] = "INTERSECTION"
    df.StreetType = df.StreetType.astype("category")

    num_lost = len(set(intersection.IntersectionId) - set(df.IntersectionId))
    logger.warning(f"{num_lost} intersections were not mapped. Dropped.")

    # dtypes
    df.IntersectionId = pd.to_numeric(df.IntersectionId, downcast="float")

    # Map volume to streets
    knn = KNeighborsClassifier(n_neighbors=1)
    knn.fit(volume[["Latitude", "Longitude"]], volume.StationId)
    with open(MODELS_DIR / "station_id_classifier.joblib", "wb") as f:
        joblib.dump(knn, f)

    df["StationId"] = knn.predict(df[["Latitude", "Longitude"]])

    # Aggregate and merge with volume
    df = (
        df[["SpeedLimitMPH", "StreetType", "StationId"]]
        .groupby(["StationId", "StreetType"], observed=True)
        .median()
        .reset_index()
    )

    exposure = df.merge(
        volume.drop(columns=["Latitude", "Longitude"]),
        on=["StationId"],
        how="inner",
    )

    # Save
    exposure = exposure.reset_index(drop=True)

    exposure.to_feather(PROC_DATA_DIR / "exposure.f")
    logger.success(f"Saved {PROC_DATA_DIR / 'exposure.f'}")

    return exposure
