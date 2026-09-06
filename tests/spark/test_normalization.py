from b2b_erp_data_integrator.spark.normalization import (
    normalize_country_column,
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
