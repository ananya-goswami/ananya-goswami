#!/usr/bin/env python3
"""Builds the profile panels - stats, featured projects, and the contribution runner."""
import datetime
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
    last = (g.get("last_day") or "")[:10]
    try:
        streak_day = datetime.date.fromisoformat(last).strftime("%b %-d")
    except Exception:
        streak_day = last

    # ---- top band: three columns split by dividers ----
    ring_r = 46
    band = f'''
  <line x1="333" y1="58" x2="333" y2="196" stroke="#1d3b36"/>
  <line x1="667" y1="58" x2="667" y2="196" stroke="#1d3b36"/>

  <text class="mono" x="167" y="112" text-anchor="middle" font-size="40" font-weight="700" fill="#F2FBF8">{g.get("contributions", "-")}</text>
  <text class="mono" x="167" y="140" text-anchor="middle" font-size="12.5" fill="#CFEAE3">Total Contributions</text>
  <text class="mono" x="167" y="164" text-anchor="middle" font-size="11" fill="#4e6b66">{esc(first)} to present</text>

  <circle cx="500" cy="112" r="{ring_r}" fill="none" stroke="url(#streak)" stroke-width="4.5" stroke-linecap="round"/>
  <circle cx="500" cy="67" r="15" fill="#050c10"/>
  <g transform="translate(500 67) scale(1.62)" fill="none" stroke="#3DE8AC" stroke-width="1.3" stroke-linejoin="round" stroke-linecap="round">
    <path d="M1-9.6C4-5.8 6.2-3 6.2 1A6.2 6.2 0 01-6.2 1C-6.2-1.6-4.6-3.8-2.4-5.4-2.6-2.8-1.4-1.6.4-1.8-1.4-4.2-1-7.2 1-9.6Z">
      <animate attributeName="opacity" values="1;.55;1" dur="2.4s" repeatCount="indefinite"/>
    </path>
  </g>
  <text class="mono" x="500" y="124" text-anchor="middle" font-size="34" font-weight="700" fill="#F2FBF8">{g.get("current_streak", "-")}</text>
  <text class="mono" x="500" y="180" text-anchor="middle" font-size="12.5" font-weight="700" fill="#2CD6EC">Current Streak</text>
  <text class="mono" x="500" y="200" text-anchor="middle" font-size="11" fill="#7D8590">{esc(streak_day)}</text>

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
  <linearGradient id="streak" x1="0" y1="0" x2="0.4" y2="1">
    <stop offset="0" stop-color="#C7ACFF"/><stop offset="1" stop-color="#9B78F0"/>
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


RUN_LEVELS = ["#1b2c33", "#2f7f68", "#3fae86", "#5FD8A8", "#8FE9F5"]
RUN_SKIN = {
    "shell": "#B9C7D4",     # robot chassis (legacy)
    "shade": "#7C94A6",
    "visor": "#08161c",
    "eye": "#5FD8A8",
    "cap_h": "#5FD8A8",     # pixel hero: cap
    "cap_hd": "#2f7f68",
    "face": "#F7E3C6",
    "ink": "#08161c",
    "coat": "#3FAE86",
    "coat_d": "#24725C",
    "belt": "#FFD54A",
    "pants": "#1F5E72",
    "boot": "#E0A42B",
    "hill": "#0d2129",      # scenery
    "hill2": "#102a30",
    "cloud": "#16333c",
    "brick": "#0f1d23",
    "flag": "#5FD8A8",
    "bolt": "#FFD54A",      # coins
    "bolt_dk": "#E0A42B",
    "cap": "#E1554E",       # mushroom
    "cap_dot": "#FFF1E0",
    "stem": "#F5E3C8",
    "shellg": "#4CAF50",    # turtle
    "shellg_dk": "#2E7D32",
    "skin": "#CDE58C",
    "ground": "#14242b",
    "ground_top": "#2f7f68",
}


def _px(rows, pal, px=1.0, ox=0.0, oy=0.0):
    """Render a character-map sprite as pixel rects. Origin is the sprite's
    bottom-centre, so a sprite sits on the ground at y=0."""
    h = len(rows)
    w = max(len(r) for r in rows)
    out = []
    for ry, row in enumerate(rows):
        run_c, run_x0, run_n = None, 0, 0
        def flush():
            if run_c and run_c in pal:
                x = ox + (run_x0 - w / 2.0) * px
                y = oy + (ry - h) * px
                out.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{run_n * px:.2f}" '
                           f'height="{px:.2f}" fill="{pal[run_c]}"/>')
        for rx in range(w + 1):
            c = row[rx] if rx < len(row) else "."
            if c == run_c:
                run_n += 1
                continue
            flush()
            run_c, run_x0, run_n = c, rx, 1
    return "".join(out)


HERO_A = [
    "..HHHHH...",
    ".HHHHHHHH.",
    ".HHHHHHHH.",
    "..dddddd..",
    "..FFFFFF..",
    "..FeFFeF..",
    "..FFFFFF..",
    ".CCCCCCCC.",
    "cCCCBBCCCc",
    "cCCCCCCCCc",
    "..PPPPPP..",
    "..PP..PP..",
    "..PP..PP..",
    ".SSS..SSS.",
]
HERO_B = [
    "..HHHHH...",
    ".HHHHHHHH.",
    ".HHHHHHHH.",
    "..dddddd..",
    "..FFFFFF..",
    "..FeFFeF..",
    "..FFFFFF..",
    ".CCCCCCCC.",
    "cCCCBBCCCc",
    "cCCCCCCCCc",
    "..PPPPPP..",
    ".PPP..PPP.",
    ".PP....PP.",
    "SS......SS",
]
HERO_JUMP = [
    "c.HHHHH..c",
    "ccHHHHHHcc",
    ".cHHHHHHc.",
    "..dddddd..",
    "..FFFFFF..",
    "..FeFFeF..",
    "..FFFFFF..",
    "..CCCCCC..",
    "..CCBBCC..",
    "..CCCCCC..",
    "..PPPPPP..",
    ".PPPPPPPP.",
    "SSS....SSS",
    "..........",
]
COIN_PX = [
    "..gg..",
    ".gllg.",
    ".glgg.",
    ".gggg.",
    ".gggg.",
    "..gg..",
]
MUSH_PX = [
    "..mmmm..",
    ".mwwmmm.",
    "mmwwmmwm",
    "mmmmmwwm",
    "mwmmmmmm",
    ".ssFFss.",
    "..FFFF..",
]
TURT_PX = [
    "..tttt..",
    ".tggggt.",
    "ktgggggt",
    "kkggggg.",
    ".kkkkkk.",
    "..k..k..",
]


def _hero_pal():
    S = RUN_SKIN
    return {"H": S["cap_h"], "d": S["cap_hd"], "F": S["face"], "e": S["ink"],
            "C": S["coat"], "c": S["coat_d"], "B": S["belt"], "P": S["pants"],
            "S": S["boot"]}


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


def build_runner_panel(weeks, total=None):
    """A little pixel robot runs the contribution grid, popping the days you showed up on."""
    CELL, PITCH, TOP = 12, 16, 26
    grid = _levels(weeks)
    cols = len(grid)
    GW = cols * PITCH
    GRID_BOT = TOP + 7 * PITCH
    GROUND = GRID_BOT + 20           # standing surface
    IH = GROUND + 16
    T = 24.0                         # seconds per loop

    X0, X1 = -22.0, GW + 22.0

    # ---- pick the blocks worth jumping for ----
    events, last_col = [], -99
    for i, col in enumerate(grid):
        filled = [r for r, l in enumerate(col) if l > 0]
        if not filled:
            continue
        r = max(filled)                       # the lowest lit cell, easiest to reach
        cell_bottom = TOP + r * PITCH + CELL
        apex = GROUND - (cell_bottom + 16)    # how high the feet have to go
        if apex > 80 or i - last_col < 2:     # out of reach, or too soon after the last hop
            continue
        events.append({"col": i, "row": r, "apex": max(10.0, apex),
                       "x": i * PITCH + 2 + CELL / 2.0})
        last_col = i
    if len(events) > 16:                      # thin them out, keep the spread
        step = len(events) / 16.0
        events = [events[int(k * step)] for k in range(16)]

    # ---- pace it: dash across the quiet months, cruise through the busy ones ----
    stops = [X0] + [e["x"] for e in events] + [X1]
    weight = [max(abs(stops[i + 1] - stops[i]), 1.0) ** 0.55 + 7.0
              for i in range(len(stops) - 1)]
    scale = T / sum(weight)
    marks, acc = [0.0], 0.0
    for w in weight:
        acc += w * scale
        marks.append(acc)
    marks[-1] = T
    for k, e in enumerate(events):
        e["t"] = marks[k + 1]
    run_x = (";".join(f"{x:.1f},{GROUND}" for x in stops),
             ";".join(f"{m / T:.5f}" for m in marks))

    prize = {}                                # most blocks give a coin
    if len(events) >= 4:
        prize[len(events) // 2] = "mushroom"

    # ---- robot vertical track ----
    JD = 0.66
    vals, keys = ["0,0"], [0.0]
    for e in events:
        t0, t1 = e["t"] - JD / 2, e["t"] + JD / 2
        h = e["apex"]
        for frac, lift in ((0.0, 0.0), (0.28, 0.72), (0.5, 1.0), (0.72, 0.72), (1.0, 0.0)):
            keys.append((t0 + frac * (t1 - t0)) / T)
            vals.append(f"0,{-h * lift:.1f}")
    keys.append(1.0)
    vals.append("0,0")
    keys = [min(max(k, 0.0), 1.0) for k in keys]
    for i in range(1, len(keys)):              # keyTimes must never step backwards
        keys[i] = max(keys[i], keys[i - 1])
    robot_y = (";".join(vals), ";".join(f"{k:.5f}" for k in keys))

    # thruster fires only while airborne
    fl_v, fl_k = ["0"], [0.0]
    for e in events:
        t0, t1 = e["t"] - JD / 2, e["t"] + JD / 2
        for frac, o in ((0.0, 0.0), (0.18, 1.0), (0.82, 1.0), (1.0, 0.0)):
            fl_k.append((t0 + frac * (t1 - t0)) / T)
            fl_v.append(str(o))
    fl_k.append(1.0)
    fl_v.append("0")
    fl_k = [min(max(k, 0.0), 1.0) for k in fl_k]
    for i in range(1, len(fl_k)):
        fl_k[i] = max(fl_k[i], fl_k[i - 1])

    # ---- the grid, with the hit cells flashing and dimming ----
    hit = {(e["col"], e["row"]): i for i, e in enumerate(events)}
    cells = []
    for i, col in enumerate(grid):
        for r, lv in enumerate(col):
            x, y = i * PITCH + 2, TOP + r * PITCH
            fill = RUN_LEVELS[lv]
            k = hit.get((i, r))
            if k is None:
                cells.append(f'<rect class="k" x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{fill}"/>')
                continue
            t = events[k]["t"]
            a, b, c = t / T, (t + 0.09) / T, (t + 0.26) / T
            cells.append(
                f'<rect class="k" x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{fill}">'
                f'<animateTransform attributeName="transform" type="translate" dur="{T}s" repeatCount="indefinite"'
                f' values="0,0;0,0;0,-6;0,0;0,0" keyTimes="0;{a:.5f};{b:.5f};{c:.5f};1"/>'
                f'<animate attributeName="fill" dur="{T}s" repeatCount="indefinite"'
                f' values="{fill};{fill};#FFF3C4;{RUN_LEVELS[1]};{RUN_LEVELS[1]}"'
                f' keyTimes="0;{a:.5f};{b:.5f};{c:.5f};1"/>'
                f'</rect>')

    # ---- what comes out of each block ----
    pops = []
    for k, e in enumerate(events):
        cx = e["col"] * PITCH + 2 + CELL / 2
        cy = TOP + e["row"] * PITCH
        a, b, c = e["t"] / T, (e["t"] + 0.1) / T, (e["t"] + 0.75) / T
        dyg = GROUND - cy          # how far down to the ground from this block
        if prize.get(k) == "mushroom":
            pops.append(
                f'<g opacity="0"><animate attributeName="opacity" dur="{T}s" repeatCount="indefinite"'
                f' values="0;0;1;1;0;0" keyTimes="0;{a:.5f};{b:.5f};{(e["t"]+2.5)/T:.5f};{(e["t"]+2.8)/T:.5f};1"/>'
                f'<g transform="translate({cx} {cy})">'
                f'<animateTransform attributeName="transform" type="translate" dur="{T}s" repeatCount="indefinite"'
                f' additive="sum" values="0,0;0,0;0,-16;0,-16;18,{dyg};94,{dyg};94,{dyg}"'
                f' keyTimes="0;{a:.5f};{b:.5f};{(e["t"]+0.5)/T:.5f};{(e["t"]+1.1)/T:.5f};{(e["t"]+2.8)/T:.5f};1"/>'
                f'{_px(MUSH_PX, {"m": RUN_SKIN["cap"], "w": RUN_SKIN["cap_dot"], "F": RUN_SKIN["stem"], "s": "#D8C3A2"}, 1.6, 0, 5.6)}'
                f'</g></g>')
        else:
            pops.append(
                f'<g opacity="0"><animate attributeName="opacity" dur="{T}s" repeatCount="indefinite"'
                f' values="0;0;1;1;0;0" keyTimes="0;{a:.5f};{b:.5f};{(e["t"]+0.5)/T:.5f};{c:.5f};1"/>'
                f'<g transform="translate({cx} {cy})">'
                f'<animateTransform attributeName="transform" type="translate" dur="{T}s" repeatCount="indefinite"'
                f' additive="sum" values="0,0;0,0;0,-20;0,-24;0,-24"'
                f' keyTimes="0;{a:.5f};{b:.5f};{c:.5f};1"/>'
                f'<g><animateTransform attributeName="transform" type="scale" dur="0.62s"'
                f' repeatCount="indefinite" values="1,1;0.15,1;1,1;0.15,1;1,1" keyTimes="0;0.25;0.5;0.75;1"/>'
                f'{_px(COIN_PX, {"g": RUN_SKIN["bolt"], "l": "#FFF3C4"}, 1.5, 0, 4.5)}'
                f'</g></g></g>')

    # ---- one turtle, timed to wander under a jump ----
    turtle = ""
    if events:
        e = events[len(events) // 3]
        vt = (GW + 44.0) / T * 0.55
        lead = min(6.0, e["t"] - 0.2)
        xt0 = e["x"] + vt * lead
        ts = e["t"] - lead
        te = ts + (xt0 + 30) / vt
        te = min(te, T)
        turtle = (
            f'<g opacity="0"><animate attributeName="opacity" dur="{T}s" repeatCount="indefinite"'
            f' values="0;0;1;1;0;0" keyTimes="0;{ts/T:.5f};{(ts+0.25)/T:.5f};{(te-0.25)/T:.5f};{te/T:.5f};1"/>'
            f'<g transform="translate({xt0} {GROUND})">'
            f'<animateTransform attributeName="transform" type="translate" dur="{T}s" repeatCount="indefinite"'
            f' additive="sum" values="0,0;0,0;{-vt*(te-ts):.1f},0;{-vt*(te-ts):.1f},0"'
            f' keyTimes="0;{ts/T:.5f};{te/T:.5f};1"/>'
            f'<g><animateTransform attributeName="transform" type="translate" dur="0.5s"'
            f' repeatCount="indefinite" values="0,0;0,-1;0,0" keyTimes="0;0.5;1"/>'
            f'{_px(TURT_PX, {"t": RUN_SKIN["shellg_dk"], "g": RUN_SKIN["shellg"], "k": RUN_SKIN["skin"]}, 1.7, 0, 0)}'
            f'<rect x="-6.8" y="-6.4" width="1.6" height="1.6" fill="#18321a"/>'
            f'</g></g></g>')

    # ---- the pixel hero ----
    S = RUN_SKIN
    HP = _hero_pal()
    PX = 1.15
    run_a = _px(HERO_A, HP, PX)
    run_b = _px(HERO_B, HP, PX)
    jump_f = _px(HERO_JUMP, HP, PX)
    air_v = ";".join(fl_v)
    air_k = ";".join(f"{k:.5f}" for k in fl_k)
    gnd_v = ";".join("1" if v == "0" else "0" for v in fl_v)

    robot = f'''<g>
  <animateTransform attributeName="transform" type="translate" dur="{T}s" repeatCount="indefinite"
    calcMode="linear" values="{run_x[0]}" keyTimes="{run_x[1]}"/>
  <g>
    <animateTransform attributeName="transform" type="translate" dur="{T}s" repeatCount="indefinite"
      calcMode="linear" values="{robot_y[0]}" keyTimes="{robot_y[1]}"/>
    <ellipse cx="0" cy="0" rx="7" ry="2" fill="#000" fill-opacity=".35"/>
    <g opacity="1">
      <animate attributeName="opacity" dur="{T}s" repeatCount="indefinite"
        values="{gnd_v}" keyTimes="{air_k}"/>
      <g>{run_a}<animate attributeName="opacity" values="1;0" keyTimes="0;0.5"
        dur="0.34s" calcMode="discrete" repeatCount="indefinite"/></g>
      <g opacity="0">{run_b}<animate attributeName="opacity" values="0;1" keyTimes="0;0.5"
        dur="0.34s" calcMode="discrete" repeatCount="indefinite"/></g>
    </g>
    <g opacity="0">
      <animate attributeName="opacity" dur="{T}s" repeatCount="indefinite"
        values="{air_v}" keyTimes="{air_k}"/>
      {jump_f}
    </g>
  </g>
</g>'''

    # ---- scenery: pixel clouds up top, low hills along the ground ----
    scenery = ""
    for cx in range(40, GW, 210):
        scenery += (f'<g fill="{S["cloud"]}" transform="translate({cx} 6)">'
                    f'<rect x="4" y="0" width="14" height="4"/><rect x="0" y="4" width="26" height="4"/>'
                    f'<rect x="8" y="-4" width="8" height="4"/></g>')
    for hx in range(0, GW, 132):
        scenery += (f'<g fill="{S["hill"]}" transform="translate({hx} {GROUND})">'
                    f'<rect x="18" y="-4" width="48" height="4"/><rect x="26" y="-8" width="32" height="4"/>'
                    f'<rect x="34" y="-12" width="16" height="4"/></g>')

    bricks = ""
    for bx in range(0, GW, 16):
        bricks += f'<rect x="{bx + 15}" y="{GROUND + 2}" width="1" height="{IH - GROUND - 2}" fill="{S["brick"]}"/>'
    bricks += f'<rect x="0" y="{GROUND + 8}" width="{GW}" height="1" fill="{S["brick"]}"/>'

    inner = f'''<svg x="0" y="0" width="{GW}" height="{IH}" viewBox="0 0 {GW} {IH}">
{scenery}
<rect x="0" y="{GROUND}" width="{GW}" height="{IH - GROUND}" fill="{S['ground']}"/>
<rect x="0" y="{GROUND}" width="{GW}" height="1.6" fill="{S['ground_top']}" fill-opacity=".8"/>
{bricks}
{''.join(cells)}
{''.join(pops)}
{turtle}
{robot}
</svg>'''

    W = 1000
    inner_w = W - 64
    k = inner_w / GW
    inner_h = IH * k
    H = int(inner_h + 52)
    hud = ""
    if total is not None:
        hud = (f'<g transform="translate(40 44)" opacity=".9">'
               f'{_px(COIN_PX, {"g": S["bolt"], "l": "#FFF3C4"}, 1.6, 0, 4.8)}'
               f'<text class="rmono" x="11" y="4" font-size="12.5" fill="#CFEAE3">x {total}</text></g>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="contribution runner">
<defs>
  <linearGradient id="rbg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#04070a"/><stop offset="60%" stop-color="#060e12"/><stop offset="100%" stop-color="#04090c"/>
  </linearGradient>
  <radialGradient id="rglow"><stop offset="0%" stop-color="#9BE7C4" stop-opacity=".12"/><stop offset="100%" stop-color="#9BE7C4" stop-opacity="0"/></radialGradient>
  <pattern id="rscan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#7fffd4" fill-opacity=".028"/></pattern>
  <clipPath id="rwin"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14"/></clipPath>
</defs>
<style>.rmono {{ font-family: ui-monospace, "SF Mono", "JetBrains Mono", Consolas, monospace; }}
  .k {{ shape-rendering: geometricPrecision; rx: 3px; ry: 3px; }}</style>
<rect width="{W}" height="{H}" rx="14" fill="url(#rbg)"/>
<ellipse cx="500" cy="{H}" rx="520" ry="200" fill="url(#rglow)"/>
<svg x="32" y="26" width="{inner_w}" height="{inner_h:.0f}" viewBox="0 0 {GW} {IH}" preserveAspectRatio="xMidYMid meet">
{inner}
</svg>
{hud}
<g clip-path="url(#rwin)"><rect width="{W}" height="{H}" fill="url(#rscan)"/></g>
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
