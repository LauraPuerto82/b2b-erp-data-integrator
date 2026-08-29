from b2b_erp_data_integrator.models.customer import CanonicalCustomer
from b2b_erp_data_integrator.models.external_source_customer import (
    ExternalSourceCustomer,
)


def map_customer(data: dict) -> ExternalSourceCustomer:
    customer = CanonicalCustomer(
        name=data["name"],
        tax_id=data["tax_id"],
        country=data["country"],
        email=data.get("email"),
    )

    return ExternalSourceCustomer(
        source_system="ERP_A",
        external_id=data["customer_id"],
        customer=customer,
    )
