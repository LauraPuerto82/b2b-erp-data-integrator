from b2b_erp_data_integrator.models.customer import CanonicalCustomer
from b2b_erp_data_integrator.models.external_source_customer import (
    ExternalSourceCustomer,
)
from b2b_erp_data_integrator.normalization.country import normalize_country
from b2b_erp_data_integrator.normalization.tax_id import normalize_tax_id


def get_mapped_value(
    data: dict,
    field_mapping: dict,
    canonical_field: str,
):
    source_field = field_mapping[canonical_field]
    return data[source_field]


def map_canonical_customer(
    data: dict,
    field_mapping: dict,
) -> CanonicalCustomer:
    country = normalize_country(get_mapped_value(data, field_mapping, "country"))

    return CanonicalCustomer(
        name=get_mapped_value(data, field_mapping, "name"),
        tax_id=normalize_tax_id(
            get_mapped_value(data, field_mapping, "tax_id"),
            country=country,
        ),
        country=country,
        email=data.get(field_mapping["email"]),
    )


def map_customer(
    data: dict,
    source_system: str,
    field_mapping: dict,
) -> ExternalSourceCustomer:
    customer = map_canonical_customer(data, field_mapping)

    return ExternalSourceCustomer(
        source_system=source_system,
        external_id=get_mapped_value(data, field_mapping, "external_id"),
        customer=customer,
    )
