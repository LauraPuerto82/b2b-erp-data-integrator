from b2b_erp_data_integrator.models.customer import CanonicalCustomer


def test_create_canonical_customer():
    customer = CanonicalCustomer(
        name="ACME SL",
        tax_id="B12345678",
        country="ES",
        email="info@acme.es",
    )

    assert customer.name == "ACME SL"
    assert customer.tax_id == "B12345678"
    assert customer.country == "ES"
    assert customer.email == "info@acme.es"


def test_create_canonical_customer_without_email():
    customer = CanonicalCustomer(
        name="ACME SL",
        tax_id="B12345678",
        country="ES",
    )

    assert customer.email is None
