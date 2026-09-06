import sys

import pytest

from b2b_erp_data_integrator.integrations.erp_b.customer import (
    ERP_B_CUSTOMER_MAPPING,
)
from b2b_erp_data_integrator.spark.run import run_customer_pipeline


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Spark local output writes require Hadoop winutils on Windows",
)
def test_run_customer_pipeline(tmp_path, spark_session):
    input_path = tmp_path / "customers.csv"
    processed_path = tmp_path / "processed"
    rejected_path = tmp_path / "rejected"

    input_path.write_text(
        "client_code,legal_name,vat_number,country,contact_email\n"
        "C001,ACME S.L., es-b12 345-678 ,Spain,info@acme.es\n"
        "C002,ACME Sociedad Limitada,ESB12345678,Spain,contact@acme.es\n"
        "C003,Globex S.L., es-b1234 ,Spain,info@globex.es\n",
        encoding="utf-8",
    )

    run_customer_pipeline(
        spark=spark_session,
        input_path=str(input_path),
        processed_path=str(processed_path),
        rejected_path=str(rejected_path),
        field_mapping=ERP_B_CUSTOMER_MAPPING,
    )

    processed = spark_session.read.parquet(str(processed_path))
    rejected = spark_session.read.json(str(rejected_path))

    processed_rows = processed.collect()
    rejected_rows = rejected.collect()

    assert len(processed_rows) == 1
    assert len(rejected_rows) == 1

    processed_row = processed_rows[0]
    rejected_row = rejected_rows[0]

    assert processed_row.customer_id is not None
    assert processed_row.tax_id == "B12345678"
    assert processed_row.country == "ES"

    assert rejected_row.external_id == "C003"
    assert rejected_row.tax_id == "B1234"
    assert rejected_row.country == "ES"
    assert rejected_row.reason == "Invalid tax ID"
