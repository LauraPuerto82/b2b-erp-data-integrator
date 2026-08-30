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

------------------------------------------------------------------------

# Known Technical Debt

No known technical debt has been recorded yet.

Technical limitations that are deliberately accepted as the project evolves will be documented here when they represent unresolved engineering work rather than an architectural decision.
