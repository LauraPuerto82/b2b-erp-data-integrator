from pathlib import Path

from b2b_erp_data_integrator.integrations.customer_erp_provider import (
    CustomerERPProvider,
)
from b2b_erp_data_integrator.models.identified_canonical_customer import (
    deduplicate_customers,
    identify_customer,
)
from b2b_erp_data_integrator.output import (
    write_processed_parquet,
    write_rejected_jsonl,
)
from b2b_erp_data_integrator.processing.customer_csv import process_customer_csv
from b2b_erp_data_integrator.processing.run import ProcessingRun


def run_customer_pipeline(
    input_path: Path,
    provider: CustomerERPProvider,
    processed_path: Path,
    rejected_path: Path,
) -> ProcessingRun:
    run = process_customer_csv(
        path=input_path,
        provider=provider,
    )

    if run.result is None:
        return run

    identified_customers = (
        identify_customer(external_customer.customer)
        for external_customer in run.result.processed
    )

    unique_customers = deduplicate_customers(identified_customers)

    write_processed_parquet(
        path=processed_path,
        customers=unique_customers,
    )

    write_rejected_jsonl(
        path=rejected_path,
        rejected=run.result.rejected,
    )

    return run
