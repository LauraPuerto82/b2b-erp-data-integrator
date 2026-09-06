import sys

import pytest

from b2b_erp_data_integrator.spark.output import write_processed_parquet


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Spark local Parquet writes require Hadoop winutils on Windows",
)
def test_write_processed_parquet(tmp_path, spark_session):
    dataframe = spark_session.createDataFrame(
        [
            ("C001", "ACME S.L.", "B12345678", "ES", "info@acme.es"),
        ],
        [
            "external_id",
            "name",
            "tax_id",
            "country",
            "email",
        ],
    )

    output_path = tmp_path / "processed"

    write_processed_parquet(
        dataframe=dataframe,
        path=str(output_path),
    )

    result = spark_session.read.parquet(str(output_path))
    row = result.first()

    assert row is not None
    assert result.columns == [
        "external_id",
        "name",
        "tax_id",
        "country",
        "email",
    ]
    assert row.external_id == "C001"
    assert row.name == "ACME S.L."
    assert row.tax_id == "B12345678"
    assert row.country == "ES"
    assert row.email == "info@acme.es"
