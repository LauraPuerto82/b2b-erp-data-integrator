from b2b_erp_data_integrator.integrations.customer_erp_provider import (
    CustomerERPProvider,
)
from b2b_erp_data_integrator.mapping.customer import map_customer
from b2b_erp_data_integrator.models.external_source_customer import (
    ExternalSourceCustomer,
)

ERP_B_CUSTOMER_MAPPING = {
    "external_id": "client_code",
    "name": "legal_name",
    "tax_id": "vat_number",
    "country": "country",
    "email": "contact_email",
}


def map_erp_b_customer(data: dict) -> ExternalSourceCustomer:
    return map_customer(
        data=data,
        source_system="ERP_B",
        field_mapping=ERP_B_CUSTOMER_MAPPING,
    )


ERP_B_CUSTOMER_PROVIDER = CustomerERPProvider(
    source_system="ERP_B",
    field_mapping=ERP_B_CUSTOMER_MAPPING,
    mapper=map_erp_b_customer,
)
