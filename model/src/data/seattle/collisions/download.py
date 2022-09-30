import os
from pathlib import Path

from loguru import logger

from src.data import download_file


def download_seattle_collision_data(save_folder: Path, overwrite: bool = False):
    url = (
        "https://data-seattlecitygis.opendata.arcgis.com/datasets"
        "/SeattleCityGIS::collisions-all-years.geojson"
    )

    save_folder = save_folder / "seattle" / "collisions"
    save_folder.mkdir(parents=True, exist_ok=True)
    file_name = "collisions.geojson"

    if os.path.exists(save_folder / file_name) and not overwrite:
        logger.warning(f"File {file_name} already exists.")
        return

    download_file(url, save_folder / file_name)
