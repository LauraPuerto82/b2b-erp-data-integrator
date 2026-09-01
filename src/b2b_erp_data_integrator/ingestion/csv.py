import csv
from collections.abc import Iterator
from pathlib import Path


def read_csv(path: Path) -> Iterator[dict]:
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for record in reader:
            yield dict(record)
