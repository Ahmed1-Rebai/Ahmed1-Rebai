"""Collect contribution and language stats for the activity card.

With a token that belongs to the profile owner (PROFILE_TOKEN secret, classic PAT
with `repo` + `read:user`) the GraphQL calendar includes private contributions
and private repositories' languages. Without one, it falls back to the public
contribution calendar, which includes private counts only if "Include private
contributions on my profile" is enabled in GitHub settings. GITHUB_TOKEN, when
present, is only used to lift REST rate limits on that fallback path.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

CACHE = Path(__file__).resolve().parent.parent / "assets" / "stats.json"
API = "https://api.github.com"
SKIP_LANGS = {"HTML", "CSS", "SCSS", "Dockerfile", "Makefile", "Shell", "Batchfile", "PowerShell", "GLSL",
              "Jupyter Notebook", "Objective-C", "Swift", "Kotlin", "CMake"}
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

QUERY = """
query($login: String!) {
  viewer { login }
  user(login: $login) {
    contributionsCollection {
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel weekday } }
      }
    }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      nodes {
        isPrivate
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } }
      }
    }
  }
}
"""


def _request(url: str, token: str | None, body: dict | None = None) -> bytes:
    headers = {"User-Agent": "profile-readme-builder", "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def _graphql(login: str, token: str) -> dict:
    res = json.loads(_request(f"{API}/graphql", token, {"query": QUERY, "variables": {"login": login}}))
    if res.get("errors"):
        raise RuntimeError(res["errors"])
    data = res["data"]
    user = data["user"]
    cc = user["contributionsCollection"]
    days = [{"date": d["date"], "count": d["contributionCount"], "level": LEVELS[d["contributionLevel"]],
             "weekday": d["weekday"]}
            for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    langs: dict[str, int] = defaultdict(int)
    public = 0
    for repo in user["repositories"]["nodes"]:
        public += not repo["isPrivate"]
        for e in repo["languages"]["edges"]:
            langs[e["node"]["name"]] += e["size"]
    own = data["viewer"]["login"].lower() == login.lower()
    return {"days": days, "languages": langs, "repos": public,
            "includes_private": own or cc["restrictedContributionsCount"] > 0}


def _public(login: str, token: str | None) -> dict:
    html = _request(f"https://github.com/users/{login}/contributions", None).decode()
    counts = {}
    for m in re.finditer(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
        n = re.match(r"(\d+) contribution", m.group(2))
        counts[m.group(1)] = int(n.group(1)) if n else 0
    days = []
    for m in re.finditer(r'<td[^>]*data-date="([\d-]+)"[^>]*id="([^"]+)"[^>]*data-level="(\d)"', html):
        date = dt.date.fromisoformat(m.group(1))
        days.append({"date": m.group(1), "count": counts.get(m.group(2), 0), "level": int(m.group(3)),
                     "weekday": (date.weekday() + 1) % 7})
    days.sort(key=lambda d: d["date"])
    if not days:
        raise RuntimeError("could not parse the public contribution calendar")

    repos = json.loads(_request(f"{API}/users/{login}/repos?per_page=100&type=owner", token))
    langs: dict[str, int] = defaultdict(int)
    for r in repos:
        if r["fork"]:
            continue
        for name, size in json.loads(_request(r["languages_url"], token)).items():
            langs[name] += size
    return {"days": days, "languages": langs, "repos": sum(not r["fork"] for r in repos), "includes_private": False}


def _streaks(days: list[dict]) -> tuple[int, int]:
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)
    current = 0
    tail = days[:-1] if days and not days[-1]["count"] else days  # today may just not have started yet
    for d in reversed(tail):
        if not d["count"]:
            break
        current += 1
    return current, longest


def month_name(date: str) -> str:
    return dt.date.fromisoformat(date).strftime("%b")


def load(login: str, offline: bool = False) -> dict:
    if offline and CACHE.exists():
        return json.loads(CACHE.read_text())
    owner_token = os.environ.get("PROFILE_TOKEN")
    try:
        raw = _graphql(login, owner_token) if owner_token else _public(login, os.environ.get("GITHUB_TOKEN"))
    except (OSError, RuntimeError) as e:  # network errors, rate limits, API errors
        if not CACHE.exists():
            raise
        print(f"warning: could not refresh stats ({e}); reusing {CACHE.name}", file=sys.stderr)
        return json.loads(CACHE.read_text())
    days = raw["days"]
    current, longest = _streaks(days)
    langs = {k: v for k, v in raw["languages"].items() if k not in SKIP_LANGS}
    total_bytes = sum(langs.values()) or 1
    ranked = sorted(langs.items(), key=lambda kv: -kv[1])
    st = {
        "days": days,
        "total": sum(d["count"] for d in days),
        "current_streak": current,
        "longest_streak": longest,
        "peak_day": max((d["count"] for d in days), default=0),
        "repos": raw["repos"],
        "languages": [(k, v / total_bytes) for k, v in ranked],
        "includes_private": raw["includes_private"],
        "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
    }
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(st, separators=(",", ":")))
    return st
