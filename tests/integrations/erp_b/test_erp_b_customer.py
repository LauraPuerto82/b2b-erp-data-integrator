from b2b_erp_data_integrator.integrations.erp_b.customer import map_customer


def test_map_erp_b_customer():
    data = {
        "client_code": "0001",
        "legal_name": "ACME S.L.",
        "vat_number": "ESB12345678",
        "country": "Spain",
        "contact_email": "info@acme.es",
    }

    result = map_customer(data)

    assert result.source_system == "ERP_B"
    assert result.external_id == "0001"
    assert result.customer.name == "ACME S.L."
    assert result.customer.tax_id == "B12345678"
    assert result.customer.country == "ES"
    assert result.customer.email == "info@acme.es"
