from collections.abc import Callable

from b2b_erp_data_integrator.exceptions import CustomerValidationError

from b2b_erp_data_integrator.models.external_source_customer import (
    ExternalSourceCustomer,
)

from b2b_erp_data_integrator.processing.result import (
    BatchResult,
    RejectedRecord,
)


def process_customers(
    records: list[dict],
    mapper: Callable[[dict], ExternalSourceCustomer],
) -> BatchResult:
    result = BatchResult()

    for record in records:
        try:
            customer = mapper(record)
            result.processed.append(customer)
        except CustomerValidationError as exc:
            result.rejected.append(
                RejectedRecord(
                    raw_record=record,
                    reason=str(exc),
                )
            )

    return result
