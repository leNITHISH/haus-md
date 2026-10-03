import logging

import config

log = logging.getLogger(__name__)

TABLES = ["house_full", "house_rolling"]


def export_table(con, table, out_path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    con.sql(f"COPY {table} TO '{out_path}' (FORMAT PARQUET)")
    log.info("wrote %s", out_path)
    return out_path


def export_all(con, out_dir=None):
    out_dir = out_dir or config.OUTPUT_DIR
    return [export_table(con, table, out_dir / f"{table}.parquet") for table in TABLES]
