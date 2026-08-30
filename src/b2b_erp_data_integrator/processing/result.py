from dataclasses import dataclass, field

from b2b_erp_data_integrator.models.external_source_customer import (
    ExternalSourceCustomer,
)


@dataclass
class RejectedRecord:
    raw_record: dict
    reason: str


@dataclass
class BatchResult:
    processed: list[ExternalSourceCustomer] = field(default_factory=list)
    rejected: list[RejectedRecord] = field(default_factory=list)
