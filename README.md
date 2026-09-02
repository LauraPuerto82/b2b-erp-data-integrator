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

## Next stages

The current pipeline runs locally. Persistence and output traceability are the next design area.

S3 and AWS Glue are planned later in the project as cloud data-platform components, after the local integration semantics and processing boundaries are established. They are not yet implemented.
