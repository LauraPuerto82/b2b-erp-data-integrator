from datetime import UTC, datetime
from pathlib import Path

from b2b_erp_data_integrator.exceptions import IngestionError
from b2b_erp_data_integrator.ingestion import read_csv, read_csv_fields
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


def process_customer_csv(
    path: Path,
    provider: CustomerERPProvider,
) -> ProcessingRun:
    started_at = datetime.now(UTC)

    try:
        available_fields = read_csv_fields(path)

        required_fields = get_required_customer_source_fields(provider.field_mapping)

        validate_required_fields(
            available_fields=available_fields,
            required_fields=required_fields,
        )

        records = read_csv(path)

        result = process_customers(
            records=records,
            mapper=provider.mapper,
        )

        return ProcessingRun(
            source_system=provider.source_system,
            input_source=str(path),
            started_at=started_at,
            finished_at=datetime.now(UTC),
            status=ProcessingRunStatus.COMPLETED,
            result=result,
        )
    except IngestionError as error:
        return ProcessingRun(
            source_system=provider.source_system,
            input_source=str(path),
            started_at=started_at,
            finished_at=datetime.now(UTC),
            status=ProcessingRunStatus.FAILED,
            error=str(error),
        )
