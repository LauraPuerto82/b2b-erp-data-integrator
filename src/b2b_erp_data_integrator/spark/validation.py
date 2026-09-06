from pyspark.sql import Column
from pyspark.sql import functions as F


def validate_tax_id_column(
    tax_id_column: Column,
    country_column: Column,
) -> Column:
    return F.when(
        country_column == "ES",
        F.length(tax_id_column) == 9,
    ).otherwise(F.lit(True))
