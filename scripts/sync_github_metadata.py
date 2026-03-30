#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "projects.yaml"
GITHUB_RE = re.compile(r"https?://github\.com/([^/]+)/([^/#?]+)")


def load_catalog() -> dict[str, Any]:
    with DATA_FILE.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("Invalid catalog file.")
    return data


def save_catalog(data: dict[str, Any]) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, width=120)


def get_token() -> str | None:
    env_token = os.getenv("GITHUB_TOKEN")
    if env_token:
        return env_token
    try:
        out = subprocess.check_output(["gh", "auth", "token"], text=True, stderr=subprocess.DEVNULL).strip()
        return out or None
    except Exception:
        return None


def fetch_repo(owner: str, repo: str, token: str | None) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "awesome-agent-harness-sync"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_repo_via_gh(owner: str, repo: str) -> dict[str, Any]:
    out = subprocess.check_output(
        [
            "gh",
            "repo",
            "view",
            f"{owner}/{repo}",
            "--json",
            "nameWithOwner,stargazerCount,updatedAt,pushedAt,isArchived,isPrivate,licenseInfo",
        ],
        text=True,
    )
    payload = json.loads(out)
    return {
        "full_name": payload.get("nameWithOwner", f"{owner}/{repo}"),
        "stargazers_count": payload.get("stargazerCount", 0),
        "updated_at": payload.get("updatedAt"),
        "pushed_at": payload.get("pushedAt"),
        "archived": payload.get("isArchived", False),
        "private": payload.get("isPrivate", False),
        "license": {
            "spdx_id": (
                ((payload.get("licenseInfo") or {}).get("key"))
                if payload.get("licenseInfo")
                else None
            )
        },
    }


def fetch_repo_with_retry(owner: str, repo: str, token: str | None) -> dict[str, Any]:
    last_err: Exception | None = None
    for i in range(3):
        try:
            return fetch_repo(owner, repo, token)
        except Exception as e:
            last_err = e
            time.sleep(0.25 * (2**i))
    # Fallback to gh CLI when direct API requests are flaky.
    try:
        return fetch_repo_via_gh(owner, repo)
    except Exception as e:
        if last_err:
            raise RuntimeError(f"{last_err}; fallback error: {e}") from e
        raise


def normalize_license(payload: dict[str, Any]) -> str:
    lic = payload.get("license")
    if not lic:
        return "none"
    return lic.get("spdx_id") or lic.get("key") or "unknown"


def main() -> None:
    catalog = load_catalog()
    token = get_token()
    entries = catalog.get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("`entries` must be a list.")

    total = 0
    updated = 0
    warnings: list[str] = []
    github_jobs: list[tuple[int, str, str]] = []
    for idx, entry in enumerate(entries):
        total += 1
        url = str(entry.get("repo_url", ""))
        m = GITHUB_RE.match(url)
        if m:
            owner, repo = m.group(1), m.group(2).removesuffix(".git")
            github_jobs.append((idx, owner, repo))

    print(f"Total entries: {total}")
    print(f"GitHub entries to sync: {len(github_jobs)}")

    def worker(job: tuple[int, str, str]) -> tuple[int, dict[str, Any] | None, str | None]:
        idx, owner, repo = job
        try:
            payload = fetch_repo_with_retry(owner, repo, token)
            return idx, payload, None
        except urllib.error.HTTPError as e:
            return idx, None, f"{owner}/{repo}: HTTP {e.code}"
        except Exception as e:  # pragma: no cover
            return idx, None, f"{owner}/{repo}: {e}"

    done = 0
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(worker, j) for j in github_jobs]
        for fut in as_completed(futures):
            idx, payload, err = fut.result()
            done += 1
            if done % 10 == 0 or done == len(github_jobs):
                print(f"Synced {done}/{len(github_jobs)} ...")
            if err:
                warnings.append(err)
                continue

            assert payload is not None
            entry = entries[idx]
            owner, repo = payload["full_name"].split("/", 1)
            entry["stars_snapshot"] = int(payload.get("stargazers_count", 0))
            pushed = payload.get("pushed_at") or payload.get("updated_at") or ""
            entry["updated_at"] = pushed.split("T")[0] if pushed else "1970-01-01"
            entry["license"] = normalize_license(payload)
            if payload.get("archived"):
                warnings.append(f"archived repo: {owner}/{repo}")
            if payload.get("private"):
                warnings.append(f"private repo: {owner}/{repo}")
            updated += 1

    # Keep deterministic ordering for mirrors.
    category_order = [c["name_en"] for c in catalog.get("categories", [])]
    order_map = {name: i for i, name in enumerate(category_order)}
    entries.sort(
        key=lambda x: (
            order_map.get(x.get("category", ""), 999),
            -int(x.get("stars_snapshot", 0)),
            str(x.get("name", "")).lower(),
        )
    )

    catalog.setdefault("catalog", {})
    catalog["catalog"]["last_verified"] = dt.date.today().isoformat()

    save_catalog(catalog)

    print(f"Processed entries: {total}")
    print(f"GitHub metadata refreshed: {updated}")
    if warnings:
        print("Warnings:")
        for w in warnings:
            print(f"- {w}")
    print("Done.")


if __name__ == "__main__":
    main()
