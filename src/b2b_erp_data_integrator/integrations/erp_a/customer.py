from b2b_erp_data_integrator.integrations.customer_erp_provider import (
    CustomerERPProvider,
)
from b2b_erp_data_integrator.mapping.customer import map_customer
from b2b_erp_data_integrator.models.external_source_customer import (
    ExternalSourceCustomer,
)

ERP_A_CUSTOMER_MAPPING = {
    "external_id": "customer_id",
    "name": "name",
    "tax_id": "tax_id",
    "country": "country",
    "email": "email",
}


def map_erp_a_customer(data: dict) -> ExternalSourceCustomer:
    return map_customer(
        data=data,
        source_system="ERP_A",
        field_mapping=ERP_A_CUSTOMER_MAPPING,
    )


ERP_A_CUSTOMER_PROVIDER = CustomerERPProvider(
    source_system="ERP_A",
    field_mapping=ERP_A_CUSTOMER_MAPPING,
    mapper=map_erp_a_customer,
)
