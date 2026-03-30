# Contributing

Thanks for improving **Awesome Agent Harness**.

## What belongs here

Please add items that help practitioners build reliable agent harnesses in real
workflows, especially:

- harness runtimes and orchestrators
- coding-agent systems with inspectable workflows
- sandboxed execution environments
- benchmark/eval harnesses
- observability and AgentOps tooling
- protocols/specs/repo-local agent instruction standards
- guardrails, gateways, and governance controls

Out of scope (unless directly harness-related):

- generic AI news
- pure model-release announcements
- paper-only entries without practical implementation value

## Quality bar

For GitHub projects, prefer entries that are:

- active in the last 12 months
- clearly scoped (what problem they solve in harness engineering)
- reasonably documented
- non-duplicative with existing entries

No hard star threshold is required.

## Source of truth

This repository is data-driven:

- Edit **only** `data/projects.yaml` for entry changes.
- Run:

```bash
python3 scripts/sync_github_metadata.py
python3 scripts/render_readme.py
python3 scripts/verify_catalog.py
```

- Commit generated files together (`README.md`, `README_zh.md`, verification
  report) with your data changes.

## Entry schema

Every entry in `data/projects.yaml` must include:

- `name`
- `repo_url`
- `category`
- `summary_en`
- `summary_zh`
- `tags`
- `stars_snapshot`
- `updated_at`
- `why_included`

## Pull request checklist

- Link is reachable
- Category is correct
- Summary is concise and practical
- Mirrors render cleanly in both READMEs
- Verification passes
