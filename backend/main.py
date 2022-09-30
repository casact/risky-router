import json
from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src import (
    DATA_DIR,
    get_frequency,
    get_per_x_vehicles,
    get_return_period,
    get_severity,
    get_time,
    get_weather,
    get_weekday,
    load_exposure,
    load_models,
)

STATION_MODELS, STATION_CLASSIFIER, SEVERITY_MODEL = load_models()
EXPOSURE = load_exposure()


app = FastAPI()

origins = ["https://riskyrouter.com/", "https://www.riskyrouter.com/", "http://localhost:5173", "http://0.0.0.0:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.post("/api/frequency")
def frequency_route(payload: dict = Body(...)):
    freq, median_daily_volume = get_frequency(
        payload, STATION_MODELS, STATION_CLASSIFIER, EXPOSURE
    )
    per_x_vehicles = get_per_x_vehicles(freq)
    return_period = get_return_period(per_x_vehicles, median_daily_volume)
    return_period_plus_1 = return_period + 1
    return {
        "per_x_vehicles": per_x_vehicles,
        "return_period": return_period,
        "return_period_plus_1": return_period_plus_1,
    }


@app.post("/api/severity")
def severity_route(
    body_type: int,
    vehicle_year: str,
    alcohol: bool,
    relative_speed: float,
):
    prob = get_severity(
        body_type=body_type,
        vehicle_year=vehicle_year,
        alcohol=alcohol,
        relative_speed=relative_speed,
        severity_model=SEVERITY_MODEL,
    )
    return {
        "injury_fatal_prob": prob,
    }


@app.get("/api/weekday")
def weekday_route():
    return get_weekday()


@app.get("/api/time")
def time_route():
    return get_time()


@app.get("/api/weather")
def weather_route():
    return get_weather()


@app.get("/api/frequency_by_hour")
def hour_route():
    with open(DATA_DIR / "frequency_by_hour.json", "r") as f:
        data = json.load(f)

    x_values = list(data.keys())
    y_values = list(data.values())
    return {"x": x_values, "y": y_values}


@app.get("/api/frequency_by_weather")
def weather_route():
    with open(DATA_DIR / "frequency_by_weather.json", "r") as f:
        data = json.load(f)

    x_values = list(data.keys())
    y_values = list(data.values())
    return {"x": x_values, "y": y_values}