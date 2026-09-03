# b2b-erp-data-integrator

Extensible B2B data integration platform for normalizing heterogeneous ERP data into canonical models.

## Current scope

The project currently implements a local customer-integration pipeline for multiple heterogeneous ERP formats.

It focuses on the engineering problems that appear before cloud-scale execution: canonical modeling, provider-specific structural mappings, normalization, validation, dataset compatibility, partial-success batch processing, and execution-level traceability.

## Current processing flow

```text
ERP CSV
   ↓
read dataset structure
   ↓
validate required source fields
   ↓
stream source records
   ↓
ERP provider
   ↓
shared mapping + normalization
   ↓
business validation
   ↓
batch processing
   ├── processed customers
   └── rejected records
   ↓
ProcessingRun
   ├── COMPLETED
   └── FAILED
```

Three example ERP providers are currently implemented. Each provider declares its source-system identity, structural field mapping, and customer mapper while sharing the canonical transformation workflow.

## Processing semantics

Record-level and dataset-level failures are intentionally different:

- Supported customer business-validation failures are preserved as rejected records and do not stop unrelated valid records from being processed.
- Missing required dataset fields are treated as ingestion failures and produce a failed processing run.
- Unexpected technical or programming exceptions are not silently converted into rejected records or expected integration failures.

A `COMPLETED` processing run may therefore contain both processed and rejected records.

## Technology

- Python 3.12
- Pydantic
- PyArrow / Parquet
- pytest
- Ruff
- MyPy
- pre-commit
- GitHub Actions

## Quality checks

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run pytest
```

## Architecture documentation

Significant design decisions, trade-offs, and intentionally deferred work are documented in `docs/ARCHITECTURE_DECISIONS.md`.

## Local output capabilities

Processed canonical customers can be assigned a stable canonical identity, deduplicated by `customer_id`, and written to Parquet in bounded batches.

Rejected source records can be written to JSONL while preserving the original record and rejection reason.

These output components are implemented and tested independently. End-to-end orchestration from `ProcessingRun` to persisted outputs is the next local pipeline step.

## Next stages

The current pipeline runs locally. The next step is to connect processing results to the implemented Parquet and JSONL output components.

S3 and AWS Glue are planned later in the project as cloud data-platform components, after the local pipeline is connected end to end. They are not yet implemented.
