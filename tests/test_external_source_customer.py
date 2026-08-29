from b2b_erp_data_integrator.models.customer import CanonicalCustomer
from b2b_erp_data_integrator.models.external_source_customer import (
    ExternalSourceCustomer,
)


def test_create_external_source_customer():
    customer = CanonicalCustomer(
        name="ACME SL",
        tax_id="B12345678",
        country="ES",
        email="info@acme.es",
    )

    external_customer = ExternalSourceCustomer(
        source_system="ERP_A",
        external_id="C001",
        customer=customer,
    )

    assert external_customer.source_system == "ERP_A"
    assert external_customer.external_id == "C001"
    assert external_customer.customer == customer
