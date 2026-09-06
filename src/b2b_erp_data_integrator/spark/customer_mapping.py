from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def map_customer_columns(
    dataframe: DataFrame,
    field_mapping: dict[str, str],
) -> DataFrame:
    return dataframe.select(
        *[
            F.col(source_field).alias(canonical_field)
            for canonical_field, source_field in field_mapping.items()
        ]
    )
