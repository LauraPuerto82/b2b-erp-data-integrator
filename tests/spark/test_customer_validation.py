from b2b_erp_data_integrator.spark.customer_validation import (
    split_valid_customers,
)


def test_split_valid_customers(spark_session):
    dataframe = spark_session.createDataFrame(
        [
            ("C001", "ACME S.L.", "B12345678", "ES", "info@acme.es"),
            ("C002", "Globex S.L.", "B1234", "ES", "info@globex.es"),
            ("C003", "Dupont SARL", "123456", "FR", "info@dupont.fr"),
        ],
        [
            "external_id",
            "name",
            "tax_id",
            "country",
            "email",
        ],
    )

    processed, rejected = split_valid_customers(dataframe)

    processed_ids = [
        row.external_id for row in processed.select("external_id").collect()
    ]
    rejected_ids = [row.external_id for row in rejected.select("external_id").collect()]

    assert processed_ids == ["C001", "C003"]
    assert rejected_ids == ["C002"]
