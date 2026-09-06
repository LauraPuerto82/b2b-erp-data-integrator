from pyspark.sql import DataFrame, SparkSession


def read_csv_dataframe(
    spark: SparkSession,
    path: str,
) -> DataFrame:
    return spark.read.option("header", True).option("inferSchema", False).csv(path)
