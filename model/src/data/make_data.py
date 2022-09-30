from pathlib import Path

import click
import pandas as pd
from loguru import logger

from src import PROC_DATA_DIR, RAW_DATA_DIR
from src.data.crss.download import download_crss_data
from src.data.crss.transform import (
    merge_crss_data,
    transform_accident_data,
    transform_distract_data,
    transform_person_data,
    transform_vehicle_data,
)
from src.data.seattle.collisions.download import download_seattle_collision_data
from src.data.seattle.collisions.transform import (
    save_seattle_risk_data,
    transform_seattle_collision_data,
)
from src.data.seattle.streets.download import (
    download_seattle_intersection_data,
    download_seattle_street_data,
    download_seattle_weather_data,
)
from src.data.seattle.streets.transform import (
    save_exposure_data,
    transform_seattle_intersection_data,
    transform_seattle_streets_data,
    transform_seattle_volume_data,
    transform_seattle_weather_data,
)


@click.command()
@click.option(
    "--start_year",
    "-sy",
    type=click.INT,
    default=2019,
    help="Start year to prepare data for",
)
@click.option(
    "--end_year",
    "-ey",
    type=click.INT,
    default=2019,
    help="End year to prepare data for",
)
@click.option(
    "--frequency",
    "-f",
    is_flag=True,
    help="Frequency only",
)
@click.option(
    "--severity",
    "-s",
    is_flag=True,
    help="Severity only",
)
@click.option(
    "--overwrite",
    "-o",
    is_flag=True,
    help="Overwrite existing data",
)
@click.option(
    "--download",
    "-d",
    is_flag=True,
    help="Download data",
)
def main(
    start_year: int,
    end_year: int,
    frequency: bool = False,
    severity: bool = False,
    overwrite: bool = False,
    download: bool = False,
):
    """
    Runs data processing scripts to turn raw data from (data/raw) into
    cleaned data ready to be analyzed (saved in data/processed).
    """
    if frequency and severity:
        pass
    elif frequency:
        logger.info("Frequency only selected.")
        severity = False
    elif severity:
        logger.info("Severity only selected.")
        frequency = False
    else:
        frequency = True
        severity = True

    years = list(range(start_year, end_year + 1))

    if frequency:
        # Exposure data
        if download:
            download_seattle_street_data(RAW_DATA_DIR, overwrite=overwrite)
            download_seattle_intersection_data(RAW_DATA_DIR, overwrite=overwrite)
            download_seattle_weather_data(RAW_DATA_DIR, overwrite=overwrite)

        if not Path(PROC_DATA_DIR / "exposure.f").exists() or overwrite:
            street_df = transform_seattle_streets_data()
            intersec_df = transform_seattle_intersection_data()
            weather_df = transform_seattle_weather_data()
            vol_df = transform_seattle_volume_data(weather_df)

            exposure = save_exposure_data(
                street=street_df, intersection=intersec_df, volume=vol_df
            )
        else:
            logger.warning(
                "Exposure data already exists. Use -o to overwrite existing data."
            )

    if severity:
        # Collision data
        if download:
            download_seattle_collision_data(RAW_DATA_DIR, overwrite=overwrite)

        if not Path(PROC_DATA_DIR / "risk.f").exists() or overwrite:
            collision_df = transform_seattle_collision_data()
            risk_df = save_seattle_risk_data(collision=collision_df)
        else:
            logger.warning(
                "Risk data already exists. Use -o to overwrite existing data."
            )

        # Accident data
        if download:
            download_crss_data(
                save_folder=RAW_DATA_DIR, years=years, overwrite=overwrite
            )

        if not Path(PROC_DATA_DIR / "accident.f").exists() or overwrite:
            accident_df = transform_accident_data(years)
            vehicle_df = transform_vehicle_data(years)
            person_df = transform_person_data(years)
            distract_df = transform_distract_data(years)

            accident_df = merge_crss_data(
                accident_df, vehicle_df, person_df, distract_df
            )
        else:
            logger.warning(
                "CRSS accident data already exists. Use -o to overwrite existing data."
            )
            accident_df = pd.read_feather(PROC_DATA_DIR / "accident.f")


if __name__ == "__main__":
    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    main()
