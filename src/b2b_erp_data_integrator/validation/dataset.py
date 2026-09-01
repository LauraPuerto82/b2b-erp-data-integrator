from b2b_erp_data_integrator.exceptions import IngestionError


def validate_required_fields(
    available_fields: set[str],
    required_fields: set[str],
) -> None:
    missing_fields = required_fields - available_fields

    if missing_fields:
        missing_fields_list = ", ".join(sorted(missing_fields))
        raise IngestionError(f"Missing required fields: {missing_fields_list}")
