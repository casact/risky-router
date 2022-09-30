from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_poisson_deviance,
    mean_squared_error,
)
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

from src import CONFIG, PROC_DATA_DIR

MIN_VOLUME = CONFIG["gbm"]["min_volume"]


def load_modelling_data():
    # Risk data
    risk = pd.read_feather(PROC_DATA_DIR / "risk.f")
    risk = risk.drop(
        columns=[
            "LightCondition",
            "NumFatalities",
            "NumInjuries",
            "NumPedestrians",
            "NumCyclists",
            "NumPersons",
            "NumSeriousInjuries",
        ]
    )

    # Exposure data
    exposure = pd.read_feather(PROC_DATA_DIR / "exposure.f")

    # Combine
    df = exposure.merge(
        risk,
        on=[
            "StationId",
            "Time",
            "StreetType",
            "WeekdayofData",
            "HourofData",
            "Weather",
        ],
        how="left",
    ).fillna(
        {
            "NumFatalities": 0,
            "NumInjuries": 0,
            "NumPersons": 0,
            "NumSeriousInjuries": 0,
            "NumVehicles": 0,
        }
    )

    df = df[df.TotalVolume > MIN_VOLUME]  # Very small volumes mess with model fit

    df["TotalVolume"] = df["TotalVolume"] / 1000  # Per 1000 vehicles
    df["Frequency"] = df["NumVehicles"] / df["TotalVolume"]

    return df


def prep_station_data(df: pd.DataFrame, station_id: int, filepath: Path):
    station_df = df.loc[df.StationId == station_id].copy()

    # Save plot of frequency and volume
    fig, (ax0, ax1, ax2) = plt.subplots(ncols=3, figsize=(16, 4))
    ax0.set_title("Number of vehicles in collision")
    _ = station_df["NumVehicles"].hist(bins=30, log=True, ax=ax0)
    ax1.set_title("Thousand vehicles per hour")
    _ = station_df["TotalVolume"].hist(bins=30, log=True, ax=ax1)
    ax2.set_title("Frequency\n(# of vehicle collisions per 1000 vehicles per hour)")
    _ = station_df["Frequency"].hist(bins=30, log=True, ax=ax2)
    plt.savefig(filepath / "freq_vol.png")
    plt.close()

    return station_df


def split_for_training(df: pd.DataFrame):
    df_train, df_test = train_test_split(df, test_size=0.2)

    avg_freq = np.average(df_train["Frequency"], weights=df_train["TotalVolume"])
    logger.info(f"Average Frequency = {avg_freq:.3%}")

    zero_vehicles = (
        df_train.loc[df_train["NumVehicles"] == 0, "TotalVolume"].sum()
        / df_train["TotalVolume"].sum()
    )
    logger.info(
        f"Fraction of exposure with zero vehicles in accident = {zero_vehicles:.2%}"
    )

    return df_train, df_test


def score_estimator(estimator, df_test):
    """Score an estimator on the test set."""
    y_pred = estimator.predict(df_test)

    mse = mean_squared_error(
        df_test["Frequency"], y_pred, sample_weight=df_test["TotalVolume"]
    )
    mae = mean_absolute_error(
        df_test["Frequency"], y_pred, sample_weight=df_test["TotalVolume"]
    )
    logger.info(f"MSE: {mse:.4f}")
    logger.info(f"MAE: {mae:.4f}")

    # Ignore non-positive predictions, as they are invalid for
    # the Poisson deviance.
    mask = y_pred > 0
    if (~mask).any():
        n_masked, n_samples = (~mask).sum(), mask.shape[0]
        logger.warning(
            "Estimator yields invalid, non-positive predictions "
            f" for {n_masked} samples out of {n_samples}. These predictions "
            "are ignored when computing the Poisson deviance."
        )

    mpd = mean_poisson_deviance(
        df_test["Frequency"][mask],
        y_pred[mask],
        sample_weight=df_test["TotalVolume"][mask],
    )
    logger.info(f"mean Poisson deviance: {mpd:.4f}")


def get_preprocessor():
    # Preprocessor
    tree_preprocessor = ColumnTransformer(
        [
            (
                "categorical",
                OrdinalEncoder(),
                ["StreetType", "WeekdayofData", "Weather"],
            ),
            ("numeric", "passthrough", ["SpeedLimitMPH", "HourofData"]),
        ],
        remainder="drop",
    )
    return tree_preprocessor


def gridsearch_gbm(df_train, df_test):
    tree_preprocessor = get_preprocessor()

    # Model
    poisson_gbrt = Pipeline(
        [
            ("preprocessor", tree_preprocessor),
            (
                "regressor",
                HistGradientBoostingRegressor(
                    loss="poisson",
                ),
            ),
        ]
    )

    # Gridsearch
    parameters = {
        "regressor__learning_rate": [0.1, 0.3, 0.5, 0.7, 1],
        "regressor__max_iter": [100, 200, 300, 500],
        "regressor__min_samples_leaf": [100, 200, 300, 500],
    }

    search = GridSearchCV(
        poisson_gbrt,
        parameters,
        scoring="neg_mean_poisson_deviance",
        cv=10,
        n_jobs=8,
        verbose=1,
    )
    search.fit(
        df_train,
        df_train["Frequency"],
        regressor__sample_weight=df_train["TotalVolume"],
    )

    model = search.best_estimator_
    best_params = search.best_params_

    # Evaluate
    score_estimator(model, df_test)

    return best_params


def fit_final_gbm(df, params, filepath):
    tree_preprocessor = get_preprocessor()

    # Model
    poisson_gbrt = Pipeline(
        [
            ("preprocessor", tree_preprocessor),
            (
                "regressor",
                HistGradientBoostingRegressor(
                    loss="poisson",
                    learning_rate=params["regressor__learning_rate"],
                    max_iter=params["regressor__max_iter"],
                    min_samples_leaf=params["regressor__min_samples_leaf"],
                ),
            ),
        ]
    )

    poisson_gbrt.fit(
        df,
        df["Frequency"],
        regressor__sample_weight=df["TotalVolume"],
    )

    with open(filepath / "freq_model.joblib", "wb") as f:
        joblib.dump(poisson_gbrt, f)
