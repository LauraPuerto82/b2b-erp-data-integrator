from pyspark.sql import DataFrame

from b2b_erp_data_integrator.spark.customer_mapping import (
    map_customer_columns,
)
from b2b_erp_data_integrator.spark.normalization import (
    normalize_country_column,
    normalize_tax_id_column,
)


def transform_customer_dataframe(
    dataframe: DataFrame,
    field_mapping: dict[str, str],
) -> DataFrame:
    mapped = map_customer_columns(
        dataframe=dataframe,
        field_mapping=field_mapping,
    )

    with_normalized_country = mapped.withColumn(
        "country",
        normalize_country_column(mapped["country"]),
    )

    return with_normalized_country.withColumn(
        "tax_id",
        normalize_tax_id_column(
            with_normalized_country["tax_id"],
            with_normalized_country["country"],
        ),
    )
