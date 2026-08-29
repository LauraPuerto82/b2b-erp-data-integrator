# Architecture Decisions & Known Technical Debt

This document records significant architectural decisions, trade-offs, and known technical limitations in the **B2B ERP Data Integrator**.

The goal is not to document every implementation detail. It is to make important engineering decisions explicit: **what problem existed, what was decided, why, which alternatives were considered, and what limitations are intentionally being accepted at the current stage of the project.**

The system is being built incrementally around concrete ERP integration scenarios. Rather than designing abstractions for hypothetical requirements upfront, the project starts with explicit implementations and introduces reusable components when recurring patterns and requirements emerge.

Some decisions are therefore intentionally scoped to the current stage of the project and may evolve as additional ERP formats, data entities, validation requirements, and processing scenarios are introduced.

------------------------------------------------------------------------

# Architecture Decisions

## ADR-001 --- Keep initial ERP field mappings in provider-specific code

**Status:** Accepted
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

# Known Technical Debt

No known technical debt has been recorded yet.

Technical limitations that are deliberately accepted as the project evolves will be documented here when they represent unresolved engineering work rather than an architectural decision.
