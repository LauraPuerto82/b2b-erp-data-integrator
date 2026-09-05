from pathlib import Path

import pyarrow.parquet as pq  # type: ignore[import-untyped]

from b2b_erp_data_integrator.integrations.erp_a.customer import (
    ERP_A_CUSTOMER_PROVIDER,
)
from b2b_erp_data_integrator.processing.pipeline import run_customer_pipeline
from b2b_erp_data_integrator.processing.run import ProcessingRunStatus


def test_run_customer_pipeline_writes_processed_parquet(tmp_path: Path):
    input_path = tmp_path / "customers.csv"
    processed_path = tmp_path / "processed.parquet"
    rejected_path = tmp_path / "rejected.jsonl"

    input_path.write_text(
        "customer_id,name,tax_id,country,email\n"
        "C001,ACME S.L.,B12345678,ES,info@acme.es\n",
        encoding="utf-8",
    )

    run_customer_pipeline(
        input_path=input_path,
        provider=ERP_A_CUSTOMER_PROVIDER,
        processed_path=processed_path,
        rejected_path=rejected_path,
    )

    assert processed_path.exists()

    table = pq.read_table(processed_path)

    assert table.num_rows == 1
    assert table.column("name").to_pylist() == ["ACME S.L."]


def test_run_customer_pipeline_writes_rejected_jsonl(tmp_path: Path):
    input_path = tmp_path / "customers.csv"
    processed_path = tmp_path / "processed.parquet"
    rejected_path = tmp_path / "rejected.jsonl"

    input_path.write_text(
        "customer_id,name,tax_id,country,email\n"
        "C001,ACME S.L.,B12345678,ES,info@acme.es\n"
        "C002,Globex S.L.,INVALID,ES,info@globex.es\n",
        encoding="utf-8",
    )

    run_customer_pipeline(
        input_path=input_path,
        provider=ERP_A_CUSTOMER_PROVIDER,
        processed_path=processed_path,
        rejected_path=rejected_path,
    )

    assert rejected_path.exists()

    lines = rejected_path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 1


def test_run_customer_pipeline_does_not_write_outputs_when_run_fails(
    tmp_path: Path,
):
    input_path = tmp_path / "customers.csv"
    processed_path = tmp_path / "processed.parquet"
    rejected_path = tmp_path / "rejected.jsonl"

    input_path.write_text(
        "customer_id,name,country,email\nC001,ACME S.L.,ES,info@acme.es\n",
        encoding="utf-8",
    )

    run = run_customer_pipeline(
        input_path=input_path,
        provider=ERP_A_CUSTOMER_PROVIDER,
        processed_path=processed_path,
        rejected_path=rejected_path,
    )

    assert run.status == ProcessingRunStatus.FAILED
    assert not processed_path.exists()
    assert not rejected_path.exists()


def test_run_customer_pipeline_deduplicates_processed_customers(
    tmp_path: Path,
):
    input_path = tmp_path / "customers.csv"
    processed_path = tmp_path / "processed.parquet"
    rejected_path = tmp_path / "rejected.jsonl"

    input_path.write_text(
        "customer_id,name,tax_id,country,email\n"
        "C001,ACME S.L.,B12345678,ES,info@acme.es\n"
        "C002,ACME Sociedad Limitada,B12345678,ES,contact@acme.es\n",
        encoding="utf-8",
    )

    run_customer_pipeline(
        input_path=input_path,
        provider=ERP_A_CUSTOMER_PROVIDER,
        processed_path=processed_path,
        rejected_path=rejected_path,
    )

    table = pq.read_table(processed_path)

    assert table.num_rows == 1
    assert table.column("name").to_pylist() == ["ACME S.L."]
