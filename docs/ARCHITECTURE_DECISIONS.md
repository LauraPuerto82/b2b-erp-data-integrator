# Architecture Decisions & Known Technical Debt

This document records significant architectural decisions, trade-offs, and known technical limitations in the **B2B ERP Data Integrator**.

The goal is not to document every implementation detail. It is to make important engineering decisions explicit: **what problem existed, what was decided, why, which alternatives were considered, and what limitations are intentionally being accepted at the current stage of the project.**

The system is being built incrementally around concrete ERP integration scenarios. Rather than designing abstractions for hypothetical requirements upfront, the project starts with explicit implementations and introduces reusable components when recurring patterns and requirements emerge.

Some decisions are therefore intentionally scoped to the current stage of the project and may evolve as additional ERP formats, data entities, validation requirements, and processing scenarios are introduced.

------------------------------------------------------------------------

# Architecture Decisions

## ADR-001 --- Keep initial ERP field mappings in provider-specific code

**Status:** Superseded by ADR-004
**Stage:** Initial ERP integration

### Context

ERP systems can expose equivalent business data using different field names.

For example:

| Canonical field | ERP A | ERP B |
| --- | --- | --- |
| external ID | `customer_id` | `client_code` |
| name | `name` | `legal_name` |
| tax ID | `tax_id` | `vat_number` |
| email | `email` | `contact_email` |

A configurable mapping system could be introduced immediately, but the project currently supports only two example ERP formats.

Designing a generic mapping mechanism before observing the differences between several integrations would require predicting which mapping and transformation capabilities will eventually be necessary.

### Decision

Implement the initial field mappings explicitly inside each ERP-specific integration.

The canonical model remains independent of provider-specific field names.

For example:

```text
ERP A                         Canonical model

customer_id      ───────→     external source identity
name             ───────→     name
tax_id           ───────→     tax_id
country          ───────→     country
email            ───────→     email
```

ERP-specific knowledge therefore remains at the integration boundary rather than leaking into canonical domain models.

### Trade-off

Adding a new ERP currently requires implementing provider-specific mapping code.

This creates some duplication between integrations and is less configurable than a declarative mapping system.

That duplication is intentionally accepted while the actual mapping requirements are still emerging.

In return, each integration remains explicit and easy to understand, test, and debug without introducing a speculative abstraction.

### Alternatives considered

- Introduce a generic configurable field mapper from the beginning.
- Store all ERP mappings in configuration files.
- Make canonical models responsible for understanding individual ERP formats.
- Implement a single mapper containing conditional logic for every ERP provider.

### Consequences

The first integrations can evolve independently while preserving a stable canonical representation.

Common mapping patterns can be identified from real implementations rather than predicted upfront.

Once stable patterns emerge, simple structural mappings may be moved to declarative configuration while transformations containing business logic can remain implemented in code.

------------------------------------------------------------------------

## ADR-002 --- Represent canonical countries using ISO 3166-1 alpha-2 codes

**Status:** Accepted
**Stage:** Canonical customer modeling

### Context

ERP systems may represent the same country using different values.

For example:

```text
Spain
España
ES
```

Allowing source-specific country representations into canonical models would make downstream processing dependent on conventions chosen by individual ERP systems.

A stable representation is therefore required at the canonical boundary.

### Decision

Represent countries in canonical models using ISO 3166-1 alpha-2 codes.

Examples include:

```text
Spain    → ES
France   → FR
Germany  → DE
```

Source-specific representations are normalized before the canonical model is created.

### Trade-off

Source values cannot simply be copied into the canonical model.

Every integration must ensure that its country representation can be converted to the canonical format.

In return, downstream components operate on one stable, language-independent representation regardless of the originating ERP.

### Alternatives considered

- Preserve the country representation supplied by each ERP.
- Store full English country names as the canonical representation.
- Store both the source country value and ISO code directly in the canonical customer model.

### Consequences

Country formatting differences remain at the integration boundary instead of propagating through the system.

Canonical customer data can be compared and processed independently of the language or naming conventions used by source ERP systems.

The normalized country code can also provide context for later normalization and identity-resolution rules.

------------------------------------------------------------------------

## ADR-003 --- Start country normalization with a limited explicit mapping

**Status:** Accepted for MVP
**Stage:** ERP B integration

### Context

The canonical model requires ISO 3166-1 alpha-2 country codes, while source ERP systems may provide country names.

A production integration platform could use a comprehensive ISO dataset or a dedicated country-code library.

The current integration scenarios, however, require only a small number of country representations.

Introducing comprehensive country handling at this stage would expand the implementation before broader country coverage is required.

### Decision

Start with an explicit mapping containing only the country values required by the current integration scenarios:

```text
Spain     → ES
France    → FR
Germany   → DE
```

Unsupported country values are not silently guessed or automatically converted.

The mapping is implemented as shared normalization logic rather than being embedded inside a specific ERP integration.

### Trade-off

The current implementation does not support arbitrary countries and the mapping must be extended when new integration scenarios require additional values.

This limitation is accepted because the initial goal is to validate the normalization boundary, not to build a complete country-reference dataset.

### Alternatives considered

- Introduce a third-party country-code library immediately.
- Maintain a complete ISO country dataset in the repository.
- Implement country conversion independently inside every ERP integration.
- Accept arbitrary source country values without normalization.

### Consequences

Country normalization is explicit, deterministic, and independently testable.

Multiple ERP integrations can reuse the same canonical normalization behavior.

If broader country coverage becomes necessary, the explicit dictionary should be reconsidered in favor of a maintained ISO dataset or library rather than manually expanding it indefinitely.

------------------------------------------------------------------------

## ADR-004 --- Introduce declarative structural mappings after recurring provider patterns emerged

**Status:** Accepted
**Stage:** ERP mapping generalization

### Context

The first ERP integrations intentionally implemented customer field mappings in provider-specific code, as described in ADR-001.

After implementing three ERP formats, a stable structural pattern emerged. Each integration performed the same sequence:

```text
read provider-specific fields
        ↓
normalize shared values
        ↓
construct CanonicalCustomer
        ↓
attach external source identity
```

The integrations differed primarily in the names used for equivalent source fields:

| Canonical field | ERP A | ERP B | ERP C |
| --- | --- | --- | --- |
| external ID | `customer_id` | `client_code` | `customer_code` |
| name | `name` | `legal_name` | `customer_name` |
| tax ID | `tax_id` | `vat_number` | `fiscal_id` |
| country | `country` | `country` | `country_code` |
| email | `email` | `contact_email` | `email_address` |

Country and tax-ID normalization had also already become shared behavior independent of individual ERP providers.

At this point, continuing to duplicate the complete mapping workflow in every integration would repeat stable behavior rather than preserve meaningful provider-specific logic.

### Decision

Represent simple structural field differences as declarative provider-specific mappings.

Each ERP integration declares how its source fields correspond to the canonical customer structure:

```text
ERP-specific field mapping
        ↓
shared customer mapper
        ↓
shared normalization
        ↓
CanonicalCustomer
        ↓
ExternalSourceCustomer
```

The shared mapper owns the common transformation workflow, while each ERP integration retains knowledge of its own field names and source-system identity.

Value normalization remains implemented as shared code rather than being encoded into the field-mapping configuration.

### Trade-off

The declarative mapping format intentionally supports only simple field-to-field mappings.

It does not currently model more complex transformations such as nested source paths, fallback fields, field composition, conditional rules, or provider-specific business logic.

This limitation is accepted because none of the current ERP integrations requires those capabilities.

If future integrations introduce structural differences that cannot be represented cleanly by the current mapping format, the abstraction should be extended based on those concrete requirements rather than turned prematurely into a generic transformation language.

### Alternatives considered

- Continue implementing the complete mapping workflow independently for every ERP.
- Introduce the generic mapping abstraction before multiple ERP implementations existed.
- Build a generic transformation DSL supporting arbitrary mapping rules.
- Store mapping definitions in a database at this stage.
- Move normalization rules into provider-specific mapping configuration.

### Consequences

Adding an ERP with the same structural characteristics now primarily requires declaring its field mapping rather than duplicating the customer transformation workflow.

Shared normalization and canonical model construction remain consistent across integrations.

Provider-specific field names remain isolated at the integration boundary.

The mapping definitions are currently stored in code. External persistence or runtime management of mappings is deliberately deferred until requirements such as independent updates, versioning, activation, or larger-scale mapping management emerge.

ADR-001 remains as the historical record of why the abstraction was intentionally deferred until sufficient implementation evidence existed.

------------------------------------------------------------------------

## ADR-005 --- Allow partial success for business validation failures during batch processing

**Status:** Accepted
**Stage:** Customer batch processing

### Context

ERP integrations commonly process multiple records as a batch.

A batch may contain valid customer records alongside records that fail supported business validation rules. Rejecting the entire batch because one customer contains invalid business data would unnecessarily discard records that can be processed correctly.

At the same time, not every exception represents invalid source data. Unexpected programming or technical failures may indicate that the processing pipeline itself is no longer behaving reliably.

Treating those failures as ordinary rejected records would hide system problems and could make a partially processed batch appear successful.

The batch processor therefore needs to distinguish between expected data-quality failures and unexpected processing failures.

### Decision

Process customer records independently and allow partial success when a record fails a supported business validation.

The processing flow is:

```text
source record
      ↓
provider mapper
      ↓
customer mapping and validation
      ↓
┌───────────────────────────────┐
│ valid                         │
│ → processed customer          │
│                               │
│ CustomerValidationError       │
│ → rejected record             │
│ → preserve raw input + reason │
│ → continue batch              │
│                               │
│ unexpected exception          │
│ → propagate                   │
│ → fail processing visibly     │
└───────────────────────────────┘
```

Supported customer business-validation failures are represented explicitly by `CustomerValidationError`.

The batch processor catches only this expected validation exception. It preserves the complete raw source record together with the rejection reason and continues processing subsequent records.

Unexpected exceptions are not converted into rejected records. They propagate to the caller so that technical or programming failures remain visible.

The batch processor receives the provider mapper as a callable rather than depending directly on ERP-specific mappings or configuration. Its responsibility is therefore limited to batch orchestration and result classification, while provider-specific transformation remains at the integration boundary.

### Trade-off

This approach allows valid records to be processed even when other records in the same batch contain invalid business data.

It also prevents unexpected technical failures from being silently misclassified as source-data problems.

However, the current implementation operates entirely in memory and does not yet provide persistence, checkpoints, retry behavior, or recovery semantics.

If an unexpected technical failure occurs after previous records have already been processed in memory, the exception propagates and a completed `BatchResult` is not returned.

This behavior is acceptable at the current stage because persistent batch execution and recovery have not yet been introduced.

### Alternatives considered

- Fail the entire batch when any individual record fails business validation.
- Catch all exceptions and convert every failure into a rejected record.
- Catch generic `ValueError` exceptions and treat them as data-validation failures.
- Make the batch processor aware of ERP-specific field mappings and transformation details.
- Introduce database transactions, checkpoints, retries, or persistent batch state before persistence requirements exist.

### Consequences

A batch can contain both successfully processed customers and explicitly rejected source records.

Rejected records preserve their original ERP representation and the reason for rejection, providing the information required for later inspection or reprocessing.

Business-validation failures have explicit semantics and do not stop processing of unrelated valid records.

Unexpected failures remain visible instead of being hidden as data-quality problems.

Batch orchestration is independent of individual ERP providers and can be tested using controlled mapper implementations.

Persistent batch state, transaction boundaries, batch identifiers, retry and reprocessing mechanisms, checkpoints, idempotency, persistent rejected-record storage, and richer error categorization remain deliberately deferred until persistence and operational processing requirements are introduced.

Persistent rejected-record output was subsequently partially addressed by ADR-009 through local JSONL serialization.

------------------------------------------------------------------------

## ADR-006 --- Validate dataset structure before record processing

**Status:** Accepted
**Stage:** CSV ingestion and structural validation

### Context

CSV ingestion introduces a failure mode that is different from an individual customer failing business validation.

A source dataset may be structurally incompatible with the selected ERP integration because one or more columns required to construct the mapped customer are missing.

For example, ERP B requires source fields for the canonical customer data as well as `client_code`, which provides the external source identity. A CSV that contains `legal_name`, `vat_number`, and `country` but omits `client_code` cannot produce a complete `ExternalSourceCustomer`.

Treating this as an ordinary per-record validation failure would cause every row to fail independently even though the actual problem affects the dataset as a whole.

The system therefore needs to distinguish dataset-level structural incompatibility from record-level business-data invalidity.

### Decision

Validate the available dataset fields before record processing begins.

The structural validation flow is:

```text
read dataset fields
        ↓
derive required source fields
        ↓
compare available vs required fields
        ↓
┌───────────────────────────────┐
│ all required fields present   │
│ → continue with record        │
│   processing                  │
│                               │
│ required fields missing       │
│ → IngestionError              │
│ → fail before processing rows │
└───────────────────────────────┘
```

Required canonical fields are derived from Pydantic model metadata rather than duplicated manually. The provider-specific field mapping is then used to translate those canonical requirements into the corresponding source column names.

Customer ingestion also explicitly requires the mapped `external_id` source field because `ExternalSourceCustomer` cannot be constructed without source identity. `source_system` does not require a dataset column because it is supplied by the ERP integration itself.

Optional canonical fields such as `email` are not required for dataset compatibility.

Missing required dataset fields raise `IngestionError`. This remains distinct from `CustomerValidationError`, which represents a structurally processable record that fails supported business validation.

### Trade-off

Structural validation adds a separate inspection step before record processing and requires the ingestion layer to expose dataset field information.

The current implementation derives canonical requirements through Pydantic introspection but still composes Customer-specific source requirements explicitly where provenance matters, such as `external_id`.

This is slightly less generic than attempting to infer every source requirement automatically from the complete output model. In return, it avoids hiding an important distinction: some required output fields come from the source dataset while others are constructed or supplied internally.

The generic required-field helper also remains strict when a required model field is absent from a field mapping. It does not silently ignore incomplete mapping configuration.

### Alternatives considered

- Start processing records immediately and allow missing columns to fail during mapping.
- Treat missing dataset columns as `CustomerValidationError` and reject every affected row independently.
- Maintain a separate manually duplicated list of required source columns for every ERP integration.
- Require every mapped field, including optional canonical fields such as `email`.
- Infer all required source fields directly from `ExternalSourceCustomer` without distinguishing source-provided values from internally supplied or constructed values.
- Make the generic required-field helper silently ignore required model fields that are absent from the provider mapping.

### Consequences

Structurally incompatible datasets fail early before any customer records are processed.

Dataset-level ingestion failures and record-level business-validation failures now have separate semantics and can be handled independently.

Required source fields remain aligned with the canonical model as requiredness evolves, while provider-specific mappings continue to define the source column names.

External source identity is treated as part of the minimum data required to construct a complete mapped customer, even though it is not a field of `CanonicalCustomer`.

Optional source columns may be absent without making the dataset structurally invalid.

Future ingestion formats can reuse the same structural-validation semantics as long as they can expose their available fields before record processing.

------------------------------------------------------------------------

## ADR-007 --- Track processing executions separately from batch results

**Status:** Accepted
**Stage:** Customer CSV orchestration and processing traceability

### Context

The batch-processing layer already distinguishes successfully processed customer records from records rejected because of supported business-validation failures.

`BatchResult` therefore answers a record-level question: which records were processed successfully and which were rejected.

Once CSV ingestion and orchestration were introduced, the system also needed to represent information about the execution as a whole. A processing attempt has context that exists independently of the individual record outcomes, including the ERP source, the input being processed, execution timestamps, and whether the dataset-level operation completed or failed.

This distinction becomes especially important for failures that occur before a batch result can exist. For example, a CSV dataset that is missing a required source column raises `IngestionError` during structural validation and cannot produce a meaningful `BatchResult`.

### Decision

Represent execution-level state using a separate `ProcessingRun` model rather than expanding `BatchResult` with orchestration metadata.

The responsibilities are:

```text
ProcessingRun
├── source_system
├── input_source
├── started_at
├── finished_at
├── status
├── result
└── error

BatchResult
├── processed
└── rejected
```

`ProcessingRunStatus` defines the execution states:

```text
RUNNING
   ├──→ COMPLETED
   └──→ FAILED
```

The customer CSV orchestrator returns a `ProcessingRun`.

A structurally valid dataset produces a `COMPLETED` run even when some individual records are rejected by supported business validation. Those rejected records remain part of the `BatchResult`.

A dataset-level ingestion failure represented by `IngestionError` produces a `FAILED` run with no `BatchResult` and preserves the error message for later inspection.

Unexpected exceptions are not converted into `FAILED` runs. They continue to propagate so that programming and technical failures are not silently normalized into expected integration outcomes.

ERP providers expose their `source_system` explicitly so that orchestration and future traceability do not need to infer provider identity indirectly from mapper implementation details.

### Trade-off

Introducing `ProcessingRun` adds a second result concept alongside `BatchResult`.

This creates a slightly richer model, but it keeps record-level processing outcomes separate from execution-level lifecycle and traceability.

The current implementation is still in memory. Processing runs do not yet have persistent identifiers, durable storage, retry or recovery state, or persistent links to processed and rejected outputs.

The `ProcessingRun` dataclass also does not currently enforce cross-field state invariants such as requiring `result` for every `COMPLETED` run or requiring `error` for every `FAILED` run. Those constraints are intentionally deferred until the lifecycle model needs stronger persistence or external serialization guarantees.

### Alternatives considered

- Add source, timestamps, status, and error metadata directly to `BatchResult`.
- Continue returning `BatchResult` on success and propagating all expected ingestion failures as exceptions.
- Mark a complete processing run as `FAILED` whenever any individual customer record is rejected.
- Catch every exception and convert it into a `FAILED` processing run.
- Introduce persistent run state, run identifiers, retries, and recovery semantics immediately.
- Infer the ERP source system indirectly from provider mapper behavior instead of declaring it explicitly.

### Consequences

Record-level and execution-level outcomes now have separate semantics.

A run may be `COMPLETED` while containing both processed and rejected records, preserving the partial-success behavior defined in ADR-005.

Dataset-level structural incompatibility can be represented as a failed execution even when no batch result exists.

The ERP source system and input source are available as execution context, creating a clean boundary for later persistence, observability, audit history, and reprocessing features.

Future storage decisions can persist `ProcessingRun`, processed outputs, and rejected outputs independently without changing the meaning of `BatchResult`.

Unexpected technical failures remain visible instead of being hidden as ordinary integration failures.

------------------------------------------------------------------------

## ADR-008 --- Generate stable canonical customer identities from normalized business identity

**Status:** Accepted
**Stage:** Canonical customer identity

### Context

`ExternalSourceCustomer` preserves the identity assigned by the originating ERP through `source_system` and `external_id`.

That identity is necessary for provenance, but it is not suitable as the common identity of a canonical customer. The same real customer may exist in multiple ERP systems under different external identifiers.

For example:

```text
ERP A / C001 ─┐
              ├── same canonical customer
ERP B / 0001 ─┘
```

Downstream canonical outputs therefore require an identifier that is independent of the originating ERP and remains stable when the same logical customer is processed again.

The current customer model already normalizes the fields used to establish business identity before canonical identity is generated.

### Decision

Generate a deterministic canonical `customer_id` using UUID5.

The identity key is constructed from the normalized canonical country and tax ID:

```text
country + tax_id
      ↓
identity key
      ↓
UUID5 with fixed namespace
      ↓
customer_id
```

For example:

```text
ES:B12345678
      ↓
25013cb5-a708-5c14-a1f1-f2ddbe8e9d35
```

The resulting identifier is represented together with the canonical customer as `IdentifiedCanonicalCustomer`.

`name` and `email` are intentionally excluded from the identity key. They may change without changing the underlying business identity of the customer.

External ERP identity is not removed from the processing model. `ExternalSourceCustomer` continues to preserve `source_system` and `external_id`, while canonical identity is derived downstream when canonical output is required.

### Trade-off

The identity rule assumes that normalized `country + tax_id` is sufficient to identify a customer for the current integration scenarios.

This is deliberately narrower than a complete entity-resolution or master-data-management strategy.

UUID5 also makes the identity-generation contract persistent: changing the namespace or the construction of the identity key would produce different identifiers for customers that had previously received stable IDs.

In return, the same normalized business identity produces the same canonical identifier without requiring a central database sequence or lookup.

### Alternatives considered

- Generate a random UUID4 for every processed customer.
- Reuse the external ERP identifier as the canonical customer identifier.
- Include mutable fields such as name or email in the identity key.
- Introduce a persistent identity-resolution database before a storage requirement exists.
- Implement probabilistic or fuzzy entity matching at this stage.

### Consequences

Equivalent customers from different ERP systems can independently produce the same canonical `customer_id`.

Repeated processing of the same normalized customer identity also produces the same identifier.

Canonical identity remains independent of source-system identifiers while source provenance is still preserved earlier in the processing flow.

The current rule does not resolve customers that represent the same real entity but have different or missing tax IDs. More advanced identity resolution should be introduced only if concrete integration scenarios require it.

The fixed UUID namespace and identity-key format must be treated as part of the canonical identity contract once persisted outputs depend on them.

------------------------------------------------------------------------

## ADR-009 --- Persist processed canonical customers as Parquet and rejected source records as JSONL

**Status:** Accepted for MVP
**Stage:** Local processing outputs

### Context

Batch processing produces two categories of record-level outcomes with different downstream purposes.

Successfully processed records have been mapped, normalized, and validated and are suitable for canonical downstream consumption.

Rejected records intentionally preserve their original ERP representation together with the reason they could not be processed.

These outputs therefore have different data shapes and operational requirements.

Processed canonical customers also require stable common identity before persistence. Multiple source records may resolve to the same canonical `customer_id`, and writing every occurrence independently would create duplicate canonical rows.

At the same time, Parquet is a file format rather than a database table and does not provide SQL-style primary-key constraints or `UPSERT` semantics.

### Decision

Persist the two output categories separately:

```text
BatchResult
├── processed
│      ↓
│   canonical identity
│      ↓
│   deduplicate by customer_id
│      ↓
│   Parquet
│
└── rejected
       ↓
    JSONL
```

Processed customers are transformed into `IdentifiedCanonicalCustomer` values and deduplicated by `customer_id` before canonical output.

The current duplicate-resolution policy is `first wins`. If multiple identified customers with the same `customer_id` appear in the input stream, the first representation is retained and subsequent representations are skipped.

The canonical Parquet output uses a flat schema:

```text
customer_id
name
tax_id
country
email
```

Source-system identity is intentionally not included in this canonical dataset. `ExternalSourceCustomer` continues to preserve provenance during processing, and a future lineage dataset may persist relationships between external identities and canonical identities if required.

Parquet output is written incrementally using bounded batches rather than materializing the complete canonical dataset in an additional in-memory collection. The batch size is configurable and defaults to 1,000 records.

Rejected records are written as JSON Lines. Each line preserves:

```text
raw_record
reason
```

This keeps the original source representation available for investigation and later reprocessing.

### Trade-off

Using different formats for processed and rejected outputs introduces two serialization paths.

The `first wins` duplicate policy is intentionally simple. If two ERP sources resolve to the same canonical identity but provide different non-identity values such as name or email, the current implementation does not reconcile them or define source priority.

The in-memory deduplication step retains the set of previously seen canonical UUIDs for the duration of the stream. Memory usage therefore grows with the number of unique identities even though complete customer objects are not accumulated by the deduplicator.

Parquet writing is batched, but the current design does not provide persistent global uniqueness or update semantics across separate executions.

### Alternatives considered

- Write processed and rejected records using the same output format.
- Preserve processed canonical output as JSON or JSONL instead of Parquet.
- Include `source_system` and `external_id` directly in the canonical customer dataset.
- Write every identified customer to Parquet and allow duplicate `customer_id` values.
- Treat a repeated `customer_id` as an update and overwrite previous values.
- Introduce source-priority or field-level reconciliation rules before conflicting source data has been observed.
- Load all processed customers into memory before writing the Parquet file.
- Introduce a database or table format with native merge/upsert semantics at this stage.

### Consequences

Processed and rejected outputs now have explicit and independent persistence representations.

The local customer pipeline orchestrates these outputs from a completed `ProcessingRun`: processed customers are identified, deduplicated, and written to Parquet, while rejected records are written to JSONL. A failed processing run with no `BatchResult` does not generate either output.

Canonical customer output contains at most one row per `customer_id` for the stream passed through the current deduplication step.

The deterministic identity defined in ADR-008 provides stable IDs, while deduplication prevents repeated identities within that processing stream from producing duplicate canonical rows.

This does not yet provide persistent idempotency across independent executions. Reprocessing data against an existing Parquet output does not currently perform a global lookup, merge, or upsert against previously persisted customer IDs.

The current `first wins` behavior should be reconsidered if concrete scenarios require source precedence, conflict resolution, field-level merging, or master-data-management semantics.

Batch-oriented Parquet writing keeps additional writer memory bounded by the configured batch size and provides a suitable local representation for later data-platform integration.

Rejected JSONL output preserves enough source context to investigate validation failures without forcing heterogeneous raw ERP records into the canonical Parquet schema.

Future durable storage can persist canonical Parquet output, rejected JSONL output, processing-run metadata, and external-to-canonical lineage independently.

------------------------------------------------------------------------

## ADR-010 --- Stream S3 input and avoid full-file in-memory output uploads

**Status:** Accepted
**Stage:** S3-backed pipeline execution

### Context

Introducing S3 created two additional memory boundaries around the existing customer-processing pipeline.

For input, reading the complete S3 object into `bytes` before processing would require the whole source dataset to fit in memory and would also create an unnecessary temporary `input.csv`.

For output, reading generated Parquet and JSONL files back with `Path.read_bytes()` before uploading them would create an additional complete in-memory copy of each file.

### Decision

Consume S3 CSV input directly from the object response stream:

```text
S3 object
   ↓
StreamingBody
   ↓
TextIOWrapper
   ↓
single-pass CSV structure + record parsing
   ↓
process_customer_stream()
```

Local-file and S3-backed execution therefore share the same stream-oriented customer-processing core.

For outputs, continue writing Parquet and JSONL to local temporary files, but upload those files using Boto3 file transfer instead of `Path.read_bytes()` followed by an in-memory object upload.

```text
ProcessingRun
   ↓
shared output processing
   ↓
temporary Parquet / JSONL files
   ↓
Boto3 file upload
   ↓
S3
```

S3 integration is developed and tested against MiniStack through Boto3, both locally and in GitHub Actions.

### Trade-off

The S3 input path no longer requires the complete object to be held in memory and does not create a temporary input file.

Output upload also avoids loading the complete generated file into memory before transfer.

However, generated Parquet and JSONL outputs still use temporary local files. The current implementation therefore improves memory behavior without claiming to provide a fully diskless streaming pipeline.

Keeping temporary output files is accepted at this stage because Parquet serialization already writes in bounded batches and removing the file boundary would add complexity around seekable output targets, multipart upload behavior, buffering, failure recovery, and finalization.

MiniStack validates the S3 API integration but does not replace validation of IAM, networking, service limits, observability, or other operational concerns in a real AWS environment.

### Alternatives considered

- Read the complete S3 input object into memory before processing.
- Download the S3 input to a temporary local file.
- Read generated output files completely with `Path.read_bytes()` before uploading them.
- Eliminate all temporary output files immediately.
- Implement multipart upload orchestration directly.
- Use a real AWS account for development and CI.

### Consequences

S3 input shares the same stream-oriented processing core as local CSV ingestion.

The S3 execution path does not create a temporary `input.csv` and does not require a complete in-memory copy of the source object before processing.

Generated Parquet and JSONL outputs retain their bounded local serialization behavior, while S3 upload no longer creates an additional complete `bytes` representation of each file.

MiniStack allows the S3 integration boundary to be exercised locally and in GitHub Actions without incurring AWS infrastructure costs.

Real AWS deployment remains a separate future concern.

------------------------------------------------------------------------

## ADR-011 --- Introduce a Spark DataFrame processing path without replacing the stream-oriented Python pipeline

**Status:** Accepted
**Stage:** Distributed processing and AWS Glue preparation

### Context

The existing Python pipeline already provides validated semantics for local files and S3-backed execution: provider mapping, normalization, validation, canonical identity, deduplication, processed Parquet output, and rejected-record output.

The next concrete requirement is to prepare the project for AWS Glue, whose managed ETL execution model is built around Apache Spark.

Replacing the existing Python pipeline with Spark would couple previously validated stream-oriented behavior to a distributed execution engine. At the same time, wrapping the existing row-by-row Python pipeline unchanged inside Glue would not make meaningful use of Spark's DataFrame execution model.

### Decision

Introduce a separate Spark DataFrame processing path.

The Spark path preserves the same canonical intent while expressing transformations using DataFrame operations:

```text
source dataset
      ↓
Spark DataFrame
      ↓
provider structural mapping
      ↓
normalization
      ↓
validation
      ↓
processed / rejected DataFrames
      ↓
canonical identity
      ↓
deduplication
      ↓
Parquet / JSON outputs
```

The existing Python stream-oriented pipeline remains valid for its local-file and S3-backed use cases.

### Trade-off

The repository now contains two processing implementations, so canonical semantics must remain intentionally aligned between them.

This duplication is accepted because the execution models solve different problems. The Python path is explicit and stream-oriented, while the Spark path delegates distributed transformation planning and execution to Spark.

### Alternatives considered

- Replace the existing Python pipeline entirely with Spark.
- Run the existing row-by-row Python processing unchanged inside Glue.
- Introduce Spark and Glue simultaneously during deployment.
- Build a generic execution-engine abstraction before both implementations existed.

### Consequences

Spark-specific behavior can be tested independently.

The project can demonstrate both stream-oriented processing and distributed DataFrame processing.

The Spark path becomes the processing core used by the AWS Glue adapter.

------------------------------------------------------------------------

## ADR-012 --- Prefer native Spark DataFrame expressions and use a localized Python UDF for UUID5 identity

**Status:** Accepted
**Stage:** Spark transformation design

### Context

Spark transformations can be expressed using native DataFrame operations or Python UDFs.

Native expressions remain visible to Spark's planner and are generally preferable for mapping, normalization, validation, filtering, and deduplication.

Canonical customer identity already has an established contract: normalized `country + tax_id` is converted to UUID5 using a fixed namespace.

Changing the algorithm only to avoid a Python UDF would cause the same customer to receive different identifiers depending on the processing engine.

### Decision

Use native Spark DataFrame expressions for structural mapping, normalization, validation, filtering, and deduplication.

Use a localized Python UDF only for UUID5 identity generation so that the Spark and Python pipelines preserve the same canonical `customer_id` contract.

### Trade-off

The UUID5 UDF introduces a JVM/Python execution boundary and may be less efficient than a fully native Spark expression.

That cost is accepted because identity consistency across processing engines is more important than replacing the established contract with a different hash.

### Alternatives considered

- Implement all Spark transformations as Python UDFs.
- Replace UUID5 with a Spark-native hash.
- Generate identity only after collecting Spark rows into Python.
- Maintain different identity schemes for Python and Spark.

### Consequences

Most transformations remain Spark-native and optimizable.

Canonical identity remains consistent between Python and Spark.

If identity generation becomes a measured performance bottleneck, its implementation can be revisited without silently changing the canonical identity contract.

------------------------------------------------------------------------

## ADR-013 --- Keep AWS Glue runtime concerns outside the reusable Spark processing core

**Status:** Accepted
**Stage:** AWS Glue integration

### Context

AWS Glue introduces runtime-specific concepts including `getResolvedOptions`, `SparkContext`, `GlueContext`, Glue `Job`, `Job.init`, and `Job.commit`.

Embedding these concerns directly inside Spark transformation functions would make the processing core dependent on AWS Glue and harder to test locally.

The `awsglue` package is also supplied by the target Glue runtime rather than being a normal local dependency.

### Decision

Keep the Glue entry point thin and separate runtime adaptation from reusable Spark processing.

```text
glue/main.py
      ↓
Glue runtime setup
      ↓
glue/runtime.py
      ↓
CustomerJobArguments
      ↓
glue/customer_job.py
      ↓
source mapping selection
      ↓
spark/run.py
      ↓
Spark processing core
```

`main.py` owns Glue runtime initialization and lifecycle.

`runtime.py` converts resolved Glue options into the project's job-argument model.

`customer_job.py` selects the source mapping and delegates to the Spark pipeline.

### Trade-off

The Glue integration contains several small modules instead of one self-contained script.

This adds some structure, but each module has a narrow responsibility and the Spark processing core remains independently testable.

### Alternatives considered

- Put Glue initialization, mapping selection, transformations, and output logic in one script.
- Make Spark modules import `awsglue` directly.
- Install the Glue runtime locally as a normal project dependency.
- Mock the entire Glue runtime throughout the Spark test suite.

### Consequences

Spark transformation tests do not require AWS Glue.

Glue-specific imports remain isolated.

The Glue entry point remains close to the target runtime while reusable processing code remains platform-independent.

------------------------------------------------------------------------

## ADR-014 --- Treat Spark and AWS Glue libraries as runtime-provided deployment dependencies

**Status:** Accepted
**Stage:** Packaging and runtime compatibility

### Context

The project is packaged as a Python wheel for deployment.

A clean wheel installation demonstrated that Spark-dependent modules cannot be imported in a bare Python environment without PySpark.

That does not mean PySpark should be bundled into the application wheel. AWS Glue supplies Spark/PySpark and `awsglue` as part of its managed runtime.

### Decision

Keep the project wheel focused on project-owned Python code.

PySpark remains a development and test dependency, while Spark/PySpark and `awsglue` are treated as runtime-provided dependencies in AWS Glue.

Static analysis explicitly tolerates missing local `awsglue.*` implementations because those modules intentionally exist only in the target runtime.

### Trade-off

A completely bare Python environment cannot execute Spark-dependent project modules unless PySpark is installed separately.

Likewise, the Glue entry point cannot run as an ordinary local script without a Glue-compatible runtime.

These limitations are accepted because they reflect the target platform boundary rather than missing application dependencies.

### Alternatives considered

- Add PySpark as a normal production dependency of the wheel.
- Vendor AWS Glue libraries into the project.
- Disable static analysis for the complete Glue module.
- Avoid packaging the Spark/Glue integration with the project.

### Consequences

The project artifact reflects dependency ownership more accurately.

Development and CI environments install PySpark explicitly.

The target Glue runtime is responsible for providing Spark and Glue libraries.

------------------------------------------------------------------------

## ADR-015 --- Support Python 3.11 for the AWS Glue target runtime

**Status:** Accepted
**Stage:** AWS Glue runtime compatibility

### Context

Local development had primarily used Python 3.12, while the selected Glue target runtime uses Python 3.11.

A successful Python 3.12 test run does not prove that source syntax, dependencies, packaging metadata, or behavior are compatible with Python 3.11.

### Decision

Lower the project's supported Python floor to 3.11 and verify the target runtime explicitly.

Compatibility was checked by compiling the source and tests under Python 3.11, executing the test suite with Python 3.11, rebuilding the wheel, and installing that wheel in a clean Python 3.11 environment.

### Trade-off

Supporting Python 3.11 adds another compatibility dimension and prevents adopting Python-only features that require a newer minimum version without reconsidering the Glue target.

### Alternatives considered

- Assume Python 3.12 compatibility implies Python 3.11 compatibility.
- Discover version incompatibilities only during Glue deployment.
- Change the Glue target solely to match the development interpreter.
- Maintain a separate Glue-specific source tree.

### Consequences

The project declares `requires-python = ">=3.11"`.

Python 3.11 compatibility is supported by executable evidence rather than assumption.

Local development may still use Python 3.12.

------------------------------------------------------------------------

## ADR-016 --- Validate Spark filesystem output in Linux CI when local Windows Hadoop support is insufficient

**Status:** Accepted for development
**Stage:** Spark test execution

### Context

Spark transformations run locally on Windows, but some local filesystem write operations depend on Hadoop-native behavior that may require Windows-specific utilities such as `winutils`.

Adding arbitrary native binaries only to make local output tests pass would introduce environment and security complexity unrelated to the Linux-based Glue target.

### Decision

Keep Spark transformation and non-problematic tests runnable locally.

Tests that specifically depend on unsupported Windows Hadoop filesystem behavior are skipped on Windows and executed normally in Linux CI.

Do not weaken production output behavior or introduce unofficial Windows-native binaries merely to eliminate the local skips.

### Trade-off

The local Windows test run contains intentional skips and therefore does not exercise every Spark filesystem output path.

Those behaviors must remain covered by Linux CI.

### Alternatives considered

- Install an unofficial `winutils` binary.
- Remove Spark filesystem output tests.
- Mock all Spark writes.
- Change output behavior solely to accommodate Windows.
- Require local Linux development.

### Consequences

Local development remains simpler and safer.

Linux CI becomes part of the Spark validation strategy rather than only a duplicate of local execution.

------------------------------------------------------------------------

## ADR-017 --- Keep Glue job inputs explicit and supplied at execution time

**Status:** Accepted
**Stage:** Glue job orchestration

### Context

The Glue job must know which ERP mapping to use and where to read and write data.

Hard-coding those values would mix stable job implementation with one particular execution and could require separate scripts or job definitions for different ERP sources.

### Decision

Represent the current job execution contract using:

```text
source_system
input_path
processed_path
rejected_path
```

`source_system` selects one of the supported mappings for ERP A, ERP B, or ERP C.

Input and output paths are execution-time configuration.

### Trade-off

The mapping registry is still code-based, so adding an ERP requires a code change and deployment.

The argument contract is intentionally small and does not yet attempt to model arbitrary transformation configuration, schema versions, retries, or operational tuning.

### Alternatives considered

- Hard-code paths and source system in the Glue entry point.
- Create one Glue implementation per ERP.
- Store mappings and all runtime configuration in a database immediately.
- Build a generic dynamic configuration platform before a concrete requirement exists.

### Consequences

One Glue job implementation can execute against multiple supported ERP layouts.

Stable infrastructure concerns remain separate from run-specific data locations.

External mapping persistence remains deliberately deferred until requirements such as independent updates, versioning, activation, or larger-scale mapping management emerge.

------------------------------------------------------------------------

## ADR-018 --- Defer commitment to a Glue infrastructure definition until MiniStack deployment is validated end to end

**Status:** Accepted for current stage
**Stage:** Glue deployment preparation

### Context

The Glue application boundary, target-runtime compatibility, and packaging strategy are implemented, but the deployment mechanism has not yet been validated end to end.

CloudFormation was explored as one possible infrastructure mechanism, but the draft template has not been used to create and execute the project job.

MiniStack has now been verified to expose the Glue `GetJobs` API, providing a concrete local control-plane boundary for the next deployment stage.

Committing an unvalidated infrastructure template would present an experiment as a supported deployment capability.

### Decision

Do not treat the current CloudFormation draft as completed project infrastructure.

First exercise the local Glue deployment flow end to end:

```text
build project artifact
      ↓
make script and artifact available
      ↓
create or update Glue job
      ↓
start Glue job run
      ↓
execute Spark pipeline
      ↓
write processed / rejected outputs
      ↓
verify results
```

Once the working command sequence is known, provide reproducible deployment scripts for both Windows and Linux and decide which infrastructure definition belongs in the repository.

### Trade-off

The repository does not yet contain a committed, reproducible Glue deployment definition.

That is accepted temporarily because it is more accurate than presenting an unproven draft as finished infrastructure.

### Alternatives considered

- Commit the current CloudFormation draft immediately.
- Require a real AWS account before continuing.
- Treat a successful `GetJobs` call as equivalent to a successful job deployment.
- Provide only Windows deployment automation.

### Consequences

The current documentation can distinguish clearly between implemented Glue integration code and pending Glue deployment.

The next stage has an observable acceptance criterion: a reproducible MiniStack Glue job run that produces verifiable outputs on both supported scripting paths.

# Known Technical Debt

## TD-001 --- Persistent idempotency across processing executions

**Related decisions:** ADR-008, ADR-009

### Current limitation

Deduplication currently applies only within a single processing execution.

The deduplication state (`seen_customer_ids`) is held in memory for the duration of the stream and is discarded when the execution finishes. A later execution therefore does not know which canonical customer IDs were persisted by previous runs.

The deterministic UUID5 identity defined in ADR-008 ensures that the same normalized business identity produces the same `customer_id` across executions. It does not, by itself, prevent that customer from being persisted again in a later execution.

This affects scenarios such as:

- retrying the same input file after a failure;
- intentionally reprocessing a previously processed file;
- receiving a later ERP export containing customers that were already processed in an earlier run.

In each case, a later execution may produce a `customer_id` that already exists in previously persisted canonical output. The current Parquet output does not perform a global lookup, merge, or upsert against that prior state.

### Why it is deferred

Persistent cross-run idempotency depends on the final persistence strategy and on the required semantics for repeated customers. The system will need to decide whether an existing canonical customer should be ignored, updated, or reconciled when new data for the same `customer_id` arrives.

Introducing a database, global index, merge process, or table format with update semantics before those persistence requirements are established would prematurely constrain the design.

### Future resolution

When durable persistence is introduced, the architecture must provide an explicit mechanism for detecting previously persisted `customer_id` values across executions and define the behavior for repeated identities.

Until then, the current guarantees are deliberately limited to deterministic canonical identity and in-stream deduplication within a processing execution. Persistent idempotency across independent executions is not guaranteed.
