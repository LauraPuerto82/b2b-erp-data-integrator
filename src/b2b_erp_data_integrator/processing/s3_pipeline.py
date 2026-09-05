from io import TextIOWrapper
from pathlib import Path

from b2b_erp_data_integrator.integrations.customer_erp_provider import (
    CustomerERPProvider,
)
from b2b_erp_data_integrator.processing.customer_csv import (
    process_customer_stream,
)
from b2b_erp_data_integrator.processing.pipeline import write_processing_outputs
from b2b_erp_data_integrator.processing.run import ProcessingRun
from b2b_erp_data_integrator.storage import (
    stream_s3_object,
    upload_s3_file,
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

    write_processing_outputs(
        run=run,
        processed_path=processed_path,
        rejected_path=rejected_path,
    )

    if processed_path.exists():
        upload_s3_file(
            client=client,
            bucket=bucket,
            key=processed_key,
            path=processed_path,
        )

    if rejected_path.exists():
        upload_s3_file(
            client=client,
            bucket=bucket,
            key=rejected_key,
            path=rejected_path,
        )

    return run
