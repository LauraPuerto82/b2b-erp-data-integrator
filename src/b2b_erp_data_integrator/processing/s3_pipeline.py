from pathlib import Path

from b2b_erp_data_integrator.integrations.customer_erp_provider import (
    CustomerERPProvider,
)
from b2b_erp_data_integrator.processing.pipeline import run_customer_pipeline
from b2b_erp_data_integrator.processing.run import ProcessingRun
from b2b_erp_data_integrator.storage import read_s3_object, write_s3_object


def run_customer_s3_pipeline(
    client,
    bucket: str,
    input_key: str,
    processed_key: str,
    rejected_key: str,
    provider: CustomerERPProvider,
    temp_dir: Path,
) -> ProcessingRun:
    input_path = temp_dir / "input.csv"
    processed_path = temp_dir / "processed.parquet"
    rejected_path = temp_dir / "rejected.jsonl"

    input_content = read_s3_object(
        client=client,
        bucket=bucket,
        key=input_key,
    )

    input_path.write_bytes(input_content)

    run = run_customer_pipeline(
        input_path=input_path,
        provider=provider,
        processed_path=processed_path,
        rejected_path=rejected_path,
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
