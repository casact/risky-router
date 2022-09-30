from pathlib import Path
from typing import List

from src.data import traverse_nhtsa_and_download_files


def download_crss_data(save_folder: Path, years: List[int], overwrite: bool = False):
    """
    Download FARS data from the NHTSA website.
    """
    traverse_nhtsa_and_download_files(
        start_folder="nhtsa/downloads/CRSS/",
        save_folder=save_folder,
        years=years,
        overwrite=overwrite,
    )
