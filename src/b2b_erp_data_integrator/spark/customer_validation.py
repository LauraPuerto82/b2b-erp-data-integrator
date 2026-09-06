from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from b2b_erp_data_integrator.spark.validation import (
    validate_tax_id_column,
)


def split_valid_customers(
    dataframe: DataFrame,
) -> tuple[DataFrame, DataFrame]:
    is_valid = validate_tax_id_column(
        dataframe["tax_id"],
        dataframe["country"],
    )

    processed = dataframe.filter(is_valid)
    rejected = dataframe.filter(~is_valid).withColumn(
        "reason",
        F.lit("Invalid tax ID"),
    )

    return processed, rejected
