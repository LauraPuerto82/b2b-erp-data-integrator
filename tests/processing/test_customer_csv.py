from pathlib import Path

from b2b_erp_data_integrator.integrations.erp_b.customer import (
    ERP_B_CUSTOMER_PROVIDER,
)
from b2b_erp_data_integrator.processing.customer_csv import process_customer_csv
from b2b_erp_data_integrator.processing.run import ProcessingRunStatus


def test_process_customer_csv(tmp_path: Path):
    csv_path = tmp_path / "customers.csv"

    csv_path.write_text(
        "client_code,legal_name,vat_number,country,contact_email\n"
        "0001,ACME S.L.,ESB12345678,Spain,info@acme.es\n",
        encoding="utf-8",
    )

    run = process_customer_csv(
        path=csv_path,
        provider=ERP_B_CUSTOMER_PROVIDER,
    )

    assert run.status == ProcessingRunStatus.COMPLETED
    assert run.source_system == "ERP_B"
    assert run.input_source == str(csv_path)
    assert run.started_at is not None
    assert run.finished_at is not None
    assert run.error is None
    assert run.result is not None
    assert len(run.result.processed) == 1
    assert len(run.result.rejected) == 0

    customer = run.result.processed[0]

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

    run = process_customer_csv(
        path=csv_path,
        provider=ERP_B_CUSTOMER_PROVIDER,
    )

    assert run.status == ProcessingRunStatus.FAILED
    assert run.source_system == "ERP_B"
    assert run.input_source == str(csv_path)
    assert run.started_at is not None
    assert run.finished_at is not None
    assert run.result is None
    assert run.error is not None
    assert "vat_number" in run.error


def test_process_customer_csv_completes_with_rejected_records(tmp_path: Path):
    csv_path = tmp_path / "customers.csv"

    csv_path.write_text(
        "client_code,legal_name,vat_number,country,contact_email\n"
        "0001,ACME S.L.,ESB12345678,Spain,info@acme.es\n"
        "0002,Globex S.L.,INVALID,Spain,info@globex.es\n",
        encoding="utf-8",
    )

    run = process_customer_csv(
        path=csv_path,
        provider=ERP_B_CUSTOMER_PROVIDER,
    )

    assert run.status == ProcessingRunStatus.COMPLETED
    assert run.result is not None
    assert len(run.result.processed) == 1
    assert len(run.result.rejected) == 1
