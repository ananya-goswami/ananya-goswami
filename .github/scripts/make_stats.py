#!/usr/bin/env python3
"""Builds the profile panels - stats, featured projects, and the contribution runner."""
import json
import math
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


# ------------------------------------------------------------------ alpha keying
def _feather(mask, radius=0.9):
        """Soften a hard 0/255 cut into an anti-aliased edge.
        
            A flood-filled silhouette is a perfect binary mask, which reads as a
                jagged, stair-stepped cutout once it is scaled down into the README.
                    A touch of blur on just the alpha channel gives every sprite the same
                        clean, anti-aliased edge as the rest of the reference art.
                            """
        import numpy as np
        from PIL import Image, ImageFilter
        soft = Image.fromarray(mask.astype("uint8"), "L").filter(ImageFilter.GaussianBlur(radius))
        return np.asarray(soft, dtype=float)
    

def _silhouette(d, np, cut=24.0):
    """Solid alpha: only background reachable from the crop edge is cut away.

    Dark pixels inside a sprite (navy jacket, hair) sit close to the panel
    colours, so a plain distance key makes the sprite see-through. Flooding in
    from the border instead keeps every enclosed pixel fully opaque.
    """
    from collections import deque
    h, w = d.shape
    raw = d < cut
    bgish = raw.copy()                  # erode: a 1px seam is not background
    bgish[1:, :] &= raw[:-1, :]
    bgish[:-1, :] &= raw[1:, :]
    bgish[:, 1:] &= raw[:, :-1]
    bgish[:, :-1] &= raw[:, 1:]
    bgish[0, :] = raw[0, :]             # the rim still has to seed the flood
    bgish[-1, :] = raw[-1, :]
    bgish[:, 0] = raw[:, 0]
    bgish[:, -1] = raw[:, -1]
    outside = np.zeros((h, w), dtype=bool)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if bgish[y, x] and not outside[y, x]:
                outside[y, x] = True
                q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if bgish[y, x] and not outside[y, x]:
                outside[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and bgish[ny, nx] and not outside[ny, nx]:
                outside[ny, nx] = True
                q.append((ny, nx))
    grown = outside.copy()              # dilate back onto the true background
    grown[1:, :] |= outside[:-1, :]
    grown[:-1, :] |= outside[1:, :]
    grown[:, 1:] |= outside[:, :-1]
    grown[:, :-1] |= outside[:, 1:]
    return _feather(np.where(grown & raw, 0.0, 255.0))

_USED = {}      # sprite id -> (data uri, w, h), for one <defs> entry each


def sprite_defs():
    """<image> definitions for every sprite that was actually placed."""
    return "".join(f'<image id="sp-{n}" x="0" y="0" width="{w}" height="{h}"'
                   f' xlink:href="{u}"/>' for n, (u, w, h) in _USED.items())


# ---------------------------------------------------------------- sprite sheet
# The reference atlas holds complete flipbooks for the avatar, turtle, leaf,
# and snake. Timing code below gives each pose one logical job.
SHEET_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                          "assets", "sprite-sheet.png")
SHEET_BG = (0, 26, 28)
SHEET_PAD = 3
# The ground line each panel of the sheet is drawn on. Frames keep their own
# distance from it, so a jump frame really does sit higher than a run frame.
SHEET_BASE = {"avatar": 221.0, "turtle": 454.0, "lettuce": 665.0, "snake": 884.0}
# row: (panel, [(x0, y0, x1, y1, centre line of the body), ...])
SHEET_ROWS = {
    "run": ("avatar", [(22, 113, 98, 217, 60), (100, 114, 175, 215, 137), (177, 113, 250, 217, 213), (251, 113, 326, 207, 288), (326, 109, 401, 216, 363), (405, 110, 480, 214, 442), (484, 109, 559, 213, 521), (564, 111, 637, 209, 600)]),
    "jump": ("avatar", [(748, 134, 819, 217, 783), (830, 100, 902, 217, 866), (914, 106, 986, 217, 950), (995, 127, 1066, 216, 1030)]),
    "hit": ("avatar", [(1106, 120, 1179, 218, 1142), (1190, 111, 1261, 217, 1225), (1274, 122, 1351, 216, 1312)]),
    "land": ("avatar", [(1397, 134, 1469, 217, 1433), (1488, 136, 1560, 217, 1524), (1571, 115, 1646, 217, 1608)]),
    "twalk": ("turtle", [(33, 393, 103, 446, 68), (125, 399, 193, 447, 159), (208, 393, 279, 446, 243), (296, 398, 364, 446, 330), (382, 393, 451, 446, 416), (466, 396, 532, 446, 499)]),
    "teat": ("turtle", [(566, 407, 607, 451, 586), (620, 401, 690, 449, 655), (740, 402, 811, 450, 775), (833, 406, 904, 450, 868), (925, 417, 957, 449, 941), (1028, 380, 1102, 449, 1065)]),
    "thide": ("turtle", [(1143, 393, 1215, 447, 1179), (1231, 399, 1295, 448, 1263), (1317, 401, 1372, 449, 1344), (1402, 409, 1461, 448, 1431), (1488, 407, 1548, 449, 1518), (1578, 398, 1641, 448, 1609)]),
    "lpop": ("lettuce", [(467, 609, 500, 649, 483), (555, 591, 600, 656, 577)]),
    "lfall": ("lettuce", [(685, 612, 723, 652, 704), (777, 607, 814, 648, 795), (872, 606, 910, 648, 891)]),
    "lslide": ("lettuce", [(1286, 621, 1330, 659, 1308)]),
    "sslith": ("snake", [(27, 812, 135, 878, 81), (155, 815, 252, 880, 203), (264, 816, 363, 880, 313), (377, 815, 473, 879, 425), (488, 811, 593, 877, 540), (610, 811, 715, 877, 662), (731, 814, 837, 877, 784), (851, 810, 958, 878, 904)]),
    "stongue": ("snake", [(1006, 814, 1121, 878, 1063), (1145, 806, 1261, 879, 1203)]),
    "scont": ("snake", [(1349, 812, 1446, 879, 1397), (1465, 814, 1561, 878, 1513)]),
}
_SHEET = None


def sheet():
    """Cut every sheet frame out, keyed to transparency.

    Returns {(row, i): (data_uri, w, h, ox, oy)}, where ox/oy is the frame's own
    anchor: the centre line of the body and the ground it stands on. Two frames
    placed at the same point therefore line their bodies and their feet up,
    instead of lining up two bounding boxes of different sizes.
    """
    global _SHEET
    if _SHEET is not None:
        return _SHEET
    _SHEET = {}
    try:
        import base64, io
        import numpy as np
        from PIL import Image
        src = Image.open(SHEET_PATH).convert("RGB")
    except Exception as exc:
        print("sheet skipped:", exc)
        return _SHEET
    bg = np.array(SHEET_BG, dtype=float)
    for row, (panel, frames) in SHEET_ROWS.items():
        base_y = SHEET_BASE[panel]
        for i, (x0, y0, x1, y1, ax) in enumerate(frames):
            cx0, cy0 = x0 - SHEET_PAD, y0 - SHEET_PAD
            crop = src.crop((cx0, cy0, x1 + SHEET_PAD, y1 + SHEET_PAD))
            a = np.array(crop).astype(float)
            d = np.linalg.norm(a - bg, axis=2)
            alpha = _silhouette(d, np, cut=10.0)
            # Two things used to leave the sheet's own backdrop on screen. The
            # feather inside _silhouette blurs the mask outwards as well as in,
            # so pure background pixels came out up to 60% opaque and painted a
            # teal fringe round every sprite; and background trapped inside a
            # shape - the hollow of the snake's tail, the gap under her shoe -
            # is unreachable by a flood that starts at the border, so it stayed
            # solid. Capping the alpha by how far the pixel actually is from the
            # backdrop colour clears both: on this sheet the backdrop reaches
            # d=10 and the nearest real sprite pixel is d=32, so the cut lands
            # in open space and takes nothing with it.
            alpha = np.minimum(alpha, np.clip((d - 12.0) / 14.0, 0.0, 1.0) * 255.0)
            img = Image.fromarray(np.dstack([a, alpha]).astype(np.uint8), "RGBA")
            buf = io.BytesIO()
            flat = img.convert("RGB").quantize(colors=96, method=Image.FASTOCTREE).convert("RGBA")
            flat.putalpha(img.getchannel("A"))
            flat.save(buf, "PNG", optimize=True)
            _SHEET[(row, i)] = (
                "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(),
                img.width, img.height, ax - cx0, base_y - cy0)
    return _SHEET


def sheet_use(row, i, scale=1.0, dx=0.0, dy=0.0):
    """One sheet frame, drawn with its anchor on the origin."""
    got = sheet().get((row, i))
    if not got:
        return ""
    uri, w, h, ox, oy = got
    fid = "sf-%s%d" % (row, i)
    _USED[fid] = (uri, w, h)
    return (f'<use xlink:href="#sp-{fid}" transform="translate({dx - ox * scale:.1f}'
            f' {dy - oy * scale:.1f}) scale({scale:.4f})"/>')


def sheet_row(row, scale=1.0, dx=0.0, dy=0.0, only=None):
    """Frames of a row, in order, ready to hand to flipbook() or sequence()."""
    idx = range(len(SHEET_ROWS[row][1])) if only is None else only
    return [sheet_use(row, i, scale, dx, dy) for i in idx]


# ---------------------------------------------------------------- flipbooks
def flipbook(frames, cycle, weights=None):
    """Loop frames on their own clock, independent of the panel's timeline.

    One nested <animate> per frame, repeating every `cycle` seconds, costs the
    same whether the walk lasts two seconds or fifty, so a cycle never has to be
    unrolled across the whole 56s panel.
    """
    frames = [f for f in frames if f]
    if not frames:
        return ""
    ws = list(weights) if weights else [1.0] * len(frames)
    total = sum(ws) or 1.0
    out, t = "", 0.0
    for svg, w in zip(frames, ws):
        a, b = t, t + cycle * w / total
        t = b
        sv, sk = _keys(["0", "1", "0", "0"], [0.0, a, b, cycle], cycle)
        out += (f'<g opacity="0"><animate attributeName="opacity" dur="{cycle:.3f}s"'
                f' repeatCount="indefinite" calcMode="discrete"'
                f' values="{sv}" keyTimes="{sk}"/>{svg}</g>')
    return out


def sequence(frames, t0, t1, T, weights=None):
    """Play frames once, in order, across [t0, t1] of the panel's timeline."""
    frames = [f for f in frames if f]
    if not frames or t1 <= t0:
        return ""
    ws = list(weights) if weights else [1.0] * len(frames)
    total = sum(ws) or 1.0
    out, t = "", t0
    for svg, w in zip(frames, ws):
        a, b = t, t + (t1 - t0) * w / total
        t = b
        sv, sk = _keys(["0", "1", "0", "0"], [0.0, a, b, T], T)
        out += (f'<g opacity="0"><animate attributeName="opacity" dur="{T}s"'
                f' repeatCount="indefinite" calcMode="discrete"'
                f' values="{sv}" keyTimes="{sk}"/>{svg}</g>')
    return out


def bob(svg, period, rise):
    """Lift and drop a walking body on its own clock.

    A gait is not only legs. The body rises as the back leg pushes off and
    drops onto the next footfall, and without that a character slides along a
    rail however good its frames are. One period is one step, so a cycle of two
    steps gets two lifts.
    """
    if not svg or period <= 0:
        return svg
    return (f'<g><animateTransform attributeName="transform" type="translate"'
            f' dur="{period:.3f}s" repeatCount="indefinite" calcMode="spline"'
            f' values="0 0;0 {-rise:.1f};0 0" keyTimes="0;0.7;1"'
            f' keySplines="0.35 0 0.65 1;0.35 0 0.65 1"/>{svg}</g>')


def gate(svg, windows, T):
    """Show svg the whole time except inside the given windows.

    This is what lets a looping walk cycle sit underneath one-shot sequences:
    the loop keeps its own clock and simply blanks while the meal is playing.
    """
    if not svg or not windows:
        return svg
    times, vals = [0.0], ["1"]
    for a, b in sorted(windows):
        times += [a, b]
        vals += ["0", "1"]
    times.append(T)
    vals.append(vals[-1])
    gv, gk = _keys(vals, times, T)
    return (f'<g><animate attributeName="opacity" dur="{T}s" repeatCount="indefinite"'
            f' calcMode="discrete" values="{gv}" keyTimes="{gk}"/>{svg}</g>')


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
VB_W, VB_H = 2172, 724                  # reference-art coordinate space
PANEL = (33, 95, 2139, 627)
GX0, GY0, GCELL, GPX, GPY = 85.0, 180.0, 26.0, 37.2, 36.5
GROUND = 588.0                          # top of the ground line
LEVELS = ["#06313E", "#128070", "#18A088", "#20D898", "#9BEFD9"]
# Every sprite comes off the sheet at its drawn size, so one scale per
# character is all that is needed to land it at the size the panel used before.
GIRL_TARGET_H = 128.0                # her displayed height, unchanged
GIRL_S = GIRL_TARGET_H / 104.0
TURTLE_S, LEAF_S, SNAKE_S = 1.00, 0.82, 0.92
V_LEAF, V_TURTLE, V_SNAKE, V_LIMP = 19.0, 34.0, 48.0, 22.0
EAT = 3.0                            # a readable set of bites, not a rapid flicker
LEAF_GAP = 39.0                      # smaller leaf halts with its edge at the mouth
# Flipbook speeds. Each is the time for one full loop of that character's cycle.
# One cycle is two steps. Her stride is 62 units a step at this scale and she
# crosses the panel at 134 units a second, so two steps have to take 0.92s; at
# the 0.60 it used to run, her legs churned half again too fast for the ground
# and she skated along instead of walking.
RUN_CYCLE = 0.92                     # 8 frames: contact, pass, contact, pass
# Its four legs are planted 43 units apart, so a step moves it about half that
# and two steps take 42/34 of a second at its walking speed.
WALK_CYCLE = 1.24
TURTLE_BOB = 2.5                     # it is 53 tall; a plod lifts about 5%
SLITHER_CYCLE = 3.30                 # body wave, then a clearly held tongue-flick hiss

# HUD star. The old one was a crop from the reference art, so it came out
# tilted a few degrees and sat low beside the x N label. This is generated
# geometry instead: a regular five-pointed star, first tip straight up, inner
# radius cos(72)/cos(36) of the outer so every arm matches, centred on the
# mid-height of the text next to it.
STAR_R, STAR_CX, STAR_CY = 15.0, 82.0, 149.5
STAR_RIN = STAR_R * math.cos(math.radians(72)) / math.cos(math.radians(36))
STAR_ARMS = [(STAR_R if k % 2 == 0 else STAR_RIN, math.radians(36 * k)) for k in range(10)]
STAR_XY = [(STAR_CX + r * math.sin(a), STAR_CY - r * math.cos(a)) for r, a in STAR_ARMS]
STAR_D = "M" + " ".join(f"{x:.2f} {y:.2f}" for x, y in STAR_XY) + "Z"
STAR_HUD = f'<path fill="#3CEDA5" d="{STAR_D}"/>'


def _keys(vals, times, T):
    """Clamp and monotonise keyTimes, returning the SMIL strings."""
    ks = [min(max(t / T, 0.0), 1.0) for t in times]
    for i in range(1, len(ks)):
        ks[i] = max(ks[i], ks[i - 1])
    return ";".join(vals), ";".join(f"{k:.5f}" for k in ks)


def _pick_cells(grid, cols):
    """Three real contribution cells, each on its own row, for the cast to pop out of.

    No mystery blocks: whatever she hits is an actual commit square. They sit in
    the right half so everyone has room to travel left, and the third is set well
    back so the snake turns up after the meal rather than during it.
    """
    start = int(cols * 0.52)
    picked, used = [], set()
    for want in (start, start + 5, start + 19):
        found = None
        for off in range(cols):
            for i in (want + off, want - off):
                if not 0 <= i < cols or any(abs(i - p["col"]) < 3 for p in picked):
                    continue
                for r in (6, 5, 4, 3, 2, 1, 0):
                    if r not in used and grid[i][r] > 0:
                        found = {"col": i, "row": r, "lv": grid[i][r]}
                        break
                if found:
                    break
            if found:
                break
        if not found:
            continue
        found["x"] = GX0 + found["col"] * GPX + GCELL / 2
        found["y"] = GY0 + found["row"] * GPY
        picked.append(found)
        used.add(found["row"])
    picked.sort(key=lambda p: p["col"])
    return picked


def build_runner_panel(weeks, total=None):
    """She runs the grid and knocks three real commit squares open.

    Out of them, in order: a leaf that settles onto the ground and drifts along it,
    a turtle that catches the leaf up and stops to eat, and a snake that comes
    through zig-zagging, which is her cue to pull into her shell.
    """
    grid = _levels(weeks)
    cols = min(len(grid), 53)
    grid = grid[-cols:]
    T = 56.0
    X0, X1 = -120.0, VB_W + 120.0
    BASE = GROUND + 4
    RUN = 18.0

    events = _pick_cells(grid, cols)
    speed = (X1 - X0) / RUN
    for e in events:
        e["t"] = (e["x"] - X0) / speed
    run_v = f"{X0:.1f},{GROUND};{X1:.1f},{GROUND};{X1:.1f},{GROUND}"
    run_k = f"0;{RUN / T:.5f};1"

    # ---- Mario-style jump: crouch, fast take-off, hang, then a firm landing ----
    # Use the displayed sprite height instead of a magic head position.  The
    # peak is timed exactly when her horizontal centre passes under the block.
    HEAD = GROUND - GIRL_TARGET_H
    JD_MAX, LIFT_MAX = 1.08, 184.0
    vals, keys = ["0,0"], [0.0]
    jump_windows = []
    for e in events:
        lift = min(LIFT_MAX, max(38.0, HEAD - (e["y"] + GCELL)))
        # A hop onto a low square is over quickly; only a full-height jump is
        # worth the whole beat. Time scales with the root of the height, the way
        # a real fall does, so a small hop stops hanging in the air - and the
        # shorter window leaves her running for longer between two blocks.
        jd = max(0.62, JD_MAX * math.sqrt(lift / LIFT_MAX))
        t0, t1 = e["t"] - jd * 0.54, e["t"] + jd * 0.46
        jump_windows.append((t0, t1))
        jump = ((0.00, 0.0), (0.08, -5.0), (0.30, lift * 0.62),
                (0.54, lift), (0.66, lift * 0.94), (0.84, lift * 0.48),
                (0.96, -3.0), (1.00, 0.0))
        for frac, part in jump:
            keys.append((t0 + frac * (t1 - t0)) / T)
            vals.append(f"0,{-part:.1f}")
    keys.append(1.0)
    vals.append("0,0")
    for i in range(1, len(keys)):
        keys[i] = min(max(keys[i], keys[i - 1]), 1.0)
    jump_v, jump_k = ";".join(vals), ";".join(f"{k:.5f}" for k in keys)

    # ---- the grid; the three squares she hits are mystery blocks ----
    hit = {(e["col"], e["row"]): e for e in events}
    cells = []
    for i, col in enumerate(grid):
        for r, lv in enumerate(col):
            x, y = GX0 + i * GPX, GY0 + r * GPY
            fill = LEVELS[lv]
            base = (f'<rect x="{x:.1f}" y="{y:.1f}" width="{GCELL}" height="{GCELL}" rx="7"'
                    f' fill="{fill}"')
            e = hit.get((i, r))
            if e is None:
                cells.append(base + "/>")
                continue
            cells.append(qblock(x + GCELL / 2, y + GCELL / 2, e["t"], T))

    def moving(inner, pts, t_in, t_out, fade=0.45):
        """Carry one already-animated character along pts: [(t, x, y)], in order.

        Its frames run on their own clocks inside `inner`, so this only has to
        deal with where the character is and whether it is on screen yet.
        """
        vals = [f"{pts[0][1]:.1f},{pts[0][2]:.1f}"] +                [f"{x:.1f},{y:.1f}" for _, x, y in pts] +                [f"{pts[-1][1]:.1f},{pts[-1][2]:.1f}"]
        times = [0.0] + [t for t, _, _ in pts] + [T]
        mv, mk = _keys(vals, times, T)
        ov, ok = _keys(["0", "0", "1", "1", "0", "0"],
                       [0.0, t_in, t_in + 0.06, t_out - fade, t_out, T], T)
        return (f'<g opacity="0"><animate attributeName="opacity" dur="{T}s"'
                f' repeatCount="indefinite" values="{ov}" keyTimes="{ok}"/>'
                f'<g><animateTransform attributeName="transform" type="translate" dur="{T}s"'
                f' repeatCount="indefinite" calcMode="linear" values="{mv}" keyTimes="{mk}"/>'
                f'{inner}</g></g>')

    # ---- the story: leaf, then turtle, then snake, all heading left ----
    e1 = events[0] if events else None
    e2 = events[1] if len(events) > 1 else None
    e3 = events[2] if len(events) > 2 else None
    pops = []

    if e1:
        t1 = e1["t"]
        lx0 = e1["x"] - 60.0
        leaf_land = t1 + 2.0
        t_eat = min(T - 22.0, leaf_land + 6.0)
        eat_x = lx0 - V_LEAF * (t_eat - leaf_land)

    if e2:
        t2 = e2["t"]
        # The second hit releases the tortoise, but the story must still read
        # leaf first, tortoise second. Keep it hidden until the leaf has landed.
        turtle_in = max(t2, leaf_land + 0.30)
        tx0 = e2["x"] - 34.0
        t_land2 = turtle_in + 1.6
        t_walk2 = t_land2 + 0.9
        # solve for the moment its mouth, not its middle, reaches the leaf
        t_eat = ((tx0 + V_TURTLE * t_walk2 - lx0 - V_LEAF * leaf_land
                  - LEAF_GAP) / (V_TURTLE - V_LEAF))
        t_eat = min(max(t_eat, t_walk2 + 1.5), T - 22.0)
        eat_x = tx0 - V_TURTLE * (t_eat - t_walk2)
        t_resume = t_eat + EAT

        def turtle_at(t):
            if t <= t_walk2:
                return tx0
            if t <= t_eat:
                return tx0 - V_TURTLE * (t - t_walk2)
            if t <= t_resume:
                return eat_x
            return eat_x - V_TURTLE * (t - t_resume)

    if e3:
        t3 = e3["t"]
        # Land far enough left that the faster snake catches the turtle while
        # both are still clearly visible, not at the edge of the panel.
        sx0 = e3["x"] - 150.0
        t_land3 = t3 + 1.5
        t_slith = t_land3 + 0.5
        t_gone = min(T - 0.5, t_slith + (sx0 + 240.0) / V_SNAKE)

        def snake_at(t):
            return sx0 - V_SNAKE * max(0.0, t - t_slith)

        # Never mid-meal: it cannot be chewing and shut in its shell at once.
        t_hide, probe = T - 7.0, max(t_slith, t_resume + 0.2)
        while probe < T - 7.0:
            if snake_at(probe) - turtle_at(probe) <= 115.0:
                t_hide = probe
                break
            probe += 0.05
        hide_x = turtle_at(t_hide)
        t_pass = min(T - 3.0, t_hide + (snake_at(t_hide) - hide_x + 175.0) / V_SNAKE)
        t_emerge = t_pass + 0.6
        t_crawl = t_emerge + 0.7
        exit_x = hide_x - V_LIMP * max(0.0, T - 0.4 - t_crawl)

    # The meal is approach, lower, two bites, then a pleased look. The leaf has
    # to lose a piece on the same beat that a bite pose lands, so both sequences
    # are measured off one set of boundaries rather than timed by hand.
    APPROACH, LOWER, BITE, HAPPY = 0.50, 0.45, 0.45, 0.70
    MEAL_WEIGHTS = [APPROACH, LOWER, BITE, BITE, HAPPY]
    _mw = sum(MEAL_WEIGHTS)
    _edge = [t_eat + EAT * sum(MEAL_WEIGHTS[:k]) / _mw for k in range(6)] if e2         else [T] * 6
    bite1, bite2, meal_done = _edge[2], _edge[3], _edge[4]
    if e1:
        # it drifts along the ground until the turtle catches it up, then it
        # sits still and loses a piece to every bite until there is none
        leaf_x = eat_x - LEAF_GAP if e2 else lx0 - V_LEAF * (T - leaf_land)
        leaf_end = meal_done if e2 else T
        leaf = (sequence(sheet_row("lpop", LEAF_S), t1, t1 + 0.55, T)
                + sequence(sheet_row("lfall", LEAF_S), t1 + 0.55, leaf_land, T))
        # Once it touches the ground, keep one fixed side facing the viewer.
        # Position animation carries this frame left; no flipping or rotation.
        grounded_leaf = sheet_use("lslide", 0, LEAF_S)
        if e2:
            # The turtle eats from the right, so the side its mouth is on has to
            # stay put and only the far side may shrink away; scaling about the
            # centre would make the leaf shuffle backwards out of its mouth.
            full_w = float(SHEET_ROWS["lslide"][1][0][2] - SHEET_ROWS["lslide"][1][0][0])
            crumb_w = float(SHEET_ROWS["teat"][1][4][2] - SHEET_ROWS["teat"][1][4][0])
            mouth = full_w * LEAF_S / 2.0
            half_s, crumb_s = LEAF_S * 0.66, LEAF_S * 0.62
            leaf += sequence([grounded_leaf], leaf_land, bite1, T)
            leaf += sequence([sheet_use("lslide", 0, half_s,
                                        dx=mouth - full_w * half_s / 2.0)], bite1, bite2, T)
            # one more bite and only the scrap the sheet draws is left
            leaf += sequence([sheet_use("teat", 4, crumb_s,
                                        dx=mouth - crumb_w * crumb_s / 2.0)],
                             bite2, meal_done, T)
        else:
            leaf += sequence([grounded_leaf], leaf_land, T, T)
        lpts = [(t1, e1["x"], e1["y"] + GCELL / 2),
                (t1 + 0.55, e1["x"] - 26.0, e1["y"] - 62.0),
                (t1 + 1.3, e1["x"] - 72.0, BASE - 34.0),
                (leaf_land, lx0, BASE)]
        if e2:  # it settles exactly where the turtle's mouth will reach it
            lpts.append((t_eat, leaf_x, BASE))
            lpts.append((leaf_end, leaf_x, BASE))
        lpts.append((T, leaf_x, BASE))
        pops.append(moving(leaf, lpts, t1, leaf_end, fade=0.06))

    if e2:
        walk = bob(flipbook(sheet_row("twalk", TURTLE_S), WALK_CYCLE),
                   WALK_CYCLE / 2.0, TURTLE_BOB)
        pts = [(turtle_in, e2["x"], e2["y"] + GCELL / 2),
               (turtle_in + 0.55, e2["x"] - 14.0, e2["y"] - 66.0),
               (t_land2, tx0, BASE),
               (t_walk2, tx0, BASE),
               (t_eat, eat_x, BASE),
               (t_resume, eat_x, BASE)]
        # It falls as a closed shell, lands, extends its head and all four legs,
        # then walks. The walking loop is gated off during every other state.
        states = sequence(sheet_row("thide", TURTLE_S, only=(4, 3, 4)),
                          turtle_in, t_land2, T)
        states += sequence(sheet_row("thide", TURTLE_S, only=(3, 2, 1, 0)),
                           t_land2, t_walk2, T)
        # Approach, mouth open, two bite poses, then the happy-heart pose. The
        # leaf is its own actor and shrinks on these same beats.
        states += sequence(sheet_row("teat", TURTLE_S, only=(1, 2, 3, 3, 5)),
                        t_eat, t_resume, T,
                        weights=MEAL_WEIGHTS)
        quiet = [(turtle_in, t_walk2), (t_eat, t_resume)]
        if e3:
            pts += [(t_hide, hide_x, BASE), (t_crawl, hide_x, BASE),
                    (T - 0.4, exit_x, BASE), (T, exit_x, BASE)]
            # head and all four legs go in fast, the closed shell sits out the
            # snake, then everything comes back out and it plods on
            shut = t_hide + 0.34
            states += sequence(sheet_row("thide", TURTLE_S, only=(0, 1, 2, 3)),
                               t_hide, shut, T)
            states += sequence([sheet_use("thide", 4, TURTLE_S)], shut, t_pass, T)
            states += sequence(sheet_row("thide", TURTLE_S, only=(3, 2, 1, 5)),
                               t_pass, t_emerge, T)
            quiet.append((t_hide, t_emerge))
        else:
            pts += [(T, eat_x - V_TURTLE * (T - t_resume), BASE)]
        pops.append(moving(gate(walk, quiet, T) + states, pts, turtle_in, T))

    if e3:
        snake_gone = max(sx0 - V_SNAKE * (t_gone - t_slith), -240.0)
        pts = [(t3, e3["x"], e3["y"] + GCELL / 2),
               (t3 + 0.55, e3["x"] - 12.0, e3["y"] - 60.0),
               (t_land3, sx0, BASE),
               (t_slith, sx0, BASE)]
        # A shallow zig-zag makes the travel direction readable without making
        # the grounded snake look as though it is hopping. The body flipbook
        # supplies the larger head-to-tail wave.
        zig_t = t_slith + 0.34
        zig_i = 0
        while zig_t < t_gone:
            zig_x = snake_at(zig_t)
            zig_y = BASE - (3.5 if zig_i % 2 == 0 else 0.0)
            pts.append((zig_t, zig_x, zig_y))
            zig_t += 0.34
            zig_i += 1
        pts += [(t_gone, snake_gone, BASE), (T, snake_gone, BASE)]

        # Run a clear tongue-flick/hiss beat in every slither cycle so the hiss
        # cannot disappear inside one brief pair of frames.
        slither = sheet_row("sslith", SNAKE_S)
        tongue = sheet_row("stongue", SNAKE_S)
        snake = flipbook(slither + tongue + tongue[::-1] + sheet_row("scont", SNAKE_S),
                         SLITHER_CYCLE,
                         weights=[1.0] * 8 + [2.0, 2.8, 2.8, 2.0, 1.0, 1.0])
        pops.append(moving(snake, pts, t3, t_gone))

    # ---- her ----
    girl = (f'<g><animateTransform attributeName="transform" type="translate" dur="{T}s"'
            f' repeatCount="indefinite" calcMode="linear" values="{run_v}" keyTimes="{run_k}"/>'
            f'<g><animateTransform attributeName="transform" type="translate" dur="{T}s"'
            f' repeatCount="indefinite" calcMode="linear" values="{jump_v}" keyTimes="{jump_k}"/>'
            f'<ellipse cx="0" cy="-4" rx="34" ry="7" fill="#000" fill-opacity=".35"/>'
            f'{girl_runner(jump_windows, T)}</g></g>')

    # ---- scenery ----
    # Bare skyline on purpose: the tiled sign boards and the grass tufts crowded
    # the strip and pulled the eye away from her run, so only the stars stay.
    back = ""

    stars = ""
    for k in range(26):
        sx = 120 + (k * 331) % (VB_W - 240)
        sy = 170 + (k * 137) % 380
        stars += (f'<rect x="{sx}" y="{sy}" width="4" height="4" fill="#9BEFD9"'
                  f' fill-opacity=".5"><animate attributeName="fill-opacity"'
                  f' values=".12;.6;.12" dur="{2.0 + (k % 5) * 0.6}s" repeatCount="indefinite"/></rect>')

    hud = ""
    if total is not None:
        hud = (STAR_HUD +
               f'<text class="rmono" x="104" y="160" font-size="30" fill="#CFEAE3">x {total}</text>')

    px0, py0, px1, py1 = PANEL
    coin_y = GCELL / 2 - GCELL * QBLOCK_S / 2 - COIN_R * 0.5
    coins = "".join(pop_coin(e["x"], e["y"] + coin_y, e["t"], T)
                    for e in events)
    coins += "".join(float_coin(fx, fy, k)
                     for k, (fx, fy) in enumerate(coin_cells(grid, cols, hit)))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
    viewBox="{px0} {py0} {px1 - px0} {py1 - py0}" width="1000" height="{(py1 - py0) * 1000 // (px1 - px0)}" role="img" aria-label="contribution runner">
     <defs>{sprite_defs()}{COIN_DEFS}</defs>
<style>.rmono {{ font-family: ui-monospace, "SF Mono", "JetBrains Mono", Consolas, monospace; }}</style>
<rect x="{px0}" y="{py0}" width="{px1 - px0}" height="{py1 - py0}" fill="#081420"/>
<clipPath id="rpanel"><rect x="{px0}" y="{py0}" width="{px1 - px0}" height="{py1 - py0}"/></clipPath>
<g clip-path="url(#rpanel)">
{stars}
{back}
<rect x="{px0}" y="{GROUND}" width="{px1 - px0}" height="{py1 - GROUND}" fill="#0B2A33"/>
<rect x="{px0}" y="{GROUND}" width="{px1 - px0}" height="6" fill="#3CEDA5"/>
{''.join(f'<rect x="{x}" y="{GROUND + 6}" width="2" height="{py1 - GROUND - 6}" fill="#07202A"/>' for x in range(int(px0), int(px1), 74))}
{''.join(cells)}
{hud}
{coins}
{''.join(pops)}
{girl}
</g>
</svg>
'''


# ---------------------------------------------------------------- coins
QBLOCK_S = 1.35     # mystery block: a little bigger than a plain cell
COIN_R = 13.0        # gold coin radius
COIN_POP = 1.15     # seconds for one coin to arc out of a block
COIN_RISE = 124.0   # how high that arc goes
COIN_DEFS = ('<radialGradient id="coinG" cx="0.36" cy="0.3" r="0.8">'
             '<stop offset="0" stop-color="#FFF6C4"/>'
             '<stop offset="0.55" stop-color="#FFD24A"/>'
             '<stop offset="1" stop-color="#E0941C"/></radialGradient>'
             '<radialGradient id="coinHalo" cx="0.5" cy="0.5" r="0.5">'
             '<stop offset="0.5" stop-color="#050A14" stop-opacity="0.95"/>'
             '<stop offset="1" stop-color="#050A14" stop-opacity="0"/>'
             '</radialGradient>')
COIN_LIFT = 21.0    # a coin floats clear above its own square

def coin_cells(grid, cols, skip):
    # Hovering coins only sit above a real contribution square, never an
    # empty one, and each takes a different row so they do not line up.
    out, k = [], 0
    step = max(3, cols // 10)
    for i in range(1, cols, step):
        opts = []
        for j in range(i, min(cols, i + step)):
            opts = [(j, r) for r in range(1, 7)
                    if grid[j][r] > 0 and (j, r) not in skip]
            if opts:
                break
        if not opts:
            continue
        c, r = opts[k % len(opts)]
        out.append((GX0 + c * GPX + GCELL / 2, GY0 + r * GPY - COIN_LIFT))
        k += 1
    return out


def coin_face(r):
    # One coin, centred on the origin: body, highlight, engraved notch.
    return (f'<circle r="{r * 1.8:.1f}" fill="url(#coinHalo)"/>'
            f'<circle r="{r:.1f}" fill="url(#coinG)" stroke="#8A5A12"'
            f' stroke-width="{r * 0.17:.2f}"/>'
            f'<ellipse cx="{-r * 0.22:.2f}" cy="{-r * 0.18:.2f}"'
            f' rx="{r * 0.3:.2f}" ry="{r * 0.46:.2f}" fill="#FFF8DC"'
            f' fill-opacity="0.7"/>'
            f'<rect x="{-r * 0.11:.2f}" y="{-r * 0.5:.2f}"'
            f' width="{r * 0.22:.2f}" height="{r:.1f}" rx="{r * 0.11:.2f}"'
            f' fill="#B9791C" fill-opacity="0.45"/>')


def coin_spin(dur, begin=0.0, r=COIN_R):
    # Mario coin flip: face on for most of the cycle, then a quick spin.
    return (f'<g>{coin_face(r)}<animateTransform attributeName="transform"'
            f' type="scale" values="1 1;1 1;0.22 1;1 1;1 1"'
            f' keyTimes="0;0.34;0.5;0.66;1"'
            f' dur="{dur:.2f}s" begin="{begin:.2f}s"'
            f' repeatCount="indefinite"/></g>')


def pop_coin(x, y, t, T, r=COIN_R):
    # Punched out of a block: quick off the face, slow at the apex, back down.
    arc = [(0.0, 0.0), (0.16, 0.52), (0.32, 0.85), (0.5, 1.0),
           (0.68, 0.85), (0.84, 0.5), (1.0, -0.04)]
    pts = [(0.0, 0.0)] + [(t + f * COIN_POP, hh) for f, hh in arc] + [(T, -0.04)]
    mv, mk = _keys([f"0,{-hh * COIN_RISE:.1f}" for _, hh in pts],
                   [tt for tt, _ in pts], T)
    ov, ok = _keys(["0", "0", "1", "1", "0", "0"],
                   [0.0, t, t + 0.02, t + COIN_POP * 0.8, t + COIN_POP, T], T)
    return (f'<g transform="translate({x:.1f} {y:.1f})" opacity="0">'
            f'<animate attributeName="opacity" dur="{T}s"'
            f' repeatCount="indefinite" values="{ov}" keyTimes="{ok}"/>'
            f'<g><animateTransform attributeName="transform" type="translate"'
            f' dur="{T}s" repeatCount="indefinite" calcMode="linear"'
            f' values="{mv}" keyTimes="{mk}"/>{coin_spin(0.9, 0.0, r)}</g></g>')


def float_coin(x, y, k, r=COIN_R):
    # Hovering coin: eased bob, staggered so a row does not move in lockstep.
    return (f'<g transform="translate({x:.1f} {y:.1f})">'
            f'<g><animateTransform attributeName="transform" type="translate"'
            f' values="0,0;0,-4;0,0" keyTimes="0;0.5;1" calcMode="spline"'
            f' keySplines="0.4 0 0.6 1;0.4 0 0.6 1"'
            f' dur="{2.1 + (k % 4) * 0.25:.2f}s" begin="{k * 0.31:.2f}s"'
            f' repeatCount="indefinite"/>'
            f'{coin_spin(1.5 + (k % 3) * 0.18, k * 0.17, r)}</g></g>')


def qblock(cx, cy, t, T, size=GCELL * QBLOCK_S):
    # A commit square she can headbutt: amber mystery block with a question
    # mark, bumps up on impact, then reads as spent.
    h = size / 2
    bv, bk = _keys(["0,0", "0,0", "0,-15", "0,4", "0,0", "0,0"],
                   [0.0, t, t + 0.12, t + 0.34, t + 0.52, T], T)
    fv, fk = _keys(["#E9A63C", "#E9A63C", "#FFF0B8", "#C98A2C", "#8A5E22",
                    "#8A5E22"],
                   [0.0, t, t + 0.08, t + 0.3, t + 0.62, T], T)
    qv, qk = _keys(["1", "1", "0", "0"], [0.0, t, t + 0.16, T], T)
    rivets = "".join(
        f'<rect x="{dx * h * 0.62 - 2.2:.1f}" y="{dy * h * 0.62 - 2.2:.1f}"'
        f' width="4.4" height="4.4" rx="1.2" fill="#7A4E16"'
        f' fill-opacity="0.75"/>'
        for dx in (-1, 1) for dy in (-1, 1))
    return (f'<g transform="translate({cx:.1f} {cy:.1f})"><g>'
            f'<animateTransform attributeName="transform" type="translate"'
            f' dur="{T}s" repeatCount="indefinite" values="{bv}"'
            f' keyTimes="{bk}"/>'
            f'<rect x="{-h:.1f}" y="{-h:.1f}" width="{size:.1f}"'
            f' height="{size:.1f}" rx="5" fill="#E9A63C" stroke="#7A4E16"'
            f' stroke-width="2.2"><animate attributeName="fill" dur="{T}s"'
            f' repeatCount="indefinite" values="{fv}" keyTimes="{fk}"/></rect>'
            f'<rect x="{-h + 3.4:.1f}" y="{-h + 3.4:.1f}"'
            f' width="{size - 6.8:.1f}" height="{size - 6.8:.1f}" rx="3"'
            f' fill="none" stroke="#FFE9A8" stroke-opacity="0.45"/>{rivets}'
            f'<text class="rmono" x="0" y="{size * 0.23:.1f}"'
            f' text-anchor="middle" font-size="{size * 0.66:.1f}"'
            f' font-weight="700" fill="#FFF8DC"><animate'
            f' attributeName="opacity" dur="{T}s" repeatCount="indefinite"'
            f' values="{qv}" keyTimes="{qk}"/>?</text></g></g>')


# ---------------------------------------------------------------- her run
# How the jump window is shared out. She rises through the four jump frames,
# strikes the block at the top over the three hit frames, and comes down through
# the three landing frames; the run cycle takes over again the moment she lands.
JUMP_W = [3.0, 3.0, 3.0, 3.0] + [1.3, 1.3, 1.3] + [2.7, 2.7, 2.7]

# The sheet's eight run frames are not in gait order: taken as drawn, the foot
# carrying her weight goes rear, front, front, rear, rear, rear, rear, front,
# so she never reads as taking alternate steps. Measured off the sprites, the
# frames sort into two clean steps - one on each foot - either side of the one
# frame where both shoes overlap under her, which is the passing pose:
#   front foot down: 8 (widest), 2, 3 (closing) -> 7 (passing)
#   rear  foot down: 4 (widest), 6, 5 (closing) -> 7 (passing)
RUN_ORDER = (7, 1, 2, 6, 3, 5, 4, 6)
RUN_BOB = 7.0                        # she is 128 tall; a run lifts about 5%


def girl_runner(jump_windows, T, baseline=6.0):
    """Her whole flipbook: an eight-frame run that alternates legs properly,
    with the jump, block hit and landing frames played over the top of it
    for each square she knocks open."""
    # Two squares can sit close enough that one jump has not finished before the
    # next begins; the first then gives way rather than drawing a second of her.
    wins = []
    for t0, t1 in sorted(jump_windows):
        if wins and t0 < wins[-1][1]:
            wins[-1] = (wins[-1][0], t0)
        wins.append((t0, t1))
    run = bob(flipbook(sheet_row("run", GIRL_S, dy=baseline, only=RUN_ORDER),
                       RUN_CYCLE), RUN_CYCLE / 2.0, RUN_BOB)
    air = ""
    for t0, t1 in wins:
        air += sequence(sheet_row("jump", GIRL_S, dy=baseline)
                        + sheet_row("hit", GIRL_S, dy=baseline)
                        + sheet_row("land", GIRL_S, dy=baseline),
                        t0, t1, T, weights=JUMP_W)
    return gate(run, wins, T) + air


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
