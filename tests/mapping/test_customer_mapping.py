from b2b_erp_data_integrator.mapping.customer import (
    get_mapped_value,
    map_canonical_customer,
    map_customer,
)


def test_get_mapped_value():
    data = {
        "client_code": "0001",
        "legal_name": "ACME S.L.",
    }

    field_mapping = {
        "external_id": "client_code",
        "name": "legal_name",
    }

    assert get_mapped_value(data, field_mapping, "name") == "ACME S.L."


def test_map_canonical_customer():
    data = {
        "client_code": "0001",
        "legal_name": "ACME S.L.",
        "vat_number": "ESB12345678",
        "country": "Spain",
        "contact_email": "info@acme.es",
    }

    field_mapping = {
        "external_id": "client_code",
        "name": "legal_name",
        "tax_id": "vat_number",
        "country": "country",
        "email": "contact_email",
    }

    customer = map_canonical_customer(data, field_mapping)

    assert customer.name == "ACME S.L."
    assert customer.tax_id == "B12345678"
    assert customer.country == "ES"
    assert customer.email == "info@acme.es"


def test_map_canonical_customer_without_optional_email():
    data = {
        "customer_id": "C001",
        "name": "ACME SL",
        "tax_id": "B12345678",
        "country": "ES",
    }

    field_mapping = {
        "external_id": "customer_id",
        "name": "name",
        "tax_id": "tax_id",
        "country": "country",
        "email": "email",
    }

    customer = map_canonical_customer(data, field_mapping)

    assert customer.email is None


def test_map_customer():
    data = {
        "client_code": "0001",
        "legal_name": "ACME S.L.",
        "vat_number": "ESB12345678",
        "country": "Spain",
        "contact_email": "info@acme.es",
    }

    field_mapping = {
        "external_id": "client_code",
        "name": "legal_name",
        "tax_id": "vat_number",
        "country": "country",
        "email": "contact_email",
    }

    result = map_customer(
        data=data,
        source_system="ERP_B",
        field_mapping=field_mapping,
    )

    assert result.source_system == "ERP_B"
    assert result.external_id == "0001"
    assert result.customer.name == "ACME S.L."
    assert result.customer.tax_id == "B12345678"
    assert result.customer.country == "ES"
    assert result.customer.email == "info@acme.es"
