import csv
from collections.abc import Iterator
from pathlib import Path
from typing import TextIO


def read_csv(path: Path) -> Iterator[dict]:
    with path.open(encoding="utf-8", newline="") as file:
        yield from read_csv_stream(file)


def read_csv_fields(path: Path) -> set[str]:
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        return set(reader.fieldnames or [])


def read_csv_stream(stream: TextIO) -> Iterator[dict]:
    reader = csv.DictReader(stream)

    for record in reader:
        yield dict(record)


def read_csv_stream_with_fields(
    stream: TextIO,
) -> tuple[set[str], Iterator[dict]]:
    reader = csv.DictReader(stream)

    fields = set(reader.fieldnames or [])

    def iter_records() -> Iterator[dict]:
        for record in reader:
            yield dict(record)

    return fields, iter_records()
