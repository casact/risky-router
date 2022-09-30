import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from imblearn.ensemble import BalancedRandomForestClassifier

from src import CONFIG, PROC_DATA_DIR


def load_modelling_data():
    X = pd.read_feather(PROC_DATA_DIR / "accident.f")

    X = X[
        [
            "HourofData",
            "Weather",
            "BodyType",
            "VehicleYear",
            "Alcohol",
            "RelativeSpeed",
            "MaximumSeverity",
        ]
    ]

    X.BodyType = np.where(X.BodyType == "FOUR_WHEEL_VEHICLE", 1, 0)
    X.Alcohol = np.where(X.Alcohol == "NO_ALCOHOL_INVOLVED", 0, 1)

    return X


def get_preprocessor():
    vehicle_year_labels = list(CONFIG["data"]["vehicle_year_bins"].keys())
    # Preprocessor
    weather_encoder = OneHotEncoder(sparse=False)
    vehicle_year_encoder = OrdinalEncoder(categories=[vehicle_year_labels])

    preprocessor = make_column_transformer(
        (weather_encoder, ["Weather"]),
        (vehicle_year_encoder, ["VehicleYear"]),
        remainder="passthrough",
        n_jobs=1,
    )
    return preprocessor


def fit_final_model(df, filepath):
    preprocessor = get_preprocessor()

    X = df.drop(columns=["MaximumSeverity"]).copy()
    y = df["MaximumSeverity"].astype(str).copy()
    y[y != "NONE_TO_MINOR_INJURY"] = 1
    y[y == "NONE_TO_MINOR_INJURY"] = 0
    y = pd.to_numeric(y, downcast="integer")

    # Model
    rf_clf = make_pipeline(
        preprocessor,
        BalancedRandomForestClassifier(random_state=42, n_jobs=-1),
    )
    rf_clf.fit(X, y)

    with open(filepath / "sev_model.joblib", "wb") as f:
        joblib.dump(rf_clf, f, compress=("xz", 1))
