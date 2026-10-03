import argparse
import logging
import sys

import duckdb

import analyze
import config
import download
import ingest
import transform
import validate
import visualize

log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Build and analyze the House, M.D. ratings warehouse.")
    parser.add_argument("--verbose", action="store_true", help="enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    download.ensure_data_files()

    con = duckdb.connect(str(config.DB_PATH))
    ingest.load_raw_tables(con)
    transform.build_house_full(con)
    transform.build_house_rolling(con)

    try:
        validate.run_all(con)
    except validate.ValidationError as e:
        log.error("data quality validation failed: %s", e)
        sys.exit(1)

    analyze.run_all(con)
    plot_path = visualize.plot_rolling_average(con)

    row_counts = {
        table: con.sql(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("house_basics", "house_episodes", "house_ratings", "house_full")
    }
    log.info("pipeline complete — row counts: %s, plot written to %s", row_counts, plot_path)


if __name__ == "__main__":
    main()
