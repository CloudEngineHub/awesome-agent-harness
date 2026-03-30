# Harness Taxonomy Iterations (v1)

This document records the 5-step iteration process used to redesign the catalog
from a generic “agent tools” view to a harness-first structure.

## Iteration 1: Clarify the object

Problem:
- Category names were too tool-type oriented.
- “Harness” itself was not explicitly defined.

Decision:
- Define harness as the reliability layer around model calls:
  orchestration + context/state + execution + protocol + eval + observability +
  governance.

Output:
- Added explicit harness definition in README templates.

## Iteration 2: Replace tool buckets with harness primitives

Problem:
- Original categories mixed implementation artifacts and domains.

Decision:
- Shift to primitive-oriented axes:
  architecture, context/state, execution, protocol contracts, evaluation,
  observability, governance, and reference implementations.

Output:
- New taxonomy draft with 9 categories (instead of flat generic buckets).

## Iteration 3: Re-map existing 100+ entries

Problem:
- Legacy entries still attached to old category names.

Decision:
- Bulk remap old categories to new taxonomy.
- Move context-heavy items into dedicated “Context & Working-State Engineering”.

Output:
- Full catalog category migration in `data/projects.yaml`.

## Iteration 4: Fill taxonomy gaps

Problem:
- Context category was underrepresented.

Decision:
- Add context-specific practical repos (`claude-mem`, `context-space`,
  `everything-claude-code`) to improve harness coverage.

Output:
- Better balance across harness primitives, still keeping GitHub-majority ratio.

## Iteration 5: Regenerate and verify

Problem:
- Presentation still exposed per-row update dates and weakly reflected
  markdown-first style.

Decision:
- Remove `Updated` column from all tables (keep one global verification date).
- Keep `updated_at` in data/verification only.
- Harden `.gitignore` to markdown-first defaults while keeping `scripts/*.py`.

Output:
- Regenerated mirrored README files.
- Verification passes with schema, ratio, link health, and mirror checks.

## Final Taxonomy (v1)

1. Harness Architecture & Orchestration
2. Context & Working-State Engineering
3. Execution Substrates & Sandboxing
4. Protocols, Tool Interfaces & Agent Contracts
5. Evaluation Harnesses & Benchmarks
6. Observability & Reliability Operations
7. Guardrails, Security & Governance
8. Reference Harness Implementations
9. Essential Readings & Ecosystem Maps

