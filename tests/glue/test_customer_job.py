import pytest

from b2b_erp_data_integrator.glue.customer_job import (
    CustomerJobArguments,
    get_customer_mapping,
    run_customer_job,
)
from b2b_erp_data_integrator.integrations.erp_a.customer import (
    ERP_A_CUSTOMER_MAPPING,
)
from b2b_erp_data_integrator.integrations.erp_b.customer import (
    ERP_B_CUSTOMER_MAPPING,
)
from b2b_erp_data_integrator.integrations.erp_c.customer import (
    ERP_C_CUSTOMER_MAPPING,
)


@pytest.mark.parametrize(
    ("source_system", "expected_mapping"),
    [
        ("ERP_A", ERP_A_CUSTOMER_MAPPING),
        ("ERP_B", ERP_B_CUSTOMER_MAPPING),
        ("ERP_C", ERP_C_CUSTOMER_MAPPING),
    ],
)
def test_get_customer_mapping(
    source_system,
    expected_mapping,
):
    assert get_customer_mapping(source_system) == expected_mapping


def test_get_customer_mapping_rejects_unsupported_source():
    with pytest.raises(ValueError, match="Unsupported source system"):
        get_customer_mapping("ERP_X")


def test_run_customer_job_uses_source_mapping(
    monkeypatch,
    spark_session,
):
    calls = {}

    def fake_run_customer_pipeline(
        spark,
        input_path,
        processed_path,
        rejected_path,
        field_mapping,
    ):
        calls["spark"] = spark
        calls["input_path"] = input_path
        calls["processed_path"] = processed_path
        calls["rejected_path"] = rejected_path
        calls["field_mapping"] = field_mapping

    monkeypatch.setattr(
        "b2b_erp_data_integrator.glue.customer_job.run_customer_pipeline",
        fake_run_customer_pipeline,
    )

    arguments = CustomerJobArguments(
        source_system="ERP_B",
        input_path="s3://bucket/raw/customers.csv",
        processed_path="s3://bucket/processed/customers/",
        rejected_path="s3://bucket/rejected/customers/",
    )

    run_customer_job(
        spark=spark_session,
        arguments=arguments,
    )

    assert calls["spark"] is spark_session
    assert calls["input_path"] == "s3://bucket/raw/customers.csv"
    assert calls["processed_path"] == "s3://bucket/processed/customers/"
    assert calls["rejected_path"] == "s3://bucket/rejected/customers/"
    assert calls["field_mapping"] == ERP_B_CUSTOMER_MAPPING
