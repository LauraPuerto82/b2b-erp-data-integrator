from b2b_erp_data_integrator.models.customer import CanonicalCustomer
from b2b_erp_data_integrator.models.external_source_customer import (
    ExternalSourceCustomer,
)
from b2b_erp_data_integrator.normalization.country import normalize_country


def map_customer(data: dict) -> ExternalSourceCustomer:
    country = normalize_country(data["country_code"])

    customer = CanonicalCustomer(
        name=data["customer_name"],
        tax_id=data["fiscal_id"],
        country=country,
        email=data.get("email_address"),
    )

    return ExternalSourceCustomer(
        source_system="ERP_C",
        external_id=data["customer_code"],
        customer=customer,
    )
