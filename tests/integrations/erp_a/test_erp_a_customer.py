from b2b_erp_data_integrator.integrations.erp_a.customer import map_erp_a_customer


def test_map_erp_a_customer():
    data = {
        "customer_id": "C001",
        "name": "ACME SL",
        "tax_id": "B12345678",
        "country": "ES",
        "email": "info@acme.es",
    }

    result = map_erp_a_customer(data)

    assert result.source_system == "ERP_A"
    assert result.external_id == "C001"
    assert result.customer.name == "ACME SL"
    assert result.customer.tax_id == "B12345678"
    assert result.customer.country == "ES"
    assert result.customer.email == "info@acme.es"
