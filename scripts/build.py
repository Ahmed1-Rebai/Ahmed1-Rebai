"""Generate every SVG used by the profile README, in dark and light variants.

    python scripts/build.py            # all assets (fetches live GitHub stats)
    python scripts/build.py --offline  # skip the network; reuse cached stats

Design rules: flat cards with hairline borders, neutral greys, a single muted
accent, serif display type, monochrome logos. Motion is reserved for the data
flowing through the architecture diagrams.
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

import content as C
import stats as S
from svgkit import ICONS, THEMES, Doc, Theme, fit, fmt, icon, measure, mix

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"


# ── shared components ─────────────────────────────────────────────────────


def frame(d: Doc, x: float, y: float, w: float, h: float, r: float = 14) -> str:
    t = d.t
    return (f'<rect x="{fmt(x + .5)}" y="{fmt(y + .5)}" width="{fmt(w - 1)}" height="{fmt(h - 1)}" rx="{fmt(r)}" '
            f'fill="{t.card}" stroke="{t.stroke}"/>')


def rule(d: Doc, x: float, y: float, w: float, color: str | None = None) -> str:
    return f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="1" fill="{color or d.t.stroke}"/>'


def label(d: Doc, x: float, y: float, s: str, color: str | None = None, size: float = 13,
          anchor: str | None = None) -> str:
    """Small uppercase mono caption."""
    return d.text(x, y, s, "mono-md", size, color or d.t.faint, anchor=anchor, ls=1.4)


def chip_label(item: str) -> tuple[str | None, str]:
    if item in ICONS:
        return item, C.LABELS.get(item, ICONS[item]["title"])
    return None, item


def chip_width(item: str, h: float, size: float, key: str) -> float:
    slug, text = chip_label(item)
    return h * 0.8 + (h * 0.48 + 8 if slug else 0) + measure(text, key, size)


def chip(d: Doc, x: float, y: float, item: str, h: float = 30, size: float = 13.5,
         key: str = "sans-md") -> tuple[str, float]:
    t = d.t
    slug, text = chip_label(item)
    w = chip_width(item, h, size, key)
    pad = h * 0.4
    out = [f'<rect x="{fmt(x + .5)}" y="{fmt(y + .5)}" width="{fmt(w - 1)}" height="{fmt(h - 1)}" rx="7" '
           f'fill="{t.card2}" stroke="{t.stroke}"/>']
    tx = x + pad
    if slug:
        ic = h * 0.48
        out.append(icon(slug, x + pad, y + (h - ic) / 2, ic, t.muted))
        tx += ic + 8
    out.append(d.text(tx, y + h / 2 + size * 0.36, text, key, size, t.muted))
    return "".join(out), w


def chip_row(d: Doc, x: float, y: float, items: list[str], maxw: float, h: float = 30, gap: float = 8,
             size: float = 13.5, key: str = "sans-md") -> tuple[str, float]:
    """Flowing chips; returns (markup, bottom y)."""
    out, cx, cy = [], x, y
    for item in items:
        w = chip_width(item, h, size, key)
        if cx > x and cx + w > x + maxw:
            cx, cy = x, cy + h + gap
        s, w = chip(d, cx, cy, item, h, size, key)
        out.append(s)
        cx += w + gap
    return "".join(out), cy + h


def packet(d: Doc, path: str, dur: float, begin: float, r: float = 2.6) -> str:
    """A small accent dot travelling along path: data moving through the system."""
    return (
        f'<circle r="{fmt(r)}" fill="{d.t.accent}" opacity="0">'
        f'<animateMotion dur="{fmt(dur)}s" begin="{fmt(begin)}s" repeatCount="indefinite" path="{path}" '
        f'calcMode="spline" keyTimes="0;1" keySplines=".45 0 .25 1"/>'
        f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.15;.8;1" dur="{fmt(dur)}s" '
        f'begin="{fmt(begin)}s" repeatCount="indefinite"/></circle>'
    )


def arrow_head(x: float, y: float, color: str, direction: str = "right", s: float = 5.5) -> str:
    pts = {
        "right": [(x, y), (x - s, y - s * 0.65), (x - s, y + s * 0.65)],
        "down": [(x, y), (x - s * 0.65, y - s), (x + s * 0.65, y - s)],
        "left": [(x, y), (x + s, y - s * 0.65), (x + s, y + s * 0.65)],
    }[direction]
    return f'<path d="M{" L".join(f"{fmt(a)} {fmt(b)}" for a, b in pts)} Z" fill="{color}"/>'


def connector(d: Doc, x1: float, y1: float, x2: float, y2: float, dur: float, begin: float) -> str:
    t = d.t
    return (f'<line x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2 - 6)}" y2="{fmt(y2)}" stroke="{t.faint}" '
            f'stroke-width="1.2"/>' + arrow_head(x2 - 1, y2, t.faint)
            + packet(d, f"M{fmt(x1)} {fmt(y1)} L{fmt(x2 - 6)} {fmt(y2)}", dur, begin))


def node(d: Doc, x: float, y: float, w: float, h: float, title: str, sub: str | None = None,
         slug: str | None = None, stroke: str | None = None) -> str:
    """A labelled box used in the architecture diagrams."""
    t = d.t
    out = [f'<rect x="{fmt(x + .5)}" y="{fmt(y + .5)}" width="{fmt(w - 1)}" height="{fmt(h - 1)}" rx="8" '
           f'fill="{t.card}" stroke="{stroke or t.stroke2}"/>']
    tx = x + 12
    if slug:
        out.append(icon(slug, x + 12, (y + 12) if sub else (y + (h - 15) / 2), 15, t.muted))
        tx = x + 34
    if sub:
        out.append(d.text(tx, y + 25, title, "sans-md", 15, t.text))
        out.append(d.text(x + 12, y + h - 13, sub, "mono", 12.5, t.faint))
    else:
        out.append(d.text(tx, y + h / 2 + 5.5, title, "sans-md", 15, t.text))
    return "".join(out)


def link_arrow(x: float, y: float, color: str, s: float = 12) -> str:
    """↗ drawn as a path so it renders identically everywhere."""
    return (f'<path d="M{fmt(x)} {fmt(y + s)} L{fmt(x + s)} {fmt(y)} M{fmt(x + s * 0.3)} {fmt(y)} '
            f'L{fmt(x + s)} {fmt(y)} L{fmt(x + s)} {fmt(y + s * 0.7)}" stroke="{color}" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def icon_tile(d: Doc, x: float, y: float, size: float, slug: str) -> str:
    t = d.t
    return (f'<rect x="{fmt(x + .5)}" y="{fmt(y + .5)}" width="{fmt(size - 1)}" height="{fmt(size - 1)}" rx="9" '
            f'fill="{t.card2}" stroke="{t.stroke}"/>'
            + icon(slug, x + size * 0.27, y + size * 0.27, size * 0.46, t.muted))


def eyebrow(d: Doc, x: float, y: float, s: str) -> str:
    """Section tag: a short accent rule followed by an uppercase caption."""
    return f'<rect x="{fmt(x)}" y="{fmt(y - 5)}" width="16" height="1.5" fill="{d.t.accent}"/>' + label(d, x + 26, y, s)


# ── hero ──────────────────────────────────────────────────────────────────


def hero(t: Theme) -> Doc:
    W, H = 1200, 372
    d = Doc(W, H, t, f"{C.NAME} — {C.ROLE}", C.TAGLINE)
    x = 56
    # availability pill, then the discipline line
    sw = measure(C.STATUS, "mono-md", 12.5, 1.4) + 40
    d.add(frame(d, 0, 0, W, H, 16),
          f'<rect x="{x + .5}" y="62.5" width="{fmt(sw - 1)}" height="29" rx="14.5" fill="{t.ok}" fill-opacity=".1" '
          f'stroke="{t.ok}" stroke-opacity=".45"/>',
          f'<circle cx="{x + 16}" cy="77" r="4" fill="{t.ok}" opacity="0">'
          f'<animate attributeName="r" values="4;11" dur="2.4s" repeatCount="indefinite"/>'
          f'<animate attributeName="opacity" values=".5;0" dur="2.4s" repeatCount="indefinite"/></circle>',
          f'<circle cx="{x + 16}" cy="77" r="4" fill="{t.ok}"/>',
          label(d, x + 28, 81.5, C.STATUS, t.ok, 12.5),
          label(d, x + sw + 16, 81.5, C.EYEBROW),
          d.text(x - 4, 198, C.NAME, "serif", 108, t.text, ls=-1),
          d.text(x, 246, C.ROLE, "sans-md", 24, t.text, ls=-0.2))
    tag, _ = d.paragraph(x, 286, C.TAGLINE, 18, 690, 28)
    d.add(tag)

    # facts panel
    px = 800
    d.add(f'<rect x="{px - 44}" y="56" width="1" height="{H - 112}" fill="{t.stroke}"/>')
    row = (H - 112) / len(C.FACTS)
    for i, (k, v) in enumerate(C.FACTS):
        ry = 56 + i * row
        if i:
            d.add(rule(d, px, ry, W - 56 - px))
        d.add(label(d, px, ry + row / 2 - 8, k, size=12.5),
              d.text(px, ry + row / 2 + 17, v, "sans-md", 17, t.text))
    return d


# ── key numbers ───────────────────────────────────────────────────────────


def tiles(t: Theme) -> Doc:
    W, H = 1200, 172
    d = Doc(W, H, t, "At a glance", "; ".join(f"{n} {a} ({b})" for n, a, b in C.TILES))
    d.add(frame(d, 0, 0, W, H, 14))
    cw = W / len(C.TILES)
    for i, (num, head, sub) in enumerate(C.TILES):
        x = i * cw + 40
        if i:
            d.add(f'<rect x="{fmt(i * cw)}" y="32" width="1" height="{H - 64}" fill="{t.stroke}"/>')
        d.add(d.text(x - 2, 88, num, "serif", 66, t.text, ls=-0.5),
              d.text(x, 123, head, "sans-md", fit(head, "sans-md", 18, cw - 64), t.text),
              d.text(x, 148, sub, "mono", fit(sub, "mono", 13.5, cw - 64), t.faint))
    return d


# ── section headings ──────────────────────────────────────────────────────


def heading(t: Theme, idx: str, title: str, sub: str) -> Doc:
    W, H = 1200, 84
    d = Doc(W, H, t, f"{idx} — {title}", f"{title} · {sub}")
    d.add(d.text(2, 52, idx, "mono-md", 13, t.accent),
          d.text(38, 55, title, "serif", 44, t.text, ls=-0.3),
          d.text(W - 2, 52, sub, "mono", 14, t.faint, anchor="end"),
          rule(d, 0, 72, W, t.stroke2))
    return d


# ── experience ────────────────────────────────────────────────────────────


def experience(t: Theme) -> Doc:
    W = 1200
    LEFT, RAIL, CX = 48, 226, 262
    MAXW = W - 48 - CX - 22
    size, lh = 17.5, 29
    d = Doc(W, 10, t, "Experience",
            "; ".join(f"{e['role']} at {e['org']} ({e['when'].title()}, {e['where'].lower()})" for e in C.EXPERIENCE))
    parts: list[str] = []
    dots: list[float] = []
    y = 52
    for n, e in enumerate(C.EXPERIENCE):
        parts += [
            d.text(CX, y + 26, e["role"], "serif", 31, t.text, ls=-0.2),
            d.runs(CX, y + 56, [(e["org"], "sans-sb", t.text), ("   ·   Internship", "sans", t.faint)], 16.5),
            d.text(LEFT, y + 22, e["when"], "mono-md", 13.5, t.text, ls=0.6),
            label(d, LEFT, y + 45, e["where"], size=12.5),
        ]
        by = y + 98
        for b in e["bullets"]:
            parts.append(f'<rect x="{CX}" y="{fmt(by - 6)}" width="9" height="1.5" fill="{t.faint}"/>')
            s, last = d.paragraph(CX + 22, by, b, size, MAXW, lh)
            parts.append(s)
            by = last + lh + 7
        if e.get("learned"):
            s, last = d.paragraph(CX + 22, by + 2, "Learned: " + e["learned"], 19.5, MAXW, 27,
                                  base="serif-i", bold="serif-i")
            parts.append(s)
            by = last + 27 + 9
        s, bottom = chip_row(d, CX + 22, by - 6, e["chips"], MAXW, h=31, size=14)
        parts.append(s)
        dots.append(y + 17)
        y = bottom + 34
        if n < len(C.EXPERIENCE) - 1:
            parts.append(rule(d, CX, y - 1, W - 48 - CX))
            y += 36
    H = int(y + 8)
    d.h = H
    rail = f'<rect x="{RAIL}" y="{fmt(dots[0])}" width="1" height="{fmt(dots[-1] - dots[0])}" fill="{t.stroke2}"/>'
    marks = []
    for n, dy in enumerate(dots):
        marks.append(f'<circle cx="{RAIL + .5}" cy="{fmt(dy)}" r="5.5" fill="{t.card}" stroke="{t.stroke2}" '
                     f'stroke-width="1.5"/>')
        if n == 0:
            marks.append(f'<circle cx="{RAIL + .5}" cy="{fmt(dy)}" r="2.5" fill="{t.accent}"/>')
    d.add(frame(d, 0, 0, W, H, 14), rail, *marks, *parts)
    return d


# ── project cards ─────────────────────────────────────────────────────────


def text_column(d: Doc, p: dict, x: float, y: float, w: float) -> tuple[list[str], float]:
    """Eyebrow, title, body, metrics and chips for a flagship card. Returns (parts, bottom)."""
    t = d.t
    out = [eyebrow(d, x, y + 12, p["tag"]),
           d.text(x - 2, y + 78, p["title"], "serif", 54, t.text, ls=-0.5)]
    body, last = d.paragraph(x, y + 120, p["body"], 18, w, 29)
    out.append(body)
    my = last + 34
    out.append(rule(d, x, my, w))
    mx = x
    for num, l1, l2 in p["metrics"]:
        nw = measure(num, "serif", 44)
        out.append(d.text(mx, my + 62, num, "serif", 44, t.text))
        out.append(d.text(mx + nw + 10, my + 43, l1, "mono", 13.5, t.muted))
        out.append(d.text(mx + nw + 10, my + 61, l2, "mono", 13.5, t.faint))
        mx += nw + 10 + max(measure(l1, "mono", 13.5), measure(l2, "mono", 13.5)) + 28
    out.append(rule(d, x, my + 86, w))
    s, bottom = chip_row(d, x, my + 110, p["chips"], w)
    out.append(s)
    return out, bottom


def postmortem(t: Theme) -> Doc:
    p = C.FLAGSHIPS["postmortem"]
    W = 1200
    d = Doc(W, 10, t, f"{p['title']} — evidence-grounded incident postmortems",
            "Evidence plane (deterministic collectors into a Neo4j temporal graph) feeds a fenced LLM reasoning "
            "plane (LangGraph analyst and writer), whose draft is checked by a deterministic validator; failures "
            "loop back with feedback.")
    col, bottom = text_column(d, p, 48, 48, 500)

    X0, DW = 600, 552
    PH, PG = 106, 44
    total = PH * 3 + PG * 2
    H = int(max(bottom + 48, total + 96))
    d.h = H
    y0 = (H - total) / 2
    g: list[str] = []
    d.style(".fence{animation:march 1.4s linear infinite}@keyframes march{to{stroke-dashoffset:-10}}")
    planes = [("EVIDENCE PLANE", "deterministic · no LLM"), ("REASONING PLANE", "LangGraph · fenced LLM"),
              ("VERIFICATION PLANE", "deterministic · no LLM")]
    for i, (name, note) in enumerate(planes):
        py = y0 + i * (PH + PG)
        fenced = i == 1
        stroke = (f'stroke="{t.accent}" stroke-opacity=".8" stroke-dasharray="5 5" class="fence"' if fenced
                  else f'stroke="{t.stroke2}"')
        g.append(f'<rect x="{X0 + .5}" y="{fmt(py + .5)}" width="{DW - 1}" height="{PH - 1}" rx="10" '
                 f'fill="{t.card2}" {stroke}/>')
        g.append(label(d, X0 + 18, py + 27, name, t.accent if fenced else None))
        g.append(d.text(X0 + DW - 18, py + 27, note, "mono", 12, t.faint, anchor="end"))

    # evidence plane: raw sources → temporal graph
    ny = y0 + 44
    nx = X0 + 18
    for s_ in ["logs", "alerts", "deploys", "commits"]:
        w = measure(s_, "mono", 12.5) + 24
        g.append(f'<rect x="{fmt(nx + .5)}" y="{fmt(ny + .5)}" width="{fmt(w - 1)}" height="41" rx="7" '
                 f'fill="{t.card}" stroke="{t.stroke2}"/>' + d.text(nx + 12, ny + 26, s_, "mono", 12.5, t.muted))
        nx += w + 8
    gx = X0 + DW - 18 - 172
    g.append(connector(d, nx + 4, ny + 21, gx, ny + 21, 1.6, 0))
    g.append(node(d, gx, ny - 1, 172, 44, "temporal graph", None, "neo4j"))

    # reasoning plane: analyst → writer
    ry_ = y0 + PH + PG + 42
    aw = ww = 240
    axx, wx = X0 + 18, X0 + DW - 18 - ww
    g.append(node(d, axx, ry_, aw, 48, "Analyst", None, "langgraph"))
    g.append(d.text(axx + aw - 12, ry_ + 29, "ranks hypotheses", "mono", 12, t.faint, anchor="end"))
    g.append(node(d, wx, ry_, ww, 48, "Writer", None, "langgraph"))
    g.append(d.text(wx + ww - 12, ry_ + 29, "cites [src:id]", "mono", 12, t.faint, anchor="end"))
    g.append(connector(d, axx + aw + 4, ry_ + 24, wx, ry_ + 24, 1.4, 0.5))

    # verification plane: validator → pass / fail
    vy = y0 + 2 * (PH + PG) + 42
    vx, vw = X0 + 18, 196
    g.append(node(d, vx, vy, vw, 48, "Validator"))
    g.append(d.text(vx + vw - 12, vy + 29, "≥ 95% cited", "mono", 12, t.faint, anchor="end"))
    px_, pw = vx + vw + 40, 132
    fx, fw = X0 + DW - 18 - 132, 132
    g.append(f'<rect x="{px_ + .5}" y="{fmt(vy + .5)}" width="{pw - 1}" height="47" rx="8" fill="{t.card}" '
             f'stroke="{t.ok}" stroke-opacity=".7"/>'
             + d.text(px_ + pw / 2, vy + 29, "PASS → ship", "mono-md", 13, t.ok, anchor="middle"))
    g.append(f'<rect x="{fx + .5}" y="{fmt(vy + .5)}" width="{fw - 1}" height="47" rx="8" fill="{t.card}" '
             f'stroke="{t.bad}" stroke-opacity=".7"/>'
             + d.text(fx + fw / 2, vy + 29, "FAIL → retry", "mono-md", 13, t.bad, anchor="middle"))
    g.append(connector(d, vx + vw + 4, vy + 24, px_, vy + 24, 1.4, 1.2))

    # hand-offs between planes, landing on the next plane's top edge (clear of its labels)
    tgt = X0 + DW / 2 + 16
    for i, (x1, top, note) in enumerate([(gx + 86, ny + 43, "only real node IDs cross"),
                                         (wx + ww / 2, ry_ + 48, "draft + [src:id] tags")]):
        bot = y0 + (i + 1) * (PH + PG)
        path = f"M{fmt(x1)} {fmt(top)} C{fmt(x1)} {fmt(bot - 8)} {fmt(tgt)} {fmt(top + 10)} {fmt(tgt)} {fmt(bot - 6)}"
        g.append(f'<path d="{path}" stroke="{t.faint}" stroke-width="1.2"/>' + arrow_head(tgt, bot - 1, t.faint, "down"))
        g.append(packet(d, path, 2.2, 0.8 + i * 1.1))
        g.append(d.text(tgt - 14, bot - PG / 2 + 4, note, "mono", 12, t.faint, anchor="end"))

    # bounded repair loop: FAIL feeds back to the Writer
    loop = (f"M{fmt(fx + fw)} {fmt(vy + 24)} C{fmt(X0 + DW + 30)} {fmt(vy + 24)} {fmt(X0 + DW + 30)} "
            f"{fmt(ry_ + 24)} {fmt(wx + ww + 7)} {fmt(ry_ + 24)}")
    g.append(f'<path class="fence" d="{loop}" stroke="{t.bad}" stroke-opacity=".6" stroke-width="1.2" '
             f'stroke-dasharray="4 4" fill="none"/>' + arrow_head(wx + ww + 2, ry_ + 24, t.bad, "left"))
    g.append(d.text(X0 + DW + 26, (vy + ry_) / 2 + 30, "≤2×", "mono-md", 12, t.bad, anchor="end"))

    d.add(frame(d, 0, 0, W, H, 14), *col, *g, link_arrow(W - 36, 24, t.faint))
    return d


def tradepulse(t: Theme) -> Doc:
    p = C.FLAGSHIPS["tradepulse"]
    W = 1200
    d = Doc(W, 10, t, f"{p['title']} — real-time market data pipeline",
            "Tick producer → Redpanda → stream processor computing VWAP, RSI-14 and anomalies → S3 Parquet and "
            "DynamoDB sinks, with Prometheus and Grafana observability and Terraform-provisioned local AWS.")
    TX = 652
    col, bottom = text_column(d, p, TX, 48, W - TX - 48)

    X0, DW = 48, 556
    H = int(max(bottom + 48, 486))
    d.h = H
    g: list[str] = []

    # price panel
    py, ph = 48, 160
    g.append(f'<rect x="{X0 + .5}" y="{py + .5}" width="{DW - 1}" height="{ph - 1}" rx="10" fill="{t.card2}" '
             f'stroke="{t.stroke}"/>')
    g.append(label(d, X0 + 16, py + 28, "TPLS  ·  1S TICKS"))
    lx = X0 + DW - 16 - measure("VWAP 60s", "mono", 12)
    g.append(d.text(lx, py + 28, "VWAP 60s", "mono", 12, t.faint)
             + f'<line x1="{fmt(lx - 28)}" y1="{py + 24}" x2="{fmt(lx - 8)}" y2="{py + 24}" stroke="{t.accent}" '
               f'stroke-width="1.5" stroke-dasharray="3 3"/>')
    lx -= 44 + measure("price", "mono", 12)
    g.append(d.text(lx, py + 28, "price", "mono", 12, t.faint)
             + f'<line x1="{fmt(lx - 28)}" y1="{py + 24}" x2="{fmt(lx - 8)}" y2="{py + 24}" stroke="{t.text}" '
               f'stroke-width="1.5"/>')
    rnd = random.Random(7)
    pts, v, n = [], 0.0, 70
    for i in range(n):
        v += rnd.gauss(0.05, 1.0)
        if i == 47:
            v += 7.5
        pts.append(v)
    lo, hi = min(pts), max(pts)
    gx0, gx1, gy0, gy1 = X0 + 16, X0 + DW - 16, py + 50, py + ph - 18

    def P(i: int, val: float) -> str:
        return f"{fmt(gx0 + (gx1 - gx0) * i / (n - 1))} {fmt(gy1 - (gy1 - gy0) * (val - lo) / (hi - lo))}"

    line = " ".join(("M" if i == 0 else "L") + P(i, val) for i, val in enumerate(pts))
    vw = [sum(pts[max(0, i - 11):i + 1]) / len(pts[max(0, i - 11):i + 1]) for i in range(n)]
    vline = " ".join(("M" if i == 0 else "L") + P(i, val) for i, val in enumerate(vw))
    shade = d.linear([(0, t.text, 0.07), (1, t.text, 0)], "0", "0", "0", "1")
    g.append(f'<path d="{line} L{fmt(gx1)} {fmt(gy1)} L{fmt(gx0)} {fmt(gy1)} Z" fill="url(#{shade})"/>')
    g.append(f'<path d="{vline}" stroke="{t.accent}" stroke-width="1.5" stroke-dasharray="3 3"/>')
    g.append(f'<path d="{line}" stroke="{t.text}" stroke-width="1.5" stroke-linejoin="round"/>')
    ax, ay = (float(c) for c in P(47, pts[47]).split())
    g.append(f'<circle cx="{fmt(ax)}" cy="{fmt(ay)}" r="7.5" fill="none" stroke="{t.bad}" stroke-width="1.2"/>'
             f'<circle cx="{fmt(ax)}" cy="{fmt(ay)}" r="2.5" fill="{t.bad}"/>')
    lab = "anomaly · z > 3"
    g.append(d.text(ax - 14, ay + 4, lab, "mono", 12, t.bad, anchor="end"))

    # pipeline row
    ry_, rh = 244, 104
    cw_, gap = 118, 28
    cols = [X0 + i * (cw_ + gap) for i in range(4)]
    mid = ry_ + rh / 2
    g.append(node(d, cols[0], mid - 32, cw_, 64, "Producer", "GBM ticks", "python"))
    g.append(node(d, cols[1], mid - 32, cw_, 64, "Redpanda", "market.ticks", "apachekafka"))
    g.append(node(d, cols[2], mid - 32, cw_, 64, "Processor", "VWAP·RSI·z"))
    g.append(node(d, cols[3], ry_ + 2, cw_, 46, "S3 Parquet"))
    g.append(node(d, cols[3], ry_ + rh - 48, cw_, 46, "DynamoDB"))
    for i in range(2):
        g.append(connector(d, cols[i] + cw_ + 3, mid, cols[i + 1], mid, 1.3, i * 0.45))
    for j, ty in enumerate([ry_ + 25, ry_ + rh - 25]):
        x1, x2 = cols[2] + cw_ + 3, cols[3] - 6
        path = f"M{fmt(x1)} {fmt(mid)} C{fmt(x1 + 14)} {fmt(mid)} {fmt(x2 - 14)} {fmt(ty)} {fmt(x2)} {fmt(ty)}"
        g.append(f'<path d="{path}" stroke="{t.faint}" stroke-width="1.2"/>' + arrow_head(x2 + 5, ty, t.faint))
        g.append(packet(d, path, 1.3, 0.9 + j * 0.3))

    # observability band
    oy = ry_ + rh + 34
    g.append(f'<rect x="{X0 + .5}" y="{oy + .5}" width="{DW - 1}" height="63" rx="10" fill="none" '
             f'stroke="{t.stroke2}" stroke-dasharray="4 4"/>')
    ox = X0 + 18
    for slug, text in [("prometheus", "Prometheus · 15s scrape"), ("grafana", "Grafana · 3 dashboards")]:
        g.append(icon(slug, ox, oy + 13, 14, t.muted) + d.text(ox + 22, oy + 25, text, "mono", 12, t.muted))
        ox += measure(text, "mono", 12) + 44
    g.append(icon("terraform", X0 + 18, oy + 37, 14, t.muted)
             + d.text(X0 + 40, oy + 49, "Terraform → local AWS emulation (S3 · DynamoDB · Kinesis)", "mono", 12, t.muted))
    for c in cols[:3]:
        g.append(f'<line x1="{fmt(c + cw_ / 2)}" y1="{fmt(mid + 32)}" x2="{fmt(c + cw_ / 2)}" y2="{oy}" '
                 f'stroke="{t.stroke2}" stroke-dasharray="2 4"/>')

    d.add(frame(d, 0, 0, W, H, 14), *g, *col, link_arrow(W - 36, 24, t.faint))
    return d


def terminal(d: Doc, x: float, y: float, w: float) -> tuple[str, float]:
    t = d.t
    h = 94
    dark = t.name == "dark"
    bg, edge = ("#0A0B0D", t.stroke2) if dark else ("#15171B", "#15171B")
    dim, fg = "#80858E", "#E4E6EA"
    out = [f'<rect x="{fmt(x + .5)}" y="{fmt(y + .5)}" width="{fmt(w - 1)}" height="{h - 1}" rx="9" fill="{bg}" '
           f'stroke="{edge}"/>']
    for i in range(3):
        out.append(f'<circle cx="{fmt(x + 18 + i * 14)}" cy="{fmt(y + 17)}" r="4" fill="#3A3D43"/>')
    out.append(d.text(x + w - 14, y + 21, "prod-api · ssh", "mono", 11.5, dim, anchor="end"))
    ly = y + 52
    out.append(d.runs(x + 18, ly, [("ubuntu@prod-api", "mono-md", "#B7C6E6"), (":~$ ", "mono", dim),
                                   ("cd /var/w", "mono", fg)], 13.5))
    cx = x + 18 + measure("ubuntu@prod-api:~$ cd /var/w", "mono", 13.5)
    d.style(".caret{animation:blink 1.1s steps(2,start) infinite}@keyframes blink{to{visibility:hidden}}")
    out.append(f'<rect class="caret" x="{fmt(cx + 1)}" y="{fmt(ly - 12)}" width="7.5" height="16" fill="{fg}" '
               f'fill-opacity=".85"/>')
    sx = x + 18 + measure("ubuntu@prod-api:~$ cd ", "mono", 13.5)
    for sug, hot in [("/var/www/", True), ("/var/www-staging/", False)]:
        sw = measure(sug, "mono", 12) + 16
        col = fg if hot else dim
        out.append(f'<rect x="{fmt(sx + .5)}" y="{fmt(ly + 12.5)}" width="{fmt(sw - 1)}" height="21" rx="5" '
                   f'fill="{fg}" fill-opacity="{.1 if hot else 0}" stroke="{col}" stroke-opacity=".35"/>'
                   + d.text(sx + 8, ly + 27, sug, "mono", 12, col))
        sx += sw + 8
    return "".join(out), h


def schema(d: Doc, x: float, y: float, w: float) -> tuple[str, float]:
    """A tiny constellation schema: two fact tables sharing dimensions."""
    t = d.t
    h = 94
    dims = ["DIM_DATE", "DIM_TEAM", "DIM_PLAYER", "DIM_COMPETITION"]
    facts = ["FACT_MATCH", "FACT_PLAYER_STATS"]
    out = []
    dw = [measure(s, "mono", 11.5) + 18 for s in dims]
    gap = (w - sum(dw)) / (len(dims) - 1)
    dx, dpos = x, []
    for ww in dw:
        dpos.append((dx + ww / 2, y + 22))
        dx += ww + gap
    fpos = [(x + w * 0.27, y + h - 14), (x + w * 0.73, y + h - 14)]
    links = [(0, 0), (0, 1), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3)]
    for k, (fi, di) in enumerate(links):
        (fx, fy), (ddx, ddy) = fpos[fi], dpos[di]
        path = f"M{fmt(fx)} {fmt(fy - 13)} L{fmt(ddx)} {fmt(ddy + 12)}"
        out.append(f'<path d="{path}" stroke="{t.stroke2}" stroke-width="1"/>')
        out.append(packet(d, path, 2.4, k * 0.4, 2.2))
    dx = x
    for s, ww in zip(dims, dw):
        out.append(f'<rect x="{fmt(dx + .5)}" y="{fmt(y + 10.5)}" width="{fmt(ww - 1)}" height="23" rx="5" '
                   f'fill="{t.card2}" stroke="{t.stroke2}"/>' + d.text(dx + 9, y + 26, s, "mono", 11.5, t.muted))
        dx += ww + gap
    for (fx, fy), s in zip(fpos, facts):
        fw = measure(s, "mono-md", 11.5) + 20
        out.append(f'<rect x="{fmt(fx - fw / 2 + .5)}" y="{fmt(fy - 12.5)}" width="{fmt(fw - 1)}" height="25" rx="5" '
                   f'fill="{t.card}" stroke="{t.accent}" stroke-opacity=".75"/>'
                   + d.text(fx, fy + 5, s, "mono-md", 11.5, t.text, anchor="middle"))
    return "".join(out), h


def medium(t: Theme, key: str, H: int | None = None) -> tuple[Doc, int]:
    p = C.CARDS[key]
    W = 600
    d = Doc(W, H or 10, t, p["title"], p["body"].replace("**", ""))
    parts = [icon_tile(d, 36, 36, 44, p["icon"]),
             label(d, 94, 63, p["tag"], size=11.5),
             d.text(34, 140, p["title"], "serif", 38, t.text, ls=-0.3)]
    body, last = d.paragraph(36, 176, p["body"], 16.5, W - 72, 26)
    parts.append(body)
    vy = last + 26
    vis, vh = terminal(d, 36, vy, W - 72) if key == "konsol" else schema(d, 36, vy, W - 72)
    parts.append(vis)
    s, bottom = chip_row(d, 36, vy + vh + 22, p["chips"], W - 72, h=28, size=13)
    parts.append(s)
    need = int(bottom + 36)
    d.h = H or need
    d.add(frame(d, 0, 0, W, d.h, 14), *parts, link_arrow(W - 48, 40, t.faint))
    return d, need


def mini(t: Theme, p: dict, H: int | None = None) -> tuple[Doc, int]:
    W = 360
    d = Doc(W, H or 10, t, p["title"], p["body"])
    parts = [icon_tile(d, 28, 28, 38, p["icon"]),
             d.text(27, 112, p["title"], "serif", fit(p["title"], "serif", 29, W - 56), t.text, ls=-0.2)]
    body, last = d.paragraph(28, 142, p["body"], 15.5, W - 56, 23)
    parts.append(body)
    items = [chip_label(c)[1] for c in p["chips"]]
    ty = last + 32
    parts.append(d.text(28, ty, "  ·  ".join(items), "mono", 13, t.faint))
    need = int(ty + 28)
    d.h = H or need
    d.add(frame(d, 0, 0, W, d.h, 12), *parts, link_arrow(W - 40, 32, t.faint, 11))
    return d, need


# ── certifications ────────────────────────────────────────────────────────


def cert(t: Theme, c: dict) -> Doc:
    W, H = 360, 332
    name = " ".join(c["name"])
    d = Doc(W, H, t, f"Microsoft Certified: {name} {c['level'].title()} ({c['code']})",
            f"Passed {c['exam']} ({c['code']}) on {c['date']}.")
    cx, cy, R = W / 2, 110, 76

    def hexagon(r: float) -> str:
        pts = [(cx + r * math.cos(math.radians(-90 + 60 * k)), cy + r * math.sin(math.radians(-90 + 60 * k)))
               for k in range(6)]
        return "M" + " L".join(f"{fmt(a)} {fmt(b)}" for a, b in pts) + " Z"

    d.add(frame(d, 0, 0, W, H, 12),
          f'<path d="{hexagon(R)}" fill="{t.card2}" stroke="{t.stroke2}" stroke-width="1.2"/>',
          f'<path d="{hexagon(R - 8)}" stroke="{t.accent}" stroke-opacity=".65" stroke-width="1"/>',
          label(d, cx, cy - 25, "MICROSOFT", size=10.5, anchor="middle"),
          d.text(cx, cy + 11, c["code"], "serif", 34, t.text, anchor="middle"),
          label(d, cx, cy + 34, c["level"], size=10.5, anchor="middle"),
          label(d, cx, 228, "MICROSOFT CERTIFIED", size=12, anchor="middle"),
          d.text(cx, 263, name, "serif", fit(name, "serif", 29, W - 48), t.text, anchor="middle", ls=-0.2))
    text = f"Passed {c['date']}"
    tw = measure(text, "mono", 13.5) + 22
    px = cx - tw / 2
    d.add(f'<path d="M{fmt(px)} 295 l3.5 3.5 6.5 -7" stroke="{t.ok}" stroke-width="1.8" stroke-linecap="round" '
          f'stroke-linejoin="round"/>',
          d.text(px + 22, 299, text, "mono", 13.5, t.muted))
    return d


# ── stack ─────────────────────────────────────────────────────────────────


def stack(t: Theme) -> Doc:
    W = 1200
    LX, CX = 48, 228
    d = Doc(W, 10, t, "Tech stack", "; ".join(f"{cat}: " + ", ".join(chip_label(i)[1] for i in items)
                                               for cat, items in C.STACK))
    parts = []
    y = 40
    for n, (cat, items) in enumerate(C.STACK):
        s, bottom = chip_row(d, CX, y, items, W - CX - 48, h=34, gap=8, size=14.5)
        parts.append(label(d, LX, y + 21.5, cat))
        parts.append(s)
        y = bottom + 24
        if n < len(C.STACK) - 1:
            parts.append(rule(d, LX, y - 1, W - 2 * LX))
            y += 24
    H = int(y + 16)
    d.h = H
    d.add(frame(d, 0, 0, W, H, 14), *parts)
    return d


# ── live activity ─────────────────────────────────────────────────────────


def activity(t: Theme, st: dict) -> Doc:
    W = 1200
    days = st["days"]
    d = Doc(W, 10, t, "GitHub activity",
            f"{st['total']} contributions in the last year; current streak {st['current_streak']} days; "
            f"longest streak {st['longest_streak']} days.")
    parts = []
    X0, X1 = 48, W - 48

    total = f"{st['total']:,}"
    tw_ = measure(total, "serif", 64)
    parts.append(d.text(X0 - 2, 98, total, "serif", 64, t.text, ls=-0.5))
    parts.append(d.text(X0 + tw_ + 16, 78, "contributions", "sans-md", 17, t.text))
    parts.append(d.text(X0 + tw_ + 16, 99, "in the last 12 months", "sans", 15.5, t.muted))
    if st.get("includes_private"):
        px = X0 + tw_ + 16 + measure("in the last 12 months", "sans", 15.5) + 18
        pw = measure("INCLUDES PRIVATE", "mono-md", 11, 1.4) + 20
        parts.append(f'<rect x="{fmt(px + .5)}" y="81.5" width="{fmt(pw - 1)}" height="23" rx="5" fill="none" '
                     f'stroke="{t.accent}" stroke-opacity=".6"/>' + label(d, px + 10, 97, "INCLUDES PRIVATE", t.accent, 11))

    parts.append(d.text(X1, 97, "more", "mono", 13, t.faint, anchor="end"))
    lx = X1 - measure("more", "mono", 13) - 8
    for lvl in range(4, -1, -1):
        lx -= 12
        parts.append(f'<rect x="{fmt(lx)}" y="86" width="11" height="11" rx="2" fill="{t.heat[lvl]}"/>')
        lx -= 3
    parts.append(d.text(lx - 5, 97, "less", "mono", 13, t.faint, anchor="end"))

    weeks: list[list[dict]] = []
    for day in days:
        if not weeks or day["weekday"] == 0:
            weeks.append([])
        weeks[-1].append(day)
    pitch = (X1 - X0) / len(weeks)
    cell = pitch * 0.8
    top = 158
    months: dict[str, int] = {}  # month → column of its label (GitHub's rule: the week whose Sunday opens it)
    for c, wk in enumerate(weeks):
        for day in wk:
            parts.append(f'<rect x="{fmt(X0 + c * pitch)}" y="{fmt(top + day["weekday"] * pitch)}" '
                         f'width="{fmt(cell)}" height="{fmt(cell)}" rx="2.5" fill="{t.heat[day["level"]]}"/>')
        sunday = wk[0]["date"]
        if wk[0]["weekday"] == 0 and sunday[8:] <= "07" and sunday[:7] not in months and c < len(weeks) - 1:
            months[sunday[:7]] = c
    # like GitHub, also name the partial month the calendar opens on when there is room for it
    first = days[0]["date"]
    if first[:7] not in months and min(months.values(), default=len(weeks)) >= 3:
        months[first[:7]] = 0
    for m, c in months.items():
        parts.append(d.text(X0 + c * pitch, top - 14, S.month_name(m + "-01"), "mono", 13, t.faint))
    grid_bottom = top + 7 * pitch

    my = grid_bottom + 30
    parts.append(rule(d, X0, my, X1 - X0))
    metrics = [(st["current_streak"], "days", "current streak"), (st["longest_streak"], "days", "longest streak"),
               (st["peak_day"], "contributions", "busiest single day"), (st["repos"], "public", "repositories")]
    colw = 164
    for i, (num, unit, text) in enumerate(metrics):
        x = X0 + i * colw
        nw = measure(str(num), "serif", 46)
        parts.append(d.text(x - 1, my + 66, str(num), "serif", 46, t.text))
        parts.append(d.text(x + nw + 6, my + 66, unit, "sans", 14.5, t.muted))
        parts.append(d.text(x, my + 93, text, "mono", 13.5, t.faint))

    lx0 = X0 + 4 * colw + 24
    lw = X1 - lx0
    parts.append(label(d, lx0, my + 40, "TOP LANGUAGES"))
    by = my + 56
    ramp = [t.accent, mix(t.accent, t.faint, 0.45), t.muted, mix(t.muted, t.faint, 0.5), t.faint, t.stroke2]
    clip = d.uid("bar")
    d.defs.append(f'<clipPath id="{clip}"><rect x="{fmt(lx0)}" y="{fmt(by)}" width="{fmt(lw)}" height="8" rx="4"/></clipPath>')
    bx, segs = lx0, []
    langs = st["languages"][:6]
    for i, (name, share) in enumerate(langs):
        w = lw * share
        segs.append(f'<rect x="{fmt(bx)}" y="{fmt(by)}" width="{fmt(max(w - 2, 1))}" height="8" fill="{ramp[i]}"/>')
        bx += w
    parts.append(f'<rect x="{fmt(lx0)}" y="{fmt(by)}" width="{fmt(lw)}" height="8" rx="4" fill="{t.card2}"/>'
                 f'<g clip-path="url(#{clip})">{"".join(segs)}</g>')
    lgx, lgy = lx0, by + 32
    for i, (name, share) in enumerate(langs):
        text = f"{name} {share * 100:.0f}%" if share >= 0.005 else f"{name} <1%"
        w = measure(text, "mono", 13.5) + 34
        if lgx + w > X1 + 10:
            lgx, lgy = lx0, lgy + 23
        parts.append(f'<rect x="{fmt(lgx)}" y="{fmt(lgy - 9)}" width="9" height="9" rx="2" fill="{ramp[i]}"/>'
                     + d.text(lgx + 16, lgy, text, "mono", 13.5, t.muted))
        lgx += w
    bottom = max(my + 104, lgy + 12)
    parts.append(rule(d, X0, bottom + 12, X1 - X0))
    parts.append(d.text(X0, bottom + 42, f"Refreshed daily by GitHub Actions · last run {st['updated']}",
                        "mono", 13, t.faint))
    parts.append(d.text(X1, bottom + 42, "scripts/build.py", "mono", 13, t.faint, anchor="end"))
    H = int(bottom + 66)
    d.h = H
    d.add(frame(d, 0, 0, W, H, 14), *parts)
    return d


# ── footer & buttons ──────────────────────────────────────────────────────


def footer(t: Theme) -> Doc:
    W, H = 1200, 178
    d = Doc(W, H, t, "Let's build software that shows its work.", f"Contact: {C.EMAIL} · {C.LINKEDIN}")
    d.add(rule(d, 0, 1, W, t.stroke2),
          d.text(W / 2, 92, "Let's build software that shows its work.", "serif-i", 48, t.text, anchor="middle"),
          d.text(W / 2, 134, f"{C.EMAIL}   ·   {C.LINKEDIN}   ·   Sfax, Tunisia", "mono", 14, t.faint,
                 anchor="middle"))
    return d


def button(t: Theme, kind: str) -> Doc:
    H = 52
    if kind == "linkedin":
        text = "Connect on LinkedIn"
        W = int(measure(text, "sans-md", 16) + 80)
        d = Doc(W, H, t, text)
        d.add(f'<rect width="{W}" height="{H}" rx="9" fill="{t.text}"/>',
              d.text(26, 32, text, "sans-md", 16, t.card),
              link_arrow(W - 40, 20, t.card, 11))
        return d
    text = C.EMAIL
    W = int(measure(text, "mono", 14.5) + 86)
    d = Doc(W, H, t, f"Email {text}")
    d.add(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="8.5" fill="{t.card}" stroke="{t.stroke2}"/>',
          f'<rect x="26.5" y="19.5" width="20" height="14" rx="2.5" stroke="{t.muted}" stroke-width="1.4"/>'
          f'<path d="M28 21.5 L36.5 27.5 L45 21.5" stroke="{t.muted}" stroke-width="1.4" stroke-linecap="round" '
          f'stroke-linejoin="round"/>',
          d.text(60, 31, text, "mono", 14.5, t.text))
    return d


# ── main ──────────────────────────────────────────────────────────────────


def build(offline: bool) -> None:
    ASSETS.mkdir(exist_ok=True)
    st = S.load(C.LOGIN, offline)
    for t in THEMES:
        jobs = {
            "hero": hero(t),
            "tiles": tiles(t),
            "experience": experience(t),
            "postmortem": postmortem(t),
            "tradepulse": tradepulse(t),
            "stack": stack(t),
            "activity": activity(t, st),
            "footer": footer(t),
            "btn-linkedin": button(t, "linkedin"),
            "btn-email": button(t, "email"),
        }
        for slug, idx, title, sub in C.HEADINGS:
            jobs[f"h-{slug}"] = heading(t, idx, title, sub)
        # cards that sit side by side share a height
        h = max(medium(t, k)[1] for k in C.CARDS)
        for k in C.CARDS:
            jobs[f"card-{k}"] = medium(t, k, h)[0]
        h = max(mini(t, p)[1] for p in C.MINI)
        for p in C.MINI:
            jobs[f"mini-{p['repo'].lower()}"] = mini(t, p, h)[0]
        for c in C.CERTS:
            jobs[f"cert-{c['code'].lower()}"] = cert(t, c)
        for name, doc in jobs.items():
            (ASSETS / f"{name}-{t.name}.svg").write_text(doc.render())
    print(f"built {len(list(ASSETS.glob('*.svg')))} svgs → {ASSETS.relative_to(ROOT)}/")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="reuse cached stats instead of calling GitHub")
    build(ap.parse_args().offline)
