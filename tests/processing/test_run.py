from datetime import UTC, datetime

from b2b_erp_data_integrator.processing.result import BatchResult
from b2b_erp_data_integrator.processing.run import (
    ProcessingRun,
    ProcessingRunStatus,
)


def test_processing_run_statuses():
    assert ProcessingRunStatus.RUNNING == "RUNNING"
    assert ProcessingRunStatus.COMPLETED == "COMPLETED"
    assert ProcessingRunStatus.FAILED == "FAILED"


def test_processing_run_can_be_running():
    started_at = datetime.now(UTC)

    run = ProcessingRun(
        source_system="ERP_B",
        input_source="customers.csv",
        started_at=started_at,
        status=ProcessingRunStatus.RUNNING,
    )

    assert run.source_system == "ERP_B"
    assert run.input_source == "customers.csv"
    assert run.started_at == started_at
    assert run.finished_at is None
    assert run.result is None
    assert run.error is None


def test_processing_run_can_be_completed():
    started_at = datetime.now(UTC)
    finished_at = datetime.now(UTC)
    result = BatchResult()

    run = ProcessingRun(
        source_system="ERP_B",
        input_source="customers.csv",
        started_at=started_at,
        finished_at=finished_at,
        status=ProcessingRunStatus.COMPLETED,
        result=result,
    )

    assert run.status == ProcessingRunStatus.COMPLETED
    assert run.finished_at == finished_at
    assert run.result is result
    assert run.error is None


def test_processing_run_can_be_failed():
    started_at = datetime.now(UTC)
    finished_at = datetime.now(UTC)

    run = ProcessingRun(
        source_system="ERP_B",
        input_source="customers.csv",
        started_at=started_at,
        finished_at=finished_at,
        status=ProcessingRunStatus.FAILED,
        error="Missing required fields: vat_number",
    )

    assert run.status == ProcessingRunStatus.FAILED
    assert run.finished_at == finished_at
    assert run.result is None
    assert run.error == "Missing required fields: vat_number"
