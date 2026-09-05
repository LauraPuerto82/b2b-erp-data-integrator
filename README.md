# b2b-erp-data-integrator

Extensible B2B data integration platform for normalizing heterogeneous ERP data into canonical models.

## Current scope

The project currently implements a customer-integration pipeline for multiple heterogeneous ERP formats with both local-file and S3-backed execution paths.

It focuses on the engineering problems that appear before cloud-scale execution: canonical modeling, provider-specific structural mappings, normalization, validation, dataset compatibility, partial-success batch processing, execution-level traceability, streaming ingestion, and object-storage integration.

## Current processing flow

```text
Local CSV ───────────────┐
                         │
S3 object                │
   ↓                     │
StreamingBody            │
   ↓                     │
TextIOWrapper            │
   └───────────────┬─────┘
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
             │      ├── processed customers
             │      │      ↓
             │      │   canonical identity
             │      │      ↓
             │      │   deduplicate by customer_id
             │      │      ↓
             │      │   Parquet
             │      │
             │      └── rejected records
             │             ↓
             │          JSONL
             │
             └── FAILED
                    ↓
                 no outputs
```

Three example ERP providers are currently implemented. Each provider declares its source-system identity, structural field mapping, and customer mapper while sharing the canonical transformation workflow.

For S3-backed execution, source CSV data is consumed directly from the S3 response stream instead of first materializing the complete object in memory or copying it to a temporary input file.

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
- Boto3
- Amazon S3-compatible APIs
- MiniStack
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

## Output capabilities

The customer pipeline orchestrates processing results end to end for both local-file and S3-backed execution.

For a completed processing run, processed canonical customers are assigned a stable canonical identity, deduplicated by `customer_id`, and written to Parquet in bounded batches.

Rejected source records are written to JSONL while preserving the original record and rejection reason.

Structurally invalid datasets produce a failed processing run and do not generate processed or rejected outputs.

For S3-backed execution, generated Parquet and JSONL files are uploaded through Boto3 without first loading the complete output file into memory.

## S3 development environment

S3 integration is developed and tested locally using MiniStack and is also exercised in GitHub Actions.

The current implementation has not been deployed to or validated against a real AWS account.

## Next stages

The customer-integration pipeline is now connected end to end for both local files and S3-backed execution.

AWS Glue is the next planned cloud data-platform component. Real AWS deployment remains deliberately deferred while the architecture can be developed and validated against local AWS-compatible infrastructure.
