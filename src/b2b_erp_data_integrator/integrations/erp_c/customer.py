from b2b_erp_data_integrator.mapping.customer import map_customer
from b2b_erp_data_integrator.models.external_source_customer import (
    ExternalSourceCustomer,
)

ERP_C_CUSTOMER_MAPPING = {
    "external_id": "customer_code",
    "name": "customer_name",
    "tax_id": "fiscal_id",
    "country": "country_code",
    "email": "email_address",
}


def map_erp_c_customer(data: dict) -> ExternalSourceCustomer:
    return map_customer(
        data=data,
        source_system="ERP_C",
        field_mapping=ERP_C_CUSTOMER_MAPPING,
    )
