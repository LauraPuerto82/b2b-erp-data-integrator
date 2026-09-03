import json
from collections.abc import Iterable
from pathlib import Path

from b2b_erp_data_integrator.processing.result import RejectedRecord


def write_rejected_jsonl(
    path: Path,
    rejected: Iterable[RejectedRecord],
) -> None:
    with path.open("w", encoding="utf-8") as file:
        for record in rejected:
            data = {
                "raw_record": record.raw_record,
                "reason": record.reason,
            }
            file.write(json.dumps(data) + "\n")
