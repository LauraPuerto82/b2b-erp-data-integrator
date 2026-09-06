from pyspark.sql import DataFrame, SparkSession

from b2b_erp_data_integrator.spark.customer_pipeline import (
    process_customer_dataframe,
)
from b2b_erp_data_integrator.spark.ingestion import read_csv_dataframe


def process_customer_csv_dataframe(
    spark: SparkSession,
    path: str,
    field_mapping: dict[str, str],
) -> tuple[DataFrame, DataFrame]:
    dataframe = read_csv_dataframe(
        spark=spark,
        path=path,
    )

    return process_customer_dataframe(
        dataframe=dataframe,
        field_mapping=field_mapping,
    )
