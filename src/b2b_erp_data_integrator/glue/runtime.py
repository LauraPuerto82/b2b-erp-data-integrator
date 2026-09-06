from b2b_erp_data_integrator.glue.customer_job import CustomerJobArguments


def build_customer_job_arguments(
    resolved_options: dict[str, str],
) -> CustomerJobArguments:
    return CustomerJobArguments(
        source_system=resolved_options["source_system"],
        input_path=resolved_options["input_path"],
        processed_path=resolved_options["processed_path"],
        rejected_path=resolved_options["rejected_path"],
    )
