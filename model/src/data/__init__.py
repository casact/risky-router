import os
import re
from pathlib import Path
from types import MappingProxyType
from typing import List, Mapping

import pandas as pd
import requests
from bs4 import BeautifulSoup
from loguru import logger
from tqdm import tqdm

from src import CONFIG


def download_file(
    url: str, filename: Path, metadata: dict = MappingProxyType({})
) -> None:

    meta = [f"{k}: {v}" for k, v in metadata.items()]

    r = requests.get(url, stream=True)
    if r.ok:
        logger.info(f"Downloading: {url} - {' - '.join(meta)}")

        with open(filename, "wb") as f:
            for chunk in tqdm(r.iter_content(chunk_size=1024 * 8)):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
    else:
        logger.warning(f"Download failed: status code {r.status_code}\n{r.text}")


def traverse_nhtsa_and_download_files(
    start_folder: str,
    save_folder: Path,
    years: List[int] = None,
    overwrite: bool = False,
) -> None:
    url = f"https://www.nhtsa.gov/file-downloads?p={start_folder}"
    years = years or []

    source = requests.get(url).text
    soup = BeautifulSoup(source, "html.parser")

    save_path = save_folder / start_folder
    save_path.mkdir(parents=True, exist_ok=True)

    table = soup.find("table", id="nhtsa_s3")
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        if cells[0].find("img").get("src").split("/")[-1] == "up.png":
            continue
        if re.match(r"^\d{4}\/$", cells[1].find("a").text):
            if (
                len(years) > 0
                and int(re.findall(r"\d+", cells[1].find("a").text)[0]) not in years
            ):
                continue
        if cells[0].find("img").get("src").split("/")[-1] == "dir.png":
            traverse_nhtsa_and_download_files(
                start_folder + cells[1].text,
                save_folder=save_folder,
                years=years,
                overwrite=overwrite,
            )
        if cells[0].find("img").get("src").split("/")[-1] == "file.png":
            file_url = cells[1].find("a").get("href")
            file_name = cells[1].find("a").text

            if os.path.exists(save_path / file_name) and not overwrite:
                logger.warning(f"File {file_name} already exists.")
                continue

            download_file(file_url, save_path / file_name, {"Filesize": cells[2].text})


def encode_categories(encoding: Mapping, reverse: bool = False) -> Mapping:
    if reverse:
        return {v: k for k, v in encoding.items()}
    return encoding


def bin_data(col: pd.Series, bin_config_key: str) -> pd.Series:
    bins = CONFIG["data"][bin_config_key]
    labels = list(bins.keys())
    intervals = [tuple(interval) for interval in bins.values()]

    binned = pd.cut(col, bins=pd.IntervalIndex.from_tuples(intervals, closed="left"))
    binned = binned.cat.rename_categories(labels)

    return binned
