from b2b_erp_data_integrator.spark.validation import (
    validate_tax_id_column,
)


def test_validate_tax_id_column(spark_session):
    dataframe = spark_session.createDataFrame(
        [
            ("B12345678", "ES"),
            ("B1234", "ES"),
            ("123456", "FR"),
        ],
        ["tax_id", "country"],
    )

    result = dataframe.withColumn(
        "is_valid",
        validate_tax_id_column(
            dataframe["tax_id"],
            dataframe["country"],
        ),
    )

    rows = result.select(
        "tax_id",
        "country",
        "is_valid",
    ).collect()

    assert [row.is_valid for row in rows] == [
        True,
        False,
        True,
    ]
