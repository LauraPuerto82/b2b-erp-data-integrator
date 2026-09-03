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

Canonical customer output contains at most one row per `customer_id` for the stream passed through the current deduplication step.

The deterministic identity defined in ADR-008 provides stable IDs, while deduplication prevents repeated identities within that processing stream from producing duplicate canonical rows.

This does not yet provide persistent idempotency across independent executions. Reprocessing data against an existing Parquet output does not currently perform a global lookup, merge, or upsert against previously persisted customer IDs.

The current `first wins` behavior should be reconsidered if concrete scenarios require source precedence, conflict resolution, field-level merging, or master-data-management semantics.

Batch-oriented Parquet writing keeps additional writer memory bounded by the configured batch size and provides a suitable local representation for later data-platform integration.

Rejected JSONL output preserves enough source context to investigate validation failures without forcing heterogeneous raw ERP records into the canonical Parquet schema.

Future durable storage can persist canonical Parquet output, rejected JSONL output, processing-run metadata, and external-to-canonical lineage independently.

# Known Technical Debt

No known technical debt has been recorded yet.

Technical limitations that are deliberately accepted as the project evolves will be documented here when they represent unresolved engineering work rather than an architectural decision.
