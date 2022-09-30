import gc
from pathlib import Path

import click
from loguru import logger

from src import MODELS_DIR
from src.models import frequency, severity


def make_frequency_models(overwrite):
    df = frequency.load_modelling_data()
    stations = list(df.StationId.unique())
    sorted(stations)

    for station_id in stations:
        filepath = MODELS_DIR / "stations" / f"{station_id}"
        filepath.mkdir(exist_ok=True, parents=True)

        if (filepath / "freq_model.joblib").exists() and not overwrite:
            logger.warning(f"Model for station {station_id} already exists, skipping.")
            continue

        (filepath / "model_fit.log").unlink(missing_ok=True)  # Empty logs
        logger.add(filepath / "model_fit.log")
        logger.info(f"Training model for station {station_id}")

        station_df = frequency.prep_station_data(df, station_id, filepath)
        df_train, df_test = frequency.split_for_training(station_df)
        params = frequency.gridsearch_gbm(df_train, df_test)
        frequency.fit_final_gbm(station_df, params, filepath)

        logger.remove()
        gc.collect()


def make_severity_models(overwrite):
    df = severity.load_modelling_data()

    filepath = MODELS_DIR / "severity"
    filepath.mkdir(exist_ok=True, parents=True)

    if (filepath / "model.joblib").exists() and not overwrite:
        logger.warning("Severity model already exists, skipping.")
        return

    logger.add(filepath / "model_fit.log")
    logger.info("Training severity model")
    severity.fit_final_model(df, filepath)


@click.command()
# @click.option(
#     "--frequency",
#     "-f",
#     is_flag=True,
#     help="Frequency only",
# )
# @click.option(
#     "--severity",
#     "-s",
#     is_flag=True,
#     help="Severity only",
# )
@click.option(
    "--overwrite",
    "-o",
    is_flag=True,
    help="Overwrite existing models",
)
def main(
    overwrite: bool = False,
):
    """ """

    make_frequency_models(overwrite)
    make_severity_models(overwrite)


if __name__ == "__main__":
    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    main()
