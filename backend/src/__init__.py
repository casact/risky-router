from datetime import datetime
from pathlib import Path
from statistics import harmonic_mean

import joblib
import pandas as pd
import pytz
import requests
import tomli

ROOT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT_DIR / "data"  # noqa: E221

MODELS_DIR = ROOT_DIR / "models"  # noqa: E221

TIMEZONE = pytz.timezone("America/Los_Angeles")

# Configuration
with open("config.toml", "rb") as f:
    CONFIG = tomli.load(f)


def load_models():
    station_models = {}
    for folder in (MODELS_DIR / "stations").iterdir():
        with open(f"{folder}/freq_model.joblib", "rb") as f:
            model = joblib.load(f)

        station_models.update({folder.name: model})

    with open(MODELS_DIR / "severity" / "sev_model.joblib", "rb") as f:
        severity_model = joblib.load(f)

    severity_model.set_params(balancedrandomforestclassifier__n_jobs=1)

    with open(MODELS_DIR / "station_id_classifier.joblib", "rb") as f:
        station_classifier = joblib.load(f)

    return station_models, station_classifier, severity_model


def load_exposure():
    exposure = pd.read_feather(DATA_DIR / "exposure.f")
    exposure = (
        exposure.groupby(
            [
                "StationId",
                "StreetType",
                "HourofData",
                "WeekdayofData",
            ]
        )
        .agg(
            SpeedLimitMPH=("SpeedLimitMPH", "median"),
            TotalVolume=("TotalVolume", "mean"),
        )
        .reset_index()
    )

    exposure["ActualTotalVolume"] = exposure.TotalVolume
    exposure.TotalVolume = 1000

    return exposure


def query_seattle_weather_data():
    api = CONFIG["weather"]["api"]

    query = {
        "latitude": api["params"]["latitude"],
        "longitude": api["params"]["longitude"],
        "current_weather": "true",
        # "timezone": api["params"]["timezone"],
    }
    return requests.get(api["url"], params=query)


def get_weather():
    code_map = CONFIG["encoding"]["weather"]
    response = query_seattle_weather_data()
    code = dict(response.json())["current_weather"]["weathercode"]
    return code_map[str(int(code))]


def get_frequency(payload, station_models, station_classifier, exposure):
    weekday_map = CONFIG["encoding"]["weekday_of_data"]
    total_trip_time = payload["summary"]["totalTime"]

    time_of_request = datetime.now(tz=TIMEZONE)
    weekday = weekday_map[str(time_of_request.weekday())]
    hour = time_of_request.hour

    df = pd.DataFrame(payload["coordinates"])
    df.columns = ["Latitude", "Longitude"]

    df["StationId"] = station_classifier.predict(df)

    route_exposure = df.merge(exposure, on="StationId")
    df = route_exposure.loc[
        (route_exposure.WeekdayofData == weekday) & (route_exposure.HourofData == hour)
    ].copy()

    df["Weather"] = get_weather()
    for station_id in df.StationId.unique():
        pred_df = df[df["StationId"] == station_id].copy()
        freq = station_models[str(station_id)].predict(pred_df)
        df.loc[df["StationId"] == station_id, "Freq"] = (freq / 60) * (
            total_trip_time / 60
        )

    # Median daily exposure
    median_hourly = (
        route_exposure[route_exposure.StreetType == "STREET"]
        .groupby(
            ["StationId", "StreetType", "HourofData", "WeekdayofData"], observed=True
        )["ActualTotalVolume"]
        .median()
        .to_numpy()
    )

    median_daily_volume = sum(median_hourly) // 7

    return harmonic_mean(df.Freq), median_daily_volume


def get_per_x_vehicles(frequency, exposure=1000):
    return exposure // frequency


def integer_thousand_format(number):
    return f"{number:,.0f}"


def percent_format(number):
    if number < 0.01:
        return f"< {0.01:.0%}"
    return f"{number:.0%}"


def get_return_period(per_x_vehicles, daily_volume):
    return_period = per_x_vehicles // daily_volume
    return return_period


def get_severity(
    body_type: int,
    vehicle_year: str,
    alcohol: bool,
    relative_speed: float,
    severity_model,
):
    payload = {
        "BodyType": body_type,
        "VehicleYear": vehicle_year,
        "Alcohol": int(alcohol),
        "RelativeSpeed": relative_speed,
        "Distraction": 0,
    }
    columns = [
        "HourofData",
        "Weather",
        "BodyType",
        "VehicleYear",
        "Alcohol",
        "Distraction",
        "RelativeSpeed",
    ]

    time_of_request = datetime.now(tz=TIMEZONE)
    hour = time_of_request.hour

    df = pd.DataFrame(payload, index=[0])
    df["Weather"] = get_weather()
    df["HourofData"] = hour
    df = df[columns]

    _, prob = severity_model.predict_proba(df)[0]

    return prob


def get_weekday():
    weekday_map = CONFIG["encoding"]["weekday_of_data"]

    time_of_request = datetime.now(tz=TIMEZONE)
    return weekday_map[str(time_of_request.weekday())]


def get_time():
    time_of_request = datetime.now(tz=TIMEZONE)
    return f"{time_of_request.time():%Hh%M}"
