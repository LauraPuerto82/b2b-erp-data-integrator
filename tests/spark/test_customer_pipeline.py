from b2b_erp_data_integrator.integrations.erp_b.customer import (
    ERP_B_CUSTOMER_MAPPING,
)
from b2b_erp_data_integrator.spark.customer_pipeline import (
    process_customer_dataframe,
)


def test_process_customer_dataframe(spark_session):
    dataframe = spark_session.createDataFrame(
        [
            (
                "C001",
                "ACME S.L.",
                " es-b12 345-678 ",
                "Spain",
                "info@acme.es",
            ),
            (
                "C002",
                "Globex S.L.",
                " es-b1234 ",
                "Spain",
                "info@globex.es",
            ),
        ],
        [
            "client_code",
            "legal_name",
            "vat_number",
            "country",
            "contact_email",
        ],
    )

    processed, rejected = process_customer_dataframe(
        dataframe=dataframe,
        field_mapping=ERP_B_CUSTOMER_MAPPING,
    )

    processed_row = processed.first()
    rejected_row = rejected.first()

    assert processed_row is not None
    assert rejected_row is not None

    assert processed_row.external_id == "C001"
    assert processed_row.tax_id == "B12345678"
    assert processed_row.country == "ES"

    assert rejected_row.external_id == "C002"
    assert rejected_row.tax_id == "B1234"
    assert rejected_row.country == "ES"
    assert rejected_row.reason == "Invalid tax ID"
