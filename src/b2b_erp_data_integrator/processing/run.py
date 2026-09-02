from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from b2b_erp_data_integrator.processing.result import BatchResult


class ProcessingRunStatus(StrEnum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class ProcessingRun:
    source_system: str
    input_source: str
    started_at: datetime
    status: ProcessingRunStatus
    finished_at: datetime | None = None
    result: BatchResult | None = None
    error: str | None = None
