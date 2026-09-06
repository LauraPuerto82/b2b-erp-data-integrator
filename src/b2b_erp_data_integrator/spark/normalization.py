from pyspark.sql import Column
from pyspark.sql import functions as F

from b2b_erp_data_integrator.normalization.country import COUNTRY_CODES


def normalize_country_column(column: Column) -> Column:
    canonical_values = list(COUNTRY_CODES.values())

    result = F.when(
        column.isin(canonical_values),
        column,
    )

    for source_value, canonical_value in COUNTRY_CODES.items():
        result = result.when(
            column == source_value,
            F.lit(canonical_value),
        )

    return result.otherwise(F.lit(None))
