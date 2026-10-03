.PHONY: setup run test clean

setup:
	python3 -m venv venv
	venv/bin/pip install -r requirements.txt

run:
	venv/bin/python3 pipeline.py

test:
	venv/bin/pytest -q

clean:
	rm -f haus.duckdb
	rm -f output/*.png output/*.parquet
