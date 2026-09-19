"""Small SVG toolkit: theme palettes, font metrics, per-image font subsetting and
text layout. Every SVG is fully self-contained (fonts are embedded as subset
WOFF2 data URIs) because GitHub renders README images in a sandbox that cannot
load external resources."""

from __future__ import annotations

import base64
import io
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape as _escape

from fontTools import subset
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent

FONT_FILES = {
    "serif": "InstrumentSerif-400.ttf",
    "serif-i": "InstrumentSerif-Italic.ttf",
    "sans": "Inter-400.ttf",
    "sans-md": "Inter-500.ttf",
    "sans-sb": "Inter-600.ttf",
    "mono": "IBMPlexMono-400.ttf",
    "mono-md": "IBMPlexMono-500.ttf",
}
FAMILY = {key: f"ar-{key}" for key in FONT_FILES}


# ── themes ────────────────────────────────────────────────────────────────
# A deliberately quiet palette: neutral greys, one muted blue accent used
# sparingly, and two desaturated status colours for the diagrams.


@dataclass(frozen=True)
class Theme:
    name: str
    card: str
    card2: str
    stroke: str
    stroke2: str
    text: str
    muted: str
    faint: str
    accent: str
    ok: str
    bad: str
    heat: tuple[str, str, str, str, str]


DARK = Theme(
    name="dark",
    card="#111214", card2="#17181B", stroke="#25272B", stroke2="#35383E",
    text="#ECEDEF", muted="#A3A7AE", faint="#6E737B",
    accent="#8AA9E6", ok="#7DB58E", bad="#DE8A7E",
    heat=("#1B1D21", "#27344D", "#364F7C", "#5474B3", "#8AA9E6"),
)

LIGHT = Theme(
    name="light",
    card="#FFFFFF", card2="#F6F7F9", stroke="#E4E7EB", stroke2="#D2D7DE",
    text="#101317", muted="#4D545F", faint="#878D97",
    accent="#2D5BBF", ok="#1E7A45", bad="#B63B2C",
    heat=("#EEF0F3", "#CAD6EF", "#93ADE2", "#5680CE", "#2D5BBF"),
)

THEMES = (DARK, LIGHT)


def mix(a: str, b: str, t: float) -> str:
    """Blend colour a toward b by t (0..1)."""
    ra, ga, ba = (int(a[i:i + 2], 16) for i in (1, 3, 5))
    rb, gb, bb = (int(b[i:i + 2], 16) for i in (1, 3, 5))
    return "#{:02X}{:02X}{:02X}".format(
        round(ra + (rb - ra) * t), round(ga + (gb - ga) * t), round(ba + (bb - ba) * t)
    )


# ── icons (Simple Icons, CC0) — drawn monochrome ─────────────────────────

ICONS: dict[str, dict] = json.loads((HERE / "icons.json").read_text())


def icon(slug: str, x: float, y: float, size: float, fill: str) -> str:
    s = size / 24
    return f'<path transform="translate({fmt(x)} {fmt(y)}) scale({fmt(s)})" d="{ICONS[slug]["path"]}" fill="{fill}"/>'


# ── fonts ─────────────────────────────────────────────────────────────────


def fmt(v: float) -> str:
    if isinstance(v, int):
        return str(v)
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def esc(s: str) -> str:
    return _escape(s, {'"': "&quot;"})


class Font:
    def __init__(self, key: str):
        self.tt = TTFont(HERE / "fonts" / FONT_FILES[key], recalcTimestamp=False)
        self.upm = self.tt["head"].unitsPerEm
        self.cmap = self.tt.getBestCmap()
        self.hmtx = self.tt["hmtx"]

    def width(self, s: str, size: float, ls: float = 0.0) -> float:
        units = 0
        for ch in s:
            glyph = self.cmap.get(ord(ch))
            units += self.hmtx[glyph][0] if glyph else self.upm * 0.6
        return units * size / self.upm + ls * len(s)


@lru_cache(maxsize=None)
def font(key: str) -> Font:
    return Font(key)


def measure(s: str, key: str, size: float, ls: float = 0.0) -> float:
    return font(key).width(s, size, ls)


def fit(s: str, key: str, size: float, maxw: float, floor: float = 10) -> float:
    """Largest size (<= size) at which s fits within maxw."""
    while size > floor and measure(s, key, size) > maxw:
        size -= 0.25
    return size


def wrap(s: str, key: str, size: float, maxw: float) -> list[str]:
    lines: list[str] = []
    cur = ""
    for word in s.split():
        trial = f"{cur} {word}" if cur else word
        if cur and measure(trial, key, size) > maxw:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


Run = tuple[str, bool]  # (text, emphasised)


def rich_wrap(markup: str, size: float, maxw: float, base: str = "sans", bold: str = "sans-sb") -> list[list[Run]]:
    """Wrap text containing **emphasis** markers into lines of styled runs."""
    chars: list[tuple[str, bool]] = []
    on = False
    for part in re.split(r"(\*\*)", markup):
        if part == "**":
            on = not on
        else:
            chars.extend((c, on) for c in part)

    words: list[list[tuple[str, bool]]] = [[]]
    for c, b in chars:
        if c == " ":
            words.append([])
        else:
            words[-1].append((c, b))
    words = [w for w in words if w]

    def width(cs: list[tuple[str, bool]]) -> float:
        return sum(measure(c, bold if b else base, size) for c, b in cs)

    space = measure(" ", base, size)
    lines: list[list[tuple[str, bool]]] = []
    cur: list[tuple[str, bool]] = []
    cur_w = 0.0
    for w in words:
        ww = width(w)
        if cur and cur_w + space + ww > maxw:
            lines.append(cur)
            cur, cur_w = [], 0.0
        if cur:
            # the joining space takes the emphasis of the surrounding text
            cur.append((" ", cur[-1][1] and w[0][1]))
            cur_w += space
        cur.extend(w)
        cur_w += ww
    if cur:
        lines.append(cur)

    out: list[list[Run]] = []
    for line in lines:
        runs: list[Run] = []
        for c, b in line:
            if runs and runs[-1][1] == b:
                runs[-1] = (runs[-1][0] + c, b)
            else:
                runs.append((c, b))
        out.append(runs)
    return out


@lru_cache(maxsize=None)
def _embedded(key: str, chars: str) -> str:
    tt = TTFont(HERE / "fonts" / FONT_FILES[key], recalcTimestamp=False)
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern"]
    opts.name_IDs = [1, 2]
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(text=chars)
    sub.subset(tt)
    buf = io.BytesIO()
    tt.flavor = "woff2"
    tt.save(buf)
    data = base64.b64encode(buf.getvalue()).decode()
    return f'@font-face{{font-family:"{FAMILY[key]}";src:url(data:font/woff2;base64,{data}) format("woff2")}}'


# ── document ──────────────────────────────────────────────────────────────

BASE_CSS = (
    "text{font-kerning:normal}"
    "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
)


class Doc:
    """Accumulates body markup, defs and CSS for one SVG, tracking every glyph
    used so the embedded fonts can be subset to exactly what is rendered."""

    def __init__(self, w: int, h: int, t: Theme, title: str, desc: str = ""):
        self.w, self.h, self.t = w, h, t
        self.title, self.desc = title, desc
        self.body: list[str] = []
        self.defs: list[str] = []
        self.css: list[str] = []
        self.used: dict[str, set[str]] = defaultdict(set)
        self._n = 0
        self._memo: dict[str, str] = {}

    def uid(self, prefix: str = "u") -> str:
        self._n += 1
        return f"{prefix}{self._n}"

    def add(self, *parts: str) -> None:
        self.body.extend(parts)

    def style(self, css: str) -> None:
        if css not in self.css:
            self.css.append(css)

    def once(self, key: str, make) -> str:
        """Create a def the first time it is requested; return its id."""
        if key not in self._memo:
            self._memo[key] = make()
        return self._memo[key]

    # text ---------------------------------------------------------------

    def text(self, x: float, y: float, s: str, key: str = "sans", size: float = 18,
             fill: str | None = None, anchor: str | None = None, ls: float | None = None,
             opacity: float | None = None, attrs: str = "") -> str:
        self.used[key].update(s)
        a = [f'x="{fmt(x)}" y="{fmt(y)}"', f'font-family="{FAMILY[key]}"',
             f'font-size="{fmt(size)}"', f'fill="{fill or self.t.text}"']
        if anchor:
            a.append(f'text-anchor="{anchor}"')
        if ls:
            a.append(f'letter-spacing="{fmt(ls)}"')
        if opacity is not None:
            a.append(f'fill-opacity="{fmt(opacity)}"')
        if attrs:
            a.append(attrs)
        return f"<text {' '.join(a)}>{esc(s)}</text>"

    def runs(self, x: float, y: float, runs: list[tuple[str, str, str]], size: float,
             anchor: str | None = None, attrs: str = "") -> str:
        """One line of mixed styles: runs are (text, font key, fill)."""
        spans = []
        for s, key, fill in runs:
            self.used[key].update(s)
            spans.append(f'<tspan font-family="{FAMILY[key]}" fill="{fill}">{esc(s)}</tspan>')
        a = f'x="{fmt(x)}" y="{fmt(y)}" font-size="{fmt(size)}" xml:space="preserve"'
        if anchor:
            a += f' text-anchor="{anchor}"'
        if attrs:
            a += " " + attrs
        return f"<text {a}>{''.join(spans)}</text>"

    def paragraph(self, x: float, y: float, markup: str, size: float, maxw: float, lh: float,
                  fill: str | None = None, strong: str | None = None,
                  base: str = "sans", bold: str = "sans-sb", attrs: str = "") -> tuple[str, float]:
        """Wrapped rich text. Returns (markup, y of the last baseline)."""
        fill = fill or self.t.muted
        strong = strong or self.t.text
        out = []
        lines = rich_wrap(markup, size, maxw, base, bold)
        for i, line in enumerate(lines):
            out.append(self.runs(x, y + i * lh, [(s, bold if b else base, strong if b else fill) for s, b in line],
                                 size, attrs=attrs))
        return "".join(out), y + (len(lines) - 1) * lh

    # gradients ------------------------------------------------------------

    def linear(self, stops: list[tuple[float, str, float]], x1="0", y1="0", x2="1", y2="0",
               user: bool = False) -> str:
        key = f"lin{stops}{x1}{y1}{x2}{y2}{user}"

        def make() -> str:
            gid = self.uid("lg")
            units = ' gradientUnits="userSpaceOnUse"' if user else ""
            st = "".join(f'<stop offset="{fmt(o)}" stop-color="{c}" stop-opacity="{fmt(a)}"/>' for o, c, a in stops)
            self.defs.append(f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"{units}>{st}</linearGradient>')
            return gid

        return self.once(key, make)

    # output ---------------------------------------------------------------

    def render(self) -> str:
        for key, chars in sorted(self.used.items()):
            missing = "".join(sorted(c for c in chars if ord(c) not in font(key).cmap))
            if missing:
                print(f"warning: {self.title!r}: {key} has no glyph for {missing!r}", file=sys.stderr)
        fonts ="".join(_embedded(k, "".join(sorted(cs | {" "}))) for k, cs in sorted(self.used.items()) if cs)
        css = BASE_CSS + "".join(self.css)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" fill="none" role="img" aria-labelledby="title desc">'
            f'<title id="title">{esc(self.title)}</title><desc id="desc">{esc(self.desc or self.title)}</desc>'
            f"<defs><style>{fonts}{css}</style>{''.join(self.defs)}</defs>"
            f"{''.join(self.body)}</svg>\n"
        )
