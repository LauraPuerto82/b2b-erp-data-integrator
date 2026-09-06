import argparse
from dataclasses import dataclass

from pyspark.sql import SparkSession

from b2b_erp_data_integrator.integrations.erp_a.customer import (
    ERP_A_CUSTOMER_MAPPING,
)
from b2b_erp_data_integrator.integrations.erp_b.customer import (
    ERP_B_CUSTOMER_MAPPING,
)
from b2b_erp_data_integrator.integrations.erp_c.customer import (
    ERP_C_CUSTOMER_MAPPING,
)
from b2b_erp_data_integrator.spark.run import run_customer_pipeline


@dataclass(frozen=True)
class CustomerJobArguments:
    source_system: str
    input_path: str
    processed_path: str
    rejected_path: str


CUSTOMER_MAPPINGS = {
    "ERP_A": ERP_A_CUSTOMER_MAPPING,
    "ERP_B": ERP_B_CUSTOMER_MAPPING,
    "ERP_C": ERP_C_CUSTOMER_MAPPING,
}


def get_customer_mapping(
    source_system: str,
) -> dict[str, str]:
    try:
        return CUSTOMER_MAPPINGS[source_system]
    except KeyError:
        raise ValueError(f"Unsupported source system: {source_system}") from None


def parse_customer_job_arguments(
    argv: list[str],
) -> CustomerJobArguments:
    parser = argparse.ArgumentParser()

    parser.add_argument("--source-system", required=True)
    parser.add_argument("--input-path", required=True)
    parser.add_argument("--processed-path", required=True)
    parser.add_argument("--rejected-path", required=True)

    args = parser.parse_args(argv)

    return CustomerJobArguments(
        source_system=args.source_system,
        input_path=args.input_path,
        processed_path=args.processed_path,
        rejected_path=args.rejected_path,
    )


def run_customer_job(
    spark: SparkSession,
    arguments: CustomerJobArguments,
) -> None:
    field_mapping = get_customer_mapping(
        arguments.source_system,
    )

    run_customer_pipeline(
        spark=spark,
        input_path=arguments.input_path,
        processed_path=arguments.processed_path,
        rejected_path=arguments.rejected_path,
        field_mapping=field_mapping,
    )
