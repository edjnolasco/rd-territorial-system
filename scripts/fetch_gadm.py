from __future__ import annotations

from pathlib import Path
import requests

from rd_territorial_system.config import GADM_ADM1_ZIP, GADM_ADM2_ZIP
from rd_territorial_system.sources import GADM_DOM_ADM1_URL, GADM_DOM_ADM2_URL


def _download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    target.write_bytes(response.content)
    print(f"Downloaded: {target}")


if __name__ == "__main__":
    _download(GADM_DOM_ADM1_URL, GADM_ADM1_ZIP)
    _download(GADM_DOM_ADM2_URL, GADM_ADM2_ZIP)
