from uuid import uuid5

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

from b2b_erp_data_integrator.models.identified_canonical_customer import (
    CUSTOMER_ID_NAMESPACE,
)


@F.udf(returnType=StringType())
def generate_customer_id_udf(
    country: str,
    tax_id: str,
) -> str:
    identity_key = f"{country}:{tax_id}"
    return str(uuid5(CUSTOMER_ID_NAMESPACE, identity_key))


def identify_customers(
    dataframe: DataFrame,
) -> DataFrame:
    return dataframe.withColumn(
        "customer_id",
        generate_customer_id_udf(
            dataframe["country"],
            dataframe["tax_id"],
        ),
    )


def deduplicate_customers(
    dataframe: DataFrame,
) -> DataFrame:
    return dataframe.dropDuplicates(["customer_id"])
