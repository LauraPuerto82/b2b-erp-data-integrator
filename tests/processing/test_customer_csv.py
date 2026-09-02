from pathlib import Path

import pytest

from b2b_erp_data_integrator.exceptions import IngestionError
from b2b_erp_data_integrator.integrations.erp_b.customer import (
    ERP_B_CUSTOMER_PROVIDER,
)
from b2b_erp_data_integrator.processing.customer_csv import process_customer_csv


def test_process_customer_csv(tmp_path: Path):
    csv_path = tmp_path / "customers.csv"

    csv_path.write_text(
        "client_code,legal_name,vat_number,country,contact_email\n"
        "0001,ACME S.L.,ESB12345678,Spain,info@acme.es\n",
        encoding="utf-8",
    )

    result = process_customer_csv(
        path=csv_path,
        provider=ERP_B_CUSTOMER_PROVIDER,
    )

    assert len(result.processed) == 1
    assert len(result.rejected) == 0

    customer = result.processed[0]

    assert customer.source_system == "ERP_B"
    assert customer.external_id == "0001"
    assert customer.customer.name == "ACME S.L."
    assert customer.customer.tax_id == "B12345678"
    assert customer.customer.country == "ES"
    assert customer.customer.email == "info@acme.es"


def test_process_customer_csv_rejects_missing_required_fields(tmp_path: Path):
    csv_path = tmp_path / "customers.csv"

    csv_path.write_text(
        "client_code,legal_name,country,contact_email\n"
        "0001,ACME S.L.,Spain,info@acme.es\n",
        encoding="utf-8",
    )

    with pytest.raises(IngestionError, match="vat_number"):
        process_customer_csv(
            path=csv_path,
            provider=ERP_B_CUSTOMER_PROVIDER,
        )
