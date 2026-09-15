#!/usr/bin/env python3
"""Builds the profile panels - stats, featured projects, and the contribution runner."""
import json
import os
import urllib.request

USER = "ananya-goswami"
OUT = os.environ.get("STATS_OUT", "dist/highscores-v2.svg")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

HEAD = {"Accept": "application/vnd.github+json", "User-Agent": "profile-stats"}
if TOKEN:
    HEAD["Authorization"] = f"Bearer {TOKEN}"


def api(url):
    req = urllib.request.Request(url, headers=HEAD)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def collect():
    repos, page = [], 1
    while True:
        batch = api(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}")
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    own = [r for r in repos if not r.get("fork")]
    langs, repo_langs = {}, {}
    for r in own:
        try:
            got = api(r["languages_url"])
            repo_langs[r["name"]] = sorted(got, key=lambda k: -got[k])
            for lang, b in got.items():
                langs[lang] = langs.get(lang, 0) + b
        except Exception:
            pass
    deployed = [r for r in own if (r.get("homepage") or "").strip()]
    index = {r["name"]: {"homepage": r.get("homepage"),
                         "langs": [l.lower() for l in (repo_langs.get(r["name"]) or [])]}
             for r in own}
    return {
        "index": index,
        "repos": len(own),
        "deployed": len(deployed),
        "langs": sorted(langs.items(), key=lambda kv: -kv[1])[:3],
        "total_bytes": sum(langs.values()) or 1,
    }




GQL = """query($login:String!){
  user(login:$login){
    contributionsCollection{
      totalCommitContributions
      contributionCalendar{ totalContributions weeks{ contributionDays{ date weekday contributionCount } } }
    }
    pullRequests{ totalCount }
    issues{ totalCount }
    repositories(first:100, ownerAffiliations:OWNER, isFork:false){ nodes{ stargazerCount } }
  }
}"""


def graph():
    """contribution calendar, streaks, stars, PRs and issues in one call"""
    body = json.dumps({"query": GQL, "variables": {"login": USER}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        **HEAD, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)["data"]["user"]

    days = [d for w in data["contributionsCollection"]["contributionCalendar"]["weeks"]
            for d in w["contributionDays"]]
    days.sort(key=lambda d: d["date"])
    best = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        best = max(best, run)
    current = 0
    for d in reversed(days):
        if d["contributionCount"] > 0:
            current += 1
        elif current or d is not days[-1]:
            break
    weeks = []
    for w in data["contributionsCollection"]["contributionCalendar"]["weeks"]:
        col = [0] * 7
        for d in w["contributionDays"]:
            col[d["weekday"]] = d["contributionCount"]
        weeks.append(col)
    return {
        "weeks": weeks,
        "contributions": data["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "commits": data["contributionsCollection"]["totalCommitContributions"],
        "current_streak": current,
        "longest_streak": best,
        "stars": sum(n["stargazerCount"] for n in data["repositories"]["nodes"]),
        "prs": data["pullRequests"]["totalCount"],
        "issues": data["issues"]["totalCount"],
        "first_day": days[0]["date"] if days else "",
        "last_day": days[-1]["date"] if days else "",
    }


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(d, g=None):
    """Stats panel: streak band on top, stats list and language split below."""
    g = g or {}
    W, H = 1000, 444
    first = (g.get("first_day") or "")[:10]

    # ---- top band: three columns split by dividers ----
    ring_r = 46
    band = f'''
  <line x1="333" y1="58" x2="333" y2="196" stroke="#1d3b36"/>
  <line x1="667" y1="58" x2="667" y2="196" stroke="#1d3b36"/>

  <text class="mono" x="167" y="112" text-anchor="middle" font-size="40" font-weight="700" fill="#F2FBF8">{g.get("contributions", "-")}</text>
  <text class="mono" x="167" y="140" text-anchor="middle" font-size="12.5" fill="#CFEAE3">Total Contributions</text>
  <text class="mono" x="167" y="164" text-anchor="middle" font-size="11" fill="#4e6b66">{esc(first)} to present</text>

  <circle cx="500" cy="112" r="{ring_r}" fill="none" stroke="#1d3b36" stroke-width="4"/>
  <circle cx="500" cy="112" r="{ring_r}" fill="none" stroke="url(#ring)" stroke-width="4" stroke-linecap="round"
          stroke-dasharray="{2 * 3.14159 * ring_r:.0f}" stroke-dashoffset="{2 * 3.14159 * ring_r * 0.28:.0f}"
          transform="rotate(-90 500 112)">
    <animateTransform attributeName="transform" type="rotate" from="-90 500 112" to="270 500 112" dur="14s" repeatCount="indefinite"/>
  </circle>
  <circle cx="500" cy="66" r="13.5" fill="#050c10"/>
  <g transform="translate(500 64) scale(1.45)">
    <path d="M1-9.6C4-5.8 6.2-3 6.2 1A6.2 6.2 0 01-6.2 1C-6.2-1.6-4.6-3.8-2.4-5.4-2.6-2.8-1.4-1.6.4-1.8-1.4-4.2-1-7.2 1-9.6Z" fill="url(#ring)">
      <animate attributeName="opacity" values="1;.5;1" dur="2.4s" repeatCount="indefinite"/>
    </path>
    <path transform="translate(.2 3) scale(.44)" d="M1-9.6C4-5.8 6.2-3 6.2 1A6.2 6.2 0 01-6.2 1C-6.2-1.6-4.6-3.8-2.4-5.4-2.6-2.8-1.4-1.6.4-1.8-1.4-4.2-1-7.2 1-9.6Z" fill="#F2FBF8" fill-opacity=".85"/>
  </g>
  <text class="mono" x="500" y="122" text-anchor="middle" font-size="34" font-weight="700" fill="#F2FBF8">{g.get("current_streak", "-")}</text>
  <text class="mono" x="500" y="180" text-anchor="middle" font-size="12.5" fill="#9BE7C4">Current Streak</text>

  <text class="mono" x="833" y="112" text-anchor="middle" font-size="40" font-weight="700" fill="#F2FBF8">{g.get("longest_streak", "-")}</text>
  <text class="mono" x="833" y="140" text-anchor="middle" font-size="12.5" fill="#CFEAE3">Longest Streak</text>
  <text class="mono" x="833" y="164" text-anchor="middle" font-size="11" fill="#4e6b66">best run so far</text>'''

    # ---- bottom left: the stats list ----
    ICONS = {
        "star": "M0 -7 2 -2 7 -2 3 1 4.5 6 0 3 -4.5 6 -3 1 -7 -2 -2 -2Z",
        "clock": "M0 -7a7 7 0 100 14 7 7 0 100-14M0 -4v4l3 2",
        "branch": "M-4 -6v12M-4 -6a2 2 0 100 .1M-4 6a2 2 0 100 .1M4 -6a2 2 0 100 .1M4 -4v2a4 4 0 01-4 4",
        "box": "M-7 -5h14v10h-14zM-7 -1h14",
        "live": "M0 -6a6 6 0 100 12 6 6 0 100-12M0 -3v3l2 2",
    }
    lines = [
        ("star", "Total Stars Earned", g.get("stars", 0)),
        ("clock", "Commits This Year", g.get("commits", "-")),
        ("branch", "Total PRs", g.get("prs", "-")),
        ("box", "Public Repos", d["repos"]),
        ("live", "Live Builds", d["deployed"]),
    ]
    left = ""
    ly = 296
    for icon, label, val in lines:
        left += f'''
    <g transform="translate(52 {ly - 5})" fill="none" stroke="#8FD4F5" stroke-width="1.5" stroke-linejoin="round">
      <path d="{ICONS[icon]}"/>
    </g>
    <text class="mono" x="74" y="{ly}" font-size="13" fill="#CFEAE3">{label}</text>
    <text class="mono" x="430" y="{ly}" font-size="13" font-weight="700" text-anchor="end" fill="#F2FBF8">{val}</text>'''
        ly += 29

    # ---- bottom right: language split ----
    colors = ["#9BE7C4", "#8FD4F5", "#B9A7FA", "#F0ABFC"]
    bar_x, bar_w, bar_y = 530, 420, 286
    seg, legend, cursor = "", "", 0.0
    for i, (lang, b) in enumerate(d["langs"]):
        frac = b / d["total_bytes"]
        w = max(frac * bar_w, 6)
        seg += (f'<rect x="{bar_x + cursor:.1f}" y="{bar_y}" width="{w:.1f}" height="11" rx="5.5" fill="{colors[i]}">'
                f'<animate attributeName="width" values="0;{w:.1f}" dur="1.1s" begin="{0.3 + i * 0.15:.2f}s" fill="freeze"/></rect>')
        cursor += w + 3
        col, row = i % 2, i // 2
        lx = bar_x + col * 210
        lyy = bar_y + 44 + row * 28
        legend += (f'<circle cx="{lx + 5}" cy="{lyy - 4}" r="4.5" fill="{colors[i]}"/>'
                   f'<text class="mono" x="{lx + 18}" y="{lyy}" font-size="12.5" fill="#CFEAE3">{esc(lang)} {frac * 100:.1f}%</text>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="github stats">
<defs>
  <linearGradient id="bgG" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#04070a"/><stop offset="60%" stop-color="#060e12"/><stop offset="100%" stop-color="#04090c"/>
  </linearGradient>
  <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#9BE7C4"/><stop offset="0.5" stop-color="#8FD4F5"/><stop offset="1" stop-color="#B9A7FA"/>
  </linearGradient>
  <radialGradient id="glowA"><stop offset="0%" stop-color="#9BE7C4" stop-opacity=".10"/><stop offset="100%" stop-color="#9BE7C4" stop-opacity="0"/></radialGradient>
  <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#7fffd4" fill-opacity=".025"/></pattern>
  <clipPath id="win"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14"/></clipPath>
</defs>
<style>
  .mono {{ font-family: ui-monospace, "SF Mono", "JetBrains Mono", Consolas, monospace; }}
  .pulse {{ animation: pulse 3.6s ease-in-out infinite; }}
  @keyframes pulse {{ 0%,100% {{ opacity: .45 }} 50% {{ opacity: 1 }} }}
</style>
<rect width="{W}" height="{H}" rx="14" fill="url(#bgG)"/>
<ellipse cx="500" cy="{H}" rx="540" ry="230" fill="url(#glowA)"/>
<g transform="translate(0 -26)">
{band}
<line x1="34" y1="214" x2="{W - 34}" y2="214" stroke="#132824"/>
<rect x="34" y="230" width="430" height="200" rx="12" fill="#070f13" stroke="#152e2a"/>
<text class="mono" x="52" y="262" font-size="14" font-weight="700" fill="#9BE7C4">Ananya's GitHub Stats</text>
{left}
<rect x="{W - 34 - 452}" y="230" width="452" height="200" rx="12" fill="#070f13" stroke="#152e2a"/>
<text class="mono" x="530" y="262" font-size="14" font-weight="700" fill="#9BE7C4">Most Used Languages</text>
<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="11" rx="5.5" fill="#101d21"/>
{seg}{legend}
</g>
<g clip-path="url(#win)"><rect width="{W}" height="{H}" fill="url(#scan)"/></g>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="none" stroke="#9BE7C4" stroke-opacity=".26"/>
</svg>
'''




FEATURED = [
    ("Competition-Zone", "Competition Zone", "PROTOTYPE",
     "contest platform: entries, results, trophy room, XP"),
    ("fln-animation-toolkit", "FLN Animation Kit", "TOOLKIT",
     "7 drop-in animations for learning apps, fully tunable"),
    ("Keyword-class9", "Spot the Scam", "CLASS 9 / CYBER",
     "find the bait, then stop, verify, report. helpline 1930"),
    ("think-ask-act", "Think Ask Act", "CYBER SAFETY",
     "sequence the response: think, ask an adult, act after"),
    ("calm-or-react", "Calm or React", "CYBER SAFETY",
     "sort the message, name the emotion the scam leans on"),
    ("feeling-wheel-tap", "Feeling Wheel Tap", "SEL",
     "pause, notice, name the feeling, take back control"),
]


def build_projects(index):
    W, H = 1200, 452
    CW, CH, GX, GY = 566, 104, 22, 16
    cards = ""
    for i, (repo, title, tag, blurb) in enumerate(FEATURED):
        col, row = i % 2, i // 2
        x = 26 + col * (CW + GX)
        y = 96 + row * (CH + GY)
        meta = index.get(repo, {})
        live = bool((meta.get("homepage") or "").strip())
        langs = " / ".join(meta.get("langs", [])[:3]) or "html / css / js"
        cards += f'''
  <g>
    <rect x="{x}" y="{y}" width="{CW}" height="{CH}" rx="9" fill="#050d0b" stroke="#00FF9C" stroke-opacity=".20"/>
    <text class="mono" x="{x + 16}" y="{y + 22}" font-size="11" fill="#3f5f58">~/{esc(repo)}</text>
    <text class="mono" x="{x + CW - 16}" y="{y + 22}" font-size="10.5" text-anchor="end" letter-spacing="1.3"
          fill="{'#00FF9C' if live else '#3f5f58'}">{'● LIVE' if live else '○ REPO'}</text>
    <text class="mono" x="{x + 16}" y="{y + 48}" font-size="16" font-weight="700" fill="#E8FFF6">{esc(title)}</text>
    <text class="mono" x="{x + 16}" y="{y + 70}" font-size="12.5" fill="#7f9c96">{esc(blurb)}</text>
    <text class="mono" x="{x + 16}" y="{y + 90}" font-size="11" fill="#22D3EE" fill-opacity=".85">{esc(langs)}</text>
    <text class="mono" x="{x + CW - 16}" y="{y + 90}" font-size="10.5" text-anchor="end" letter-spacing="1.4"
          fill="#3ddc97" fill-opacity=".8">{esc(tag)}</text>
  </g>'''

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="featured projects">
<defs>
  <linearGradient id="bgG" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#04070a"/><stop offset="55%" stop-color="#060e11"/><stop offset="100%" stop-color="#04090c"/>
  </linearGradient>
  <radialGradient id="glowB"><stop offset="0%" stop-color="#22D3EE" stop-opacity=".12"/><stop offset="100%" stop-color="#22D3EE" stop-opacity="0"/></radialGradient>
  <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#7fffd4" fill-opacity=".03"/></pattern>
  <clipPath id="win"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14"/></clipPath>
</defs>
<style>
  .mono {{ font-family: ui-monospace, "SF Mono", "JetBrains Mono", Consolas, monospace; }}
  .car {{ animation: blink 1.05s steps(1) infinite; }}
  @keyframes blink {{ 0%,48% {{ opacity: 1 }} 49%,100% {{ opacity: 0 }} }}
</style>
<rect width="{W}" height="{H}" rx="14" fill="url(#bgG)"/>
<ellipse cx="1000" cy="380" rx="360" ry="240" fill="url(#glowB)"/>
<rect x="1" y="1" width="{W - 2}" height="32" rx="14" fill="#0a1114"/><rect x="1" y="22" width="{W - 2}" height="11" fill="#0a1114"/>
<text class="mono" x="30" y="22" font-size="12" fill="#4e6b66">~/projects</text>
<line x1="1" y1="33" x2="{W - 1}" y2="33" stroke="#00FF9C" stroke-opacity=".18"/>
<text class="mono" x="26" y="68" font-size="14" fill="#3ddc97" fill-opacity=".8" xml:space="preserve">$ ls ~/projects --featured</text>
<rect class="car" x="232" y="56" width="8" height="15" fill="#00FF9C" fill-opacity=".8"/>
{cards}
<g clip-path="url(#win)"><rect width="{W}" height="{H}" fill="url(#scan)"/></g>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="none" stroke="#00FF9C" stroke-opacity=".26"/>
</svg>
'''


# ---------------------------------------------------------------- reference art
ART_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                        "assets", "image.png")
ART_BOXES = {
    "girl":   (636, 404, 786, 586),
    "turtle": (955, 505, 1086, 586),
    "shell":  (740, 258, 856, 332),
    "qblock": (752, 346, 840, 430),
    "leaf":   (1214, 316, 1332, 400),
    "snake":  (1538, 300, 1652, 402),
    "signL":  (108, 402, 312, 572),
    "signR":  (1898, 402, 2088, 572),
    "hill":   (1655, 468, 1900, 588),
    "grass":  (1178, 530, 1264, 584),
    "star":   (52, 116, 106, 166),
    "tag":    (1628, 116, 2102, 162),
}
ART_FLAT = ("hill", "tag")          # pasted as-is, no alpha key
ART_BG = ((7, 15, 26), (0, 10, 18), (0, 14, 21), (2, 20, 30),
          (6, 49, 62), (7, 44, 57), (4, 35, 46))
_ART = None


def art():
    """Cut the runner's cast out of the reference art, keyed to transparency.

    Returns {name: (data_uri, w, h)}; empty if the art or Pillow is missing.
    """
    global _ART
    if _ART is not None:
        return _ART
    _ART = {}
    try:
        import base64, io
        import numpy as np
        from PIL import Image
    except Exception as exc:
        print("art skipped (no Pillow):", exc)
        return _ART
    try:
        src = Image.open(ART_PATH).convert("RGB")
    except Exception as exc:
        print("art skipped (no reference):", exc)
        return _ART

    bg = [np.array(c, dtype=float) for c in ART_BG]
    for name, box in ART_BOXES.items():
        crop = src.crop(box)
        if name in ART_FLAT:
            img = crop.convert("RGBA")
        else:
            a = np.array(crop).astype(float)
            d = np.stack([np.linalg.norm(a - c, axis=2) for c in bg], axis=0).min(axis=0)
            alpha = np.clip((d - 20.0) / 38.0, 0, 1) * 255
            img = Image.fromarray(np.dstack([a, alpha]).astype(np.uint8), "RGBA")
            bb = img.getbbox()
            if bb:
                img = img.crop(bb)
        buf = io.BytesIO()
        img.quantize(colors=64, method=Image.FASTOCTREE).save(buf, "PNG", optimize=True)
        _ART[name] = ("data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(),
                      img.width, img.height)
    return _ART


def sprite(name, x, y, anchor="bottom", scale=1.0, extra=""):
    """Place a sprite. x is its centre, y its baseline (or top, when anchored so)."""
    a = art().get(name)
    if not a:
        return ""
    uri, w, h = a
    w, h = w * scale, h * scale
    top = y if anchor == "top" else y - h
    return (f'<image xlink:href="{uri}" x="{x - w / 2:.1f}" y="{top:.1f}" '
            f'width="{w:.1f}" height="{h:.1f}" {extra}/>')


def _levels(weeks):
    flat = [c for w in weeks for c in w]
    mx = max(flat) if flat else 0
    out = []
    for w in weeks:
        col = []
        for c in w:
            if c <= 0:
                col.append(0)
            elif mx <= 1:
                col.append(4)
            else:
                col.append(1 + min(3, int(3.0 * (c - 1) / max(1, mx - 1) + 0.5)))
        while len(col) < 7:
            col.append(0)
        out.append(col)
    return out


# ---------------------------------------------------------------- runner panel
VB_W, VB_H = 2172, 724                 # reference-art coordinate space
PANEL = (33, 95, 2139, 627)
GX0, GY0, GCELL, GPX, GPY = 85.0, 180.0, 26.0, 37.2, 36.5
GROUND = 588.0                         # top of the ground line
BLOCK_Y = 346.0                        # top of a mystery block
LEVELS = ["#06313E", "#128070", "#18A088", "#20D898", "#9BEFD9"]


def _keys(vals, times, T):
    """Clamp and monotonise keyTimes, returning the SMIL strings."""
    ks = [min(max(t / T, 0.0), 1.0) for t in times]
    for i in range(1, len(ks)):
        ks[i] = max(ks[i], ks[i - 1])
    return ";".join(vals), ";".join(f"{k:.5f}" for k in ks)


def _prize(sprites, cx, cy, t, T, path, life):
    """A prize popping out of a block at (cx, cy) and living for `life` seconds.

    sprites: [(svg, from_dt, to_dt)] - each sprite shows over its own window.
    path:    [(dt, x, y)] - offsets from the block, in order.
    """
    vals = ["0,0"] + [f"{x:.1f},{y:.1f}" for _, x, y in path] + \
           [f"{path[-1][1]:.1f},{path[-1][2]:.1f}"]
    times = [0.0] + [t + dt for dt, _, _ in path] + [T]
    move_v, move_k = _keys(vals, times, T)
    op_v, op_k = _keys(["0", "0", "1", "1", "0", "0"],
                       [0.0, t, t + 0.06, t + life - 0.35, t + life, T], T)
    inner = ""
    for svg, a, b in sprites:
        sv, sk = _keys(["0", "0", "1", "1", "0", "0"],
                       [0.0, t + a, t + a + 0.02, t + b, t + b + 0.02, T], T)
        inner += (f'<g opacity="0"><animate attributeName="opacity" dur="{T}s"'
                  f' repeatCount="indefinite" values="{sv}" keyTimes="{sk}"/>{svg}</g>')
    return (f'<g opacity="0"><animate attributeName="opacity" dur="{T}s" repeatCount="indefinite"'
            f' values="{op_v}" keyTimes="{op_k}"/>'
            f'<g transform="translate({cx} {cy})">'
            f'<animateTransform attributeName="transform" type="translate" dur="{T}s"'
            f' repeatCount="indefinite" additive="sum" calcMode="linear"'
            f' values="{move_v}" keyTimes="{move_k}"/>{inner}</g></g>')


def build_runner_panel(weeks, total=None):
    """The avatar runs the contribution grid, knocking mystery blocks open."""
    grid = _levels(weeks)
    cols = min(len(grid), 53)
    grid = grid[-cols:]
    T = 24.0
    X0, X1 = -120.0, VB_W + 120.0

    # ---- one block per busy-ish column, spaced so they never collide ----
    events, last = [], -99
    for i, col in enumerate(grid):
        lv = max(col)
        if lv <= 0 or i - last < 7:
            continue
        events.append({"col": i, "row": col.index(lv), "lv": lv,
                       "x": GX0 + i * GPX + GCELL / 2})
        last = i
    if len(events) > 5:
        step = len(events) / 5.0
        events = [events[int(k * step)] for k in range(5)]

    # ---- pacing across the panel ----
    stops = [X0] + [e["x"] for e in events] + [X1]
    weight = [max(abs(stops[i + 1] - stops[i]), 1.0) ** 0.6 + 40.0
              for i in range(len(stops) - 1)]
    scale = T / sum(weight)
    marks, acc = [0.0], 0.0
    for w in weight:
        acc += w * scale
        marks.append(acc)
    marks[-1] = T
    for k, e in enumerate(events):
        e["t"] = marks[k + 1]
    run_v = ";".join(f"{x:.1f},{GROUND}" for x in stops)
    run_k = ";".join(f"{m / T:.5f}" for m in marks)

    # ---- her jump arc: head has to reach the underside of a block ----
    JD, LIFT = 0.95, 62.0
    vals, keys = ["0,0"], [0.0]
    for e in events:
        t0, t1 = e["t"] - JD / 2, e["t"] + JD / 2
        for frac, lift in ((0.0, 0.0), (0.3, 0.74), (0.5, 1.0), (0.7, 0.74), (1.0, 0.0)):
            keys.append((t0 + frac * (t1 - t0)) / T)
            vals.append(f"0,{-LIFT * lift:.1f}")
    keys.append(1.0)
    vals.append("0,0")
    for i in range(1, len(keys)):
        keys[i] = min(max(keys[i], keys[i - 1]), 1.0)
    jump_v, jump_k = ";".join(vals), ";".join(f"{k:.5f}" for k in keys)

    # ---- the contribution grid ----
    hit = {(e["col"], e["row"]): e for e in events}
    cells = []
    for i, col in enumerate(grid):
        for r, lv in enumerate(col):
            x, y = GX0 + i * GPX, GY0 + r * GPY
            fill = LEVELS[lv]
            e = hit.get((i, r))
            base = (f'<rect x="{x:.1f}" y="{y:.1f}" width="{GCELL}" height="{GCELL}" rx="7"'
                    f' fill="{fill}"')
            if e is None:
                cells.append(base + "/>")
                continue
            a, b, c = e["t"] / T, (e["t"] + 0.12) / T, (e["t"] + 0.4) / T
            cells.append(
                base + f'><animate attributeName="fill" dur="{T}s" repeatCount="indefinite"'
                f' values="{fill};{fill};{LEVELS[4]};{fill};{fill}"'
                f' keyTimes="0;{a:.5f};{b:.5f};{c:.5f};1"/></rect>')

    # ---- mystery blocks, one per event, hovering under the grid ----
    blocks = ""
    for e in events:
        qv, qk = _keys(["1", "1", "0", "0"], [0.0, e["t"], e["t"] + 0.08, T], T)
        bump_v, bump_k = _keys(["0,0", "0,0", "0,-16", "0,0", "0,0"],
                               [0.0, e["t"], e["t"] + 0.1, e["t"] + 0.3, T], T)
        blocks += (f'<g><animate attributeName="opacity" dur="{T}s" repeatCount="indefinite"'
                   f' values="{qv}" keyTimes="{qk}"/>'
                   f'<g><animateTransform attributeName="transform" type="translate" dur="{T}s"'
                   f' repeatCount="indefinite" values="{bump_v}" keyTimes="{bump_k}"/>'
                   f'{sprite("qblock", e["x"], BLOCK_Y, anchor="top")}</g></g>')

    # ---- what each block gives up ----
    pops = []
    for e in events:
        cx, cy, t = e["x"], BLOCK_Y, e["t"]
        drop = GROUND - BLOCK_Y
        if e["lv"] >= 3:                      # a shell that wakes up and follows her
            pops.append(_prize(
                [(sprite("shell", 0, 0), 0.0, 2.0),
                 (sprite("turtle", 0, 0), 2.0, 6.0)],
                cx, cy, t, T,
                [(0.08, 0, 0), (0.5, 10, -70), (1.1, 26, drop), (2.0, 96, drop),
                 (4.0, 190, drop), (6.0, 280, drop)], 6.2))
        elif e["lv"] == 2:                    # a leaf drifting down
            pops.append(_prize(
                [(sprite("leaf", 0, 0), 0.0, 4.0)],
                cx, cy, t, T,
                [(0.08, 0, 0), (0.5, 8, -76), (1.4, -18, drop * 0.5),
                 (2.4, 16, drop * 0.85), (3.0, 6, drop), (4.0, 6, drop)], 4.2))
        else:                                 # a little snake slithering off
            pops.append(_prize(
                [(sprite("snake", 0, 0), 0.0, 5.0)],
                cx, cy, t, T,
                [(0.08, 0, 0), (0.5, 8, -64), (1.2, 22, drop), (3.0, 130, drop),
                 (5.0, 250, drop)], 5.2))

    # ---- her ----
    girl = (f'<g><animateTransform attributeName="transform" type="translate" dur="{T}s"'
            f' repeatCount="indefinite" calcMode="linear" values="{run_v}" keyTimes="{run_k}"/>'
            f'<g><animateTransform attributeName="transform" type="translate" dur="{T}s"'
            f' repeatCount="indefinite" calcMode="linear" values="{jump_v}" keyTimes="{jump_k}"/>'
            f'<ellipse cx="0" cy="-4" rx="46" ry="9" fill="#000" fill-opacity=".35"/>'
            f'<g><animateTransform attributeName="transform" type="translate" dur="0.42s"'
            f' repeatCount="indefinite" values="0,0;0,-7;0,0" keyTimes="0;0.5;1"/>'
            f'{sprite("girl", 0, 6)}</g></g></g>')

    # ---- scenery ----
    back = ""
    for hx in range(40, VB_W, 244):
        back += sprite("hill", hx + 120, GROUND + 2)
    for gx in range(150, VB_W - 80, 302):
        back += sprite("grass", gx, GROUND + 12)
    back += sprite("signL", 215, 574) + sprite("signR", 1995, 574)

    stars = ""
    for k in range(26):
        sx = 120 + (k * 331) % (VB_W - 240)
        sy = 170 + (k * 137) % 380
        stars += (f'<rect x="{sx}" y="{sy}" width="4" height="4" fill="#9BEFD9"'
                  f' fill-opacity=".5"><animate attributeName="fill-opacity"'
                  f' values=".12;.6;.12" dur="{2.0 + (k % 5) * 0.6}s" repeatCount="indefinite"/></rect>')

    hud = ""
    if total is not None:
        hud = (sprite("star", 78, 166) +
               f'<text class="rmono" x="104" y="160" font-size="30" fill="#CFEAE3">x {total}</text>')
    hud += sprite("tag", 1865, 116, anchor="top")

    px0, py0, px1, py1 = PANEL
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
 viewBox="0 0 {VB_W} {VB_H}" width="1000" height="{VB_H * 1000 // VB_W}" role="img" aria-label="contribution runner">
<style>.rmono {{ font-family: ui-monospace, "SF Mono", "JetBrains Mono", Consolas, monospace; }}</style>
<rect width="{VB_W}" height="{VB_H}" fill="#070f1a"/>
<rect x="{px0}" y="{py0}" width="{px1 - px0}" height="{py1 - py0}" rx="30" fill="#081420"
      stroke="#2FDDA4" stroke-opacity=".14"/>
<clipPath id="rpanel"><rect x="{px0}" y="{py0}" width="{px1 - px0}" height="{py1 - py0}" rx="30"/></clipPath>
<g clip-path="url(#rpanel)">
{stars}
{back}
<rect x="{px0}" y="{GROUND}" width="{px1 - px0}" height="{py1 - GROUND}" fill="#0B2A33"/>
<rect x="{px0}" y="{GROUND}" width="{px1 - px0}" height="6" fill="#3CEDA5"/>
{''.join(f'<rect x="{x}" y="{GROUND + 6}" width="2" height="{py1 - GROUND - 6}" fill="#07202A"/>' for x in range(int(px0), int(px1), 74))}
{''.join(cells)}
{hud}
{blocks}
{''.join(pops)}
{girl}
</g>
</svg>
'''


if __name__ == "__main__":
    data = collect()
    try:
        g = graph()
    except Exception as exc:                 # never fail the whole build on one API hiccup
        print("graphql skipped:", exc)
        g = {}
    out_dir = os.path.dirname(OUT) or "."
    os.makedirs(out_dir, exist_ok=True)
    open(OUT, "w").write(build(data, g))
    open(os.path.join(out_dir, "projects-v2.svg"), "w").write(build_projects(data["index"]))
    if g.get("weeks"):
        open(os.path.join(out_dir, "runner-v2.svg"), "w").write(
            build_runner_panel(g["weeks"], total=g.get("contributions")))
        print("wrote runner-v2.svg")
    else:
        print("no calendar data - runner panel skipped")
    print("panels:", data["repos"], "repos,", data["deployed"], "live,", g.get("contributions"), "contributions")
