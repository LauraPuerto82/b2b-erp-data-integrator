from b2b_erp_data_integrator.models.customer import CanonicalCustomer
from b2b_erp_data_integrator.models.external_source_customer import (
    ExternalSourceCustomer,
)
from b2b_erp_data_integrator.normalization.country import normalize_country
from b2b_erp_data_integrator.normalization.tax_id import normalize_tax_id


def map_customer(data: dict) -> ExternalSourceCustomer:
    country = normalize_country(data["country"])

    customer = CanonicalCustomer(
        name=data["name"],
        tax_id=normalize_tax_id(data["tax_id"], country=country),
        country=country,
        email=data.get("email"),
    )

    return ExternalSourceCustomer(
        source_system="ERP_A",
        external_id=data["customer_id"],
        customer=customer,
    )
