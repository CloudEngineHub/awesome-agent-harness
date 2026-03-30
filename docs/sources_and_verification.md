# Sources and Verification

## Collection Strategy

Initial population follows a two-channel strategy:

1. Seed curation from high-signal harness and agent engineering lists.
2. Structured GitHub discovery with targeted queries (runtime, sandbox, eval,
   observability, protocol/spec, governance).
3. Reusable query templates in `docs/github_query_templates.md`.

## Primary Seed References

- [walkinglabs/awesome-harness-engineering](https://github.com/walkinglabs/awesome-harness-engineering)
- [e2b-dev/awesome-ai-agents](https://github.com/e2b-dev/awesome-ai-agents)
- [Meirtz/Awesome-Context-Engineering](https://github.com/Meirtz/Awesome-Context-Engineering)

## Verification Workflow

Run:

```bash
python3 scripts/sync_github_metadata.py
python3 scripts/render_readme.py
python3 scripts/verify_catalog.py
```

Verification covers:

- schema completeness
- category validity and ordering
- duplicate names/links
- GitHub entry activity window (last 12 months)
- mirror consistency across README files
- external link reachability (`HEAD`, then `GET` fallback)
- category counts and GitHub ratio:
  - project categories (excluding readings) target `>= 90%`
  - overall ratio reported for transparency

Reports are written to:

- `reports/verification/YYYY-MM-DD.md`
