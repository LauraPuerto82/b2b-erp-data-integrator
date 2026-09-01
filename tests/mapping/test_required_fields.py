from b2b_erp_data_integrator.mapping.customer import get_required_customer_source_fields
from b2b_erp_data_integrator.mapping.required_fields import (
    get_required_source_fields,
)
from b2b_erp_data_integrator.models.customer import CanonicalCustomer


def test_get_required_source_fields_from_canonical_model():
    field_mapping = {
        "external_id": "customer_id",
        "name": "name",
        "tax_id": "tax_id",
        "country": "country",
        "email": "email",
    }

    required_fields = get_required_source_fields(
        CanonicalCustomer,
        field_mapping,
    )

    assert required_fields == {
        "name",
        "tax_id",
        "country",
    }


def test_get_required_customer_source_fields_includes_external_id():
    field_mapping = {
        "external_id": "client_code",
        "name": "legal_name",
        "tax_id": "vat_number",
        "country": "country",
        "email": "contact_email",
    }

    required_fields = get_required_customer_source_fields(field_mapping)

    assert required_fields == {
        "client_code",
        "legal_name",
        "vat_number",
        "country",
    }
