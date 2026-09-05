from io import TextIOWrapper
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
from b2b_erp_data_integrator.processing.customer_csv import (
    process_customer_stream,
)
from b2b_erp_data_integrator.processing.run import ProcessingRun
from b2b_erp_data_integrator.storage import (
    stream_s3_object,
    write_s3_object,
)


def run_customer_s3_pipeline(
    client,
    bucket: str,
    input_key: str,
    processed_key: str,
    rejected_key: str,
    provider: CustomerERPProvider,
    temp_dir: Path,
) -> ProcessingRun:
    processed_path = temp_dir / "processed.parquet"
    rejected_path = temp_dir / "rejected.jsonl"

    body = stream_s3_object(
        client=client,
        bucket=bucket,
        key=input_key,
    )

    with TextIOWrapper(body, encoding="utf-8", newline="") as stream:
        run = process_customer_stream(
            stream=stream,
            provider=provider,
            input_source=f"s3://{bucket}/{input_key}",
        )

    if run.result is not None:
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

    if processed_path.exists():
        write_s3_object(
            client=client,
            bucket=bucket,
            key=processed_key,
            content=processed_path.read_bytes(),
        )

    if rejected_path.exists():
        write_s3_object(
            client=client,
            bucket=bucket,
            key=rejected_key,
            content=rejected_path.read_bytes(),
        )

    return run
