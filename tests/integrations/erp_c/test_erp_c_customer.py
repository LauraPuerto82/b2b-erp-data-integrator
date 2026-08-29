from b2b_erp_data_integrator.integrations.erp_c.customer import map_erp_c_customer


def test_map_erp_c_customer():
    data = {
        "customer_code": "7842",
        "customer_name": "ACME S.L.",
        "fiscal_id": "B-12345678",
        "country_code": "ES",
        "email_address": "info@acme.es",
    }

    result = map_erp_c_customer(data)

    assert result.source_system == "ERP_C"
    assert result.external_id == "7842"
    assert result.customer.name == "ACME S.L."
    assert result.customer.tax_id == "B12345678"
    assert result.customer.country == "ES"
    assert result.customer.email == "info@acme.es"
