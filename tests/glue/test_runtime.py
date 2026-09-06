from b2b_erp_data_integrator.glue.customer_job import CustomerJobArguments
from b2b_erp_data_integrator.glue.runtime import build_customer_job_arguments


def test_build_customer_job_arguments():
    resolved_options = {
        "source_system": "ERP_B",
        "input_path": "s3://bucket/raw/customers.csv",
        "processed_path": "s3://bucket/processed/customers/",
        "rejected_path": "s3://bucket/rejected/customers/",
    }

    result = build_customer_job_arguments(resolved_options)

    assert result == CustomerJobArguments(
        source_system="ERP_B",
        input_path="s3://bucket/raw/customers.csv",
        processed_path="s3://bucket/processed/customers/",
        rejected_path="s3://bucket/rejected/customers/",
    )
