from b2b_erp_data_integrator.models.customer import CanonicalCustomer
from b2b_erp_data_integrator.models.external_source_customer import (
    ExternalSourceCustomer,
)
from b2b_erp_data_integrator.normalization.country import normalize_country


def map_customer(data: dict) -> ExternalSourceCustomer:
    country = normalize_country(data["country"])

    customer = CanonicalCustomer(
        name=data["legal_name"],
        tax_id=data["vat_number"].removeprefix(country),
        country=country,
        email=data.get("contact_email"),
    )

    return ExternalSourceCustomer(
        source_system="ERP_B",
        external_id=data["client_code"],
        customer=customer,
    )
