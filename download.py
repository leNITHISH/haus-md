import logging

import requests

import config

log = logging.getLogger(__name__)

CHUNK_SIZE = 1024 * 1024  # 1 MB


def download_file(url, dest_path):
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    total = int(response.headers.get("content-length", 0))
    written = 0
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            f.write(chunk)
            written += len(chunk)
            if total:
                log.info("%s: %d/%d MB", dest_path.name, written // (1024 * 1024), total // (1024 * 1024))


def ensure_data_files(data_dir=config.DATA_DIR):
    """Download any of the raw IMDb .tsv.gz files that aren't already
    present in data_dir, so the pipeline is reproducible from a clean
    clone. Files that already exist are left alone (existence check only
    -- IMDb doesn't publish stable checksums to verify against)."""

    for filename in config.RAW_FILES:
        dest_path = data_dir / filename
        if dest_path.exists():
            log.info("%s already present, skipping download", filename)
            continue
        url = config.IMDB_BASE_URL + filename
        log.info("downloading %s", url)
        download_file(url, dest_path)
