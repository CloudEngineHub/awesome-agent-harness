#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import yaml

from render_readme import (
    DATA_FILE,
    README_EN,
    README_ZH,
    REQUIRED_ENTRY_FIELDS,
    github_ratio,
    render_readmes,
)

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "verification"
URL_RE = re.compile(r"https?://[^\s)>\"]+")
READINGS_CATEGORY = "Essential Readings & Ecosystem Maps"


def load_catalog() -> dict[str, Any]:
    with DATA_FILE.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("Invalid catalog file.")
    return data


def is_github(url: str) -> bool:
    return "github.com/" in url.lower()


def check_url(url: str, timeout: int = 12) -> tuple[str, bool, str]:
    headers = {"User-Agent": "awesome-agent-harness-verify"}
    try:
        req = urllib.request.Request(url, method="HEAD", headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = getattr(resp, "status", 200)
            if 200 <= code < 400:
                return (url, True, f"HEAD {code}")
    except urllib.error.HTTPError as e:
        if e.code in (405, 429):
            pass
        else:
            # still attempt GET fallback
            pass
    except Exception:
        pass

    try:
        req = urllib.request.Request(url, method="GET", headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = getattr(resp, "status", 200)
            if 200 <= code < 400:
                return (url, True, f"GET {code}")
            return (url, False, f"GET {code}")
    except Exception as e:
        return (url, False, str(e))


def gather_links() -> list[str]:
    urls: set[str] = set()
    for path in (README_EN, README_ZH):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for raw in URL_RE.findall(text):
            cleaned = raw.strip().strip("()[]{}<>,;\"'")
            if cleaned:
                if "img.shields.io/" in cleaned:
                    continue
                urls.add(cleaned)
    return sorted(urls)


def write_report(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify catalog integrity and link health.")
    parser.add_argument("--skip-links", action="store_true", help="Skip URL reachability checks")
    args = parser.parse_args()

    catalog = load_catalog()
    categories = [c["name_en"] for c in catalog.get("categories", [])]
    entries: list[dict[str, Any]] = catalog.get("entries", [])
    errors: list[str] = []
    warnings: list[str] = []

    # Schema checks
    for idx, entry in enumerate(entries):
        missing = [f for f in REQUIRED_ENTRY_FIELDS if f not in entry]
        if missing:
            errors.append(f"entry[{idx}] `{entry.get('name', '<unknown>')}` missing fields: {missing}")
        if entry.get("category") not in categories:
            errors.append(f"entry[{idx}] `{entry.get('name')}` has invalid category `{entry.get('category')}`")

    # Duplicate checks
    names = [str(e.get("name", "")).strip().lower() for e in entries]
    urls = [str(e.get("repo_url", "")).strip().lower() for e in entries]
    dup_names = [n for n, c in Counter(names).items() if n and c > 1]
    dup_urls = [u for u, c in Counter(urls).items() if u and c > 1]
    if dup_names:
        errors.append(f"duplicate names: {dup_names[:10]}")
    if dup_urls:
        errors.append(f"duplicate urls: {dup_urls[:10]}")

    # Activity checks for GitHub entries
    today = dt.date.today()
    threshold = today - dt.timedelta(days=365)
    stale: list[str] = []
    for e in entries:
        url = str(e.get("repo_url", ""))
        if not is_github(url):
            continue
        raw_date = str(e.get("updated_at", "1970-01-01"))
        try:
            d = dt.date.fromisoformat(raw_date)
        except Exception:
            errors.append(f"invalid updated_at date format for `{e.get('name')}`: `{raw_date}`")
            continue
        if d < threshold:
            stale.append(f"{e.get('name')} ({raw_date})")

    if stale:
        errors.append(f"stale github entries (>12 months): {len(stale)}")

    gh_count, total_count, ratio = github_ratio(entries)
    project_entries = [e for e in entries if e.get("category") != READINGS_CATEGORY]
    project_gh_count, project_total_count, project_ratio = github_ratio(project_entries)
    if total_count < 80:
        errors.append(f"entry count too small: {total_count} < 80")
    if project_ratio < 90.0:
        errors.append(
            f"project-category GitHub ratio too low: {project_ratio:.1f}% < 90.0% "
            f"(excluding `{READINGS_CATEGORY}`)"
        )
    if ratio < 80.0:
        warnings.append(f"overall GitHub ratio is {ratio:.1f}% (blogs/readings can lower this)")

    # Mirror check by regenerating and comparing
    rendered_en, rendered_zh = render_readmes(catalog)
    current_en = README_EN.read_text(encoding="utf-8") if README_EN.exists() else ""
    current_zh = README_ZH.read_text(encoding="utf-8") if README_ZH.exists() else ""
    if current_en != rendered_en:
        errors.append("README.md is out of sync with data/projects.yaml")
    if current_zh != rendered_zh:
        errors.append("README_zh.md is out of sync with data/projects.yaml")

    # Category counts
    counts = Counter([e.get("category", "") for e in entries])

    # Link checks
    reachable: list[tuple[str, str]] = []
    broken: list[tuple[str, str]] = []
    links = gather_links() if not args.skip_links else []
    if not args.skip_links:
        with ThreadPoolExecutor(max_workers=16) as pool:
            futures = [pool.submit(check_url, u) for u in links]
            for fut in as_completed(futures):
                url, ok, detail = fut.result()
                if ok:
                    reachable.append((url, detail))
                else:
                    broken.append((url, detail))
        if broken:
            errors.append(f"broken urls: {len(broken)}")

    # Report
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    date_stamp = dt.date.today().isoformat()
    report_path = REPORT_DIR / f"{date_stamp}.md"
    lines: list[str] = []
    lines.append("# Verification Report")
    lines.append("")
    lines.append(f"- Generated at: `{now}`")
    lines.append(f"- Total entries: `{total_count}`")
    lines.append(f"- GitHub entries: `{gh_count}` ({ratio:.1f}%)")
    lines.append(
        f"- GitHub in project categories (excluding `{READINGS_CATEGORY}`): "
        f"`{project_gh_count}/{project_total_count}` ({project_ratio:.1f}%)"
    )
    lines.append(f"- Categories: `{len(categories)}`")
    lines.append(f"- URL checks: `{len(links)}` total, `{len(reachable)}` reachable, `{len(broken)}` broken")
    lines.append("")
    lines.append("## Category Counts")
    lines.append("")
    lines.append("| Category | Entries |")
    lines.append("| --- | ---: |")
    for c in categories:
        lines.append(f"| {c} | {counts.get(c, 0)} |")
    lines.append("")
    lines.append("## Structural Errors")
    lines.append("")
    if errors:
        for e in errors:
            lines.append(f"- {e}")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Warnings")
    lines.append("")
    if warnings:
        for w in warnings:
            lines.append(f"- {w}")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Broken URLs")
    lines.append("")
    if broken:
        for url, detail in sorted(broken)[:200]:
            lines.append(f"- `{detail}` {url}")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Reachable URL Sample")
    lines.append("")
    for url, detail in sorted(reachable)[:30]:
        lines.append(f"- `{detail}` {url}")

    write_report(report_path, lines)
    print(f"Wrote report: {report_path}")

    if errors:
        print("Verification failed.")
        for e in errors:
            print(f"- {e}")
        sys.exit(1)
    print("Verification passed.")


if __name__ == "__main__":
    main()
