from pathlib import Path

import pyarrow.parquet as pq  # type: ignore[import-untyped]
import pytest

from b2b_erp_data_integrator.models.customer import CanonicalCustomer
from b2b_erp_data_integrator.models.identified_canonical_customer import (
    identify_customer,
)
from b2b_erp_data_integrator.output import write_processed_parquet


def test_write_processed_parquet(tmp_path: Path):
    output_path = tmp_path / "customers.parquet"

    customers = [
        identify_customer(
            CanonicalCustomer(
                name="ACME S.L.",
                tax_id="B12345678",
                country="ES",
                email="info@acme.es",
            )
        ),
        identify_customer(
            CanonicalCustomer(
                name="Globex S.L.",
                tax_id="A87654321",
                country="ES",
                email=None,
            )
        ),
    ]

    write_processed_parquet(
        path=output_path,
        customers=customers,
    )

    table = pq.read_table(output_path)

    assert table.column_names == [
        "customer_id",
        "name",
        "tax_id",
        "country",
        "email",
    ]

    assert table.to_pylist() == [
        {
            "customer_id": str(customers[0].customer_id),
            "name": "ACME S.L.",
            "tax_id": "B12345678",
            "country": "ES",
            "email": "info@acme.es",
        },
        {
            "customer_id": str(customers[1].customer_id),
            "name": "Globex S.L.",
            "tax_id": "A87654321",
            "country": "ES",
            "email": None,
        },
    ]


def test_write_processed_parquet_writes_multiple_batches(tmp_path: Path):
    output_path = tmp_path / "customers.parquet"

    customers = [
        identify_customer(
            CanonicalCustomer(
                name=f"Customer {index}",
                tax_id=f"B1234567{index}",
                country="ES",
            )
        )
        for index in range(3)
    ]

    write_processed_parquet(
        path=output_path,
        customers=customers,
        batch_size=2,
    )

    table = pq.read_table(output_path)

    assert table.num_rows == 3


def test_write_processed_parquet_rejects_invalid_batch_size(tmp_path: Path):
    output_path = tmp_path / "customers.parquet"

    with pytest.raises(ValueError, match="batch_size"):
        write_processed_parquet(
            path=output_path,
            customers=[],
            batch_size=0,
        )
