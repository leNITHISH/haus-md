import duckdb

import export
import transform


def test_export_all_writes_parquet_with_matching_row_counts(clean_con, tmp_path):
    transform.build_house_full(clean_con)
    transform.build_house_rolling(clean_con)

    paths = export.export_all(clean_con, out_dir=tmp_path)

    assert {p.name for p in paths} == {"house_full.parquet", "house_rolling.parquet"}
    for path in paths:
        assert path.exists()
        count = duckdb.sql(f"SELECT COUNT(*) FROM read_parquet('{path}')").fetchone()[0]
        assert count == 6
