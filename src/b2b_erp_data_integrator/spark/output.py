from pyspark.sql import DataFrame


def write_processed_parquet(
    dataframe: DataFrame,
    path: str,
) -> None:
    dataframe.write.mode("overwrite").parquet(path)
