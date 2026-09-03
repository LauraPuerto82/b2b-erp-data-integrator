import json
from pathlib import Path

from b2b_erp_data_integrator.output.rejected_jsonl import write_rejected_jsonl
from b2b_erp_data_integrator.processing.result import RejectedRecord


def test_write_rejected_jsonl_writes_rejected_record(tmp_path: Path):
    output_path = tmp_path / "rejected.jsonl"

    rejected = [
        RejectedRecord(
            raw_record={
                "client_code": "0002",
                "legal_name": "Globex S.L.",
                "vat_number": "INVALID",
                "country": "Spain",
                "contact_email": "info@globex.es",
            },
            reason="Invalid Spanish tax ID",
        )
    ]

    write_rejected_jsonl(
        path=output_path,
        rejected=rejected,
    )

    lines = output_path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 1

    data = json.loads(lines[0])

    assert data == {
        "raw_record": {
            "client_code": "0002",
            "legal_name": "Globex S.L.",
            "vat_number": "INVALID",
            "country": "Spain",
            "contact_email": "info@globex.es",
        },
        "reason": "Invalid Spanish tax ID",
    }


def test_write_rejected_jsonl_writes_one_line_per_record(tmp_path: Path):
    output_path = tmp_path / "rejected.jsonl"

    rejected = [
        RejectedRecord(
            raw_record={"client_code": "0002"},
            reason="Invalid tax ID",
        ),
        RejectedRecord(
            raw_record={"client_code": "0003"},
            reason="Unsupported country",
        ),
    ]

    write_rejected_jsonl(
        path=output_path,
        rejected=rejected,
    )

    lines = output_path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 2

    first = json.loads(lines[0])
    second = json.loads(lines[1])

    assert first["raw_record"]["client_code"] == "0002"
    assert first["reason"] == "Invalid tax ID"

    assert second["raw_record"]["client_code"] == "0003"
    assert second["reason"] == "Unsupported country"
