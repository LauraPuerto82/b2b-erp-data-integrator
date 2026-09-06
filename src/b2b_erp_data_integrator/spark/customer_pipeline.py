from pyspark.sql import DataFrame

from b2b_erp_data_integrator.spark.customer_transform import (
    transform_customer_dataframe,
)
from b2b_erp_data_integrator.spark.customer_validation import split_valid_customers


def process_customer_dataframe(
    dataframe: DataFrame,
    field_mapping: dict[str, str],
) -> tuple[DataFrame, DataFrame]:
    transformed = transform_customer_dataframe(
        dataframe=dataframe,
        field_mapping=field_mapping,
    )

    return split_valid_customers(transformed)
