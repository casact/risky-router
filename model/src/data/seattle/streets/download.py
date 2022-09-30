import json
import os
from pathlib import Path

import requests
from loguru import logger

from src import CONFIG
from src.data import download_file


def download_seattle_street_data(save_folder: Path, overwrite: bool = False):
    url = (
        "https://opendata.arcgis.com/api/v3/datasets"
        "/73f5184d9062458c81ff86e5f5bcdbb8_9"
        "/downloads/data"
        "?format=geojson"
        "&spatialRefId=4326"
        "&where=1=1"
    )

    save_folder = save_folder / "seattle" / "streets"
    save_folder.mkdir(parents=True, exist_ok=True)
    file_name = "streets.geojson"

    if os.path.exists(save_folder / file_name) and not overwrite:
        logger.warning(f"File {file_name} already exists.")
        return

    download_file(url, save_folder / file_name)


def download_seattle_intersection_data(save_folder: Path, overwrite: bool = False):
    url = (
        "https://data-seattlecitygis.opendata.arcgis.com"
        "/datasets/SeattleCityGIS::intersections-3.geojson"
    )

    save_folder = save_folder / "seattle" / "intersections"
    save_folder.mkdir(parents=True, exist_ok=True)
    file_name = "intersections.geojson"

    if os.path.exists(save_folder / file_name) and not overwrite:
        logger.warning(f"File {file_name} already exists.")
        return

    download_file(url, save_folder / file_name)


def download_seattle_volume_data(save_folder: Path, overwrite: bool = False):
    url = "https://data.seattle.gov/api/views/fe9f-nc4f/rows.csv?accessType=DOWNLOAD"

    save_folder = save_folder / "seattle" / "volume"
    save_folder.mkdir(parents=True, exist_ok=True)
    file_name = "volume.csv"

    if os.path.exists(save_folder / file_name) and not overwrite:
        logger.warning(f"File {file_name} already exists.")
    else:
        download_file(url, save_folder / file_name)

    url = (
        "https://data.seattle.gov/api/views/fe9f-nc4f/files"
        "/77367d8d-278e-4a2a-a388-8449be33639f"
        "?download=true"
        "&filename=Location%20Lat%20Long.xlsx"
    )
    file_name = "latlong.xlsx"

    if os.path.exists(save_folder / file_name) and not overwrite:
        logger.warning(f"File {file_name} already exists.")
    else:
        download_file(url, save_folder / file_name)


def download_seattle_weather_data(save_folder: Path, overwrite: bool = False):
    api = CONFIG["weather"]["api"]

    save_folder = save_folder / "seattle" / "weather"
    save_folder.mkdir(parents=True, exist_ok=True)
    file_name = "weather.json"

    if os.path.exists(save_folder / file_name) and not overwrite:
        logger.warning(f"File {file_name} already exists.")
    else:
        query = {
            "latitude": api["params"]["latitude"],
            "longitude": api["params"]["longitude"],
            "start_date": f"{api['params']['start_date']:%Y-%m-%d}",
            "end_date": f"{api['params']['end_date']:%Y-%m-%d}",
            "hourly": api["params"]["hourly"],
        }
        response = requests.get(api["url"], params=query)

        with open(save_folder / file_name, "w") as f:
            json.dump(response.json(), f)
