import json
from pathlib import Path
import click
import pandas as pd
from src import PROC_DATA_DIR
from src.models.frequency import load_modelling_data


def frequency_by_hour():
    df = load_modelling_data()
    df = df.groupby(["HourofData"])[["NumVehicles", "TotalVolume"]].sum()
    df["Frequency"] = df.NumVehicles / df.TotalVolume
    df.Frequency.to_json(PROC_DATA_DIR / "frequency_by_hour.json")


def frequency_by_weather():
    df = load_modelling_data()
    df = df.groupby(["Weather"])[["NumVehicles", "TotalVolume"]].sum()
    df["Frequency"] = df.NumVehicles / df.TotalVolume
    df.Frequency.to_json(PROC_DATA_DIR / "frequency_by_weather.json")


def frequency_heatmap():
    street = pd.read_feather(PROC_DATA_DIR / "streets.f")
    street = street[["PointId", "Longitude", "Latitude"]].drop_duplicates().copy()

    risk = pd.read_feather(PROC_DATA_DIR / "risk.f")
    risk = risk[["StationId", "NumVehicles", "Longitude", "Latitude"]].copy()
    df = street.merge(risk, on=["Longitude", "Latitude"]).drop_duplicates()

    # Exposure data
    exposure = pd.read_feather(PROC_DATA_DIR / "exposure.f")
    exposure = exposure.groupby(["StationId"])[["TotalVolume"]].sum()
    exposure = exposure[exposure.TotalVolume > 0]
    exposure["TotalVolume"] = exposure["TotalVolume"] / 1000  # Per 1000 vehicles

    df = df.merge(exposure, on=["StationId"])
    df["Frequency"] = df.NumVehicles / df.TotalVolume

    with open(PROC_DATA_DIR / "frequency_heatmap.json", "w") as f:
        json.dump(df[["Latitude", "Longitude", "Frequency"]].to_numpy().tolist(), f)


@click.command()
def main():
    """ """

    frequency_by_hour()
    frequency_by_weather()
    frequency_heatmap()


if __name__ == "__main__":
    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    main()
