import json
from collections.abc import Iterable
from pathlib import Path

import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]

from b2b_erp_data_integrator.models.identified_canonical_customer import (
    IdentifiedCanonicalCustomer,
)
from b2b_erp_data_integrator.processing.result import RejectedRecord


def write_rejected_jsonl(
    path: Path,
    rejected: Iterable[RejectedRecord],
) -> None:
    with path.open("w", encoding="utf-8") as file:
        for record in rejected:
            data = {
                "raw_record": record.raw_record,
                "reason": record.reason,
            }
            file.write(json.dumps(data) + "\n")


PROCESSED_CUSTOMER_SCHEMA = pa.schema(
    [
        ("customer_id", pa.string()),
        ("name", pa.string()),
        ("tax_id", pa.string()),
        ("country", pa.string()),
        ("email", pa.string()),
    ]
)


def _customers_to_table(
    customers: list[IdentifiedCanonicalCustomer],
) -> pa.Table:
    rows = [
        {
            "customer_id": str(customer.customer_id),
            "name": customer.customer.name,
            "tax_id": customer.customer.tax_id,
            "country": customer.customer.country,
            "email": customer.customer.email,
        }
        for customer in customers
    ]

    return pa.Table.from_pylist(
        rows,
        schema=PROCESSED_CUSTOMER_SCHEMA,
    )


def write_processed_parquet(
    path: Path,
    customers: Iterable[IdentifiedCanonicalCustomer],
    batch_size: int = 1_000,
) -> None:

    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    batch: list[IdentifiedCanonicalCustomer] = []

    with pq.ParquetWriter(path, PROCESSED_CUSTOMER_SCHEMA) as writer:
        for customer in customers:
            batch.append(customer)

            if len(batch) == batch_size:
                writer.write_table(_customers_to_table(batch))
                batch.clear()

        if batch:
            writer.write_table(_customers_to_table(batch))
