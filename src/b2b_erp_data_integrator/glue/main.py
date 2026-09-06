import sys

from awsglue.context import GlueContext  # pyright: ignore[reportMissingImports]
from awsglue.job import Job  # pyright: ignore[reportMissingImports]
from awsglue.utils import getResolvedOptions  # pyright: ignore[reportMissingImports]
from pyspark.context import SparkContext

from b2b_erp_data_integrator.glue.customer_job import run_customer_job
from b2b_erp_data_integrator.glue.runtime import build_customer_job_arguments

CUSTOMER_JOB_ARGUMENTS = [
    "source_system",
    "input_path",
    "processed_path",
    "rejected_path",
]


def main() -> None:
    resolved_options = getResolvedOptions(
        sys.argv,
        [
            "JOB_NAME",
            *CUSTOMER_JOB_ARGUMENTS,
        ],
    )

    spark_context = SparkContext.getOrCreate()
    glue_context = GlueContext(spark_context)
    spark = glue_context.spark_session

    job = Job(glue_context)
    job.init(
        resolved_options["JOB_NAME"],
        resolved_options,
    )

    arguments = build_customer_job_arguments(resolved_options)

    run_customer_job(
        spark=spark,
        arguments=arguments,
    )

    job.commit()


if __name__ == "__main__":
    main()
