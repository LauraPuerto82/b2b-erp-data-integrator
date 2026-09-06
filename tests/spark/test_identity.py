from b2b_erp_data_integrator.models.customer import CanonicalCustomer
from b2b_erp_data_integrator.models.identified_canonical_customer import (
    generate_customer_id,
)
from b2b_erp_data_integrator.spark.identity import (
    deduplicate_customers,
    identify_customers,
)


def test_identify_customers_uses_same_identity_as_python(spark_session):
    dataframe = spark_session.createDataFrame(
        [
            (
                "C001",
                "ACME S.L.",
                "B12345678",
                "ES",
                "info@acme.es",
            ),
        ],
        [
            "external_id",
            "name",
            "tax_id",
            "country",
            "email",
        ],
    )

    result = identify_customers(dataframe)

    row = result.first()

    assert row is not None

    customer = CanonicalCustomer(
        name="ACME S.L.",
        tax_id="B12345678",
        country="ES",
        email="info@acme.es",
    )
    expected_customer_id = generate_customer_id(customer)

    assert row.customer_id == str(expected_customer_id)


def test_deduplicate_customers_by_customer_id(spark_session):
    dataframe = spark_session.createDataFrame(
        [
            (
                "C001",
                "ACME S.L.",
                "B12345678",
                "ES",
                "info@acme.es",
            ),
            (
                "C002",
                "ACME Sociedad Limitada",
                "B12345678",
                "ES",
                "contact@acme.es",
            ),
        ],
        [
            "external_id",
            "name",
            "tax_id",
            "country",
            "email",
        ],
    )

    identified = identify_customers(dataframe)
    deduplicated = deduplicate_customers(identified)

    rows = deduplicated.collect()

    assert len(rows) == 1
