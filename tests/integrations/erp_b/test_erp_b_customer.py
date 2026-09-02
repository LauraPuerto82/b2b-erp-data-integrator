from b2b_erp_data_integrator.integrations.erp_b.customer import (
    ERP_B_CUSTOMER_MAPPING,
    ERP_B_CUSTOMER_PROVIDER,
    map_erp_b_customer,
)


def test_map_erp_b_customer():
    data = {
        "client_code": "0001",
        "legal_name": "ACME S.L.",
        "vat_number": "ESB12345678",
        "country": "Spain",
        "contact_email": "info@acme.es",
    }

    result = map_erp_b_customer(data)

    assert result.source_system == "ERP_B"
    assert result.external_id == "0001"
    assert result.customer.name == "ACME S.L."
    assert result.customer.tax_id == "B12345678"
    assert result.customer.country == "ES"
    assert result.customer.email == "info@acme.es"


def test_erp_b_customer_provider():
    assert ERP_B_CUSTOMER_PROVIDER.field_mapping == ERP_B_CUSTOMER_MAPPING
    assert ERP_B_CUSTOMER_PROVIDER.mapper is map_erp_b_customer
