from pathlib import Path

import pytest

from b2b_erp_data_integrator.exceptions import IngestionError
from b2b_erp_data_integrator.ingestion.csv import (
    read_csv_fields,
)
from b2b_erp_data_integrator.integrations.erp_b.customer import (
    ERP_B_CUSTOMER_MAPPING,
)
from b2b_erp_data_integrator.mapping.customer import (
    get_required_customer_source_fields,
)
from b2b_erp_data_integrator.validation.dataset import validate_required_fields


def test_validate_required_fields_passes_when_all_required_fields_exist():
    available_fields = {
        "customer_id",
        "name",
        "tax_id",
        "country",
        "email",
    }
    required_fields = {
        "name",
        "tax_id",
        "country",
    }

    validate_required_fields(
        available_fields,
        required_fields,
    )


def test_validate_required_fields_fails_when_required_field_is_missing():
    available_fields = {
        "customer_id",
        "name",
        "country",
        "email",
    }
    required_fields = {
        "name",
        "tax_id",
        "country",
    }

    with pytest.raises(IngestionError, match="tax_id"):
        validate_required_fields(
            available_fields,
            required_fields,
        )


def test_validate_customer_dataset_structure_from_mapping():
    field_mapping = {
        "external_id": "client_code",
        "name": "legal_name",
        "tax_id": "vat_number",
        "country": "country",
        "email": "contact_email",
    }

    required_fields = get_required_customer_source_fields(
        field_mapping,
    )

    available_fields = {
        "client_code",
        "legal_name",
        "vat_number",
        "country",
    }

    validate_required_fields(
        available_fields,
        required_fields,
    )


def test_csv_fails_validation_when_required_customer_column_is_missing(
    tmp_path: Path,
):
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text(
        "client_code,legal_name,country,contact_email\n"
        "0001,ACME S.L.,Spain,info@acme.es\n",
        encoding="utf-8",
    )

    available_fields = read_csv_fields(csv_path)

    required_fields = get_required_customer_source_fields(
        ERP_B_CUSTOMER_MAPPING,
    )

    with pytest.raises(IngestionError, match="vat_number"):
        validate_required_fields(
            available_fields,
            required_fields,
        )
