from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from b2b_erp_data_integrator.exceptions import IngestionError
from b2b_erp_data_integrator.ingestion import (
    read_csv_stream_with_fields,
)
from b2b_erp_data_integrator.integrations.customer_erp_provider import (
    CustomerERPProvider,
)
from b2b_erp_data_integrator.mapping.customer import get_required_customer_source_fields
from b2b_erp_data_integrator.processing.customer import process_customers
from b2b_erp_data_integrator.processing.run import (
    ProcessingRun,
    ProcessingRunStatus,
)
from b2b_erp_data_integrator.validation.dataset import validate_required_fields


def process_customer_stream(
    stream: TextIO,
    provider: CustomerERPProvider,
    input_source: str,
) -> ProcessingRun:
    started_at = datetime.now(UTC)

    try:
        available_fields, records = read_csv_stream_with_fields(stream)

        required_fields = get_required_customer_source_fields(provider.field_mapping)

        validate_required_fields(
            available_fields=available_fields,
            required_fields=required_fields,
        )

        result = process_customers(
            records=records,
            mapper=provider.mapper,
        )

        return ProcessingRun(
            source_system=provider.source_system,
            input_source=input_source,
            started_at=started_at,
            finished_at=datetime.now(UTC),
            status=ProcessingRunStatus.COMPLETED,
            result=result,
        )

    except IngestionError as error:
        return ProcessingRun(
            source_system=provider.source_system,
            input_source=input_source,
            started_at=started_at,
            finished_at=datetime.now(UTC),
            status=ProcessingRunStatus.FAILED,
            error=str(error),
        )


def process_customer_csv(
    path: Path,
    provider: CustomerERPProvider,
) -> ProcessingRun:
    with path.open(encoding="utf-8", newline="") as stream:
        return process_customer_stream(
            stream=stream,
            provider=provider,
            input_source=str(path),
        )
