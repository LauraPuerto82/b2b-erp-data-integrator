from pyspark.sql import SparkSession

from b2b_erp_data_integrator.spark.customer_csv_pipeline import (
    process_customer_csv_dataframe,
)
from b2b_erp_data_integrator.spark.output import (
    write_processed_parquet,
    write_rejected_json,
)


def run_customer_pipeline(
    spark: SparkSession,
    input_path: str,
    processed_path: str,
    rejected_path: str,
    field_mapping: dict[str, str],
) -> None:
    processed, rejected = process_customer_csv_dataframe(
        spark=spark,
        path=input_path,
        field_mapping=field_mapping,
    )

    write_processed_parquet(
        dataframe=processed,
        path=processed_path,
    )
    write_rejected_json(
        dataframe=rejected,
        path=rejected_path,
    )
