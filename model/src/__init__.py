# fmt: off
from pathlib import Path

import tomli

# Paths
ROOT_DIR = Path(__file__).resolve().parents[1]

RAW_DATA_DIR  = ROOT_DIR / "data" / "raw"  # noqa: E221
PROC_DATA_DIR = ROOT_DIR / "data" / "processed"  # noqa: E221

MODELS_DIR    = ROOT_DIR / "models"  # noqa: E221


# Configuration
with open(ROOT_DIR / "config.toml", "rb") as f:
    CONFIG = tomli.load(f)

with open(ROOT_DIR / "references" / "data_schema.toml", "rb") as f:
    DATA_SCHEMA = tomli.load(f)


# Constants
EPSILON = 1e-7

SECONDS_PER_MINUTE   = 60                             # noqa: E221
SECONDS_PER_HOUR     = 60 * SECONDS_PER_MINUTE        # noqa: E221
SECONDS_PER_DAY      = 24 * SECONDS_PER_HOUR          # noqa: E221
SECONDS_PER_WEEK     = 7  * SECONDS_PER_DAY           # noqa: E221

# 1 interval is 5 minutes or 300 seconds
INTERVAL             = 300                            # noqa: E221
INTERVALS_PER_MINUTE = SECONDS_PER_MINUTE / INTERVAL  # noqa: E221
INTERVALS_PER_HOUR   = SECONDS_PER_HOUR   / INTERVAL  # noqa: E221
INTERVALS_PER_DAY    = SECONDS_PER_DAY    / INTERVAL  # noqa: E221
INTERVALS_PER_WEEK   = SECONDS_PER_WEEK   / INTERVAL  # noqa: E221

INTERVALS_PER_TIME_OF_DAY = {
    label: (interval[1] - interval[0]) * INTERVALS_PER_HOUR
    for label, interval in CONFIG["data"]["hour_bins"].items()
}
# fmt: on
