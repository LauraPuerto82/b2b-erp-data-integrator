from b2b_erp_data_integrator.spark.normalization import (
    normalize_country_column,
    normalize_tax_id_column,
)


def test_normalize_country_column(spark_session):
    dataframe = spark_session.createDataFrame(
        [
            ("Spain",),
            ("ES",),
            ("Italy",),
        ],
        ["country"],
    )

    result = dataframe.withColumn(
        "normalized_country",
        normalize_country_column(dataframe["country"]),
    )

    rows = result.select(
        "country",
        "normalized_country",
    ).collect()

    assert [(row.country, row.normalized_country) for row in rows] == [
        ("Spain", "ES"),
        ("ES", "ES"),
        ("Italy", None),
    ]


def test_normalize_tax_id_column(spark_session):
    dataframe = spark_session.createDataFrame(
        [
            (" es-b12 345-678 ", "ES"),
            ("ESB12345678", "ES"),
            ("B12345678", "ES"),
            ("fr 12-34 56", "FR"),
        ],
        ["tax_id", "country"],
    )

    result = dataframe.withColumn(
        "normalized_tax_id",
        normalize_tax_id_column(
            dataframe["tax_id"],
            dataframe["country"],
        ),
    )

    rows = result.select(
        "tax_id",
        "country",
        "normalized_tax_id",
    ).collect()

    assert [row.normalized_tax_id for row in rows] == [
        "B12345678",
        "B12345678",
        "B12345678",
        "123456",
    ]
