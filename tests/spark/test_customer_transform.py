from b2b_erp_data_integrator.integrations.erp_b.customer import (
    ERP_B_CUSTOMER_MAPPING,
)
from b2b_erp_data_integrator.spark.customer_transform import (
    transform_customer_dataframe,
)


def test_transform_customer_dataframe(spark_session):
    dataframe = spark_session.createDataFrame(
        [
            (
                "C001",
                "ACME S.L.",
                " es-b12 345-678 ",
                "Spain",
                "info@acme.es",
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

    result = transform_customer_dataframe(
        dataframe=dataframe,
        field_mapping=ERP_B_CUSTOMER_MAPPING,
    )

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
