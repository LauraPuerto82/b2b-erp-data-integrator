from uuid import UUID

from b2b_erp_data_integrator.models.customer import CanonicalCustomer
from b2b_erp_data_integrator.models.identified_canonical_customer import (
    IdentifiedCanonicalCustomer,
    generate_customer_id,
    identify_customer,
)


def test_identified_canonical_customer():
    customer = CanonicalCustomer(
        name="ACME S.L.",
        tax_id="B12345678",
        country="ES",
        email="info@acme.es",
    )

    customer_id = UUID("12345678-1234-5678-1234-567812345678")

    identified_customer = IdentifiedCanonicalCustomer(
        customer_id=customer_id,
        customer=customer,
    )

    assert identified_customer.customer_id == customer_id
    assert identified_customer.customer == customer


def test_generate_customer_id_is_stable():
    customer = CanonicalCustomer(
        name="ACME S.L.",
        tax_id="B12345678",
        country="ES",
        email="info@acme.es",
    )

    customer_id = generate_customer_id(customer)

    assert customer_id == UUID("25013cb5-a708-5c14-a1f1-f2ddbe8e9d35")


def test_generate_customer_id_depends_only_on_identity_fields():
    first = CanonicalCustomer(
        name="ACME S.L.",
        tax_id="B12345678",
        country="ES",
        email="info@acme.es",
    )

    second = CanonicalCustomer(
        name="ACME Sociedad Limitada",
        tax_id="B12345678",
        country="ES",
        email="contact@acme.es",
    )

    assert generate_customer_id(first) == generate_customer_id(second)


def test_generate_customer_id_changes_for_different_identity():
    first = CanonicalCustomer(
        name="ACME S.L.",
        tax_id="B12345678",
        country="ES",
    )

    second = CanonicalCustomer(
        name="Globex S.L.",
        tax_id="A87654321",
        country="ES",
    )

    assert generate_customer_id(first) != generate_customer_id(second)


def test_identify_customer():
    customer = CanonicalCustomer(
        name="ACME S.L.",
        tax_id="B12345678",
        country="ES",
        email="info@acme.es",
    )

    result = identify_customer(customer)

    assert result.customer_id == generate_customer_id(customer)
    assert result.customer == customer
