from pydantic import BaseModel


def get_required_source_fields(
    model: type[BaseModel],
    field_mapping: dict[str, str],
) -> set[str]:
    required_model_fields = {
        field_name
        for field_name, field_info in model.model_fields.items()
        if field_info.is_required()
    }

    return {field_mapping[field_name] for field_name in required_model_fields}
