from pyspark.sql import DataFrame


def write_processed_parquet(
    dataframe: DataFrame,
    path: str,
) -> None:
    dataframe.write.mode("overwrite").parquet(path)


def write_rejected_json(
    dataframe: DataFrame,
    path: str,
) -> None:
    dataframe.write.mode("overwrite").json(path)
