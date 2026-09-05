import pyarrow.parquet as pq  # type: ignore[import-untyped]
import pytest
from botocore.exceptions import ClientError  # type: ignore[import-untyped]

from b2b_erp_data_integrator.integrations.erp_a.customer import (
    ERP_A_CUSTOMER_PROVIDER,
)
from b2b_erp_data_integrator.processing.run import ProcessingRunStatus
from b2b_erp_data_integrator.processing.s3_pipeline import run_customer_s3_pipeline
from b2b_erp_data_integrator.storage import read_s3_object, write_s3_object


def test_run_customer_s3_pipeline_writes_processed_parquet(
    tmp_path,
    s3_client,
    s3_bucket,
):
    input_key = "input/erp-a/customers.csv"
    processed_key = "processed/customers.parquet"
    rejected_key = "rejected/customers.jsonl"

    write_s3_object(
        client=s3_client,
        bucket=s3_bucket,
        key=input_key,
        content=(
            b"customer_id,name,tax_id,country,email\n"
            b"C001,ACME S.L.,B12345678,ES,info@acme.es\n"
        ),
    )

    run_customer_s3_pipeline(
        client=s3_client,
        bucket=s3_bucket,
        input_key=input_key,
        processed_key=processed_key,
        rejected_key=rejected_key,
        provider=ERP_A_CUSTOMER_PROVIDER,
        temp_dir=tmp_path,
    )

    parquet_content = read_s3_object(
        client=s3_client,
        bucket=s3_bucket,
        key=processed_key,
    )

    parquet_path = tmp_path / "result.parquet"
    parquet_path.write_bytes(parquet_content)

    table = pq.read_table(parquet_path)

    assert table.num_rows == 1
    assert table.column("name").to_pylist() == ["ACME S.L."]
    assert not (tmp_path / "input.csv").exists()


def test_run_customer_s3_pipeline_writes_rejected_jsonl(
    tmp_path,
    s3_client,
    s3_bucket,
):

    input_key = "input/erp-a/customers-with-rejected.csv"
    processed_key = "processed/customers-with-rejected.parquet"
    rejected_key = "rejected/customers-with-rejected.jsonl"

    write_s3_object(
        client=s3_client,
        bucket=s3_bucket,
        key=input_key,
        content=(
            b"customer_id,name,tax_id,country,email\n"
            b"C001,ACME S.L.,B12345678,ES,info@acme.es\n"
            b"C002,Globex S.L.,INVALID,ES,info@globex.es\n"
        ),
    )

    run_customer_s3_pipeline(
        client=s3_client,
        bucket=s3_bucket,
        input_key=input_key,
        processed_key=processed_key,
        rejected_key=rejected_key,
        provider=ERP_A_CUSTOMER_PROVIDER,
        temp_dir=tmp_path,
    )

    rejected_content = read_s3_object(
        client=s3_client,
        bucket=s3_bucket,
        key=rejected_key,
    )

    lines = rejected_content.decode("utf-8").splitlines()

    assert len(lines) == 1


def test_run_customer_s3_pipeline_does_not_write_outputs_when_run_fails(
    tmp_path,
    s3_client,
    s3_bucket,
):

    input_key = "input/erp-a/invalid-structure.csv"
    processed_key = "processed/invalid-structure.parquet"
    rejected_key = "rejected/invalid-structure.jsonl"

    write_s3_object(
        client=s3_client,
        bucket=s3_bucket,
        key=input_key,
        content=(b"customer_id,name,country,email\nC001,ACME S.L.,ES,info@acme.es\n"),
    )

    run = run_customer_s3_pipeline(
        client=s3_client,
        bucket=s3_bucket,
        input_key=input_key,
        processed_key=processed_key,
        rejected_key=rejected_key,
        provider=ERP_A_CUSTOMER_PROVIDER,
        temp_dir=tmp_path,
    )

    assert run.status == ProcessingRunStatus.FAILED

    with pytest.raises(ClientError):
        s3_client.head_object(
            Bucket=s3_bucket,
            Key=processed_key,
        )

    with pytest.raises(ClientError):
        s3_client.head_object(
            Bucket=s3_bucket,
            Key=rejected_key,
        )
