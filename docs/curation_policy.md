# Curation Policy

## Scope

- Domain: harness engineering for AI agents.
- Focus: implementation-first resources, mainly GitHub projects.
- Initial target size: 80+ entries.
- Language: mirrored English/Chinese README files.

Harness is defined as the reliability layer around a model, including
orchestration, context/state management, execution environments, tool
interfaces, evaluation, observability, and governance.

## Inclusion Criteria

For project entries:

- Directly relevant to harness reliability, control, evaluation, execution, or
  operations.
- Active in the last 12 months (`updated_at`).
- Public and non-archived.
- Short practical description (EN + ZH) that explains harness value.

For non-project references:

- Limited to high-signal methodology references (typically 5-10 entries).
- Must be primary technical write-ups, not generic commentary.

## Fixed Taxonomy (Order)

1. Harness Architecture & Orchestration
2. Context & Working-State Engineering
3. Execution Substrates & Sandboxing
4. Protocols, Tool Interfaces & Agent Contracts
5. Evaluation Harnesses & Benchmarks
6. Observability & Reliability Operations
7. Guardrails, Security & Governance
8. Reference Harness Implementations
9. Essential Readings & Ecosystem Maps

## Data Contract

The single source of truth is `data/projects.yaml`.

Required fields per entry:

`name | repo_url | category | summary_en | summary_zh | tags | stars_snapshot | updated_at | why_included`

## Synchronization Rules

- `README.md` and `README_zh.md` must be generated from the same data file.
- Category order and entry order must be identical across languages.
- New entries should be inserted in their category and then sorted by stars
  descending, tie-broken by name.
