# b2b-erp-data-integrator

Extensible B2B data integration platform for normalizing heterogeneous ERP data into canonical models.

## Current scope

The project currently implements a customer-integration pipeline for multiple heterogeneous ERP formats with local-file, S3-backed, and Spark DataFrame processing paths.

It focuses on canonical modeling, provider-specific structural mappings, normalization, validation, dataset compatibility, partial-success batch processing, execution-level traceability, streaming ingestion, object-storage integration, distributed Spark transformations, and preparation for AWS Glue execution.

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

## Spark processing path

A second processing path has been introduced with PySpark to prepare the integration pipeline for distributed execution in AWS Glue.

```text
CSV / S3-compatible input
        ↓
Spark DataFrame
        ↓
provider field mapping
        ↓
canonical column normalization
        ↓
business validation
        ↓
processed / rejected DataFrames
        ↓
canonical identity
        ↓
deduplicate by customer_id
        ↓
processed → Parquet
rejected  → JSON
```

The Spark path reuses the existing ERP A, ERP B, and ERP C structural mappings rather than embedding source-system conditionals into the Spark processing core.

Most transformations are expressed using native Spark DataFrame operations. Canonical UUID5 identity generation is intentionally implemented as a localized Python UDF so that the same normalized customer identity produces the same `customer_id` in both the Python and Spark processing paths.

## AWS Glue integration

The project now includes a thin AWS Glue runtime adapter around the Spark processing core.

```text
AWS Glue runtime
        ↓
getResolvedOptions
        ↓
GlueContext / SparkSession
        ↓
CustomerJobArguments
        ↓
source-system mapping selection
        ↓
Spark customer pipeline
        ↓
Job.commit()
```

The Glue-specific entry point is intentionally separated from reusable Spark transformation logic.

The current job arguments are:

```text
source_system
input_path
processed_path
rejected_path
```

`source_system` selects the mapping for ERP A, ERP B, or ERP C, while input and output paths remain execution-time configuration.

The Glue integration is packaged and deployed locally through MiniStack. The Glue job has been executed and validated end to end, including S3 input upload, Glue/Spark execution, processed Parquet output, rejected JSON output, and content-level assertions.

## Deployment

The AWS Glue pipeline can be deployed and executed locally using MiniStack, providing an AWS-compatible environment without requiring a real AWS account.

The repository includes reproducible deployment and lifecycle scripts for both Windows and Linux/WSL:

- deploy the local AWS environment and Glue job;
- execute the end-to-end pipeline;
- stop the local environment;
- clean deployed resources and generated artifacts.

The E2E flow has been validated from S3 input through Glue/Spark execution to processed Parquet and rejected JSON outputs.

For architecture details, prerequisites, infrastructure resources, and execution commands, see [`infrastructure/README.md`](infrastructure/README.md).

## Processing semantics

Record-level and dataset-level failures are intentionally different:

- Supported customer business-validation failures are preserved as rejected records and do not stop unrelated valid records from being processed.
- Missing required dataset fields are treated as ingestion failures and produce a failed processing run.
- Unexpected technical or programming exceptions are not silently converted into rejected records or expected integration failures.

A `COMPLETED` processing run may therefore contain both processed and rejected records.

## Technology

- Python 3.11+ (local development also uses Python 3.12)
- Pydantic
- PyArrow / Parquet
- PySpark 3.5
- AWS Glue runtime integration
- Boto3
- Amazon S3-compatible APIs
- MiniStack
- pytest
- Ruff
- MyPy
- pre-commit
- GitHub Actions
- uv

## Packaging and Glue runtime compatibility

The project can be packaged as a Python wheel with:

```bash
uv build
```

The wheel contains project-owned Python code. PySpark and `awsglue` are treated as runtime-provided dependencies for AWS Glue rather than bundled into the application artifact.

Because the target Glue runtime uses Python 3.11, compatibility has been checked separately from the main Python 3.12 development environment: the source tree compiles under Python 3.11, the test suite has been executed under Python 3.11, and the generated wheel installs successfully in a clean Python 3.11 environment.

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

The AWS-compatible local deployment now provisions the S3 bucket, uploads the Glue script and application wheel, creates the Glue IAM role and Glue job, and executes the customer pipeline end to end.

Reproducible lifecycle scripts are provided for both Windows and Linux/WSL to deploy, validate, stop, and clean the local environment. The end-to-end test uploads an ERP B dataset, runs the Glue job, waits for completion, verifies processed Parquet and rejected JSON outputs, and validates their contents.

Detailed infrastructure and local deployment documentation is available in `infrastructure/README.md`.

The current implementation has not been deployed to or validated against a real AWS account.

## Next stages

The customer-integration pipeline is now implemented for local-file, S3-backed, and Spark processing paths, and the AWS Glue runtime adapter has been deployed and validated end to end in MiniStack.

The AWS-compatible local deployment flow is complete, with reproducible deployment, end-to-end validation, stop, and cleanup scripts for both Windows and Linux/WSL.

Real AWS deployment remains deliberately deferred. A future stage can validate the same infrastructure and Glue workload against a real AWS account.
