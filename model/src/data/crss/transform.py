from typing import List
from zipfile import ZipFile

import pandas as pd
from loguru import logger

from src import DATA_SCHEMA, PROC_DATA_DIR, RAW_DATA_DIR
from src.data import encode_categories


def reduce_weather(col: pd.Series) -> pd.Series:
    out_col = col.copy()

    out_col = out_col.cat.add_categories(["OVERCAST"])

    out_col[out_col == "BLOWING_SAND_SOIL_DIRT"] = "OTHER"
    out_col[out_col == "BLOWING_SNOW"] = "SNOW"
    out_col[out_col == "CLOUDY"] = "OVERCAST"
    out_col[out_col == "FREEZING_RAIN"] = "RAIN"
    out_col[out_col == "NOT_REPORTED"] = "OTHER"
    out_col[out_col == "SEVERE_CROSSWINDS"] = "OTHER"
    out_col[out_col == "SLEET_HAIL"] = "RAIN"
    out_col[out_col == "UNKNOWN"] = "OTHER"

    removals = [
        "BLOWING_SAND_SOIL_DIRT",
        "BLOWING_SNOW",
        "CLOUDY",
        "FREEZING_RAIN",
        "NOT_REPORTED",
        "SEVERE_CROSSWINDS",
        "SLEET_HAIL",
        "UNKNOWN",
    ]

    for cat in removals:
        try:
            out_col = out_col.cat.remove_categories(removals=[cat])
        except ValueError:
            continue

    return out_col


def reduce_maximum_severity(col: pd.Series) -> pd.Series:
    out_col = col.copy()

    out_col = out_col.cat.add_categories(["OTHER", "NONE_TO_MINOR_INJURY"])

    out_col[out_col == "NO_INJURY"] = "NONE_TO_MINOR_INJURY"
    out_col[out_col == "POSSIBLE_INJURY"] = "NONE_TO_MINOR_INJURY"
    out_col[out_col == "MINOR_INJURY"] = "NONE_TO_MINOR_INJURY"
    out_col[out_col == "INJURED_UNKNOWN_SEVERITY"] = "OTHER"
    out_col[out_col == "DIED_PRIOR"] = "OTHER"
    out_col[out_col == "NO_OCCUPANTS"] = "OTHER"
    out_col[out_col == "UNKNOWN"] = "OTHER"

    removals = [
        "NO_INJURY",
        "POSSIBLE_INJURY",
        "MINOR_INJURY",
        "INJURED_UNKNOWN_SEVERITY",
        "DIED_PRIOR",
        "NO_OCCUPANTS",
        "UNKNOWN",
    ]

    for cat in removals:
        try:
            out_col = out_col.cat.remove_categories(removals=[cat])
        except ValueError:
            continue

    return out_col


def reduce_body_type(col: pd.Series) -> pd.Series:
    out_col = col.copy()

    out_col[col <= 39] = "FOUR_WHEEL_VEHICLE"
    out_col[col >= 80] = "LESS_THAN_FOUR_WHEEL_VEHICLE"

    return out_col.astype("category")


def reduce_distraction(col: pd.Series) -> pd.Series:
    out_col = col.copy()

    out_col = out_col.cat.add_categories(["MOBILE_PHONE"])

    out_col[out_col == "LOOKED_BUT_DID_NOT_SEE"] = "OTHER"
    out_col[out_col == "BY_OTHER_OCCUPANTS"] = "OTHER"
    out_col[out_col == "BY_A_MOVING_OBJECT_IN_VEHICLE"] = "OTHER"
    out_col[out_col == "WHILE_TALKING_OR_LISTENING_PHONE"] = "MOBILE_PHONE"
    out_col[out_col == "WHILE_MANIPULATING_PHONE"] = "MOBILE_PHONE"
    out_col[out_col == "WHILE_ADJUSTING_AUDIO_CLIMATE"] = "OTHER"
    out_col[out_col == "WHILE_ADJUSTING_OTHER"] = "OTHER"
    out_col[out_col == "WHILE_USING_REACHING_DEVICE"] = "OTHER"
    out_col[out_col == "OUTSIDE_PERSON_OBJECT"] = "OTHER"
    out_col[out_col == "EATING_DRINKING"] = "OTHER"
    out_col[out_col == "SMOKING"] = "OTHER"
    out_col[out_col == "OTHER_MOBILE_PHONE"] = "MOBILE_PHONE"
    out_col[out_col == "NO_DRIVER"] = "OTHER"
    out_col[out_col == "INATTENTION"] = "OTHER"
    out_col[out_col == "CARELESS"] = "OTHER"
    out_col[out_col == "INATTENTIVE"] = "OTHER"
    out_col[out_col == "OTHER_UNKNOWN"] = "OTHER"
    out_col[out_col == "INATTENTIVE_UNKNOWN"] = "OTHER"
    out_col[out_col == "NOT_REPORTED"] = "OTHER"
    out_col[out_col == "DAY_DREAMING"] = "OTHER"
    out_col[out_col == "OTHER"] = "OTHER"
    out_col[out_col == "UNKNOWN"] = "OTHER"

    removals = [
        "LOOKED_BUT_DID_NOT_SEE",
        "BY_OTHER_OCCUPANTS",
        "BY_A_MOVING_OBJECT_IN_VEHICLE",
        "WHILE_TALKING_OR_LISTENING_PHONE",
        "WHILE_MANIPULATING_PHONE",
        "WHILE_ADJUSTING_AUDIO_CLIMATE",
        "WHILE_ADJUSTING_OTHER",
        "WHILE_USING_REACHING_DEVICE",
        "OUTSIDE_PERSON_OBJECT",
        "EATING_DRINKING",
        "SMOKING",
        "OTHER_MOBILE_PHONE",
        "NO_DRIVER",
        "INATTENTION",
        "CARELESS",
        "INATTENTIVE",
        "DISTRACTED_UNKNOWN",
        "INATTENTIVE_UNKNOWN",
        "NOT_REPORTED",
        "DAY_DREAMING",
        "UNKNOWN",
    ]

    for cat in removals:
        try:
            out_col = out_col.cat.remove_categories(removals=[cat])
        except ValueError:
            continue

    return out_col


def transform_accident_data(years: List[int]) -> pd.DataFrame:
    logger.info(
        f"Transforming CRSS accident data for years: [{', '.join([str(y) for y in years])}]"
    )

    schema = DATA_SCHEMA["crss"]["accident"]

    accident_dfs = []

    for year in years:
        data_path = (
            RAW_DATA_DIR
            / "nhtsa"
            / "downloads"
            / "CRSS"
            / str(year)
            / f"CRSS{year}SAS.zip"
        )

        with ZipFile(data_path) as zf:
            with zf.open("accident.sas7bdat") as f:
                accident_dfs.append(pd.read_sas(f, format="sas7bdat"))

    logger.info(f"Merging {len(accident_dfs)} CRSS accident dataframes and saving.")
    df = pd.concat(accident_dfs)

    # Drop unnecessary columns
    df = df.drop(columns=list(set(df.columns) - set(schema["columns"].keys())))
    df = df.rename(columns=schema["columns"])

    # Convert to appropriate data types
    df.CaseId = pd.to_numeric(df.CaseId, downcast="integer")
    df.HourofData = pd.to_numeric(df.HourofData, downcast="integer").astype("category")
    df.Weather = pd.to_numeric(df.Weather, downcast="integer")

    # Category mappings
    df.Weather = df.Weather.map(
        encode_categories(encoding=schema["weather"], reverse=True)
    ).astype("category")

    # Reduce categories
    df.Weather = reduce_weather(df.Weather)

    # Rename columns, filter, and save
    df = df[df.Weather != "OTHER"]
    df.Weather = df.Weather.cat.remove_categories(["OTHER"])
    df = df.reset_index(drop=True)

    df.to_feather(PROC_DATA_DIR / "crss_accident.f")
    logger.success(f"Saved {PROC_DATA_DIR / 'crss_accident.f'}")

    return df


def transform_vehicle_data(years: List[int]) -> pd.DataFrame:
    logger.info(
        f"Transforming CRSS vehicle data for years: [{', '.join([str(y) for y in years])}]"
    )

    schema = DATA_SCHEMA["crss"]["vehicle"]

    vehicle_dfs = []

    for year in years:
        data_path = (
            RAW_DATA_DIR
            / "nhtsa"
            / "downloads"
            / "CRSS"
            / str(year)
            / f"CRSS{year}SAS.zip"
        )

        with ZipFile(data_path) as zf:
            with zf.open("vehicle.sas7bdat") as f:
                vehicle_dfs.append(pd.read_sas(f, format="sas7bdat"))

    logger.info(f"Merging {len(vehicle_dfs)} CRSS vehicle dataframes and saving.")
    df = pd.concat(vehicle_dfs)

    # Drop unnecessary columns
    df = df.drop(columns=list(set(df.columns) - set(schema["columns"].keys())))
    df = df.rename(columns=schema["columns"])

    # Convert to appropriate data types
    df.CaseId = pd.to_numeric(df.CaseId, downcast="integer")
    df.VehicleId = pd.to_numeric(df.VehicleId, downcast="integer")
    df.VehicleYear = pd.to_numeric(df.VehicleYear, downcast="integer")
    df.BodyType = pd.to_numeric(df.BodyType, downcast="integer")
    df.Speed = pd.to_numeric(df.Speed, downcast="integer")
    df.SpeedLimit = pd.to_numeric(df.SpeedLimit, downcast="integer")
    df.MaximumSeverity = pd.to_numeric(df.MaximumSeverity, downcast="integer")
    df.Alcohol = pd.to_numeric(df.Alcohol, downcast="integer")

    # Filter
    df = df[
        df.BodyType.isin(
            [
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                17,
                10,
                11,
                13,
                14,
                15,
                16,
                19,
                20,
                21,
                22,
                28,
                29,
                30,
                31,
                32,
                33,
                34,
                39,
                80,
                81,
                82,
                83,
                84,
                85,
                86,
                87,
                88,
                89,
                90,
            ]
        )
    ]

    # Category mappings
    df.MaximumSeverity = df.MaximumSeverity.map(
        encode_categories(encoding=schema["maximum_severity"], reverse=True)
    ).astype("category")
    df.Alcohol = df.Alcohol.map(
        encode_categories(encoding=schema["alcohol"], reverse=True)
    ).astype("category")

    # Reduce categories
    df.MaximumSeverity = reduce_maximum_severity(df.MaximumSeverity)
    df.BodyType = reduce_body_type(df.BodyType)

    # Rename columns, filter, and save
    df = df[df.MaximumSeverity != "OTHER"]
    df.MaximumSeverity = df.MaximumSeverity.cat.remove_categories(["OTHER"])
    df = df.reset_index(drop=True)

    df.to_feather(PROC_DATA_DIR / "crss_vehicle.f")
    logger.success(f"Saved {PROC_DATA_DIR / 'crss_vehicle.f'}")

    return df


def transform_person_data(years: List[int]) -> pd.DataFrame:
    logger.info(
        f"Transforming CRSS person data for years: [{', '.join([str(y) for y in years])}]"
    )

    schema = DATA_SCHEMA["crss"]["person"]

    person_dfs = []

    for year in years:
        data_path = (
            RAW_DATA_DIR
            / "nhtsa"
            / "downloads"
            / "CRSS"
            / str(year)
            / f"CRSS{year}SAS.zip"
        )

        with ZipFile(data_path) as zf:
            with zf.open("person.sas7bdat") as f:
                person_dfs.append(pd.read_sas(f, format="sas7bdat"))

    logger.info(f"Merging {len(person_dfs)} CRSS person dataframes and saving.")
    df = pd.concat(person_dfs)

    # Drop unnecessary columns and data
    df = df.drop(columns=list(set(df.columns) - set(schema["columns"].keys())))
    df = df.rename(columns=schema["columns"])
    df = df[df.PersonType == 1]
    df = df.drop(columns=["PersonType"])

    # Convert to appropriate data types
    df.CaseId = pd.to_numeric(df.CaseId, downcast="integer")
    df.AgeofDriver = pd.to_numeric(df.AgeofDriver, downcast="integer")

    # Rename columns, filter, and save
    df = df.reset_index(drop=True)

    df.to_feather(PROC_DATA_DIR / "crss_person.f")
    logger.success(f"Saved {PROC_DATA_DIR / 'crss_person.f'}")

    return df


def transform_distract_data(years: List[int]) -> pd.DataFrame:
    logger.info(
        f"Transforming CRSS distract data for years: [{', '.join([str(y) for y in years])}]"
    )

    schema = DATA_SCHEMA["crss"]["distract"]

    distract_dfs = []

    for year in years:
        data_path = (
            RAW_DATA_DIR
            / "nhtsa"
            / "downloads"
            / "CRSS"
            / str(year)
            / f"CRSS{year}SAS.zip"
        )

        with ZipFile(data_path) as zf:
            with zf.open("distract.sas7bdat") as f:
                distract_dfs.append(pd.read_sas(f, format="sas7bdat"))

    logger.info(f"Merging {len(distract_dfs)} CRSS distract dataframes and saving.")
    df = pd.concat(distract_dfs)

    # Drop unnecessary columns and data
    df = df.drop(columns=list(set(df.columns) - set(schema["columns"].keys())))
    df = df.rename(columns=schema["columns"])

    # Convert to appropriate data types
    df.CaseId = pd.to_numeric(df.CaseId, downcast="integer")
    df.Distraction = pd.to_numeric(df.Distraction, downcast="integer")

    # Category mappings
    df.Distraction = df.Distraction.map(
        encode_categories(encoding=schema["distraction"], reverse=True)
    ).astype("category")

    # Reduce categories
    df.Distraction = reduce_distraction(df.Distraction)

    # Rename columns, filter, and save
    df = df[(df.Distraction != "OTHER")]
    df.Distraction = df.Distraction.cat.remove_categories(["OTHER"])
    df = df.reset_index(drop=True)

    df.to_feather(PROC_DATA_DIR / "crss_distract.f")
    logger.success(f"Saved {PROC_DATA_DIR / 'crss_distract.f'}")

    return df


def merge_crss_data(
    accident_df: pd.DataFrame,
    vehicle_df: pd.DataFrame,
    person_df: pd.DataFrame,
    distract_df: pd.DataFrame,
) -> pd.DataFrame:
    logger.info("Merging CRSS data.")
    df = accident_df.merge(vehicle_df, on=["CaseId"])
    df = df.merge(person_df, on=["CaseId"])
    df = df.merge(distract_df, on=["CaseId"])

    # Filter
    df = df[
        (df.Speed > 0)
        & (df.Speed < 200)
        & (df.SpeedLimit > 0)
        & (df.SpeedLimit < 99)
        & (df.AgeofDriver < 120)
        & (df.AgeofDriver >= 15)
        & (df.VehicleYear > 1900)
        & (df.VehicleYear <= 2030)
    ]
    df["RelativeSpeed"] = df.Speed / df.SpeedLimit

    df.dropna().reset_index(drop=True).to_feather(PROC_DATA_DIR / "accident.f")
    logger.info("Saving accident data.")
    logger.success(f"Saved {PROC_DATA_DIR / 'accident.f'}")
    return df
