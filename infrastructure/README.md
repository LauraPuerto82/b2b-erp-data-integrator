# Infrastructure

This directory contains the infrastructure definitions used to run the B2B ERP Data Integrator on AWS-compatible services.

The project uses AWS Glue as the execution environment for the ETL pipeline and S3 as the storage layer for input data, processed records, rejected records, and deployment artifacts.

## Architecture

The local environment reproduces the AWS execution flow using MiniStack and the AWS Glue 5 Docker image.

```text
CSV input
    |
    v
Amazon S3
    |
    v
AWS Glue Job
    |
    +--------------------+
    |                    |
    v                    v
Processed records     Rejected records
Parquet               JSON
    |                    |
    v                    v
Amazon S3             Amazon S3
```

The Glue job loads the application package from S3 and executes the same transformation and validation logic used by the application.

## Infrastructure definition

The AWS infrastructure definition is located at:

```text
infrastructure/aws/glue.yaml
```

It defines the resources required by the Glue workload, including:

- IAM role used by the Glue job.
- S3 permissions for reading input data and writing pipeline outputs.
- Glue job configuration.
- Deployment artifact locations.

The same definition is used as the basis for local deployment, with the Glue job created through the AWS-compatible MiniStack APIs where required by the local environment.

## Local environment

Local AWS services are provided by MiniStack:

```text
http://localhost:4566
```

Glue jobs run using:

```text
public.ecr.aws/glue/aws-glue-libs:5
```

The local deployment creates the S3 bucket:

```text
b2b-erp-data-integrator-local
```

with the following logical structure:

```text
raw/
├── erp_a/
└── erp_b/

processed/
├── erp_a/
└── erp_b/

rejected/
├── erp_a/
└── erp_b/

scripts/
└── main.py

artifacts/
└── b2b_erp_data_integrator-*.whl
```

## Local lifecycle

The repository provides equivalent lifecycle scripts for Windows and Linux.

### Windows

Requires PowerShell 7+.

```powershell
.\scripts\windows\deploy-local.ps1
.\scripts\windows\test-e2e.ps1
.\scripts\windows\stop-local.ps1
.\scripts\windows\clean-local.ps1
```

### Linux / WSL

```bash
./scripts/linux/deploy-local.sh
./scripts/linux/test-e2e.sh
./scripts/linux/stop-local.sh
./scripts/linux/clean-local.sh
```

The lifecycle is:

```text
deploy-local
    |
    v
Create local AWS environment
    |
    v
test-e2e
    |
    v
Upload CSV → Run Glue → Validate S3 outputs
    |
    +----> stop-local   Stop the environment
    |
    +----> clean-local  Remove the environment and generated artifacts
```

`stop-local` preserves the MiniStack container so the environment can be stopped without deleting it.

`clean-local` removes the MiniStack container, residual Glue containers, generated build artifacts, and temporary deployment files. Docker images and developer environments are intentionally preserved.

## End-to-end validation

The E2E test exercises the deployed pipeline rather than calling the transformation code directly.

It:

1. uploads an ERP B CSV dataset to S3;
2. starts the Glue job;
3. waits for the job to complete;
4. verifies that processed Parquet output was generated;
5. verifies that rejected JSON output was generated;
6. validates the contents of both outputs.

The test dataset contains one valid and one invalid customer. The valid customer must reach the processed dataset, while the invalid tax ID must be routed to the rejected dataset with its rejection reason.

This validates the complete path:

```text
S3 → Glue/Spark → application package → validation/transformation → S3
```

rather than only the application logic in isolation.
