#!/usr/bin/env python3
"""Builds the profile panels - stats, featured projects, and the contribution runner."""
import io
import json
import math
import os
import re
import random
import urllib.request
from datetime import datetime, timezone

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
    langs, repo_langs, repo_bytes = {}, {}, {}
    for r in own:
        try:
            got = api(r["languages_url"])
            repo_langs[r["name"]] = sorted(got, key=lambda k: -got[k])
            repo_bytes[r["name"]] = got
            for lang, b in got.items():
                langs[lang] = langs.get(lang, 0) + b
        except Exception:
            pass
    deployed = [r for r in own if (r.get("homepage") or "").strip()]
    # Everything a project card shows, so the panel ages with the repos.
    index = {r["name"]: {"homepage": r.get("homepage"),
                         "langs": [l.lower() for l in (repo_langs.get(r["name"]) or [])],
                         "bytes": repo_bytes.get(r["name"], {}),
                         "stars": r.get("stargazers_count", 0),
                         "pushed": r.get("pushed_at", "")}
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
        "active_days": sum(1 for d in days if d["contributionCount"] > 0),
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
    # Only numbers that say something: zero stars, a handful of public repos
    # (most game repos are private) and live-build counts undersold the work.
    lines = [
        ("clock", "Commits This Year", g.get("commits", "-")),
        ("live", "Active Days", g.get("active_days", "-")),
        ("star", "Games Shipped", "30+"),
        ("box", "Grades Covered", "KG to Class 9"),
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




# Her pick, newest work first.  The order is hers, not the API's - pushed_at
# would put calm-or-react above real-or-fake-sender and Portfolio above
# Competition Zone, and neither is how she ranks them.
FEATURED = [
    ("fln-animation-toolkit", "FLN Animation Kit", "TOOLKIT",
     "7 drop-in animations"),
    ("aaru_ki_cheenk", "Aaru Ki Cheenk", "STORY GAME",
     "one choice at a time"),
    ("Keyword-class9", "Tactic Decoder", "CLASS 9 / CYBER",
     "name the tactic used"),
    ("feeling-wheel-tap", "Feeling Wheel Tap", "SEL",
     "notice and name it"),
    ("think-ask-act", "Think Ask Act", "CYBER SAFETY",
     "think, ask, then act"),
    ("real-or-fake-sender", "Real or Fake Sender", "CYBER SAFETY",
     "check who is really writing"),
    ("calm-or-react", "Calm or React", "CYBER SAFETY",
     "the emotion behind it"),
    ("Competition-Zone", "Competition Zone", "PROTOTYPE",
     "entries, results, trophies"),
    ("Portfolio", "Portfolio", "SITE",
     "the rest of the work"),
]

# GitHub's own linguist colours, so the dots and the ring mean the same thing
# here as they do on the repo pages.
LANG_HUE = {
    "html": "#E34C26", "css": "#563D7C", "javascript": "#F1E05A",
    "typescript": "#3178C6", "python": "#3572A5", "shell": "#89E051",
    "scss": "#C6538C", "java": "#B07219", "c++": "#F34B7D",
    "dart": "#00B4AB", "cmake": "#DA3434", "vue": "#41B883",
}
LANG_REST = "#2A4A46"                    # everything past the top three
TILE_TINT = ["#14544A", "#1A4A63", "#39356A", "#57384C", "#1F5240",
             "#16405F", "#48386B", "#26564E", "#563B3B"]


def _ago(iso, now=None):
    """'10d ago' / '4mo ago', the way GitHub writes it on a repo card."""
    if not iso:
        return ""
    t = datetime.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    days = ((now or datetime.now(timezone.utc)) - t).days
    if days < 1:
        return "updated today"
    if days < 30:
        return f"updated {days}d ago"
    if days < 365:
        return f"updated {days // 30}mo ago"
    return f"updated {days // 365}y ago"


def _pill(x, y, text):
    """One outlined tech chip.  Returns the markup and how wide it came out.

    Trimmed from 10.5px to 9.5 with less padding, because at the old size
    javascript + css + python came to 190px against the 178 the ring leaves,
    and the third chip was being dropped on the cards with the longest
    language names - the ones that most needed all three.
    """
    w = 10.0 + len(text) * 6.0
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="17" rx="8.5"'
            f' fill="#0A1F1C" stroke="#22D3EE" stroke-opacity=".34"/>'
            f'<text class="mono" x="{x + w / 2:.1f}" y="{y + 12.1:.1f}" font-size="9.5"'
            f' text-anchor="middle" fill="#7FD8EE">{esc(text)}</text>'), w


def _donut(cx, cy, r, slices, delay):
    """The language ring: one arc per language, drawn in on load, and silent.

    No names and no percentages.  The ring is the proportion and nothing
    else - it was tried both ways, cycling the names through the middle and
    then as a hoverable bar under the card, and neither earned its space.

    stroke-dasharray places each arc and stroke-dashoffset walks it round, so
    the whole ring is one circle element per slice and no path maths.
    """
    circ = 2 * math.pi * r
    out = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#0C221E"'
           f' stroke-width="{RING_W}"/>']
    off = 0.0
    for sl in slices:
        frac, col = sl[0], sl[1]
        arc = max(circ * frac - (RING_GAP if len(slices) > 1 else 0), 0.6)
        # The name and the share ride along as data- attributes.  They do
        # nothing in the README, where this is a flat <img>, but the live page
        # inlines the same file and reads them off each arc.
        tag = (f' class="arc" data-lang="{esc(sl[2])}" data-pct="{100.0 * frac:.0f}"'
               if len(sl) > 2 else ' data-rest="1"')
        out.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}"'
            f' stroke-width="{RING_W}"{tag}'
            f' stroke-dasharray="{arc:.2f} {circ - arc:.2f}" stroke-dashoffset="{-off:.2f}"'
            f' transform="rotate(-90 {cx} {cy})">'
            f'<animate attributeName="stroke-dasharray" values="0 {circ:.2f};{arc:.2f} {circ - arc:.2f}"'
            f' dur="0.9s" begin="{delay:.2f}s" fill="freeze" calcMode="spline"'
            f' keyTimes="0;1" keySplines=".4 0 .2 1"/></circle>')
        off += circ * frac
    if slices and len(slices[0]) > 2:
        pct, col, name = 100.0 * slices[0][0], slices[0][1], slices[0][2]
        out.append(
            f'<text class="mono" x="{cx}" y="{cy + 2}" font-size="11.5" font-weight="700"'
            f' text-anchor="middle" fill="#E8FFF6">{pct:.0f}%</text>'
            f'<text class="mono" x="{cx}" y="{cy + 12}" font-size="6.5" letter-spacing=".6"'
            f' text-anchor="middle" fill="#9FC4BC">{esc({'javascript': 'JS', 'typescript': 'TS'}.get(name.lower(), name.upper()[:6]))}</text>')
    return "".join(out)


# The fallback mark, for a project with no artwork of its own.  Built on a
# 24x24 grid, monoline at 1.9, so it sits at one weight whatever it is scaled
# to - which is now most of a 260x188 panel, where it looks thin next to a
# real screenshot.  Only Portfolio still lands here.
def _ic(body, stroke="#CFF3FF", fill="none"):
    return (f'<g fill="{fill}" stroke="{stroke}" stroke-width="1.9"'
            f' stroke-linecap="round" stroke-linejoin="round">{body}</g>')


def _icon_frames():
    """Three onion-skinned frames: a flipbook, which is what the kit makes."""
    return _ic('<rect x="2.5" y="6.5" width="12" height="12" rx="2.6" opacity=".38"/>'
               '<rect x="6" y="4.5" width="12" height="12" rx="2.6" opacity=".66"/>'
               '<rect x="9.5" y="2.5" width="12" height="12" rx="2.6"/>'
               '<path d="M14 8.5v3.6l3-1.8z" fill="#7FE9C4" stroke="none"/>', "#7FE9C4")


def _icon_book():
    """An open book: the story runs one page, one choice, at a time."""
    return _ic('<path d="M12 6.4C10.2 4.7 7.6 4.2 4 4.6v13c3.6-.4 6.2.1 8 1.8"/>'
               '<path d="M12 6.4c1.8-1.7 4.4-2.2 8-1.8v13c-3.6-.4-6.2.1-8 1.8z"/>'
               '<path d="M12 6.4v13"/>', "#F2C98A")


def _icon_hook():
    """A message on a hook - the bait the game teaches them to spot."""
    return _ic('<path d="M3.5 5.5h11a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2H8l-3.5 3v-3H3.5a2 2 0'
               ' 0 1-2-2v-5a2 2 0 0 1 2-2z" transform="translate(1.2 1)"/>'
               '<path d="M20 3.2v7.4a3 3 0 0 1-6 0" stroke="#FF9A6C"/>'
               '<circle cx="20" cy="2.6" r="1.1" fill="#FF9A6C" stroke="none"/>', "#FFC65C")


def _icon_wheel():
    """The feeling wheel itself, quartered the way the app colours it."""
    return ('<g stroke="none">'
            '<path d="M12 12 12 2a10 10 0 0 1 10 10z" fill="#FFC65C" opacity=".92"/>'
            '<path d="M12 12h10a10 10 0 0 1-10 10z" fill="#7FE9C4" opacity=".92"/>'
            '<path d="M12 12v10A10 10 0 0 1 2 12z" fill="#8FB8FF" opacity=".92"/>'
            '<path d="M12 12H2A10 10 0 0 1 12 2z" fill="#FF9AAE" opacity=".92"/>'
            '<circle cx="12" cy="12" r="3.4" fill="#06140F"/>'
            '<circle cx="12" cy="12" r="1.5" fill="#EAF6FF"/></g>')


def _icon_flow():
    """Three beats in order: think, ask, act."""
    return _ic('<circle cx="4" cy="12" r="2.6"/><circle cx="12" cy="12" r="2.6"/>'
               '<circle cx="20" cy="12" r="2.6"/>'
               '<path d="M6.8 12h2.4M14.8 12h2.4"/>'
               '<path d="M12 9.4V5.2" opacity=".55"/>'
               '<path d="M20 14.6v4.2" opacity=".55"/>', "#6FD8F0")


def _icon_sender():
    """An envelope that will not say who sent it."""
    return _ic('<rect x="2" y="5" width="20" height="14" rx="2.6"/>'
               '<path d="M2.8 6.6 12 13.2l9.2-6.6"/>'
               '<circle cx="19" cy="17.4" r="4.1" fill="#06140F" stroke="#06140F"/>'
               '<circle cx="19" cy="17.4" r="3.4" stroke="#FFD166"/>'
               '<path d="M17.9 16.3a1.15 1.15 0 1 1 1.35 1.75v.5" stroke="#FFD166"'
               ' stroke-width="1.35"/>'
               '<circle cx="19.2" cy="19.4" r=".5" fill="#FFD166" stroke="none"/>', "#B9A7FA")


def _icon_pulse():
    """Flat, then the spike - calm on the left, reacting on the right."""
    return _ic('<path d="M1.6 12h5.6l2-4.6 2.6 9.6 2.2-6.2 1.7 3.2h4.7"/>'
               '<circle cx="7.2" cy="12" r="1.35" fill="#FF8A8A" stroke="none" opacity=".9"/>',
               "#FF8A8A")


def _icon_trophy():
    """A cup: entries, results, and the room they end up in."""
    return _ic('<path d="M7 3.5h10v5.2a5 5 0 0 1-10 0z"/>'
               '<path d="M7 5h-3a3 3 0 0 0 3 3M17 5h3a3 3 0 0 1-3 3"/>'
               '<path d="M12 13.7v3.1M8.6 20.5h6.8l-.7-3.7H9.3z"/>', "#F5C451")


def _icon_window():
    """A browser with the work laid out in it."""
    return _ic('<rect x="2" y="4" width="20" height="16" rx="2.4"/>'
               '<path d="M2 8.4h20"/>'
               '<circle cx="5" cy="6.2" r=".7" fill="#CFE9F5" stroke="none"/>'
               '<circle cx="7.4" cy="6.2" r=".7" fill="#CFE9F5" stroke="none"/>'
               '<rect x="5" y="11" width="6" height="6" rx="1.2" opacity=".55"/>'
               '<rect x="13" y="11" width="6" height="6" rx="1.2" opacity=".55"/>', "#CFE9F5")


ICONS = {
    "fln-animation-toolkit": _icon_frames,
    "aaru_ki_cheenk": _icon_book,
    "Keyword-class9": _icon_hook,
    "feeling-wheel-tap": _icon_wheel,
    "think-ask-act": _icon_flow,
    "real-or-fake-sender": _icon_sender,
    "calm-or-react": _icon_pulse,
    "Competition-Zone": _icon_trophy,
    "Portfolio": _icon_window,
}


# A project with real artwork of its own uses it instead of a drawn mark.  The
# file is a square crop kept in assets/ rather than fetched at build time: CI
# would otherwise depend on the game still being deployed, and a 404 there
# should not be able to empty a tile here.
# A project whose whole subject is motion gets a tile that moves, and it has
# to move the way the toolkit does - the first two passes invented a drift
# and neither matched.
# The sky is the toolkit's own, read out of its index.html rather than guessed:
#   linear-gradient(180deg,#5cc0f7 0%,#8fd6fb 55%,#c4e9fd 100%)
#
# So is the motion, which the first two attempts got wrong.  Its buildSky()
# lays stars on rays out of the centre and sgFly walks each one straight
# outward, linearly, from r0 to r1 - it is a field flying past the viewer, not
# stars bobbing in place.  Each fades up over the first tenth of its trip,
# holds, and fades out over the last sixth, so nothing pops in or out.  Two
# layers at different scales, offset in angle, give it depth.
SKY = (("0", "#5cc0f7"), ("0.55", "#8fd6fb"), ("1", "#c4e9fd"))

# Its own numbers are lanes=16 in two layers, r 40->260, 8-15s, size 5-15px.
# At 46px those become invisible - a 10px star in a 700px panel is half a pixel
# here - so the proportions are rebuilt for the tile: fewer lanes so it is not
# white noise, bigger stars, and a duration matched to the shorter trip rather
# than copied, or it would crawl.
# Its own numbers are lanes=16 in two layers, r 40->260, 8-15s, size 5-15px.
# None of that survives the move to 46px.  Sixteen stars all leaving one point
# in a space this small read as a burst rather than a sky, and they pile up
# near the middle where the rays converge; so there are ten, the rays are
# jittered off the even fan that made it look mechanical, and they start
# further out where there is already room between them.
# Five lanes was a 46px compromise: any more and the stars landed on top of
# each other and the tile read as static noise.  A full panel has room for the
# toolkit's own count, and the trip is long enough that they can run off the
# edge instead of fading out politely short of it - the panel clip catches them.
SKY_LANES = 18
SKY_LAYERS = ((0.0, 1.00), (10.0, 0.68), (20.0, 0.46))   # angle offset, size scale
SKY_JITTER = 6.0                             # degrees, so the fan is not a wheel
SKY_R0, SKY_R1 = 7.0, 124.0                  # panel units; past the corner, then clipped
SKY_DUR = (3.2, 5.6)
SKY_SIZE = (3.0, 7.0)

# The five shapes it cycles, lifted from the sheet's own data-URI sprites.
_S_STAR = ("M32 5.5c1.6 0 3 .9 3.7 2.4l6.1 12.4 13.7 2c1.6.2 3 1.4 3.5 3s.1 3.3-1.1 4.4"
           "l-9.9 9.6 2.3 13.6c.3 1.6-.4 3.3-1.7 4.2s-3.1 1.1-4.6.3L32 51l-12.2 6.4"
           "c-1.5.8-3.2.7-4.6-.3s-2-2.6-1.7-4.2l2.3-13.6-9.9-9.6c-1.2-1.1-1.6-2.9-1.1-4.4"
           "s1.9-2.7 3.5-3l13.7-2 6.1-12.4C29 6.4 30.4 5.5 32 5.5z")
_S_SPARK = ("M32 2c1.6 12.6 15.4 26.4 30 30-14.6 3.6-28.4 17.4-30 30"
            "-1.6-12.6-15.4-26.4-30-30C16.6 28.4 30.4 14.6 32 2z")


def _scene_defs_stars():
    stops = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in SKY)
    return f'<linearGradient id="flnsky" x1="0" y1="0" x2="0" y2="1">{stops}</linearGradient>'


def _sky_shape(kind, s):
    """One of its shapes, centred on the origin at `s` pixels across.

    The toolkit cycles five: filled star, outlined star, sparkle, ring, dot.
    Only three are kept here.  Its outline star is a 4.5 stroke in a 64 unit
    box, which at six pixels across comes to a third of a pixel, and the ring
    is no better - both arrive as grey smudge rather than as a shape, and they
    are most of what made the tile look messy.
    """
    k = s / 64.0
    if kind == 0:
        return (f'<path d="{_S_STAR}" fill="#FFFFFF"'
                f' transform="translate({-s / 2:.2f} {-s / 2:.2f}) scale({k:.4f})"/>')
    if kind == 1:
        return (f'<path d="{_S_SPARK}" fill="#FFFFFF"'
                f' transform="translate({-s / 2:.2f} {-s / 2:.2f}) scale({k:.4f})"/>')
    return f'<circle r="{s / 2.6:.2f}" fill="#FFFFFF" fill-opacity=".92"/>'


def _scene_stars(x, y):
    """The toolkit's start screen: a starfield flying out of the middle."""
    rnd = random.Random(20260921)                     # same sky on every build
    cx, cy = x + ART_W / 2, y + CH / 2
    r0, r1 = SKY_R0, SKY_R1
    out = [f'<rect x="{x}" y="{y}" width="{ART_W}" height="{CH}" fill="url(#flnsky)"/>']
    for li, (rot, scale) in enumerate(SKY_LAYERS):
        for i in range(SKY_LANES):
            a = math.radians(360.0 / SKY_LANES * i + rot
                             + rnd.uniform(-SKY_JITTER, SKY_JITTER))
            ca, sa = math.cos(a), math.sin(a)
            size = (SKY_SIZE[0] + rnd.random() * (SKY_SIZE[1] - SKY_SIZE[0])) * scale
            dur = SKY_DUR[0] + rnd.random() * (SKY_DUR[1] - SKY_DUR[0])
            o = 0.65 + rnd.random() * 0.30
            x1, y1 = cx + r0 * ca, cy + r0 * sa
            x2, y2 = cx + r1 * ca, cy + r1 * sa
            out.append(
                f'<g opacity="0">'
                f'<animate attributeName="opacity" values="0;{o:.2f};{o:.2f};0"'
                f' keyTimes="0;0.06;0.80;1" dur="{dur:.2f}s"'
                f' begin="-{rnd.random() * dur:.2f}s" repeatCount="indefinite"/>'
                f'<animateTransform attributeName="transform" type="translate"'
                f' values="{x1:.1f} {y1:.1f};{x2:.1f} {y2:.1f}" dur="{dur:.2f}s"'
                f' begin="-{rnd.random() * dur:.2f}s" repeatCount="indefinite"'
                f' calcMode="linear"/>'
                f'{_sky_shape((i + li) % 3, size)}</g>')
    return "".join(out)


# Think Ask Act's bee is shipped as three registered layers - body and two
# wings on the same 260px canvas - which is the game saying the wings move.
# Keeping them separate here keeps that: the wings beat about the point each
# one joins the body, and the whole bee rides a slow hover under it.
BEE_PARTS = ("proj-bee-body.png", "proj-bee-wing-l.png", "proj-bee-wing-r.png")
BEE_ROOT_L = (14.0, 44.0)         # where each wing meets the body, in the
BEE_ROOT_R = (59.0, 52.0)         # 80px space the parts were saved at
BEE_BEAT = 0.34                   # seconds for one full up-and-down beat


def _scene_defs_bee():
    return ""


def _scene_bee(x, y):
    """The bee off the envelope, wings beating."""
    body, wl, wr = (_photo_uri(n) for n in BEE_PARTS)
    if not body:
        return ""
    k = (CH * 0.62) / 80.0                # the parts are 80px square
    ox, oy = x + (ART_W - 80 * k) / 2.0, y + (CH - 80 * k) / 2.0
    wing = ('<g><animateTransform attributeName="transform" type="rotate"'
            ' values="{a} {rx} {ry};{b} {rx} {ry};{a} {rx} {ry}" dur="%s s"'
            ' repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1"'
            ' keySplines=".4 0 .6 1;.4 0 .6 1"/>'
            '<image xlink:href="{u}" x="0" y="0" width="80" height="80"/></g>'
            % BEE_BEAT).replace(" s", "s")
    return (f'<rect x="{x}" y="{y}" width="{ART_W}" height="{CH}" fill="#F0A92B"/>'
            f'<circle cx="{x + ART_W / 2}" cy="{y + CH / 2}" r="{CH * 0.33:.1f}"'
            f' fill="#54309B"/>'
            f'<g transform="translate({ox:.2f} {oy:.2f}) scale({k:.4f})">'
            f'<g><animateTransform attributeName="transform" type="translate"'
            f' values="0 0;0 -5.6;0 0" dur="2.1s" repeatCount="indefinite"'
            f' calcMode="spline" keyTimes="0;0.5;1"'
            f' keySplines=".45 0 .55 1;.45 0 .55 1"/>'
            + wing.format(a=-13, b=12, rx=BEE_ROOT_L[0], ry=BEE_ROOT_L[1], u=wl)
            + wing.format(a=13, b=-12, rx=BEE_ROOT_R[0], ry=BEE_ROOT_R[1], u=wr)
            + f'<image xlink:href="{body}" x="0" y="0" width="80" height="80"/>'
            f'</g></g>')




# Aaru Ki Cheenk's card is its own title screen, rebuilt from the game's
# layers so it moves the way the game does: the painted sky sways, Aaru bobs
# on his bike, the title wobbles, the play button beats with a ring pulsing
# out of it, the hand taps, and a few dust motes rise. The keyframes are the
# game's own (artSway, heroIdle, titleIdle, startBeat, startPulse, handTap,
# moteRise). Layer positions are in the game's stage pixels; the card shows a
# 3:2 window of that stage, with the title group moved in a little so it fits.
AARU_WIN = (66.4, 7.2, 625.0, 415.0)         # x, y, w, h of the window on the stage
AARU_LAYERS = {                              # file, stage x, stage y
    "bg":    ("proj-aaru-bg.jpg", 7.9, 7.2),
    "hero":  ("proj-aaru-hero.png", 64.9, 15.2),
    "title": ("proj-aaru-title.png", 369.9, 50.2),
    "btn":   ("proj-aaru-btn.png", 478.9, 295.2),
    "hand":  ("proj-aaru-hand.png", 517.9, 379.2),
}
_EASE = ".42 0 .58 1"                         # CSS ease-in-out


def _asset_layer(name):
    """(data uri, width, height) of an asset, or None."""
    try:
        import base64
        from PIL import Image
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", name)
        with Image.open(path) as im:
            w, h = im.size
        mime = "image/jpeg" if name.endswith(".jpg") else "image/png"
        with open(path, "rb") as fh:
            return f"data:{mime};base64," + base64.b64encode(fh.read()).decode(), w, h
    except Exception as exc:
        print("aaru layer skipped:", name, exc)
        return None


def _sway(values, dur, cx, cy, kind):
    """An alternate ease-in-out loop (CSS 'infinite alternate') about a centre."""
    v = ";".join(values + values[-2::-1])
    k = ";".join(f"{i / (2 * (len(values) - 1)):.4f}" for i in range(2 * len(values) - 1))
    splines = ";".join([_EASE] * (2 * len(values) - 2))
    anim = (f'<animateTransform attributeName="transform" type="{kind}" values="{v}"'
            f' keyTimes="{k}" dur="{2 * dur}s" repeatCount="indefinite" calcMode="spline"'
            f' keySplines="{splines}"/>')
    if kind == "scale":
        return (f'<g transform="translate({cx:.2f} {cy:.2f})"><g>{anim}'
                f'<g transform="translate({-cx:.2f} {-cy:.2f})">', '</g></g></g>')
    return f'<g>{anim}', '</g>'


def _scene_defs_aaru():
    return ""


def _scene_aaru(x, y):
    got = {k: _asset_layer(f) for k, (f, _, _) in AARU_LAYERS.items()}
    if not all(got.values()):
        uri = _photo_uri("proj-art-aaru.png")
        return (f'<image xlink:href="{uri}" x="{x}" y="{y}" width="{ART_W}" height="{CH}"'
                f' preserveAspectRatio="xMidYMid slice"/>') if uri else ""
    wx, wy, ww, wh = AARU_WIN
    k = CH / wh
    ox = x + (ART_W - ww * k) / 2.0           # centre the window if the shapes differ

    def place(key):
        uri, w, h = got[key]
        _, sx, sy = AARU_LAYERS[key]
        px, py = ox + (sx - wx) * k, y + (sy - wy) * k
        return uri, px, py, w * k, h * k

    out = []
    # the sky: artSway, 14 s each way, about its centre
    uri, px, py, w, h = place("bg")
    cx, cy = px + w / 2, py + h / 2
    t0, t1 = _sway(["0 0", f"{4 * k:.2f} {-4 * k:.2f}"], 14, cx, cy, "translate")
    r0, r1 = _sway([f"-0.22 {cx:.1f} {cy:.1f}", f"0.22 {cx:.1f} {cy:.1f}"], 14, cx, cy, "rotate")
    s0, s1 = _sway(["1.02", "1.035"], 14, cx, cy, "scale")
    out.append(t0 + r0 + s0 + f'<image xlink:href="{uri}" x="{px:.2f}" y="{py:.2f}"'
               f' width="{w:.2f}" height="{h:.2f}" preserveAspectRatio="none"/>' + s1 + r1 + t1)
    # dust motes rising from the road (moteRise)
    rnd = random.Random(5)
    for i in range(5):
        mx = x + ART_W * (0.08 + 0.18 * i + rnd.uniform(-0.03, 0.03))
        my = y + CH * rnd.uniform(0.72, 0.92)
        dur = rnd.choice([15.6, 17.6, 13.8, 16.4, 14.6])
        dx = rnd.uniform(-10, 10)
        out.append(f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="{rnd.uniform(1.1, 2.0):.1f}" fill="#FFF3D6"'
                   f' opacity="0"><animate attributeName="opacity" values="0;.8;.45;0"'
                   f' keyTimes="0;.25;.7;1" dur="{dur}s" begin="{-rnd.uniform(0, dur):.1f}s"'
                   f' repeatCount="indefinite"/><animateTransform attributeName="transform"'
                   f' type="translate" values="0 0;{dx:.1f} {-CH * 0.42:.1f}" dur="{dur}s"'
                   f' begin="{-rnd.uniform(0, dur):.1f}s" repeatCount="indefinite"/></circle>')
    # Aaru: heroIdle, 4.6 s each way
    uri, px, py, w, h = place("hero")
    cx, cy = px + w / 2, py + h / 2
    t0, t1 = _sway(["0 0", f"{-0.0035 * w:.2f} {-0.007 * h:.2f}"], 4.6, cx, cy, "translate")
    r0, r1 = _sway([f"0 {cx:.1f} {cy:.1f}", f"-0.35 {cx:.1f} {cy:.1f}"], 4.6, cx, cy, "rotate")
    out.append(t0 + r0 + f'<image xlink:href="{uri}" x="{px:.2f}" y="{py:.2f}" width="{w:.2f}"'
               f' height="{h:.2f}"/>' + r1 + t1)
    # the title: titleIdle, 6.2 s each way
    uri, px, py, w, h = place("title")
    cx, cy = px + w / 2, py + h / 2
    t0, t1 = _sway(["0 0", f"0 {-0.014 * h:.2f}"], 6.2, cx, cy, "translate")
    r0, r1 = _sway([f"0 {cx:.1f} {cy:.1f}", f"0.5 {cx:.1f} {cy:.1f}"], 6.2, cx, cy, "rotate")
    s0, s1 = _sway(["1", "1.014"], 6.2, cx, cy, "scale")
    out.append(t0 + r0 + s0 + f'<image xlink:href="{uri}" x="{px:.2f}" y="{py:.2f}"'
               f' width="{w:.2f}" height="{h:.2f}"/>' + s1 + r1 + t1)
    # the play button: startBeat, with the startPulse ring, 2.4 s
    uri, px, py, w, h = place("btn")
    cx, cy = px + w / 2, py + h / 2
    ring = (f'<g transform="translate({cx:.2f} {cy:.2f})"><g>'
            f'<animateTransform attributeName="transform" type="scale" values="1;1.55;1.55"'
            f' keyTimes="0;.7;1" dur="2.4s" repeatCount="indefinite" calcMode="spline"'
            f' keySplines="0 0 .58 1;0 0 1 1"/>'
            f'<ellipse rx="{w * 0.44:.2f}" ry="{h * 0.42:.2f}" fill="none" stroke="#784E1E"'
            f' stroke-opacity=".55" stroke-width="1"><animate attributeName="opacity"'
            f' values=".85;0;0" keyTimes="0;.7;1" dur="2.4s" repeatCount="indefinite"/>'
            f'</ellipse></g></g>')
    beat = (f'<g transform="translate({cx:.2f} {cy:.2f})"><g>'
            f'<animateTransform attributeName="transform" type="scale"'
            f' values="1;1.055;0.996;1.01;1;1" keyTimes="0;.14;.32;.48;.64;1" dur="2.4s"'
            f' repeatCount="indefinite" calcMode="spline"'
            f' keySplines="{_EASE};{_EASE};{_EASE};{_EASE};0 0 1 1"/>'
            f'<image xlink:href="{uri}" x="{-w / 2:.2f}" y="{-h / 2:.2f}" width="{w:.2f}"'
            f' height="{h:.2f}"/></g></g>')
    out.append(ring + beat)
    # the tapping hand (handTap): two taps, then rest, rotated -9 degrees
    uri, px, py, w, h = place("hand")
    cx, cy = px + w / 2, py + h / 2
    ys = [0.06, -0.15, 0.06, -0.11, 0.06, 0.06]
    out.append(f'<g><animateTransform attributeName="transform" type="translate"'
               f' values="{";".join(f"0 {v * h:.2f}" for v in ys)}" keyTimes="0;.09;.2;.29;.4;1"'
               f' dur="2.4s" repeatCount="indefinite" calcMode="spline"'
               f' keySplines="{";".join([_EASE] * 5)}"/>'
               f'<g transform="rotate(-9 {cx:.1f} {cy:.1f})"><image xlink:href="{uri}" x="{px:.2f}"'
               f' y="{py:.2f}" width="{w:.2f}" height="{h:.2f}"/></g></g>')
    return f'<rect x="{x}" y="{y}" width="{ART_W}" height="{CH}" fill="#E9D8B4"/>' + "".join(out)


# Keywords (Class 9) - a short trailer of its two cyber moments, no text
# panels: a scanner torch sweeps the cards, each card glowing in its own neon
# as the clues hidden in it light up (the game shows these under a 96px
# spotlight), then the Phishing card powers on - it flips over to its fully
# decoded face, pulses, and flips back. Coordinates are the game's screen
# pixels; the card shows a 3:2 window on the first three cards.
KW_WIN = (252.0, 128.0, 535.0, 357.0)
KW_T = 9.0
KW_CARDS = [((259, 142, 158, 337), "#FF3B5C"), ((443, 142, 158, 337), "#FFB020"),
            ((627, 142, 158, 337), "#E040FB")]


def _scene_defs_kw():
    return ""


def _scene_kw(x, y):
    got = {k: _asset_layer(v) for k, v in (("row", "proj-kw-row.jpg"),
                                            ("reveal", "proj-kw-reveal.jpg"))}
    if not all(got.values()):
        uri = _photo_uri("proj-art-tactic.png")
        return (f'<image xlink:href="{uri}" x="{x}" y="{y}" width="{ART_W}" height="{CH}"'
                f' preserveAspectRatio="xMidYMid slice"/>') if uri else ""
    T = KW_T
    wx, wy, ww, wh = KW_WIN
    k = CH / wh
    row_uri, _, _ = got["row"]
    rev_uri, _, _ = got["reveal"]
    # the stored layers are cut from (247, 80) on the screen, 729 x 486
    lx, ly, lw, lh = 247.0, 80.0, 729.0, 486.0

    def kt(*ts):
        return ";".join(f"{t / T:.4f}" for t in ts)

    out = [f'<g transform="translate({x:.2f} {y:.2f}) scale({k:.5f}) translate({-wx} {-wy})">',
           f'<image xlink:href="{row_uri}" x="{lx}" y="{ly}" width="{lw}" height="{lh}"/>']
    # ---- the scanner torch: card 1, card 2, card 3, then away
    pts = [(0.0, 300, 210), (0.3, 300, 210), (1.1, 345, 360), (1.8, 520, 230),
           (2.6, 525, 380), (3.3, 700, 250), (4.0, 690, 390), (4.4, 690, 390), (T, 300, 210)]
    xs = ";".join(str(p[1]) for p in pts)
    ys = ";".join(str(p[2]) for p in pts)
    ks = kt(*[p[0] for p in pts])
    spl = ";".join([".45 0 .55 1"] * (len(pts) - 1))
    move = (f'<animate attributeName="cx" values="{xs}" keyTimes="{ks}" dur="{T}s" repeatCount="indefinite"'
            f' calcMode="spline" keySplines="{spl}"/><animate attributeName="cy" values="{ys}"'
            f' keyTimes="{ks}" dur="{T}s" repeatCount="indefinite" calcMode="spline" keySplines="{spl}"/>')
    torch_on = (f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="{kt(0, 0.1, 0.4, 4.2, 4.6, T)}"'
                f' dur="{T}s" repeatCount="indefinite"/>')
    defs = ('<defs><radialGradient id="kwTorchG"><stop offset="0" stop-color="#fff"/>'
            '<stop offset=".55" stop-color="#fff"/><stop offset=".63" stop-color="#fff" stop-opacity=".5"/>'
            '<stop offset=".72" stop-color="#fff" stop-opacity="0"/></radialGradient>'
            f'<mask id="kwTorch" maskUnits="userSpaceOnUse" x="{lx}" y="{ly}" width="{lw}" height="{lh}">'
            f'<circle r="105" fill="url(#kwTorchG)">{move}</circle></mask>')
    for i, (_, col) in enumerate(KW_CARDS):
        defs += (f'<radialGradient id="kwG{i}"><stop offset="0" stop-color="{col}" stop-opacity=".75"/>'
                 f'<stop offset=".45" stop-color="{col}" stop-opacity=".35"/>'
                 f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>')
        cx0, cy0, cw, ch = KW_CARDS[i][0]
        defs += (f'<clipPath id="kwC{i}"><rect x="{cx0 + 6}" y="{cy0 + 6}" width="{cw - 12}"'
                 f' height="{ch - 12}" rx="14"/></clipPath>')
    out.append(defs + '</defs>')
    # neon glow inside whichever card the torch is over (each in its own colour)
    spans = [(0.3, 1.8), (1.8, 3.3), (3.3, 4.4)]
    glow = ""
    for i, (a, b) in enumerate(spans):
        glow += (f'<g clip-path="url(#kwC{i})"><circle r="170" fill="url(#kwG{i})" opacity="0">{move}'
                 f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="{kt(0, a, a + 0.3, b - 0.1, b + 0.25, T)}"'
                 f' dur="{T}s" repeatCount="indefinite"/></circle></g>')
    out.append(f'<g opacity="0">{torch_on}<image xlink:href="{rev_uri}" x="{lx}" y="{ly}"'
               f' width="{lw}" height="{lh}" mask="url(#kwTorch)"/>'
               f'<g style="mix-blend-mode:screen">{glow}</g></g>')
    # ---- the Phishing card powers on: flips to its fully decoded face, pulses, flips back
    (cx0, cy0, cw, ch), col = KW_CARDS[0]
    mid = cx0 + cw / 2
    f0, f1, f2, f3 = 4.8, 5.15, 7.6, 7.95
    sx = (f'<animateTransform attributeName="transform" type="scale" values="1 1;1 1;0.02 1;1 1;1 1;0.02 1;1 1;1 1"'
          f' keyTimes="{kt(0, f0, f1, f1 + 0.35, f2, f3, f3 + 0.35, T)}" dur="{T}s" repeatCount="indefinite"'
          f' calcMode="spline" keySplines="0 0 1 1;.55 0 1 .45;0 .55 .45 1;0 0 1 1;.55 0 1 .45;0 .55 .45 1;0 0 1 1"/>')
    face_on = (f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="{kt(0, f1, f1 + 0.01, f3, f3 + 0.01, T)}"'
               f' dur="{T}s" repeatCount="indefinite" calcMode="discrete"/>')
    pulse = (f'<animate attributeName="opacity" values=".2;.85;.2" dur="1.1s" repeatCount="indefinite"/>')
    clip = f'<clipPath id="kwFlip"><rect x="{cx0 - 4}" y="{cy0 - 6}" width="{cw + 8}" height="{ch + 12}" rx="16"/></clipPath>'
    out.append(f'<defs>{clip}</defs><g transform="translate({mid} 0)"><g>{sx}<g transform="translate({-mid} 0)">'
               # the card's own face during the flip (the scene behind is hidden by it)
               f'<rect x="{cx0 - 2}" y="{cy0 - 4}" width="{cw + 4}" height="{ch + 8}" fill="#0b0e1c" opacity="0">'
               f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="{kt(0, f0, f0 + 0.01, f3 + 0.35, f3 + 0.36, T)}"'
               f' dur="{T}s" repeatCount="indefinite" calcMode="discrete"/></rect>'
               f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="{kt(0, f0, f0 + 0.01, f3 + 0.35, f3 + 0.36, T)}"'
               f' dur="{T}s" repeatCount="indefinite" calcMode="discrete"/>'
               f'<image xlink:href="{row_uri}" x="{lx}" y="{ly}" width="{lw}" height="{lh}" clip-path="url(#kwFlip)"/></g>'
               f'<g opacity="0">{face_on}<image xlink:href="{rev_uri}" x="{lx}" y="{ly}" width="{lw}" height="{lh}"'
               f' clip-path="url(#kwFlip)"/><g clip-path="url(#kwC0)" style="mix-blend-mode:screen"><circle cx="{mid}" cy="{cy0 + ch * 0.45}" r="190"'
               f' fill="url(#kwG0)">{pulse}</circle></g>'
               f'<rect x="{cx0 + 2}" y="{cy0 + 2}" width="{cw - 4}" height="{ch - 4}" rx="16" fill="none"'
               f' stroke="{col}" stroke-width="3">{pulse}</rect></g>'
               '</g></g></g>')
    out.append('</g>')
    return "".join(out)


# Feeling Wheel - a trailer of the spin: the knob is pressed, the wheel whips
# round four times and coasts to a stop on FEAR, the slice flares red, the
# warning sign bursts out of it with shock rings, and the rainy town flashes.
# Screen pixels from the game; the card shows a 3:2 window around the wheel.
FW_WIN = (432.0, 150.0, 555.0, 370.0)
FW_T = 7.5
FW_C = (713.7, 306.6, 104.0)                  # disc centre and radius
FW_FEAR = 27.0                                # turn that brings FEAR to the top


def _scene_defs_fw():
    return ""


def _scene_fw(x, y):
    names = (("bg", "proj-fw-bg.jpg"), ("stand", "proj-fw-stand.png"),
             ("disc", "proj-fw-disc.jpg"), ("knob", "proj-fw-knob.png"))
    got = {k: _asset_layer(v) for k, v in names}
    if not all(got.values()):
        uri = _photo_uri("proj-art-wheel.png")
        return (f'<image xlink:href="{uri}" x="{x}" y="{y}" width="{ART_W}" height="{CH}"'
                f' preserveAspectRatio="xMidYMid slice"/>') if uri else ""
    T = FW_T
    wx, wy, ww, wh = FW_WIN
    k = CH / wh
    cx, cy, r = FW_C

    def kt(*ts):
        return ";".join(f"{t / T:.4f}" for t in ts)

    def anim(attr, vals, ts, extra=""):
        return (f'<animate attributeName="{attr}" values="{vals}" keyTimes="{kt(*ts)}" dur="{T}s"'
                f' repeatCount="indefinite"{extra}/>')

    def img(key, px, py):
        uri, w, h = got[key]
        return f'<image xlink:href="{uri}" x="{px}" y="{py}" width="{w}" height="{h}"/>'

    s0, s1, land = 0.6, 4.0, 4.0
    out = [f'<g transform="translate({x:.2f} {y:.2f}) scale({k:.5f}) translate({-wx} {-wy})">',
           '<defs><radialGradient id="fwRed"><stop offset="0" stop-color="#FF2A3D" stop-opacity="0"/>'
           '<stop offset=".6" stop-color="#FF2A3D" stop-opacity="0"/>'
           '<stop offset="1" stop-color="#FF0A22" stop-opacity=".75"/></radialGradient>'
           '<radialGradient id="fwHalo"><stop offset="0" stop-color="#FF5A5A" stop-opacity=".9"/>'
           '<stop offset=".5" stop-color="#FF2A3D" stop-opacity=".35"/>'
           '<stop offset="1" stop-color="#FF2A3D" stop-opacity="0"/></radialGradient>'
           f'<clipPath id="fwDiscC"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath></defs>',
           img("bg", wx, wy)]
    # the danger flash over the town
    out.append(f'<rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" fill="url(#fwRed)" opacity="0">'
               + anim("opacity", "0;0;.8;.35;.6;.35;0;0", (0, land, land + 0.15, land + 0.6, land + 1.1,
                                                          land + 2.0, T - 0.4, T)) + '</rect>')
    # everything on the stand shakes for a beat as it lands
    shake = ";".join(["0 0", "0 0", "-4 1", "4 -1", "-3 0", "2 1", "0 0", "0 0"])
    out.append(f'<g><animateTransform attributeName="transform" type="translate" values="{shake}"'
               f' keyTimes="{kt(0, land, land + .06, land + .12, land + .18, land + .24, land + .32, T)}"'
               f' dur="{T}s" repeatCount="indefinite"/>')
    out.append(img("stand", 590, 195))
    # the disc: four turns and a coast, ending where it began (FEAR on top)
    a0, a1 = FW_FEAR, FW_FEAR + 4 * 360
    spin = (f'<animateTransform attributeName="transform" type="rotate"'
            f' values="{a0} {cx} {cy};{a0} {cx} {cy};{a1} {cx} {cy};{a1} {cx} {cy}"'
            f' keyTimes="{kt(0, s0, s1, T)}" dur="{T}s" repeatCount="indefinite" calcMode="spline"'
            f' keySplines="0 0 1 1;.3 .1 .15 1;0 0 1 1"/>')
    duri, dw, dh = got["disc"]
    out.append(f'<g clip-path="url(#fwDiscC)"><g transform="rotate(0)">{spin}'
               f'<image xlink:href="{duri}" x="607" y="200"'
               f' width="{dw}" height="{dh}"/></g>'
               # motion blur: a soft veil over the disc while it is fast
               f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#fff" opacity="0">'
               + anim("opacity", "0;0;.28;.1;0;0", (0, s0, s0 + .4, s0 + 1.6, s1 - .6, T)) + '</circle></g>')
    # FEAR flares: the top slice (72 degrees about straight up) lit red
    import math
    p1 = (cx + r * math.sin(math.radians(-36)), cy - r * math.cos(math.radians(-36)))
    p2 = (cx + r * math.sin(math.radians(36)), cy - r * math.cos(math.radians(36)))
    wedge = f'M{cx} {cy}L{p1[0]:.1f} {p1[1]:.1f}A{r} {r} 0 0 1 {p2[0]:.1f} {p2[1]:.1f}Z'
    out.append(f'<path d="{wedge}" fill="#FF7A88" stroke="#FFE3E6" stroke-width="3" opacity="0"'
               f' style="mix-blend-mode:screen">'
               + anim("opacity", "0;0;.95;.35;.8;.35;.8;0;0",
                      (0, land, land + .1, land + .5, land + .9, land + 1.3, land + 1.7, T - .5, T)) + '</path>')
    out.append('</g>')
    # the knob: pressed to start, then ticking against the pegs as it slows
    kuri, kw, kh = got["knob"]
    kx, ky = 682 + kw / 2, 177 + 4
    ticks = [0, s0 - .25, s0 - .1, s0]
    vals = ["0", "0", "0", "0"]
    t, gap, sgn = s0, 0.07, 1
    while t < s1 - 0.1:
        t += gap
        ticks.append(t)
        vals.append(f"{14 * sgn}")
        sgn = -sgn
        gap *= 1.28
    ticks += [s1, T]
    vals += ["0", "0"]
    rot = ";".join(f"{v} {kx:.1f} {ky}" for v in vals)
    press = (f'<animateTransform attributeName="transform" type="translate"'
             f' values="0 0;0 0;0 6;0 0;0 0" keyTimes="{kt(0, s0 - .3, s0 - .12, s0, T)}" dur="{T}s"'
             f' repeatCount="indefinite"/>')
    out.append(f'<g>{press}<g><animateTransform attributeName="transform" type="rotate" values="{rot}"'
               f' keyTimes="{kt(*ticks)}" dur="{T}s" repeatCount="indefinite"/>{img("knob", 682, 177)}</g></g>')
    # the warning sign bursts up out of the slice, with shock rings
    sx, sy = cx, cy + 6
    for i, d in enumerate((0, .25, .5)):
        out.append(f'<circle cx="{sx}" cy="{sy}" r="20" fill="none" stroke="#FF4757" stroke-width="4" opacity="0">'
                   + anim("r", "30;30;190;190", (0, land + d, land + d + .9, T))
                   + anim("opacity", "0;0;.9;0;0", (0, land + d, land + d + .05, land + d + .9, T))
                   + anim("stroke-width", "6;6;.5;.5", (0, land + d, land + d + .9, T)) + '</circle>')
    pop = (f'<animateTransform attributeName="transform" type="scale" values="0;0;2.1;1.45;1.65;1.55;1.55;0;0"'
           f' keyTimes="{kt(0, land + .1, land + .4, land + .55, land + .7, land + .85, T - .7, T - .45, T)}"'
           f' dur="{T}s" repeatCount="indefinite" calcMode="spline"'
           f' keySplines="0 0 1 1;.2 .8 .3 1;{_EASE};{_EASE};{_EASE};0 0 1 1;.5 0 1 .5;0 0 1 1"/>')
    rise = (f'<animateTransform attributeName="transform" type="translate"'
            f' values="{cx} {cy - 70};{cx} {cy - 70};{sx} {sy};{sx} {sy - 6};{sx} {sy}"'
            f' keyTimes="{kt(0, land + .1, land + .45, land + 1.8, T)}" dur="{T}s" repeatCount="indefinite"'
            f' calcMode="spline" keySplines="0 0 1 1;.2 .8 .3 1;{_EASE};{_EASE}"/>')
    beat = (f'<animate attributeName="opacity" values=".55;1;.55" dur=".9s" repeatCount="indefinite"/>')
    out.append(f'<g>{rise}<g>{pop}'
               f'<circle r="70" fill="url(#fwHalo)">{beat}</circle>'
               '<path d="M0 -40L38 28Q40 34 34 34H-34Q-40 34 -38 28Z" fill="#FF2A3D" stroke="#FFE066"'
               ' stroke-width="5" stroke-linejoin="round"/>'
               '<rect x="-5" y="-17" width="10" height="30" rx="5" fill="#fff"/>'
               '<circle cx="0" cy="23" r="5.5" fill="#fff"/></g></g>')
    out.append('</g>')
    return "".join(out)


# Calm or React - a trailer of the sort: a wet "?" card lifts off the deck,
# spins through the rain and drops into CALM, the bin flares green and its
# rat pops up grinning; the next card dives into REACT, the bin flares red
# and the scammer rat pops up smirking. Screen pixels from the game.
CR_WIN = (257.0, 60.0, 733.0, 489.0)
CR_T = 8.0


def _scene_defs_cr():
    return ""


def _scene_cr(x, y):
    names = (("bg", "proj-cr-bg.jpg"), ("card", "proj-cr-card.png"),
             ("calm", "proj-cr-rat-calm.png"), ("react", "proj-cr-rat-react.png"))
    got = {k: _asset_layer(v) for k, v in names}
    if not all(got.values()):
        uri = _photo_uri("proj-art-calm.png")
        return (f'<image xlink:href="{uri}" x="{x}" y="{y}" width="{ART_W}" height="{CH}"'
                f' preserveAspectRatio="xMidYMid slice"/>') if uri else ""
    T = CR_T
    wx, wy, ww, wh = CR_WIN
    k = CH / wh

    def kt(*ts):
        return ";".join(f"{t / T:.4f}" for t in ts)

    def rep(extra=""):
        return f' dur="{T}s" repeatCount="indefinite"{extra}'

    curi = got["card"][0]
    cw, ch = 98.0, 149.0
    dx, dy = 624.0, 398.0                    # the deck
    out = [f'<g transform="translate({x:.2f} {y:.2f}) scale({k:.5f}) translate({-wx} {-wy})">',
           f'<image xlink:href="{got["bg"][0]}" x="257" y="0" width="733" height="576"/>',
           '<defs>']
    for n, col in (("g", "#3DFF7A"), ("r", "#FF3B4E")):
        out.append(f'<radialGradient id="cr{n}"><stop offset="0" stop-color="{col}" stop-opacity=".95"/>'
                   f'<stop offset=".45" stop-color="{col}" stop-opacity=".4"/>'
                   f'<stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>')
    out.append('<clipPath id="crRatC"><rect x="257" y="250" width="733" height="248"/></clipPath></defs>')
    # the deck underneath: two cards that stay put
    for i, off in enumerate((18, 9)):
        out.append(f'<image xlink:href="{curi}" x="{dx - cw / 2}" y="{dy - ch / 2 + off}" width="{cw}"'
                   f' height="{ch}" opacity=".9"/>')

    # each throw: (start, land, bin centre, colour, rat key, rat x)
    throws = [(0.6, 1.8, (393.0, 458.0), "g", "calm", 297.0),
              (3.9, 5.1, (862.0, 458.0), "r", "react", 853.0)]
    for n, (t0, t1, (bx, by), col, rat, rx) in enumerate(throws):
        # the card: lift, then arc into the bin, flipping and shrinking
        lift = t0 + 0.35
        mx, my = (dx + bx) / 2, 150.0
        path = f'M{dx} {dy}L{dx} {dy - 26}Q{mx} {my} {bx} {by}'
        vis = (f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="{kt(0, t0 - .5, t0 - .2, T - .9, T - .7, T)}"'
               f'{rep()}/>') if n else (
               f'<animate attributeName="opacity" values="1;1;0;0;1" keyTimes="{kt(0, T - .9, T - .7, T - .5, T)}"{rep()}/>')
        mot = (f'<animateMotion path="{path}" keyPoints="0;0;.06;1;1;0;0" keyTimes="{kt(0, t0, lift, t1, T - .69, T - .68, T)}"'
               f' calcMode="spline" keySplines="0 0 1 1;.3 0 .5 1;.5 0 .9 .6;0 0 1 1;0 0 1 1;0 0 1 1"{rep()}/>')
        flip = (f'<animateTransform attributeName="transform" type="scale"'
                f' values="1 1;1 1;1.08 1.08;-.8 .8;.6 .6;-.5 .5;.45 .45;.45 .45;1 1;1 1"'
                f' keyTimes="{kt(0, t0, lift, lift + .3, lift + .55, lift + .75, t1, T - .69, T - .68, T)}"{rep()}/>')
        tilt = (f'<animateTransform attributeName="transform" type="rotate" values="0;0;-6;14;-10;8;0;0"'
                f' keyTimes="{kt(0, t0, t0 + .15, lift + .25, lift + .5, lift + .7, t1, T)}" additive="sum"{rep()}/>')
        out.append(f'<g>{vis}<g>{mot}<g>{flip}{tilt}<image xlink:href="{curi}" x="{-cw / 2}" y="{-ch / 2}"'
                   f' width="{cw}" height="{ch}"/></g></g></g>')
        # the bin flares
        out.append(f'<g style="mix-blend-mode:screen"><ellipse cx="{bx}" cy="{by - 30}" rx="150" ry="130"'
                   f' fill="url(#cr{col})" opacity="0"><animate attributeName="opacity"'
                   f' values="0;0;1;.35;.7;0;0" keyTimes="{kt(0, t1, t1 + .1, t1 + .5, t1 + .8, t1 + 1.8, T)}"{rep()}/>'
                   '</ellipse></g>')
        ring = "#3DFF7A" if col == "g" else "#FF3B4E"
        for i, d in enumerate((0, .2)):
            out.append(f'<ellipse cx="{bx}" cy="{by - 70}" rx="20" ry="8" fill="none" stroke="{ring}"'
                       f' stroke-width="5" opacity="0">'
                       f'<animate attributeName="rx" values="20;20;170;170" keyTimes="{kt(0, t1 + d, t1 + d + .8, T)}"{rep()}/>'
                       f'<animate attributeName="ry" values="8;8;60;60" keyTimes="{kt(0, t1 + d, t1 + d + .8, T)}"{rep()}/>'
                       f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="{kt(0, t1 + d, t1 + d + .05, t1 + d + .8, T)}"{rep()}/>'
                       '</ellipse>')
        # sparks spray up out of the bin
        rnd = random.Random(11 + n)
        for i in range(10):
            ex = bx + rnd.uniform(-95, 95)
            ey = by - rnd.uniform(150, 250)
            s = t1 + rnd.uniform(0, .25)
            out.append(f'<circle r="{rnd.uniform(2.5, 4.5):.1f}" fill="{"#CFFFD9" if col == "g" else "#FFD0D5"}" opacity="0">'
                       f'<animate attributeName="cx" values="{bx};{bx};{ex:.0f};{ex:.0f}" keyTimes="{kt(0, s, s + .9, T)}"'
                       f' calcMode="spline" keySplines="0 0 1 1;.2 .7 .4 1;0 0 1 1"{rep()}/>'
                       f'<animate attributeName="cy" values="{by - 60};{by - 60};{ey:.0f};{ey + 30:.0f};{ey + 30:.0f}" keyTimes="{kt(0, s, s + .7, s + 1.2, T)}"'
                       f' calcMode="spline" keySplines="0 0 1 1;.2 .7 .4 1;.5 0 1 1;0 0 1 1"{rep()}/>'
                       f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="{kt(0, s, s + .05, s + 1.2, T)}"{rep()}/></circle>')
        # the rat pops up out of the bin, bobs, and ducks back down
        ruri = got[rat][0]
        r0 = t1 + .25
        rx = bx - 100
        bob = "0 0;0 0;0 -168;0 -146;0 -156;0 -146;0 -156;0 -146;0 0;0 0"
        out.append(f'<g clip-path="url(#crRatC)"><g><animateTransform attributeName="transform" type="translate"'
                   f' values="{bob}" keyTimes="{kt(0, r0, r0 + .3, r0 + .45, r0 + .7, r0 + .95, r0 + 1.2, r0 + 1.45, r0 + 1.8, T)}"'
                   f' calcMode="spline" keySplines="0 0 1 1;.2 .8 .3 1;{";".join([_EASE] * 5)};.5 0 1 1;0 0 1 1"{rep()}/>'
                   + (f'<animateTransform attributeName="transform" type="rotate" additive="sum"'
                      f' values="0 {rx + 65} 600;0 {rx + 65} 600;-6 {rx + 65} 600;6 {rx + 65} 600;-6 {rx + 65} 600;6 {rx + 65} 600;0 {rx + 65} 600;0 {rx + 65} 600"'
                      f' keyTimes="{kt(0, r0 + .45, r0 + .6, r0 + .8, r0 + 1.0, r0 + 1.2, r0 + 1.4, T)}"{rep()}/>' if rat == "react" else "")
                   + f'<image xlink:href="{ruri}" x="{rx}" y="508" width="130" height="130"/></g></g>')
    out.append('</g>')
    return "".join(out)


# Think Ask Act - a trailer of its finale: confetti over the park, the
# shield badge bursts in, Avi cheers, the crowned bee loops round the sealed
# envelope, the seal pops, the flap swings open and the superpower card
# springs out in a spray of sparks. Window pixels on the game's final board.
TA_T = 8.0


def _scene_defs_ta():
    return ""


def _scene_ta(x, y):
    names = (("bg", "proj-ta-bg.jpg"), ("avi", "proj-ta-avi.png"), ("badge", "proj-ta-badge.png"),
             ("bee", "proj-ta-bee.png"), ("wing", "proj-ta-wing.png"))
    got = {k: _asset_layer(v) for k, v in names}
    if not all(got.values()):
        uri = _photo_uri("proj-art-bee.png")
        return (f'<image xlink:href="{uri}" x="{x}" y="{y}" width="{ART_W}" height="{CH}"'
                f' preserveAspectRatio="xMidYMid slice"/>') if uri else ""
    T = TA_T
    k = CH / 390.0

    def kt(*ts):
        return ";".join(f"{t / T:.4f}" for t in ts)

    def rep(extra=""):
        return f' dur="{T}s" repeatCount="indefinite"{extra}'

    def img(key, px, py, s=1.0, extra=""):
        uri, w, h = got[key]
        return (f'<image xlink:href="{uri}" x="{px}" y="{py}" width="{w * s:.1f}" height="{h * s:.1f}"{extra}/>')

    out = [f'<g transform="translate({x:.2f} {y:.2f}) scale({k:.5f})">', img("bg", 0, 0),
           '<defs><linearGradient id="taEnv" x1="0" y1="0" x2=".5" y2="1"><stop offset="0" stop-color="#FFD76E"/>'
           '<stop offset=".55" stop-color="#F4B73C"/><stop offset="1" stop-color="#E09B1F"/></linearGradient>'
           '<linearGradient id="taFlap" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFE294"/>'
           '<stop offset="1" stop-color="#F7C554"/></linearGradient>'
           '<radialGradient id="taSeal" cx=".38" cy=".3" r=".8"><stop offset="0" stop-color="#8A5CF6"/>'
           '<stop offset=".7" stop-color="#5B2A9C"/></radialGradient>'
           '<radialGradient id="taCard" cx=".5" cy=".38" r=".75"><stop offset="0" stop-color="#FFF8EC"/>'
           '<stop offset=".7" stop-color="#FBE9C6"/><stop offset="1" stop-color="#F3D8A3"/></radialGradient>'
           '<radialGradient id="taGlow"><stop offset="0" stop-color="#FFE9A8" stop-opacity=".9"/>'
           '<stop offset="1" stop-color="#FFE9A8" stop-opacity="0"/></radialGradient></defs>']
    # Avi cheering (guide-bob)
    out.append(f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -5;0 0"'
               f' dur="1.6s" repeatCount="indefinite" calcMode="spline" keySplines="{_EASE};{_EASE}"/>'
               f'{img("avi", 14, 150, 0.9)}</g>')
    # the badge bursts in, with rays, then breathes
    bx, by = 128.0, 74.0
    bw, bh = got["badge"][1] * .55, got["badge"][2] * .55
    rays = "".join(f'<path d="M0 0L{70 * math.cos(math.radians(a - 6)):.1f} {70 * math.sin(math.radians(a - 6)):.1f}'
                   f'L{70 * math.cos(math.radians(a + 6)):.1f} {70 * math.sin(math.radians(a + 6)):.1f}Z"/>'
                   for a in range(0, 360, 30))
    out.append(f'<g transform="translate({bx} {by})"><g fill="#FFF4B0" opacity="0">'
               f'<animate attributeName="opacity" values="0;.55;.25;.25;0" keyTimes="{kt(0, .5, 1.2, T - .6, T)}"{rep()}/>'
               f'<animateTransform attributeName="transform" type="rotate" values="0;360" dur="14s" repeatCount="indefinite"/>'
               f'{rays}</g><g><animateTransform attributeName="transform" type="scale"'
               f' values="0;0;1.25;.95;1;1;1.05;1;0" keyTimes="{kt(0, .1, .45, .6, .75, 4, 4.4, T - .5, T)}"'
               f' calcMode="spline" keySplines="0 0 1 1;.2 .8 .3 1;{_EASE};{_EASE};0 0 1 1;{_EASE};{_EASE};.5 0 1 .5"{rep()}/>'
               f'{img("badge", -bw / 2, -bh / 2, .55)}</g></g>')
    # the envelope, floating (power-float)
    ex, ey, ew, eh = 300.0, 240.0, 190.0, 114.0
    mx = ew / 2
    t_pop, t_flap, t_card, t_close = 2.2, 2.35, 2.6, 6.6
    out.append(f'<g transform="translate({ex} {ey})"><g><animateTransform attributeName="transform" type="translate"'
               f' values="0 0;0 -7;0 0" dur="2.4s" repeatCount="indefinite" calcMode="spline" keySplines="{_EASE};{_EASE}"/>')
    # glow behind once it opens
    out.append(f'<circle cx="{mx}" cy="-10" r="140" fill="url(#taGlow)" opacity="0">'
               f'<animate attributeName="opacity" values="0;0;1;.6;.6;0;0" keyTimes="{kt(0, t_card, t_card + .3, t_card + 1, t_close, t_close + .4, T)}"{rep()}/></circle>')
    out.append(f'<rect width="{ew}" height="{eh}" rx="12" fill="#C9850F"/>')
    # the open flap, behind the card
    out.append(f'<g transform="translate(0 0)"><g><animateTransform attributeName="transform" type="scale"'
               f' values="1 0;1 0;1 -1;1 -1;1 0;1 0" keyTimes="{kt(0, t_flap + .12, t_flap + .35, t_close + .1, t_close + .35, T)}"{rep()}/>'
               f'<path d="M0 0H{ew}L{mx} 78Z" fill="url(#taFlap)" stroke="#E8A93A" stroke-width="1.5"/></g></g>')
    # the card springs out
    cw, ch = 132.0, 150.0
    rise = (f'<animateTransform attributeName="transform" type="translate"'
            f' values="0 0;0 0;0 -150;0 -128;0 -136;0 -136;0 0;0 0"'
            f' keyTimes="{kt(0, t_card, t_card + .4, t_card + .58, t_card + .75, t_close, t_close + .45, T)}"'
            f' calcMode="spline" keySplines="0 0 1 1;.2 .8 .3 1;{_EASE};{_EASE};0 0 1 1;.5 0 .9 .6;0 0 1 1"{rep()}/>')
    tilt = (f'<animateTransform attributeName="transform" type="rotate" additive="sum"'
            f' values="0 {mx} 60;0 {mx} 60;-4 {mx} 60;3 {mx} 60;0 {mx} 60;0 {mx} 60"'
            f' keyTimes="{kt(0, t_card + .3, t_card + .6, t_card + .9, t_card + 1.2, T)}"{rep()}/>')
    shield = (f'<g transform="translate({mx} {28 + ch * .38})">'
              '<path d="M0 -40C14 -30 26 -28 34 -28C34 6 22 28 0 40C-22 28 -34 6 -34 -28C-26 -28 -14 -30 0 -40Z"'
              ' fill="#7B4BE0" stroke="#FFD23F" stroke-width="4"/>'
              '<path d="M-14 0L-4 11L16 -11" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round"'
              ' stroke-linejoin="round"/></g>')
    out.append(f'<clipPath id="taPocket"><rect x="-200" y="-400" width="{ew + 400}" height="{400 + eh - 6}"/></clipPath>'
               f'<g clip-path="url(#taPocket)"><g>{rise}{tilt}<rect x="{mx - cw / 2}" y="20" width="{cw}" height="{ch}" rx="12" fill="url(#taCard)"'
               f' stroke="#fff" stroke-opacity=".6" stroke-width="2"/>{shield}'
               f'<rect x="{mx - 34}" y="{28 + ch * .38 + 56}" width="68" height="7" rx="3.5" fill="#E2C48C"/></g></g>')
    # the front pocket of the envelope
    out.append(f'<path d="M0 26L{mx} 70L{ew} 26V{eh - 12}Q{ew} {eh} {ew - 12} {eh}H12Q0 {eh} 0 {eh - 12}Z"'
               f' fill="url(#taEnv)"/><path d="M0 {eh - 4}L{mx} 62L{ew} {eh - 4}" fill="none" stroke="#D99124"'
               f' stroke-width="1.5" opacity=".7"/>')
    # the closed flap folds up and away
    out.append(f'<g><animateTransform attributeName="transform" type="scale"'
               f' values="1 1;1 1;1 0;1 0;1 1;1 1" keyTimes="{kt(0, t_flap, t_flap + .12, t_close + .35, t_close + .6, T)}"{rep()}/>'
               f'<path d="M0 0H{ew}L{mx} 78Z" fill="url(#taFlap)" stroke="#E8A93A" stroke-width="1.5"/></g>')
    # the seal pulses, then pops
    out.append(f'<g transform="translate({mx} 60)"><g><animateTransform attributeName="transform" type="scale"'
               f' values="1;1.08;1;1.08;1.5;0;0;1;1" keyTimes="{kt(0, .6, 1.2, 1.8, t_pop, t_pop + .15, t_close + .6, t_close + .9, T)}"{rep()}/>'
               f'<animate attributeName="opacity" values="1;1;0;0;1;1" keyTimes="{kt(0, t_pop, t_pop + .15, t_close + .6, t_close + .7, T)}"{rep()}/>'
               '<circle r="26" fill="url(#taSeal)" stroke="#fff" stroke-opacity=".35" stroke-width="2"/>'
               '<path d="M0 -15C6 -11 11 -10 14 -10C14 4 9 12 0 16C-9 12 -14 4 -14 -10C-11 -10 -6 -11 0 -15Z" fill="#53BDEB"/>'
               '</g></g>')
    # the spark burst
    cols = ['#FFD23F', '#FF8E63', '#8A5CF6', '#53BDEB']
    for i in range(14):
        a = i / 14 * 2 * math.pi
        d = 70 + (i % 3) * 30
        px, py = mx + math.cos(a) * d, -40 + math.sin(a) * d * .8
        out.append(f'<circle r="{4 + (i % 2) * 2}" fill="{cols[i % 4]}" opacity="0">'
                   f'<animate attributeName="cx" values="{mx};{mx};{px:.0f};{px:.0f}" keyTimes="{kt(0, t_card + .15, t_card + .85, T)}"'
                   f' calcMode="spline" keySplines="0 0 1 1;.2 .8 .3 1;0 0 1 1"{rep()}/>'
                   f'<animate attributeName="cy" values="20;20;{py:.0f};{py + 20:.0f};{py + 20:.0f}" keyTimes="{kt(0, t_card + .15, t_card + .85, t_card + 1.3, T)}"'
                   f' calcMode="spline" keySplines="0 0 1 1;.2 .8 .3 1;.5 0 1 1;0 0 1 1"{rep()}/>'
                   f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="{kt(0, t_card + .15, t_card + .2, t_card + 1.3, T)}"{rep()}/></circle>')
    out.append('</g></g>')
    # the crowned bee loops round the envelope (bee-orbit), wings flapping
    cxo, cyo = ex + mx, ey + 30
    orbit = (f'M{cxo + 130} {cyo}A130 70 0 1 1 {cxo - 130} {cyo}A130 70 0 1 1 {cxo + 130} {cyo}')
    wuri, ww_, wh_ = got["wing"]
    wing = (f'<g transform="translate(46 30)"><g><animateTransform attributeName="transform" type="scale"'
            f' values="1 1;1 .35;1 1" dur=".16s" repeatCount="indefinite"/>'
            f'<image xlink:href="{wuri}" x="{-ww_ / 2:.1f}" y="{-wh_:.1f}" width="{ww_}" height="{wh_}"/></g></g>')
    bw2, bh2 = got["bee"][1] * .62, got["bee"][2] * .62
    out.append(f'<g><animateMotion path="{orbit}" dur="5.2s" repeatCount="indefinite"/>'
               f'<g transform="translate({-bw2 / 2:.1f} {-bh2 / 2:.1f})"><g transform="scale(.62)">{wing}'
               f'{img("bee", 0, 0)}</g></g></g>')
    # confetti all the way down
    rnd = random.Random(21)
    pal = ['#FF5C8A', '#FFD23F', '#53BDEB', '#7BE07B', '#8A5CF6', '#FF8E63']
    for i in range(18):
        cx_ = rnd.uniform(10, 575)
        dur = rnd.uniform(3.2, 5.2)
        out.append(f'<rect x="-4" y="-7" width="8" height="14" rx="2" fill="{pal[i % 6]}">'
                   f'<animateMotion path="M{cx_:.0f} -20C{cx_ + 30:.0f} 120 {cx_ - 30:.0f} 260 {cx_ + rnd.uniform(-20, 20):.0f} 410"'
                   f' dur="{dur:.1f}s" begin="{-rnd.uniform(0, dur):.1f}s" repeatCount="indefinite" rotate="auto"/></rect>')
    out.append('</g>')
    return "".join(out)


# Real or Fake Sender - a trailer of the catch: messages pop up beside Tej,
# a magnifier sweeps them, glints on the safe ones, flares red on the one
# with the fake link, and a FAKE stamp slams down on it; the safe ones get
# their ticks, then the shield badge bursts in and Tej gives a thumbs up.
RF_T = 8.0


def _scene_defs_rf():
    return ""


def _scene_rf(x, y):
    names = (("bg", "proj-rf-bg.jpg"), ("tej", "proj-rf-tej.png"), ("up", "proj-rf-tej-up.png"),
             ("badge", "proj-rf-badge.png"))
    got = {k: _asset_layer(v) for k, v in names}
    if not all(got.values()):
        uri = _photo_uri("proj-art-shield.png")
        return (f'<image xlink:href="{uri}" x="{x}" y="{y}" width="{ART_W}" height="{CH}"'
                f' preserveAspectRatio="xMidYMid slice"/>') if uri else ""
    T = RF_T
    k = CH / 384.0

    def kt(*ts):
        return ";".join(f"{t / T:.4f}" for t in ts)

    def rep(extra=""):
        return f' dur="{T}s" repeatCount="indefinite"{extra}'

    def img(key, px, py, s=1.0):
        uri, w, h = got[key]
        return f'<image xlink:href="{uri}" x="{px}" y="{py}" width="{w * s:.1f}" height="{h * s:.1f}"/>'

    out = [f'<g transform="translate({x:.2f} {y:.2f}) scale({k:.5f})">', img("bg", 0, 0),
           '<defs><radialGradient id="rfRed"><stop offset="0" stop-color="#FF3B4E" stop-opacity=".85"/>'
           '<stop offset="1" stop-color="#FF3B4E" stop-opacity="0"/></radialGradient>'
           '<radialGradient id="rfSun"><stop offset="0" stop-color="#FFFFFF" stop-opacity=".95"/>'
           '<stop offset=".5" stop-color="#E9F7FF" stop-opacity=".45"/><stop offset="1" stop-color="#E9F7FF" stop-opacity="0"/>'
           '</radialGradient><filter id="rfSh" x="-20%" y="-20%" width="140%" height="160%">'
           '<feDropShadow dx="0" dy="4" stdDeviation="5" flood-color="#4B3A9C" flood-opacity=".3"/></filter></defs>']
    # falling snow
    rnd = random.Random(8)
    for i in range(22):
        sx = rnd.uniform(0, 576)
        dur = rnd.uniform(5, 9)
        out.append(f'<circle r="{rnd.uniform(1.2, 2.8):.1f}" fill="#fff" opacity=".85">'
                   f'<animateMotion path="M{sx:.0f} -10C{sx + 20:.0f} 120 {sx - 20:.0f} 250 {sx + 10:.0f} 395"'
                   f' dur="{dur:.1f}s" begin="{-rnd.uniform(0, dur):.1f}s" repeatCount="indefinite"/></circle>')
    # Tej: presenting, then thumbs up once the catch is made
    t_win = 4.8
    tw, th = got["tej"][1], got["tej"][2]
    uw, uh = got["up"][1], got["up"][2]
    out.append(f'<g opacity="1"><animate attributeName="opacity" values="1;1;0;0;1" keyTimes="{kt(0, t_win, t_win + .2, T - .3, T)}"{rep()}/>'
               f'{img("tej", 4, 384 - th + 8)}</g>'
               f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="{kt(0, t_win, t_win + .2, T - .3, T)}"{rep()}/>'
               f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -6;0 0" dur=".9s"'
               f' repeatCount="indefinite"/>{img("up", 18, 384 - uh + 8)}</g></g>')
    # three messages; the middle one carries the fake link
    bubbles = [(236.0, 56.0, False), (262.0, 146.0, True), (236.0, 236.0, False)]
    BW, BH = 280.0, 72.0
    t_stamp = 3.3
    for i, (bx, by, fake) in enumerate(bubbles):
        t_in = 0.25 + i * 0.35
        lines = (f'<rect x="{bx + 18}" y="{by + 18}" width="{BW - 70}" height="9" rx="4.5" fill="#C9CFE6"/>'
                 f'<rect x="{bx + 18}" y="{by + 34}" width="{BW - 110}" height="9" rx="4.5" fill="#C9CFE6"/>')
        if fake:
            lines += (f'<rect x="{bx + 18}" y="{by + 50}" width="{BW - 150}" height="9" rx="4.5" fill="#3B6FE0">'
                      f'<animate attributeName="fill" values="#3B6FE0;#3B6FE0;#FF2A3D;#FF2A3D;#3B6FE0"'
                      f' keyTimes="{kt(0, 2.75, 2.85, T - .5, T)}"{rep()}/></rect>')
        else:
            lines += f'<rect x="{bx + 18}" y="{by + 50}" width="{BW - 140}" height="9" rx="4.5" fill="#C9CFE6"/>'
        pop = (f'<animateTransform attributeName="transform" type="scale" values="0;0;1.08;1;1;0;0"'
               f' keyTimes="{kt(0, t_in, t_in + .25, t_in + .4, t_win - .3, t_win, T)}" calcMode="spline"'
               f' keySplines="0 0 1 1;.2 .8 .3 1;{_EASE};0 0 1 1;.5 0 1 .5;0 0 1 1"{rep()}/>')
        shake = ""
        if fake:
            sv = "0 0;0 0;-6 0;6 0;-4 0;3 0;0 0;0 0"
            shake = (f'<animateTransform attributeName="transform" type="translate" additive="sum" values="{sv}"'
                     f' keyTimes="{kt(0, t_stamp, t_stamp + .05, t_stamp + .1, t_stamp + .15, t_stamp + .2, t_stamp + .26, T)}"{rep()}/>')
        tint = (f'<rect x="{bx}" y="{by}" width="{BW}" height="{BH}" rx="18" fill="#FF3B4E" opacity="0">'
                f'<animate attributeName="opacity" values="0;0;.22;.22;0" keyTimes="{kt(0, t_stamp, t_stamp + .05, T - .5, T)}"{rep()}/></rect>') if fake else ""
        out.append(f'<g transform="translate({bx} {by + BH / 2})"><g>{pop}{shake}<g transform="translate({-bx} {-by - BH / 2})">'
                   f'<path d="M{bx + 18} {by}H{bx + BW - 18}Q{bx + BW} {by} {bx + BW} {by + 18}V{by + BH - 18}'
                   f'Q{bx + BW} {by + BH} {bx + BW - 18} {by + BH}H{bx + 22}L{bx} {by + BH + 10}L{bx + 6} {by + BH - 14}'
                   f'V{by + 18}Q{bx} {by} {bx + 18} {by}Z" fill="#fff" filter="url(#rfSh)"/>{lines}{tint}')
        if fake:
            # the FAKE stamp slams down
            sx_, sy_ = bx + BW - 74, by + BH / 2
            out.append(f'<g transform="translate({sx_} {sy_}) rotate(-12)"><g opacity="0">'
                       f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="{kt(0, t_stamp - .12, t_stamp - .1, T - .5, T)}"{rep()}/>'
                       f'<animateTransform attributeName="transform" type="scale" values="2.6;2.6;1;1.08;1;1"'
                       f' keyTimes="{kt(0, t_stamp - .12, t_stamp, t_stamp + .1, t_stamp + .2, T)}" calcMode="spline"'
                       f' keySplines="0 0 1 1;.6 0 1 .6;{_EASE};{_EASE};0 0 1 1"{rep()}/>'
                       '<rect x="-56" y="-22" width="112" height="44" rx="8" fill="#fff" fill-opacity=".85"'
                       ' stroke="#E8192C" stroke-width="5"/>'
                       '<rect x="-49" y="-15" width="98" height="30" rx="4" fill="none" stroke="#E8192C" stroke-width="1.5"/>'
                       '<text x="0" y="10" text-anchor="middle" font-family="Arial Black,Impact,Arial,sans-serif"'
                       ' font-weight="900" font-size="28" letter-spacing="3" fill="#E8192C">FAKE</text></g></g>')
        else:
            # a tick for the safe ones
            cx_, cy_ = bx + BW - 26, by + 22
            out.append(f'<g transform="translate({cx_} {cy_})"><g><animateTransform attributeName="transform" type="scale"'
                       f' values="0;0;1.3;1;1" keyTimes="{kt(0, 4.1 + i * .05, 4.35 + i * .05, 4.5 + i * .05, T)}"{rep()}/>'
                       '<circle r="16" fill="#22C55E" stroke="#fff" stroke-width="3"/>'
                       '<path d="M-7 0L-2 6L8 -6" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round"'
                       ' stroke-linejoin="round"/></g></g>')
        out.append('</g></g></g>')
    # the shock ring off the stamp
    sxr, syr = bubbles[1][0] + BW - 74, bubbles[1][1] + BH / 2
    out.append(f'<circle cx="{sxr}" cy="{syr}" r="20" fill="url(#rfRed)" opacity="0">'
               f'<animate attributeName="r" values="20;20;140;140" keyTimes="{kt(0, t_stamp, t_stamp + .5, T)}"{rep()}/>'
               f'<animate attributeName="opacity" values="0;0;.9;0;0" keyTimes="{kt(0, t_stamp, t_stamp + .04, t_stamp + .5, T)}"{rep()}/></circle>')
    # the magnifier sweeps the messages
    lens = [(0, 620, 40), (1.3, 620, 40), (1.7, 420, 92), (2.2, 400, 92), (2.6, 360, 182), (3.15, 352, 182),
            (3.6, 400, 272), (4.2, 420, 272), (4.7, 720, 430), (T, 720, 430)]
    xs = ";".join(f"{p[1]} {p[2]}" for p in lens)
    ks = kt(*[p[0] for p in lens])
    spl = ";".join([".45 0 .55 1"] * (len(lens) - 1))
    flare = (f'<circle r="34" fill="#FF3B4E" opacity="0"><animate attributeName="opacity"'
             f' values="0;0;.55;.25;.55;0;0" keyTimes="{kt(0, 2.6, 2.8, 2.95, 3.1, 3.4, T)}"{rep()}/></circle>')
    glint = (f'<circle r="34" fill="#7CFFB0" opacity="0"><animate attributeName="opacity"'
             f' values="0;0;.45;0;0;.45;0;0" keyTimes="{kt(0, 1.75, 1.95, 2.25, 3.65, 3.85, 4.2, T)}"{rep()}/></circle>')
    out.append(f'<g><animateTransform attributeName="transform" type="translate" values="{xs}" keyTimes="{ks}"'
               f' calcMode="spline" keySplines="{spl}"{rep()}/>'
               '<path d="M24 24L58 58" stroke="#6B3E1E" stroke-width="12" stroke-linecap="round"/>'
               '<path d="M24 24L58 58" stroke="#A86A3B" stroke-width="7" stroke-linecap="round"/>'
               '<circle r="34" fill="#E9F7FF" fill-opacity=".28"/>' + flare + glint +
               '<circle r="34" fill="none" stroke="#C99A4A" stroke-width="8"/>'
               '<circle r="34" fill="none" stroke="#F2D18A" stroke-width="3"/>'
               '<path d="M-20 -12A24 24 0 0 1 -6 -24" stroke="#fff" stroke-width="5" stroke-linecap="round" fill="none" opacity=".8"/>'
               '</g>')
    # the badge bursts in
    bw, bh = got["badge"][1] * 1.15, got["badge"][2] * 1.15
    gx, gy = 392.0, 186.0
    rays = "".join(f'<path d="M0 0L{120 * math.cos(math.radians(a - 5)):.1f} {120 * math.sin(math.radians(a - 5)):.1f}'
                   f'L{120 * math.cos(math.radians(a + 5)):.1f} {120 * math.sin(math.radians(a + 5)):.1f}Z"/>'
                   for a in range(0, 360, 24))
    out.append(f'<g transform="translate({gx} {gy})"><circle r="120" fill="url(#rfSun)" opacity="0">'
               f'<animate attributeName="opacity" values="0;0;1;.7;0;0" keyTimes="{kt(0, t_win, t_win + .3, T - .8, T - .4, T)}"{rep()}/></circle>'
               f'<g fill="#FFF7C2" opacity="0"><animate attributeName="opacity" values="0;0;.6;.35;0;0"'
               f' keyTimes="{kt(0, t_win, t_win + .3, T - .8, T - .4, T)}"{rep()}/>'
               f'<animateTransform attributeName="transform" type="rotate" values="0;360" dur="12s" repeatCount="indefinite"/>{rays}</g>'
               f'<g><animateTransform attributeName="transform" type="scale" values="0;0;1.3;.92;1.04;1;1;0;0"'
               f' keyTimes="{kt(0, t_win, t_win + .3, t_win + .45, t_win + .6, t_win + .75, T - .8, T - .45, T)}" calcMode="spline"'
               f' keySplines="0 0 1 1;.2 .8 .3 1;{_EASE};{_EASE};{_EASE};0 0 1 1;.5 0 1 .5;0 0 1 1"{rep()}/>'
               f'<image xlink:href="{got["badge"][0]}" x="{-bw / 2:.1f}" y="{-bh / 2:.1f}" width="{bw:.1f}" height="{bh:.1f}"/></g>')
    for i in range(12):
        a = i / 12 * 2 * math.pi
        d = 95 + (i % 3) * 25
        out.append(f'<path d="M0 -7L2 -2L7 0L2 2L0 7L-2 2L-7 0L-2 -2Z" fill="#FFE066" opacity="0">'
                   f'<animateMotion path="M0 0L{math.cos(a) * d:.0f} {math.sin(a) * d:.0f}" keyPoints="0;0;1;1"'
                   f' keyTimes="{kt(0, t_win + .2, t_win + 1, T)}" calcMode="spline" keySplines="0 0 1 1;.2 .8 .3 1;0 0 1 1"{rep()}/>'
                   f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="{kt(0, t_win + .2, t_win + .3, t_win + 1.4, T)}"{rep()}/></path>')
    out.append('</g></g>')
    return "".join(out)


ICON_SCENE = {"fln-animation-toolkit": (_scene_defs_stars, _scene_stars),
              "real-or-fake-sender": (_scene_defs_rf, _scene_rf),
              "think-ask-act": (_scene_defs_ta, _scene_ta),
              "calm-or-react": (_scene_defs_cr, _scene_cr),
              "feeling-wheel-tap": (_scene_defs_fw, _scene_fw),
              "aaru_ki_cheenk": (_scene_defs_aaru, _scene_aaru),
              "Keyword-class9": (_scene_defs_kw, _scene_kw)}


# Artwork beats a drawn mark wherever a project already has its own, and the
# crop matters more than the source: at 46px a whole screen is mush, so each
# of these is the one element that survives - a face, a lit card, a wheel.
ART_PHOTO = {"Competition-Zone": "proj-art-zone.png",
             # Optional: drop these files into assets/ and they replace the
             # drawn star / bee scenes and the plain Portfolio icon.
             "fln-animation-toolkit": "proj-art-fln.png",
             "Portfolio": "proj-art-portfolio.png"}
_PHOTO_CACHE = {}


def _photo_uri(name):
    """The artwork, inlined, so the card stays one self-contained file."""
    if name not in _PHOTO_CACHE:
        import base64
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "..", "assets", name)
        try:
            with open(path, "rb") as fh:
                _PHOTO_CACHE[name] = ("data:image/png;base64,"
                                      + base64.b64encode(fh.read()).decode())
        except Exception as exc:
            print("project icon skipped:", name, exc)
            _PHOTO_CACHE[name] = ""
    return _PHOTO_CACHE[name]


def _tile_defs(repo):
    """Anything a tile needs in the card's one <defs>, rather than its own."""
    got = ICON_SCENE.get(repo)
    if repo in ART_PHOTO and _photo_uri(ART_PHOTO[repo]):
        return ""                        # a real picture replaces the scene
    return got[0]() if got else ""


def _art_clip_path(x, y, r=10):
    """The panel outline: rounded where it meets the card, square where it
    meets the text.  A plain rx would notch the inner edge instead."""
    return (f'M{x + ART_W} {y}H{x + r}a{r} {r} 0 0 0 -{r} {r}V{y + CH - r}'
            f'a{r} {r} 0 0 0 {r} {r}H{x + ART_W}Z')


def _art(x, y, repo, tint):
    """The picture panel: the left 46% of the card, floor to ceiling.

    Everything is drawn inside the panel's own clip rather than fitted to it,
    so a scene can run its stars off the edge without them appearing in the
    middle of the blurb.
    """
    scene = ICON_SCENE.get(repo)
    uri = _photo_uri(ART_PHOTO[repo]) if repo in ART_PHOTO else ""
    if scene and not uri:
        inner = scene[1](x, y)
    else:
        if uri:
            # slice, not meet: the file is cut to the panel's aspect already,
            # but this keeps a rounding error from letting the card show through.
            inner = (f'<image xlink:href="{uri}" x="{x}" y="{y}" width="{ART_W}"'
                     f' height="{CH}" preserveAspectRatio="xMidYMid slice"/>')
        else:
            art = ICONS.get(repo)
            k = (CH * 0.36) / 24.0
            inner = (f'<rect x="{x}" y="{y}" width="{ART_W}" height="{CH}" fill="{tint}"/>'
                     f'<g transform="translate({x + ART_W / 2 - 12 * k:.1f}'
                     f' {y + CH / 2 - 12 * k:.1f}) scale({k:.3f})">'
                     f'{art() if art else ""}</g>')
    return (f'<g clip-path="url(#art)">{inner}'
            f'<rect x="{x}" y="{y}" width="{ART_W}" height="{CH}" fill="url(#fade)"/></g>'
            f'<path d="M{x + ART_W} {y}V{y + CH}" stroke="#00FF9C" stroke-opacity=".20"/>')


def _clip_text(s, n):
    return s if len(s) <= n else s[:n - 1].rstrip(" ,.") + "…"


# The artwork is not an icon on the card, it is half of the card: a landscape
# panel bleeding to the top, bottom and left edges, with the text panel butted
# against its right.  That is why there is no header rule any more - a line
# across the whole card would cut the picture in two.
CW, CH = 566, 188                        # 3.01:1, the shape the artwork wants
ART_W = CW // 2                          # half the card exactly, full bleed
TEXT_X = ART_W + 16                      # the text panel starts here
BLURB_CH = 27                            # what fits before the ring, at 11.5px

# Half the card for the picture leaves 23px less for the words, which the
# longest title and the longest blurb had both already filled.  The ring gives
# it back: out towards the edge and a touch smaller, which costs it nothing -
# it holds no text now, so it only has to read as a chart.
RING_CX, RING_CY, RING_R, RING_W = CW - 46, 96, 27, 6
RING_GAP = 2.4                           # px of track between two slices

# Leave this alone unless a stale image is genuinely stuck.
#
# It exists because renaming a card is the one certain way past a cached copy.
# But the readme lives on main and the cards are built onto the output branch,
# so a bump points the page at files that will not exist for another ninety
# seconds, and every card on the profile is a broken link until CI catches up.
# That happened twice.  A visibly broken page for a minute and a half is worse
# than an image that takes a few minutes to turn over on its own - raw.github
# serves these with max-age=300, so a plain content change gets there by
# itself.  Change the contents and wait; only bump if something is wedged.
CARD_REV = "h"


# The game repos are private, so the API hands back no languages for them.
# These are their shares (from the README tooltips), used only when the API
# returns nothing - update a line here if a project's mix changes a lot.
LANG_FALLBACK = {
    "fln-animation-toolkit": {"HTML": 92, "Python": 8},
    "aaru_ki_cheenk": {"JavaScript": 67, "CSS": 16, "Python": 15},
    "Keyword-class9": {"CSS": 55, "JavaScript": 40, "HTML": 5},
    "feeling-wheel-tap": {"CSS": 40, "JavaScript": 31, "HTML": 29},
    "think-ask-act": {"CSS": 46, "HTML": 31, "JavaScript": 23},
    "real-or-fake-sender": {"CSS": 61, "JavaScript": 28, "HTML": 11},
    "calm-or-react": {"HTML": 38, "CSS": 33, "JavaScript": 29},
    "Competition-Zone": {"HTML": 100},
    "Portfolio": {"HTML": 100},
}


def _card(i, repo, title, tag, blurb, meta, x=2, y=2):
    """One project card, drawn with its top-left at (x, y)."""
    live = bool((meta.get("homepage") or "").strip())
    by = meta.get("bytes") or LANG_FALLBACK.get(repo, {})
    total = sum(by.values()) or 1
    top = sorted(by.items(), key=lambda kv: -kv[1])[:3]

    # No written rows any more - the ring says the names and the shares itself,
    # so each slice carries its language along and the right-hand column is
    # free for the artwork to push into.
    slices = [(b / total, LANG_HUE.get(lang.lower(), "#6E8A99"), lang) for lang, b in top]
    rest = 1.0 - sum(sl[0] for sl in slices)
    if rest > 0.005:
        slices.append((rest, LANG_REST))

    px, pills, stop = x + TEXT_X, "", x + RING_CX - RING_R - 8
    for lang, _ in top:
        chip, w = _pill(px, y + 99, lang.lower())
        if px + w > stop:
            break
        pills += chip
        px += w + 7

    return f'''
  <g>
    <rect x="{x}" y="{y}" width="{CW}" height="{CH}" rx="10" fill="#050f0d"
          stroke="#00FF9C" stroke-opacity=".17"/>

    {_art(x, y, repo, TILE_TINT[i % len(TILE_TINT)])}

    <circle cx="{x + TEXT_X + 4}" cy="{y + 16}" r="3" fill="{'#00FF9C' if live else '#33534e'}"/>
    <text class="mono" x="{x + TEXT_X + 15}" y="{y + 20}" font-size="10.5"
          fill="#557a73">{esc(USER)}/{esc(repo)}</text>
    <text class="mono" x="{x + CW - 15}" y="{y + 20}" font-size="9.5" text-anchor="end"
          letter-spacing="1.2" fill="{'#00FF9C' if live else '#3f5f58'}"
          fill-opacity=".85">{'LIVE' if live else ''}</text>

    <text class="mono" x="{x + TEXT_X}" y="{y + 62}" font-size="15.5" font-weight="700"
          fill="#E8FFF6">{esc(title)}<tspan fill="#00FF9C" fill-opacity=".75">_</tspan></text>
    <text class="mono" x="{x + TEXT_X}" y="{y + 84}" font-size="11.5"
          fill="#7f9c96">{esc(_clip_text(blurb, BLURB_CH))}</text>
    {pills}
    <text class="mono" x="{x + TEXT_X}" y="{y + 158}" font-size="10.5" fill="#557a73"
          xml:space="preserve">{('★ ' + str(meta['stars']) + '   ') if meta.get('stars') else ''}{esc(_ago(meta.get('pushed')))}</text>
    <text class="mono" x="{x + CW - 15}" y="{y + 158}" font-size="9.5" text-anchor="end"
          letter-spacing="1.3" fill="#3ddc97" fill-opacity=".75">{esc(tag)}</text>

    {_donut(x + RING_CX, y + RING_CY, RING_R, slices, 0.25 + i * 0.09)}
  </g>'''


# ------------------------------------------------------------ the hover readout
# What is wanted here is per-arc: point at the blue part of the ring, get that
# language and its share.  That is not available, and it is worth writing down
# why so it is not attempted a fourth time.
#
# A tooltip attaches to an element.  In a README the only elements are whole
# images: GitHub serves SVG through <img>, which is one flat rectangle with no
# interior, so the arcs are pixels rather than shapes.  Every way of getting a
# live document or a region map in was checked against the markdown API and
# every one is stripped - inline <svg> with a <title> per arc, <object>,
# <embed>, <iframe>, <map>, <area>, and author CSS.
#
# Giving an arc its own hover therefore means giving it its own image, and an
# image is visible.  With no visual change allowed, nothing is left to hang it
# on but the card itself - so the card carries one tooltip naming all of the
# languages at once.  Less than per-arc, and the most that exists.
README = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "readme.md")


def _lang_summary(meta):
    """"HTML 92%  .  Python 8%", or "" when there is nothing to say."""
    by = meta.get("bytes") or {}
    total = sum(by.values())
    if not total:
        return ""
    top = sorted(by.items(), key=lambda kv: -kv[1])[:3]
    return "  ·  ".join(f"{lang} {100.0 * b / total:.0f}%" for lang, b in top)


def _set_attr(tag, name, value):
    """Replace name="..." in one tag, or add it after the tag's first attribute."""
    pat = re.compile(r'\s' + name + r'="[^"]*"')
    if pat.search(tag):
        return pat.sub(f' {name}="{value}"', tag, count=1)
    cut = tag.index('"', tag.index('="') + 2) + 1
    return tag[:cut] + f' {name}="{value}"' + tag[cut:]


def _write_readme_titles(index, path=README):
    """Put each card's language split in its own tooltip, and nothing on screen.

    Rewrites in memory and checks the result before opening the file for
    writing, because a half-failed rewrite once truncated this README to
    nothing: open(...,"w") empties the file whether or not the write lands.
    """
    if not os.path.exists(path):
        print("readme titles skipped: no", path)
        return
    text = io.open(path, encoding="utf-8").read()
    out, hit = text, 0
    for repo, _title, _tag, _blurb in FEATURED:
        tip = esc(_lang_summary(index.get(repo, {})))
        row = re.compile(r'<a\s+href="[^"]+"[^>]*>\s*<img\s[^>]*proj-'
                         + re.escape(CARD_REV) + '-' + re.escape(repo) + r'\.svg"[^>]*>')
        m = row.search(out)
        if not m or not tip:
            print("readme titles: nothing to do for", repo)
            continue
        a, img = m.group(0).split("<img", 1)
        fixed = (_set_attr(a.rstrip(), "title", tip)
                 + _set_attr("<img" + img, "title", tip))
        out = out[:m.start()] + fixed + out[m.end():]
        hit += 1

    if hit != len(FEATURED):
        print(f"readme titles: only {hit}/{len(FEATURED)} cards matched, leaving it alone")
        return
    if len(out) < len(text) * 0.8 or "proj-" + CARD_REV not in out:
        print("readme titles: result looks wrong, leaving it alone")
        return
    if out == text:
        print("readme titles: already current")
        return
    io.open(path, "w", encoding="utf-8", newline="\n").write(out)
    print(f"readme titles: updated {hit} cards")


# ---------------------------------------------------------------- the live page
# The one thing a README cannot do: point at one arc of a ring and have that
# arc answer.  Inside a README the card is an <img>, which is a flat rectangle
# with no interior.  Here the very same file is inlined into the document, so
# every arc is a real <circle> again - it takes the pointer, it can highlight,
# and it can say only its own language.  Nothing is redrawn for this page; it
# is the same nine cards, given a document to live in.
PAGES_URL = f"https://{USER}.github.io/{USER}/"
FULL_NAME = "Ananya Goswami"


def _namespace_ids(svg, tag):
    """Nine cards in one document would otherwise share ids.

    Each card defines its own clip paths and gradients, and url(#art) resolves
    against the whole document - so without this every card after the first
    would be clipped by the first one's shape.
    """
    for i in sorted(set(re.findall(r'\sid="([A-Za-z][\w-]*)"', svg)), key=len, reverse=True):
        svg = (svg.replace(f'id="{i}"', f'id="{i}-{tag}"')
                  .replace(f'url(#{i})', f'url(#{i}-{tag})')
                  .replace(f'xlink:href="#{i}"', f'xlink:href="#{i}-{tag}"'))
    return svg


PAGE_CSS = """
:root { --bg:#0d1117; --panel:#050f0d; --edge:#00ff9c; --ink:#e8fff6; --dim:#7f9c96; }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--ink); padding:32px 16px 72px;
       font-family: ui-monospace,"SF Mono","JetBrains Mono",Consolas,monospace; }
header { max-width:1180px; margin:0 auto 26px; }
h1 { font-size:20px; margin:0 0 6px; letter-spacing:.5px; }
header p { margin:0; color:var(--dim); font-size:13px; line-height:1.6; }
.grid { max-width:1180px; margin:0 auto; display:grid; gap:18px;
        grid-template-columns:repeat(auto-fit,minmax(430px,1fr)); }
.card svg { width:100%; height:auto; display:block; }
.card { position:relative; }
.card .go { position:absolute; inset:0; }
.arc { cursor:pointer; transition:stroke-opacity .14s, stroke-width .14s; }
.ring-on .arc { stroke-opacity:.28; }
.arc.hot { stroke-opacity:1; stroke-width:13; }
.open { display:block; margin:8px 2px 0; font-size:11.5px; color:var(--dim);
        text-decoration:none; }
.open:hover { color:var(--edge); }
#tip { position:fixed; z-index:9; pointer-events:none; opacity:0;
       transform:translate(-50%,-140%); transition:opacity .12s;
       background:#0b1f1b; color:var(--ink); border:1px solid rgba(0,255,156,.45);
       border-radius:7px; padding:6px 11px; font-size:13px; white-space:nowrap;
       box-shadow:0 8px 24px rgba(0,0,0,.55); }
#tip.on { opacity:1; }
#tip b { color:var(--edge); font-weight:700; }
@media (max-width:520px){ .grid{grid-template-columns:1fr} body{padding:20px 10px 48px} }
"""

PAGE_JS = """
const tip = document.getElementById('tip');
let locked = null;

function show(arc, x, y) {
  tip.innerHTML = arc.dataset.lang + ' <b>' + arc.dataset.pct + '%</b>';
  tip.style.left = x + 'px'; tip.style.top = y + 'px';
  tip.classList.add('on');
}
function clear(svg) {
  svg.classList.remove('ring-on');
  svg.querySelectorAll('.arc.hot').forEach(a => a.classList.remove('hot'));
}

document.querySelectorAll('.card svg').forEach(svg => {
  const arcs = svg.querySelectorAll('.arc');
  if (!arcs.length) return;
  arcs.forEach(arc => {
    arc.addEventListener('pointermove', e => {
      if (locked && locked !== arc) return;
      svg.classList.add('ring-on');
      arcs.forEach(a => a.classList.toggle('hot', a === arc));
      show(arc, e.clientX, e.clientY);
    });
    // A click keeps one arc up, so it can be read without holding still.
    arc.addEventListener('click', e => {
      e.preventDefault(); e.stopPropagation();
      if (locked === arc) { locked = null; clear(svg); tip.classList.remove('on'); return; }
      document.querySelectorAll('.card svg').forEach(clear);
      locked = arc;
      svg.classList.add('ring-on'); arc.classList.add('hot');
      show(arc, e.clientX, e.clientY);
    });
  });
  svg.addEventListener('pointerleave', () => {
    if (locked && svg.contains(locked)) return;
    clear(svg); tip.classList.remove('on');
  });
});

document.addEventListener('click', () => {
  if (!locked) return;
  const svg = locked.ownerSVGElement;
  locked = null; clear(svg); tip.classList.remove('on');
});
"""


def build_pages(index, cards):
    """One page, the nine cards inlined, every arc alive."""
    blocks = []
    for repo, title, _tag, _blurb in FEATURED:
        svg = cards.get(f"proj-{CARD_REV}-{repo}.svg")
        if not svg:
            continue
        svg = _namespace_ids(svg, repo.replace("_", "-").lower())
        svg = svg.replace('<svg ', '<svg class="live" ', 1)
        svg = re.sub(r'\swidth="\d+" height="\d+"', "", svg, count=1)
        home = (index.get(repo, {}).get("homepage") or "").strip()
        link = (f'<a class="open" href="{esc(home)}" target="_blank" rel="noopener">'
                f'open {esc(title)} \u2197</a>') if home else ""
        blocks.append(f'<div class="card">{svg}{link}</div>')

    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(FULL_NAME)} \u2014 projects</title>'
            f'<style>{PAGE_CSS}</style></head><body>'
            f'<header><h1>{esc(FULL_NAME)} / projects</h1>'
            f'<p>The same nine cards as the profile. Here the rings are live: '
            f'point at one colour to see just that language and its share, '
            f'click to keep it up.</p></header>'
            f'<div class="grid">{"".join(blocks)}</div>'
            f'<div id="tip"></div><script>{PAGE_JS}</script></body></html>\n')


_CARD_CSS = '''<style>
  .mono { font-family: ui-monospace, "SF Mono", "JetBrains Mono", Consolas, monospace; }
</style>'''


def build_project_cards(index):
    """Each project as its own image, so the README can put a link round it.

    A README image is served as <img>, and SVG inside an <img> is inert in
    every browser - no scripts, no hover, and crucially no working <a>.  So a
    single panel can never have nine different click targets no matter how the
    links are written inside it.  Nine images, each wrapped in its own anchor
    in the README, is the only arrangement that actually clicks through.
    """
    W, H = CW + 4, CH + 4
    out = {}
    for i, (repo, title, tag, blurb) in enumerate(FEATURED):
        out[f"proj-{CARD_REV}-{repo}.svg"] = (
            f'<svg xmlns="http://www.w3.org/2000/svg"'
            f' xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}"'
            f' width="{W}" height="{H}" role="img" aria-label="{esc(title)}">'
            f'<defs><pattern id="sc" width="4" height="4" patternUnits="userSpaceOnUse">'
            f'<rect width="4" height="1" fill="#7fffd4" fill-opacity=".03"/></pattern>'
            f'<clipPath id="cw"><rect x="2" y="2" width="{CW}" height="{CH}" rx="10"/></clipPath>'
            f'<clipPath id="art"><path d="{_art_clip_path(2, 2)}"/></clipPath>'
            f'<linearGradient id="fade" x1="0" x2="1"><stop offset=".72" stop-color="#050f0d"'
            f' stop-opacity="0"/><stop offset="1" stop-color="#050f0d" stop-opacity=".9"/>'
            f'</linearGradient>'
            f'{_tile_defs(repo)}</defs>{_CARD_CSS}'
            f'{_card(i, repo, title, tag, blurb, index.get(repo, {}))}'
            f'<g clip-path="url(#cw)" pointer-events="none">'
            f'<rect width="{W}" height="{H}" fill="url(#sc)"/></g>'
            f'</svg>\n')
    return out


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


# ---------------------------------------------------------------- sprite sheets
# Each character has its own transparent sheet, drawn at about twice the size it
# appears in the panel (the *_S scales below bring it back down). The old shared
# atlas (sprite-sheet.png) is gone.
_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets")
# Turtle: 3 rows x 6 cells of 200px. Rows are walk, eat and hide, already in
# the order the story uses them.
TURTLE_SHEET_PATH = os.path.join(_ASSETS, "turtle-sheet-v1.png")
TURTLE_CELL = 200
# Snake: 2 rows x 8 cells of 260px. Row 1 is the slither; row 2 holds three
# tongue-flick frames and one with the mouth closed.
SNAKE_SHEET_PATH = os.path.join(_ASSETS, "snake-sheet-v1.png")
SNAKE_CELL = 260
# Leaf: 1 row x 6 cells of 140px: two popping out of the block, three
# fluttering down (left, level, right) and one lying flat, stem to the right.
LEAF_SHEET_PATH = os.path.join(_ASSETS, "leaf-sheet-v1.png")
LEAF_CELL = 140
# Block and coin: 2 rows x 4 cells of 128px. Row 1 is the </> block (normal,
# flashing when hit, spent); row 2 is the leaf coin spinning (front, turning,
# edge-on, turning back). Each frame is centred in its cell.
BLOCKCOIN_SHEET_PATH = os.path.join(_ASSETS, "blockcoin-sheet-v1.png")
BLOCKCOIN_CELL = 128
_BC = None
# How many frames each row has.
SHEET_ROWS = {"twalk": 6, "teat": 6, "thide": 6,
              "lpop": 2, "lfall": 3, "lslide": 1,
              "sslith": 8, "stongue": 2, "scont": 2}
_SHEET = None


def sheet():
    """Every character frame, keyed by (row, i).

    Returns {(row, i): (data_uri, w, h, ox, oy)}, where ox/oy is the frame's own
    anchor: the middle of the body and the ground it stands on. Two frames
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
    except Exception as exc:
        print("sheets skipped:", exc)
        return _SHEET
    _turtle_frames(Image, np, base64, io)
    _snake_frames(Image, np, base64, io)
    _leaf_frames(Image, np, base64, io)
    return _SHEET


def _leaf_frames(Image, np, base64, io):
    """The leaf: anchored on its middle and its lowest pixel."""
    try:
        src = Image.open(LEAF_SHEET_PATH).convert("RGBA")
    except Exception as exc:
        print("leaf sheet skipped:", exc)
        return
    rows = {"lpop": [0, 1], "lfall": [2, 3, 4], "lslide": [5]}
    for row, cells in rows.items():
        for i, c in enumerate(cells):
            cell = src.crop((c * LEAF_CELL, 0, (c + 1) * LEAF_CELL, LEAF_CELL))
            box = cell.getbbox()
            if box is None:
                continue
            img = cell.crop(box)
            buf = io.BytesIO()
            img.save(buf, "PNG", optimize=True)
            _SHEET[(row, i)] = (
                "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(),
                img.width, img.height, img.width / 2.0, float(img.height))


def _snake_frames(Image, np, base64, io):
    """Swap the snake rows for the frames on its own sheet.

    Anchored on the middle of its body (the tongue left out, so a flick never
    nudges the snake backwards) and on its lowest pixel, where it meets the
    ground.
    """
    try:
        src = Image.open(SNAKE_SHEET_PATH).convert("RGBA")
    except Exception as exc:
        print("snake sheet skipped:", exc)
        return
    rows = {"sslith": [(0, i) for i in range(8)],
            "stongue": [(1, 0), (1, 1)],
            "scont": [(1, 3), (1, 3)]}
    for row, cells in rows.items():
        for i, (r, c) in enumerate(cells):
            cell = src.crop((c * SNAKE_CELL, r * SNAKE_CELL,
                             (c + 1) * SNAKE_CELL, (r + 1) * SNAKE_CELL))
            box = cell.getbbox()
            if box is None:
                continue
            img = cell.crop(box)
            a = np.array(img).astype(int)
            red, green, blue, alpha = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
            body = (alpha > 128) & ~((red > 150) & (green < 90) & (blue < 90))
            ox = float(np.nonzero(body)[1].mean()) if body.any() else img.width / 2.0
            buf = io.BytesIO()
            img.save(buf, "PNG", optimize=True)
            _SHEET[(row, i)] = (
                "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(),
                img.width, img.height, ox, float(img.height))


def _turtle_frames(Image, np, base64, io):
    """Swap the turtle rows for the frames on its own sheet.

    Each frame is anchored on the middle of its shell (so the head pulling in
    or a leaf sticking out of its mouth never shoves the body sideways) and on
    its lowest pixel, which is where its feet meet the ground.
    """
    try:
        src = Image.open(TURTLE_SHEET_PATH).convert("RGBA")
    except Exception as exc:
        print("turtle sheet skipped:", exc)
        return
    for r, row in enumerate(("twalk", "teat", "thide")):
        for i in range(6):
            cell = src.crop((i * TURTLE_CELL, r * TURTLE_CELL,
                             (i + 1) * TURTLE_CELL, (r + 1) * TURTLE_CELL))
            box = cell.getbbox()
            if box is None:
                continue
            img = cell.crop(box)
            a = np.array(img).astype(int)
            red, green, blue, alpha = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
            shell = ((alpha > 128) & (green > red + 15) & (green > 50)
                     & (green < 150) & (blue < 100))
            ox = float(np.nonzero(shell)[1].mean()) if shell.any() else img.width / 2.0
            buf = io.BytesIO()
            img.save(buf, "PNG", optimize=True)
            _SHEET[(row, i)] = (
                "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(),
                img.width, img.height, ox, float(img.height))


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
    idx = range(SHEET_ROWS[row]) if only is None else only
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
TURTLE_S, LEAF_S, SNAKE_S = 0.50, 0.75, 0.50
V_LEAF, V_TURTLE, V_SNAKE, V_LIMP = 19.0, 34.0, 48.0, 22.0
EAT = 3.0                            # a readable set of bites, not a rapid flicker
LEAF_GAP = 52.0                      # the leaf halts with its edge at the mouth
# She crosses the panel in RUN_TIME seconds, and her legs are locked to the
# ground, so this also sets her cadence: 11 s gave ~14 frames a second and
# 14 s ~11, both too quick. 20 s gives ~8 frames a second, an unhurried
# jog with her feet still planted.
RUN_TIME = 20.0
# Flipbook speeds. Each is the time for one full loop of that character's cycle.
# Her cycle is derived below from the avatar's measured contact stride and the
# panel's ground speed.
RUN_SPEED = ((VB_W + 120.0) - (-120.0)) / RUN_TIME
JD_MAX, LIFT_MAX = 1.08, 184.0
RUN_BOUNCE = 0.0                     # Mario-style: the sprite stays level, no bob
JUMP_SAMPLE_DT = 1.0 / 50.0
# Its four legs are planted 43 units apart, so a step moves it about half that
# and two steps take 42/34 of a second at its walking speed.
WALK_CYCLE = 1.24
TURTLE_BOB = 2.5                     # it is 53 tall; a plod lifts about 5%
SLITHER_CYCLE = 3.30                 # body wave, then a clearly held tongue-flick hiss

# The tally above the grid. It sits on GX0 so the icon's left edge lines up
# with the first column of squares instead of hanging out past them, and it is
# a coin rather than a star because a coin is what these squares actually give
# up when she hits one - the number beside it counts exactly those.
HUD_R = 15.0
HUD_CX, HUD_CY = GX0 + HUD_R, 149.5
HUD_GAP = 7.0                        # space between the coin and the count
HUD_SPIN = 3.4                       # a slow flip: alive, but not pulling focus


def _keys(vals, times, T):
    """Clamp and monotonise keyTimes, returning the SMIL strings."""
    ks = [min(max(t / T, 0.0), 1.0) for t in times]
    for i in range(1, len(ks)):
        ks[i] = max(ks[i], ks[i - 1])
    return ";".join(vals), ";".join(f"{k:.5f}" for k in ks)


def _pick_cells(grid, cols):
    """Three real contribution cells, each on its own row, for the cast to pop out of.

    No mystery blocks: whatever she hits is an actual commit square. The story
    reads leaf, turtle, snake, all heading left, so the spacing matters more
    than the exact spot: the turtle's square a few columns right of the leaf's
    (so it catches the leaf up soon), and the snake's well back to the right
    (so it turns up after the meal). Every combination of lit columns is scored
    and the closest fit wins, so clustered activity still gets a usable trio.
    """
    # only squares her highest jump can reach (rows 2-6); rows 0-1 sit above it
    reach = [r for r in (6, 5, 4, 3, 2, 1, 0)
             if GROUND - GIRL_TARGET_H - (GY0 + r * GPY + GCELL) <= LIFT_MAX]
    lit = {i: [r for r in reach if grid[i][r] > 0] for i in range(cols)}
    lcols = [i for i in range(cols) if lit[i]]
    # The squares must sit far enough apart that one jump has landed before
    # the next begins. That is a time, so in columns it grows with her speed.
    G = max(3, math.ceil(1.3 * RUN_SPEED / GPX))
    aim = int(cols * 0.40)

    def rows_for(trio):
        used, out = set(), []
        for c in trio:
            r = next((r for r in lit[c] if r not in used), None)
            if r is None:
                return None
            used.add(r)
            out.append(r)
        return out

    def penalty(a, b, c):
        d1, d2 = b - a, c - b
        return (8.0 * max(0, G + 1 - d1) + 4.0 * max(0, d1 - (G + 4))
                + 3.0 * max(0, G + 6 - d2) + 0.4 * abs(a - aim))

    best = None
    for ai, a in enumerate(lcols):
        for bi in range(ai + 1, len(lcols)):
            b = lcols[bi]
            if b - a < G:
                continue
            for c in lcols[bi + 1:]:
                if c - b < G:
                    continue
                rows = rows_for((a, b, c))
                if rows is None:
                    continue
                score = penalty(a, b, c)
                if best is None or score < best[0]:
                    best = (score, (a, b, c), rows)
    picked = []
    if best is None:
        # fewer than three usable squares: take whatever is there, spaced out
        for c in lcols:
            if all(abs(c - q["col"]) >= G for q in picked) and len(picked) < 3:
                r = next((r for r in lit[c] if r not in {q["row"] for q in picked}), None)
                if r is not None:
                    picked.append({"col": c, "row": r, "lv": grid[c][r]})
    else:
        for c, r in zip(best[1], best[2]):
            picked.append({"col": c, "row": r, "lv": grid[c][r]})
    for f in picked:
        f["x"] = GX0 + f["col"] * GPX + GCELL / 2
        f["y"] = GY0 + f["row"] * GPY
    picked.sort(key=lambda q: q["col"])
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
    RUN = RUN_TIME

    events = _pick_cells(grid, cols)
    speed = (X1 - X0) / RUN
    for e in events:
        e["t"] = (e["x"] - X0) / speed
    run_v = f"{X0:.1f},{GROUND};{X1:.1f},{GROUND};{X1:.1f},{GROUND}"
    run_k = f"0;{RUN / T:.5f};1"

    # ---- projectile jump: one gravity, interrupted by the block on contact ----
    # The uninterrupted maximum jump fixes G. Each block then determines its
    # own launch velocity and flight times from the exact clearance required.
    G = 2.0 * LIFT_MAX / (JD_MAX / 2.0) ** 2
    samples = [(0.0, 0.0)]
    jumps = []
    for e in events:
        clear = min(LIFT_MAX, max(
            38.0, GROUND - GIRL_TARGET_H - (e["y"] + GCELL)))
        apex = clear + 10.0
        v0 = math.sqrt(2.0 * G * apex)
        v_hit = math.sqrt(v0 * v0 - 2.0 * G * clear)
        t_up = (v0 - v_hit) / G
        t_down = math.sqrt(2.0 * clear / G)
        t0, t1 = e["t"] - t_up, e["t"] + t_down

        # The gait is visible again only on one of its two foot contacts per
        # cycle. Leave enough time for the landing squash before that hand-off.
        step_time = RUN_CYCLE / 2.0
        resume = math.ceil((t1 + 0.14) / step_time) * step_time
        jumps.append({"t0": t0, "hit": e["t"], "t1": t1,
                      "t_up": t_up, "t_down": t_down, "resume": resume})

        if samples[-1][0] > t0:
            raise ValueError("jump windows overlap; projectile path is ambiguous")
        samples.append((t0, 0.0))
        rise_steps = max(1, math.ceil(t_up / JUMP_SAMPLE_DT))
        for i in range(1, rise_steps + 1):
            dt = t_up * i / rise_steps
            samples.append((t0 + dt, v0 * dt - 0.5 * G * dt * dt))
        fall_steps = max(1, math.ceil(t_down / JUMP_SAMPLE_DT))
        for i in range(1, fall_steps + 1):
            dt = t_down * i / fall_steps
            samples.append((e["t"] + dt, clear - 0.5 * G * dt * dt))
    samples.append((T, 0.0))
    jump_v, jump_k = _keys(
        [f"0,{-height:.3f}" for _, height in samples],
        [t for t, _ in samples], T)

    # Anticipation and landing deformation are deliberately independent of the
    # projectile translate: scaling can sell force without changing the path.
    squash = [(0.0, "1 1")]
    for jump in jumps:
        t0, hit, t1, resume = (jump[k] for k in ("t0", "hit", "t1", "resume"))
        squash += [(t0 - 0.12, "1 1"), (t0 - 0.045, "1.08 .90"),
                   (t0, ".97 1.05"), (t0 + 0.07, "1 1"),
                   (hit, "1 1"), (t1, "1 1"),
                   (t1 + 0.04, "1.10 .88"),
                   (t1 + 0.12, ".98 1.03"), (resume, "1 1")]
    squash.append((T, "1 1"))
    squash_v, squash_k = _keys([v for _, v in squash],
                                [t for t, _ in squash], T)

    # It remains on the ground; only its footprint and density respond to lift.
    shadow_ratio = [min(max(h / LIFT_MAX, 0.0), 1.0) for _, h in samples]
    shadow_rx = ";".join(f"{34.0 * (1.0 - 0.42 * r):.2f}" for r in shadow_ratio)
    shadow_ry = ";".join(f"{7.0 * (1.0 - 0.35 * r):.2f}" for r in shadow_ratio)
    shadow_opacity = ";".join(f"{0.35 * (1.0 - 0.65 * r):.3f}"
                              for r in shadow_ratio)

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
            # the real square sits underneath and shows again once the
            # spent block has faded, so nothing fake lingers in the grid
            cells.append(base + "/>")
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
        def meet(vt, vl):
            return ((tx0 + vt * t_walk2 - lx0 - vl * leaf_land - LEAF_GAP)
                    / (vt - vl))

        # Normal pace first. If the squares are too far apart for the turtle
        # to reach the leaf in time, it walks a little faster (always slower
        # than the snake) and then the leaf slows to a stop. The leaf is never
        # pulled back to the right to close the gap.
        cap = T - 22.0
        tries = [(vt, V_LEAF) for vt in (V_TURTLE, 36.0, 38.0, 40.0)]
        tries += [(40.0, vl) for vl in (14.0, 9.0, 4.0, 0.0)]
        vt, vl = tries[-1]
        for cand in tries:
            if meet(*cand) <= cap:
                vt, vl = cand
                break
        t_eat = max(meet(vt, vl), t_walk2 + 1.5)
        eat_x = tx0 - vt * (t_eat - t_walk2)
        t_resume = t_eat + EAT

        def turtle_at(t):
            if t <= t_walk2:
                return tx0
            if t <= t_eat:
                return tx0 - vt * (t - t_walk2)
            if t <= t_resume:
                return eat_x
            return eat_x - vt * (t - t_resume)

    if e3:
        # Land far enough left that the faster snake catches the turtle while
        # both are still clearly visible, not at the edge of the panel.
        sx0 = e3["x"] - 150.0

        def snake_at(t):
            return sx0 - V_SNAKE * max(0.0, t - t_slith)

        def first_contact():
            probe = t_slith
            while probe < T:
                if snake_at(probe) - turtle_at(probe) <= 115.0:
                    return probe
                probe += 0.05
            return T

        # It must come from behind and only reach the turtle once the meal is
        # over, so when the squares sit close together it stays in its block a
        # little longer rather than overtaking a turtle that is still eating.
        t3 = e3["t"]
        while True:
            t_land3 = t3 + 1.5
            t_slith = t_land3 + 0.5
            if not e2 or first_contact() >= t_resume + 0.6 or t3 > T - 20.0:
                break
            t3 += 0.1
        t_gone = min(T - 0.5, t_slith + (sx0 + 240.0) / V_SNAKE)

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
        leaf_x = (min(lx0, eat_x - LEAF_GAP) if e2
                  else lx0 - V_LEAF * (T - leaf_land))
        # The turtle's own bite frames hold the leaf in its mouth, so the leaf
        # on the ground goes the moment it is picked up.
        leaf_end = _edge[1] if e2 else T
        leaf = (sequence(sheet_row("lpop", LEAF_S), t1, t1 + 0.55, T)
                + sequence(sheet_row("lfall", LEAF_S), t1 + 0.55, leaf_land, T))
        # Once it touches the ground, keep one fixed side facing the viewer.
        # Position animation carries this frame left; no flipping or rotation.
        grounded_leaf = sheet_use("lslide", 0, LEAF_S)
        if e2:
            leaf += sequence([grounded_leaf], leaf_land, leaf_end, T)
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
        # A smooth zig-zag, sampled finely so it is a wave and not a hop: the
        # head rises and dips (never below the ground), it surges forward on
        # each push and eases between them, and the body tilts with the slope.
        # One body wave carries it one body length (~84 units), so the wave
        # and the ground agree. The surge only varies its speed by about 30%
        # (it must never slip backwards), and the rise and tilt stay gentle,
        # so it glides rather than heaves.
        ZIG_P = 84.0 / V_SNAKE
        ZIG_SURGE = 0.3 * V_SNAKE * ZIG_P / (2 * math.pi)
        ZIG_AMP, ZIG_TILT = 5.0, 4.0
        tilt = [(0.0, 0.0), (t_slith, 0.0)]
        zt = t_slith + 0.05
        while zt < t_gone:
            ph = 2 * math.pi * (zt - t_slith) / ZIG_P
            pts.append((zt, snake_at(zt) - ZIG_SURGE * math.sin(ph),
                        BASE - ZIG_AMP * (1 - math.cos(ph)) / 2))
            tilt.append((zt, ZIG_TILT * math.sin(ph)))
            zt += 0.08
        pts += [(t_gone, snake_gone, BASE), (T, snake_gone, BASE)]
        tilt += [(t_gone, 0.0), (T, 0.0)]

        # While it waits in its block it flicks its tongue; once it moves, the
        # body wave runs on the same clock as the zig-zag, so the body and the
        # path agree instead of the snake gliding along.
        slither = sheet_row("sslith", SNAKE_S)
        tongue = sheet_row("stongue", SNAKE_S)
        hiss = flipbook(tongue + tongue[::-1] + sheet_row("scont", SNAKE_S),
                        1.4, weights=[2.0, 2.8, 2.8, 2.0, 1.0, 1.0])
        wave = flipbook(slither, ZIG_P)
        body = gate(hiss, [(t_slith, T)], T) + gate(wave, [(0.0, t_slith)], T)
        tv, tk = _keys([f"{a:.1f} 0 -20" for _, a in tilt], [tt for tt, _ in tilt], T)
        snake = (f'<g><animateTransform attributeName="transform" type="rotate" dur="{T}s"'
                 f' repeatCount="indefinite" calcMode="linear" values="{tv}" keyTimes="{tk}"/>'
                 f'{body}</g>')
        pops.append(moving(snake, pts, t3, t_gone))

    # ---- her ----
    girl = (f'<g><animateTransform attributeName="transform" type="translate" dur="{T}s"'
            f' repeatCount="indefinite" calcMode="linear" values="{run_v}" keyTimes="{run_k}"/>'
            f'<ellipse cx="0" cy="-4" rx="34" ry="7" fill="#000" fill-opacity=".35">'
            f'<animate attributeName="rx" dur="{T}s" repeatCount="indefinite" calcMode="linear"'
            f' values="{shadow_rx}" keyTimes="{jump_k}"/>'
            f'<animate attributeName="ry" dur="{T}s" repeatCount="indefinite" calcMode="linear"'
            f' values="{shadow_ry}" keyTimes="{jump_k}"/>'
            f'<animate attributeName="fill-opacity" dur="{T}s" repeatCount="indefinite"'
            f' calcMode="linear" values="{shadow_opacity}" keyTimes="{jump_k}"/></ellipse>'
            f'<g><animateTransform attributeName="transform" type="translate" dur="{T}s"'
            f' repeatCount="indefinite" calcMode="linear" values="{jump_v}" keyTimes="{jump_k}"/>'
            f'<g><animateTransform attributeName="transform" type="scale" dur="{T}s"'
            f' repeatCount="indefinite" calcMode="linear" values="{squash_v}"'
            f' keyTimes="{squash_k}"/>{girl_runner(jumps, T)}</g></g></g>')

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
                  f' values=".12;.6;.12" keyTimes="0;0.5;1"'
                  f' dur="{2.0 + (k % 5) * 0.6}s" repeatCount="indefinite"/></rect>')

    hud = ""
    if total is not None:
        hud = (f'<g transform="translate({HUD_CX:.1f} {HUD_CY:.1f})">'
               f'{coin_spin(HUD_SPIN, 0.0, HUD_R)}</g>'
               f'<text class="rmono" x="{HUD_CX + HUD_R + HUD_GAP:.0f}" y="160"'
               f' font-size="30" fill="#CFEAE3">x {total}</text>')

    # the outro starts once the snake has passed and the turtle is out again
    t_cut = min(t_emerge + 1.6, T - 11.0) if e3 else T - 11.0
    outro = story_outro(t_cut, T)

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
{outro}
</g>
</svg>
'''


# ---------------------------------------------------------------- the outro: leaf storm, then the play block
# After the snake has passed and the turtle is out of its shell, a gust of
# leaves sweeps right to left and clears the scene to the play screen: the
# </> block as a play button, which she keeps bonking like any other block.
# GitHub never runs code in a README and links the whole image, so the button
# is a picture; clicking anywhere on the panel opens the game.
PLAY_SHEET_PATH = os.path.join(_ASSETS, "play-block-sheet-v1.png")    # 3 x 320px: idle, glow, squashed bump
PLAY_CELL = 320
TUMBLE_SHEET_PATH = os.path.join(_ASSETS, "leaf-tumble-sheet-v1.png")  # 8 x 256px tumble, 6 rows
# its rows are the same leaf through a year, listed here youngest first:
# spring lime, summer teal (the art as drawn), gold, orange, red, dry brown
TUMBLE_LIFE = [1, 0, 2, 3, 4, 5]
TUMBLE_CELL = 256
OUTRO_WIPE = 5.0          # gust start -> the hero leaf covers the screen; slow and smooth
OUTRO_FADE = 0.6          # the play screen fades back into the story's first frame
PLAY_BTN_H = 176.0        # the button's height on screen
PLAY_BTN_CX, PLAY_BTN_CY = 1086.0, 300.0
_STRIPS = {}


def _strip_frames(key, path, cell, n, row=0, max_px=None):
    """Frames from one row of a sheet, trimmed and registered as sprites."""
    key = f"{key}{row}-" if row else key
    if key in _STRIPS:
        return _STRIPS[key]
    out = []
    try:
        import base64, io
        from PIL import Image
        src = Image.open(path).convert("RGBA")
        for i in range(n):
            c = src.crop((i * cell, row * cell, (i + 1) * cell, (row + 1) * cell))
            box = c.getbbox()
            if box is None:
                continue
            img = c.crop(box)
            w, h = img.size
            # the picture is stored no bigger than it is drawn; its <image>
            # keeps the full size, so every frame shares one scale
            if max_px and max(w, h) > max_px:
                k = max_px / max(w, h)
                img = img.resize((max(1, round(w * k)), max(1, round(h * k))), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, "PNG", optimize=True)
            fid = f"{key}{i}"
            _USED[fid] = ("data:image/png;base64," +
                          base64.b64encode(buf.getvalue()).decode(), w, h)
            # remember where the trimmed frame sat in its cell, so a bump
            # drawn into the art keeps its offset
            out.append((fid, w, h, box))
    except Exception as exc:
        print(f"{key} sheet not used yet:", exc)
    _STRIPS[key] = out
    return out


def _strip_use(fr, height, cell, ref_h):
    """One sheet frame centred on its cell's centre; ref_h is the art's
    height in the idle frame, so every frame shares one scale."""
    fid, w, h, (x0, y0, _, _) = fr
    k = height / ref_h
    return (f'<use xlink:href="#sp-{fid}" transform="translate({(x0 - cell / 2) * k:.2f}'
            f' {(y0 - cell / 2) * k:.2f}) scale({k:.4f})"/>')


def _play_faces():
    """[idle, glow, bump] for the play block, and whether the bump is drawn in."""
    got = _strip_frames("play", PLAY_SHEET_PATH, PLAY_CELL, 3, max_px=200)
    if len(got) == 3:
        ref = got[0][2]
        return [_strip_use(f, PLAY_BTN_H, PLAY_CELL, ref) for f in got], True
    # stand-in until the art arrives: a teal block with a play triangle of
    # contribution squares on its face
    h = PLAY_BTN_H / 2

    def face(body, glow):
        tiles = ""
        step = PLAY_BTN_H / 9.0
        # columns of the triangle, tallest at the left
        for col, half in [(-2, 3), (-1, 2.4), (0, 1.8), (1, 1.2), (2, 0.6)]:
            n = int(round(half * 2))
            for r in range(n):
                y = (r - (n - 1) / 2.0) * step
                x = col * step
                tip = col == 2 or (col == 1 and abs(y) < step)
                tiles += (f'<rect x="{x - step * 0.4:.1f}" y="{y - step * 0.4:.1f}"'
                          f' width="{step * 0.8:.1f}" height="{step * 0.8:.1f}" rx="3"'
                          f' fill="{"#9BEFD9" if tip else "#06313E"}"/>')
        ring = (f'<rect x="{-h - 10:.1f}" y="{-h - 10:.1f}" width="{PLAY_BTN_H + 20:.1f}"'
                f' height="{PLAY_BTN_H + 20:.1f}" rx="30" fill="none" stroke="#3CEDA5"'
                f' stroke-opacity=".45" stroke-width="6"/>' if glow else "")
        return (ring + f'<rect x="{-h:.1f}" y="{-h:.1f}" width="{PLAY_BTN_H:.1f}"'
                f' height="{PLAY_BTN_H:.1f}" rx="24" fill="{body}" stroke="#128070"'
                f' stroke-width="8"/>' + tiles)
    return [face("#20D898", False), face("#3CEDA5", True), face("#3CEDA5", False)], False


def _tumble_leaf(size, row=0):
    got = _strip_frames("tumble", TUMBLE_SHEET_PATH, TUMBLE_CELL, 8, row, max_px=72)
    if len(got) == 8:
        ref = max(f[2] for f in got)
        return [_strip_use(f, size, TUMBLE_CELL, ref) for f in got]
    # stand-in: the story's own falling leaf frames
    return sheet_row("lfall", LEAF_S * size / 60.0)


def _planet_designs():
    """Five small, quiet planets in the panel's palette, centred on 0,0."""
    ring = lambda c, a: (f'<ellipse rx="150" ry="30" fill="none" stroke="{c}" stroke-opacity="{a}"'
                         f' stroke-width="5" transform="rotate(-14)"/>')
    front = lambda c, a: (f'<path d="M -150 0 A 150 30 0 0 0 150 0" fill="none" stroke="{c}"'
                          f' stroke-opacity="{a}" stroke-width="5" transform="rotate(-14)"/>')
    grad = lambda gid, a, b, c: (f'<radialGradient id="{gid}" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="{a}"/>'
                                 f'<stop offset=".6" stop-color="{b}"/><stop offset="1" stop-color="{c}"/></radialGradient>')
    shade = ('<circle r="74" fill="url(#plShade)"/>')
    out = []
    # 1. ringed teal giant
    out.append(grad("pl1", "#1E6B66", "#0E3A40", "#081420") + ring("#20D898", ".18")
               + '<circle r="74" fill="url(#pl1)"/>' + front("#20D898", ".3"))
    # 2. banded violet gas giant
    bands = "".join(f'<rect x="-80" y="{y}" width="160" height="{h}" fill="{c}" opacity=".55"/>'
                    for y, h, c in [(-48, 10, "#8E7CF0"), (-22, 14, "#5B4BC4"), (8, 8, "#B3A6FF"), (30, 12, "#5B4BC4")])
    out.append(grad("pl2", "#6E5FD8", "#3B2F86", "#120E2A")
               + '<clipPath id="pl2c"><circle r="80"/></clipPath>'
               + '<circle r="80" fill="url(#pl2)"/>' + f'<g clip-path="url(#pl2c)">{bands}</g>' + '<circle r="80" fill="url(#plShade)"/>')
    # 3. dusty red planet with craters
    craters = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#5A1F1C" opacity=".55"/>'
                      for x, y, r in [(-24, -18, 12), (20, 10, 9), (-8, 30, 7), (32, -26, 6), (-40, 14, 5)])
    out.append(grad("pl3", "#C9584A", "#7A2A26", "#1A0A0C") + '<circle r="66" fill="url(#pl3)"/>' + craters
               + '<circle r="66" fill="url(#plShade)"/>')
    # 4. ice world with two little moons
    out.append(grad("pl4", "#BFEFFF", "#4C9FC0", "#0C2433") + '<circle r="70" fill="url(#pl4)"/>'
               + '<ellipse cx="-10" cy="-20" rx="40" ry="10" fill="#E8FBFF" opacity=".25"/>'
               + '<circle r="70" fill="url(#plShade)"/>'
               + '<g><animateTransform attributeName="transform" type="rotate" values="0;360" dur="18s" repeatCount="indefinite"/>'
               + '<circle cx="118" cy="0" r="9" fill="#9FC9D9"/></g>'
               + '<g><animateTransform attributeName="transform" type="rotate" values="200;-160" dur="26s" repeatCount="indefinite"/>'
               + '<circle cx="150" cy="0" r="6" fill="#6E95A6"/></g>')
    # 5. golden ringed world, rings tilted the other way
    out.append(grad("pl5", "#FFE08A", "#C08A2E", "#2A1A08")
               + ring("#FFD24A", ".22").replace("rotate(-14)", "rotate(18)")
               + '<circle r="60" fill="url(#pl5)"/>' + '<circle r="60" fill="url(#plShade)"/>'
               + front("#FFD24A", ".35").replace("rotate(-14)", "rotate(18)"))
    return out


def per_loop(items, T):
    """Show items[k] during loop k of the panel, in turn; the order turns daily."""
    n = len(items)
    if n == 1:
        return items[0]
    start = datetime.now(timezone.utc).timetuple().tm_yday % n
    order = items[start:] + items[:start]
    span = n * T
    out = ""
    for k, d in enumerate(order):
        vals, keys = _keys(["0", "1", "0", "0"] if k else ["1", "0", "0", "0"],
                           [0.0, k * T, (k + 1) * T, span] if k else [0.0, T, span, span], span)
        out += (f'<g opacity="0"><animate attributeName="opacity" dur="{span:.1f}s" repeatCount="indefinite"'
                f' calcMode="discrete" values="{vals}" keyTimes="{keys}"/>{d}</g>')
    return out


def planets(cx, cy, T):
    """One planet per loop of the panel, in turn; the first one changes daily."""
    designs = _planet_designs()
    n = len(designs)
    start = datetime.now(timezone.utc).timetuple().tm_yday % n
    order = designs[start:] + designs[:start]
    span = n * T
    out = ('<defs><radialGradient id="plShade" cx=".75" cy=".75" r=".75">'
           '<stop offset=".55" stop-color="#081420" stop-opacity="0"/>'
           '<stop offset="1" stop-color="#081420" stop-opacity=".75"/></radialGradient></defs>')
    for k, d in enumerate(order):
        vals, keys = _keys(["0", "1", "0", "0"] if k else ["1", "0", "0", "0"],
                           [0.0, k * T, (k + 1) * T, span] if k else [0.0, T, span, span], span)
        out += (f'<g opacity="0"><animate attributeName="opacity" dur="{span:.1f}s" repeatCount="indefinite"'
                f' calcMode="discrete" values="{vals}" keyTimes="{keys}"/>'
                f'<g transform="translate({cx:.0f} {cy:.0f})">{d}</g></g>')
    return out


def story_outro(t_cut, T):
    px0, py0, px1, py1 = PANEL
    W, H = px1 - px0, py1 - py0
    t_cover = t_cut + OUTRO_WIPE
    rnd = random.Random(7)

    # The play screen is fully in place at t_switch, when the hero leaf has
    # opened onto all of it.
    t_switch = t_cover
    fade_v, fade_k = _keys(["0", "0", "1", "1", "0", "0"],
                           [0.0, t_cut, t_cut + 0.01, T - OUTRO_FADE, T - 0.01, T], T)

    # ---- the play screen ----
    faces, drawn_bump = _play_faces()
    t_on = t_switch + 0.3
    bonks, b = [], t_on + 1.4
    while b < T - OUTRO_FADE - 1.2:
        bonks.append(b)
        b += 3.2
    bump_len = 0.34
    quiet = [(bk, bk + bump_len) for bk in bonks]
    glow = gate(flipbook(faces[:2], 1.3), quiet, T)
    bumps = "".join(sequence([faces[2]], bk, bk + bump_len, T) for bk in bonks)
    # the bump frame is drawn squashed, not raised, so it is lifted here too
    if True:
        vals, times = ["0,0"], [0.0]
        for bk in bonks:
            vals += ["0,0", "0,-18", "0,3", "0,0"]
            times += [bk, bk + 0.12, bk + 0.26, bk + bump_len]
        vals.append("0,0"); times.append(T)
        lv, lk = _keys(vals, times, T)
        lift = (f'<animateTransform attributeName="transform" type="translate"'
                f' dur="{T}s" repeatCount="indefinite" values="{lv}" keyTimes="{lk}"/>')
    button = (f'<g transform="translate({PLAY_BTN_CX:.1f} {PLAY_BTN_CY:.1f})">'
              f'<g>{lift}{glow}{bumps}</g></g>')
    coins = "".join(pop_coin(PLAY_BTN_CX, PLAY_BTN_CY - PLAY_BTN_H / 2 - 10, bk, T, r=18.0)
                    for bk in bonks)
    # six leaf coins orbit the block on a tilted ring; the front half of the
    # ring is drawn again over the block so they pass in front of it
    ORX, ORY, OPER = 200.0, 44.0, 7.0
    ring_path = (f"M {-ORX:.0f},0 a {ORX:.0f},{ORY:.0f} 0 1,0 {2 * ORX:.0f},0"
                 f" a {ORX:.0f},{ORY:.0f} 0 1,0 {-2 * ORX:.0f},0")
    orbit = "".join(
        f'<g><animateMotion path="{ring_path}" dur="{OPER}s" repeatCount="indefinite"'
        f' begin="{-k * OPER / 6:.2f}s"/>{coin_spin(1.6 + (k % 3) * 0.2, k * 0.17, 15.0)}</g>'
        for k in range(6))
    ocy = PLAY_BTN_CY + 8
    ring = (f'<ellipse cx="{PLAY_BTN_CX}" cy="{ocy}" rx="{ORX}" ry="{ORY}" fill="none"'
            f' stroke="#20D898" stroke-opacity=".14" stroke-width="2" stroke-dasharray="4 10"/>')
    orbit_back = f'<g transform="translate({PLAY_BTN_CX} {ocy})">{orbit}</g>'
    orbit_front = (f'<clipPath id="orbitFront"><rect x="{PLAY_BTN_CX - ORX - 40}" y="{ocy}"'
                   f' width="{2 * ORX + 80}" height="{ORY + 40}"/></clipPath>'
                   f'<g clip-path="url(#orbitFront)">{orbit_back}</g>')

    # minimal space: a faint nebula, two drifting star layers, a ringed
    # planet low on the right, a shooting star now and then
    srnd = random.Random(11)
    def star_layer(n, sizes, drift):
        out = ""
        for k in range(n):
            x, y = srnd.uniform(0, W), srnd.uniform(py0 + 10, GROUND - 30)
            sz = srnd.choice(sizes)
            d = srnd.uniform(1.8, 4.2)
            for dx in (0, W):     # two copies so the drift wraps seamlessly
                out += (f'<rect x="{px0 + x + dx:.0f}" y="{y:.0f}" width="{sz}" height="{sz}"'
                        f' fill="#CFEAE3" opacity=".5"><animate attributeName="opacity"'
                        f' values=".15;.75;.15" dur="{d:.1f}s" begin="{-srnd.uniform(0, d):.1f}s"'
                        f' repeatCount="indefinite"/></rect>')
        return (f'<g><animateTransform attributeName="transform" type="translate"'
                f' values="0 0;{-W} 0" dur="{drift}s" repeatCount="indefinite"/>{out}</g>')
    stars = star_layer(40, [2, 2, 3], 160) + star_layer(14, [3, 4], 70)
    sky = (f'<defs><radialGradient id="neb1"><stop offset="0" stop-color="#20D898" stop-opacity=".10"/>'
           f'<stop offset="1" stop-color="#20D898" stop-opacity="0"/></radialGradient>'
           f'<radialGradient id="neb2"><stop offset="0" stop-color="#7B6CF6" stop-opacity=".09"/>'
           f'<stop offset="1" stop-color="#7B6CF6" stop-opacity="0"/></radialGradient>'
           f'<radialGradient id="planet" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#1E6B66"/>'
           f'<stop offset=".6" stop-color="#0E3A40"/><stop offset="1" stop-color="#081420"/></radialGradient>'
           f'<radialGradient id="halo"><stop offset="0" stop-color="#20D898" stop-opacity=".22"/>'
           f'<stop offset="1" stop-color="#20D898" stop-opacity="0"/></radialGradient>'
           f'<linearGradient id="streak" x1="0" x2="1"><stop offset="0" stop-color="#CFEAE3" stop-opacity="0"/>'
           f'<stop offset="1" stop-color="#CFEAE3" stop-opacity=".9"/></linearGradient></defs>'
           f'<ellipse cx="{px0 + W * 0.28}" cy="{py0 + 150}" rx="520" ry="210" fill="url(#neb2)"/>'
           f'<ellipse cx="{px0 + W * 0.72}" cy="{py0 + 260}" rx="560" ry="230" fill="url(#neb1)"/>'
           + stars
           + planets(px0 + W * 0.86, py0 + 175, T) +
           # a small moon on the left
           f'<circle cx="{px0 + W * 0.12:.0f}" cy="{py0 + 110}" r="16" fill="#12404A"/>'
           f'<circle cx="{px0 + W * 0.12 - 5:.0f}" cy="{py0 + 105}" r="16" fill="#081420" opacity=".55"/>')
    for k, (sx, sy, beg) in enumerate([(0.62, 60, 1.0), (0.30, 120, 4.2)]):
        x0s, y0s = px0 + W * sx, py0 + sy
        sky += (f'<g opacity="0"><animate attributeName="opacity" values="0;1;0;0"'
                f' keyTimes="0;.05;.14;1" dur="6.5s" begin="{beg}s" repeatCount="indefinite"/>'
                f'<g><animateTransform attributeName="transform" type="translate"'
                f' values="{x0s:.0f} {y0s};{x0s - 260:.0f} {y0s + 90};{x0s - 260:.0f} {y0s + 90}"'
                f' keyTimes="0;.14;1" dur="6.5s" begin="{beg}s" repeatCount="indefinite"/>'
                f'<rect x="0" y="-1.5" width="120" height="3" rx="1.5" fill="url(#streak)"'
                f' transform="rotate(160)"/></g></g>')
    halo = (f'<ellipse cx="{PLAY_BTN_CX}" cy="{PLAY_BTN_CY}" rx="170" ry="150" fill="url(#halo)">'
            f'<animate attributeName="opacity" values=".7;1;.7" dur="2.6s" repeatCount="indefinite"/></ellipse>')

    # her, under the block, running on the spot and jumping to bonk it
    G = 2.0 * LIFT_MAX / (JD_MAX / 2.0) ** 2
    head = GROUND - GIRL_TARGET_H
    clear = max(30.0, head - (PLAY_BTN_CY + PLAY_BTN_H / 2))
    v0 = math.sqrt(2.0 * G * (clear + 8.0))
    v_hit = math.sqrt(max(0.0, v0 * v0 - 2.0 * G * clear))
    t_up, t_down = (v0 - v_hit) / G, math.sqrt(2.0 * clear / G)
    jumps, samples = [], [(0.0, 0.0)]
    for bk in bonks:
        t0 = bk - t_up
        jumps.append({"t0": t0, "hit": bk, "t1": bk + t_down, "t_up": t_up,
                      "t_down": t_down, "resume": bk + t_down + 0.14})
        samples.append((t0, 0.0))
        for i in range(1, 9):
            dt = t_up * i / 8
            samples.append((t0 + dt, v0 * dt - 0.5 * G * dt * dt))
        for i in range(1, 9):
            dt = t_down * i / 8
            samples.append((bk + dt, clear - 0.5 * G * dt * dt))
    samples.append((T, 0.0))
    jv, jk = _keys([f"0,{-y:.2f}" for _, y in samples], [t for t, _ in samples], T)
    her = (f'<g transform="translate({PLAY_BTN_CX:.1f} {GROUND:.1f})">'
           f'<ellipse cx="0" cy="-4" rx="34" ry="7" fill="#000" fill-opacity=".35"/>'
           f'<g><animateTransform attributeName="transform" type="translate" dur="{T}s"'
           f' repeatCount="indefinite" calcMode="linear" values="{jv}" keyTimes="{jk}"/>'
           f'{girl_runner(jumps, T)}</g></g>')
    # the ground slides under her so running on the spot reads as running
    stripes = "".join(f'<rect x="{x}" y="{GROUND + 6}" width="2" height="{py1 - GROUND - 6}"'
                      f' fill="#07202A"/>' for x in range(int(px0), int(px1) + 148, 74))
    ground = (f'<rect x="{px0}" y="{GROUND}" width="{W}" height="{py1 - GROUND}" fill="#0B2A33"/>'
              f'<rect x="{px0}" y="{GROUND}" width="{W}" height="6" fill="#3CEDA5"/>'
              f'<g><animateTransform attributeName="transform" type="translate"'
              f' values="0 0;-74 0" dur="{74.0 / RUN_SPEED:.3f}s" repeatCount="indefinite"/>'
              f'{stripes}</g>')
    # The story dissolves behind the gust: a soft-edged wipe follows the
    # leaves from right to left and leaves the empty space sky behind.
    SOFT = 380.0
    wv, wk = _keys([f"{px1 + 40:.0f} 0", f"{px1 + 40:.0f} 0", f"{px0 - SOFT - 40:.0f} 0",
                    f"{px0 - SOFT - 40:.0f} 0"],
                   [0.0, t_cut + 0.25, t_cut + OUTRO_WIPE - 0.35, T], T)
    wipe = (f'<linearGradient id="wipeEdge" x1="0" x2="1"><stop offset="0" stop-color="#000"/>'
            f'<stop offset="1" stop-color="#fff"/></linearGradient>'
            f'<mask id="outroWipe" maskUnits="userSpaceOnUse" x="{px0 - 10}" y="{py0 - 10}"'
            f' width="{W + 20}" height="{H + 20}"><g>'
            f'<animateTransform attributeName="transform" type="translate" dur="{T}s"'
            f' repeatCount="indefinite" calcMode="spline" values="{wv}" keyTimes="{wk}"'
            f' keySplines="0 0 1 1;.45 0 .55 1;0 0 1 1"/>'
            f'<rect x="0" y="{py0 - 10}" width="{SOFT:.0f}" height="{H + 20}" fill="url(#wipeEdge)"/>'
            f'<rect x="{SOFT:.0f}" y="{py0 - 10}" width="{W + 200}" height="{H + 20}" fill="#fff"/>'
            f'</g></mask>')
    backdrop = (f'<g mask="url(#outroWipe)">'
                f'<rect x="{px0}" y="{py0}" width="{W}" height="{H}" fill="#081420"/>{sky}{ground}</g>')
    play_layer = f'{halo}{ring}{orbit_back}{coins}{button}{orbit_front}{her}'
    screen = wipe + backdrop      # the play layer is added with the hero leaf below

    # ---- the gust: leaves on curved, swirling paths, with depth ----
    # Near leaves are big, fast and bright; far ones small, slow and dim. The
    # gust is a year going by: the first leaves in are spring green, the last
    # ones dry brown.
    lives = [_tumble_leaf(70.0, r) for r in TUMBLE_LIFE]
    specs = []
    for i in range(48):
        d = rnd.random()                          # depth: 0 far .. 1 near
        a = t_cut + rnd.uniform(0.0, 2.0)
        dur = 4.6 - 1.6 * d + rnd.uniform(-0.2, 0.2)
        specs.append((d, a, dur, i))
    specs.sort()                                  # far leaves are drawn first
    leaves = ""
    for d, a, dur, i in specs:
        z = a + dur
        y0 = py0 + rnd.uniform(-20, H + 20)
        y1 = y0 + rnd.uniform(-160, 120)
        x_a, x_z = px1 + 120, px0 - 220
        amp = rnd.uniform(60, 190) * (1 if i % 2 else -1)
        path = (f"M {x_a:.0f},{y0:.0f} C {x_a - W * 0.35:.0f},{y0 - amp:.0f}"
                f" {x_z + W * 0.35:.0f},{y1 + amp:.0f} {x_z:.0f},{y1:.0f}")
        if i % 6 == 0:                            # some get caught in a little eddy
            mx, my = px0 + W * rnd.uniform(0.35, 0.7), y0 + amp * 0.3
            r = rnd.uniform(40, 80)
            path = (f"M {x_a:.0f},{y0:.0f} Q {(x_a + mx) / 2:.0f},{y0 - amp:.0f} {mx:.0f},{my:.0f}"
                    f" a {r:.0f},{r:.0f} 0 1,1 0,{2 * r:.0f} a {r:.0f},{r:.0f} 0 1,1 0,{-2 * r:.0f}"
                    f" Q {(mx + x_z) / 2:.0f},{my + amp:.0f} {x_z:.0f},{y1:.0f}")
        kt = f"0;{a / T:.5f};{min(z, T - 0.01) / T:.5f};1"
        stage = min(len(lives) - 1, int((a - t_cut) / 2.0 * len(lives)))
        frames = lives[stage]
        k = i % len(frames)
        spin = flipbook(frames[k:] + frames[:k], rnd.uniform(1.2, 1.7))
        size = 0.55 + 0.95 * d
        leaves += _ep_shown(
            f'<g opacity="{0.45 + 0.55 * d:.2f}"><animateMotion path="{path}" dur="{T}s"'
            f' repeatCount="indefinite" calcMode="linear" keyPoints="0;0;1;1" keyTimes="{kt}"/>'
            f'<g transform="scale({size:.2f}) rotate({rnd.uniform(-30, 30):.0f})">{spin}</g></g>',
            [(a, z)], T)

    # ---- the hero leaf: one leaf comes out of the gust towards the camera ----
    # It drifts to the middle tumbling and turns face on. Then it grows, and as
    # it grows it turns into a window: the play screen shows inside its
    # outline, so the leaf "opens" onto the next scene until it fills it.
    # Each loop it is a different colour, cycling through the leaf's year.
    cx, cy = px0 + W / 2, py0 + H / 2
    h_in, h_mid, h_grow = t_cut + 0.6, t_cut + 2.6, t_cut + 3.3
    # its tumble reuses the gust's small frames; only its face-on frame, the
    # one that grows, is stored larger (the file has a size budget)
    looks = []
    for li, row in enumerate(TUMBLE_LIFE):
        fr = _strip_frames("heroface", TUMBLE_SHEET_PATH, TUMBLE_CELL, 1, row, max_px=160)
        small = _tumble_leaf(80.0, row)
        if fr and small:
            ref = max(f[2] for f in _strip_frames("tumble", TUMBLE_SHEET_PATH, TUMBLE_CELL, 8, row, max_px=72))
            looks.append(small[1:] + [_strip_use(fr[0], 80.0, TUMBLE_CELL, ref)])
    if not looks:
        looks = [lives[1]]
    sil = _strip_frames("heroshape", TUMBLE_SHEET_PATH, TUMBLE_CELL, 1, 0, max_px=160)
    shape = (_strip_use(sil[0], 80.0, TUMBLE_CELL, max(f[2] for f in sil)) if sil
             else looks[0][0])
    # path: in from the upper right, curving to the centre, then still
    mv, mk = _keys([f"{px1 + 100:.0f},{py0 + 60:.0f}", f"{px1 + 100:.0f},{py0 + 60:.0f}",
                    f"{px0 + W * 0.75:.0f},{py0 + 40:.0f}", f"{cx:.0f},{cy:.0f}",
                    f"{cx:.0f},{cy:.0f}"],
                   [0.0, h_in, (h_in + h_mid) / 2, h_mid, T], T)
    # size: a smooth ease-in zoom that reaches full cover at t_switch
    COVER = 70.0
    sv, st = ["1 1", "1 1"], [0.0, h_grow]
    n = 18
    for j in range(1, n + 1):
        f = j / n
        e = f * f * (3 - 2 * f)                     # smoothstep, so it eases in and out
        k = math.exp(math.log(COVER) * e)
        sv.append(f"{k:.3f} {k:.3f}")
        st.append(h_grow + (t_switch - h_grow) * f)
    sv += [f"{COVER:.1f} {COVER:.1f}"]
    st += [T]
    sv_, sk_ = _keys(sv, st, T)
    rv, rk = _keys(["0", "0", "-20", "-20"], [0.0, h_grow, t_switch, T], T)

    def carried(inner):
        return (f'<g><animateTransform attributeName="transform" type="translate" dur="{T}s"'
                f' repeatCount="indefinite" calcMode="spline" values="{mv}" keyTimes="{mk}"'
                f' keySplines="0 0 1 1;.4 0 .6 1;.4 0 .6 1;0 0 1 1"/>'
                f'<g><animateTransform attributeName="transform" type="scale" dur="{T}s"'
                f' repeatCount="indefinite" calcMode="linear" values="{sv_}" keyTimes="{sk_}"/>'
                f'<g><animateTransform attributeName="transform" type="rotate" dur="{T}s"'
                f' repeatCount="indefinite" calcMode="linear" values="{rv}" keyTimes="{rk}"/>'
                f'{inner}</g></g></g>')

    # the window: an alpha mask in the leaf's shape, then the whole panel
    mon, mok = _keys(["0", "0", "1", "1"], [0.0, h_grow, h_grow + 0.01, T], T)
    full, fk = _keys(["0", "0", "1", "1"], [0.0, t_switch, t_switch + 0.01, T], T)
    window_mask = (f'<mask id="leafWindow" mask-type="alpha" maskUnits="userSpaceOnUse"'
                   f' x="{px0 - 10}" y="{py0 - 10}" width="{W + 20}" height="{H + 20}">'
                   f'<g opacity="0"><animate attributeName="opacity" dur="{T}s" repeatCount="indefinite"'
                   f' calcMode="discrete" values="{mon}" keyTimes="{mok}"/>{carried(shape)}</g>'
                   f'<rect x="{px0 - 10}" y="{py0 - 10}" width="{W + 20}" height="{H + 20}" fill="#fff"'
                   f' opacity="0"><animate attributeName="opacity" dur="{T}s" repeatCount="indefinite"'
                   f' calcMode="discrete" values="{full}" keyTimes="{fk}"/></rect></mask>')
    through = (f'<g mask="url(#leafWindow)"><rect x="{px0}" y="{py0}" width="{W}" height="{H}"'
               f' fill="#081420"/>{sky}{ground}{play_layer}</g>')

    # the visible leaf: tumbling in, then its colour melts away into the window
    vo, vk = _keys(["0", "0", "1", "1", "0", "0"],
                   [0.0, h_in, h_in + 0.3, h_grow + 0.3, h_grow + 0.9, T], T)
    coloured = [sequence([flipbook(lk[:-1], 1.4)], h_in, h_grow, T) + sequence([lk[-1]], h_grow, T, T)
                for lk in looks]
    visible = (f'<g opacity="0"><animate attributeName="opacity" dur="{T}s" repeatCount="indefinite"'
               f' calcMode="linear" values="{vo}" keyTimes="{vk}"/>'
               f'{carried(per_loop(coloured, T))}</g>')
    # a thin glowing rim keeps the leaf's outline readable while it opens
    rim = (f'<g opacity="0"><animate attributeName="opacity" dur="{T}s" repeatCount="indefinite"'
           f' calcMode="linear" values="0;0;.9;.9;0;0"'
           f' keyTimes="{";".join(f"{x / T:.5f}" for x in [0, h_grow + 0.3, h_grow + 0.8, t_switch - 0.5, t_switch, T])}"/>'
           f'<g filter="url(#leafRim)">{carried(shape)}</g></g>')
    # outline only: the leaf's shape grown by a few units, minus the shape
    rim = ('<filter id="leafRim" x="-5%" y="-5%" width="110%" height="110%">'
           '<feMorphology in="SourceAlpha" operator="dilate" radius="4" result="grow"/>'
           '<feComposite in="grow" in2="SourceAlpha" operator="out" result="ring"/>'
           '<feFlood flood-color="#9BEFD9"/><feComposite in2="ring" operator="in" result="line"/>'
           '<feGaussianBlur in="line" stdDeviation="3" result="glow"/>'
           '<feMerge><feMergeNode in="glow"/><feMergeNode in="line"/></feMerge></filter>') + rim
    screen += window_mask + through
    leaves += rim + visible

    return (f'<g opacity="0"><animate attributeName="opacity" dur="{T}s"'
            f' repeatCount="indefinite" calcMode="linear" values="{fade_v}"'
            f' keyTimes="{fade_k}"/>{screen}{leaves}</g>')


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


def _bc_frames():
    """Block and coin frames from their sheet, registered as sprites.

    Returns {"blk0".."blk2", "coin0".."coin3": (fid, w, h)}, or {} when the
    sheet is missing (the drawn fallbacks are used then).
    """
    global _BC
    if _BC is not None:
        return _BC
    _BC = {}
    try:
        import base64, io
        from PIL import Image
        src = Image.open(BLOCKCOIN_SHEET_PATH).convert("RGBA")
    except Exception as exc:
        print("block/coin sheet skipped:", exc)
        return _BC
    C = BLOCKCOIN_CELL
    for name, row, n in (("blk", 0, 3), ("coin", 1, 4)):
        for i in range(n):
            cell = src.crop((i * C, row * C, (i + 1) * C, (row + 1) * C))
            box = cell.getbbox()
            if box is None:
                continue
            img = cell.crop(box)
            buf = io.BytesIO()
            img.save(buf, "PNG", optimize=True)
            fid = f"bc-{name}{i}"
            _USED[fid] = ("data:image/png;base64," +
                          base64.b64encode(buf.getvalue()).decode(), img.width, img.height)
            _BC[f"{name}{i}"] = (fid, img.width, img.height)
    return _BC


def _bc_use(key, height):
    """One block/coin frame centred on the origin, `height` units tall."""
    fid, w, h = _bc_frames()[key]
    k = height / h
    return (f'<use xlink:href="#sp-{fid}" transform="translate({-w * k / 2:.2f}'
            f' {-height / 2:.2f}) scale({k:.4f})"/>')


def coin_face(r):
    # One coin, centred on the origin. Drawn only if the coin sheet is missing.
    return (f'<circle r="{r * 1.8:.1f}" fill="url(#coinHalo)"/>'
            f'<circle r="{r:.1f}" fill="url(#coinG)" stroke="#8A5A12"'
            f' stroke-width="{r * 0.17:.2f}"/>')


def coin_spin(dur, begin=0.0, r=COIN_R):
    """The leaf coin: faces the viewer most of the cycle, then turns once."""
    if "coin0" not in _bc_frames():
        return (f'<g>{coin_face(r)}<animateTransform attributeName="transform"'
                f' type="scale" values="1 1;1 1;0.22 1;1 1;1 1"'
                f' keyTimes="0;0.34;0.5;0.66;1"'
                f' dur="{dur:.2f}s" begin="{begin:.2f}s"'
                f' repeatCount="indefinite"/></g>')
    frames = [_bc_use(f"coin{i}", r * 2.0) for i in range(4)]
    # start each coin on a different frame so a row of them is not in lockstep
    shift = int(begin * 7) % 4
    order = frames[shift:] + frames[:shift]
    weights = [3.0, 1.0, 1.0, 1.0][shift:] + [3.0, 1.0, 1.0, 1.0][:shift]
    return (f'<circle r="{r * 1.8:.1f}" fill="url(#coinHalo)"/>'
            + flipbook(order, dur, weights=weights))


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
    # A commit square she can headbutt: the </> block, which bumps up on
    # impact, flashes, then reads as spent before fading back into the grid.
    bv, bk = _keys(["0,0", "0,0", "0,-15", "0,4", "0,0", "0,0"],
                   [0.0, t, t + 0.12, t + 0.34, t + 0.52, T], T)
    ov, ok = _keys(["1", "1", "0", "0", "1"],
                   [0.0, t + 1.4, t + 2.0, T - 0.6, T], T)
    frames = _bc_frames()
    if "blk0" in frames:
        def shown(key, vals, times):
            v, k = _keys(vals, times, T)
            return (f'<g><animate attributeName="opacity" dur="{T}s"'
                    f' repeatCount="indefinite" calcMode="discrete"'
                    f' values="{v}" keyTimes="{k}"/>{_bc_use(key, size)}</g>')
        face = (shown("blk0", ["1", "1", "0", "0"], [0.0, t, t, T])
                + shown("blk1", ["0", "0", "1", "0", "0"], [0.0, t, t, t + 0.3, T])
                + shown("blk2", ["0", "0", "1", "1"], [0.0, t + 0.3, t + 0.3, T]))
    else:
        h = size / 2
        face = (f'<rect x="{-h:.1f}" y="{-h:.1f}" width="{size:.1f}"'
                f' height="{size:.1f}" rx="5" fill="#18A088"/>')
    return (f'<g transform="translate({cx:.1f} {cy:.1f})"><g>'
            f'<animate attributeName="opacity" dur="{T}s" repeatCount="indefinite"'
            f' values="{ov}" keyTimes="{ok}"/>'
            f'<animateTransform attributeName="transform" type="translate"'
            f' dur="{T}s" repeatCount="indefinite" values="{bv}"'
            f' keyTimes="{bk}"/>{face}</g></g>')


# ---------------------------------------------------------------- her, from the supplied avatar
AVATAR_SHEET_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "..", "assets", "runner-avatar-sheet-v9.png")
AVATAR_COLS, AVATAR_ROWS = 4, 4
AVATAR_CELL = 362.0
AVATAR_SCALE = GIRL_TARGET_H / AVATAR_CELL
RUN_LIMB_SPLIT_Y = 270
_AVATAR = None

# v9 sheet: the shoes are about 152 source px apart at contact, and one run
# cycle is two steps (one per leg).
RUN_STEP = 152.0 * AVATAR_SCALE
# The run, in the order the sheet holds it. The near leg is the one with the
# cream stripe; the near arm is the one whose sleeve lies over the hoodie, and
# it always swings opposite to the near leg.
#   0 near leg forward (widest), near fist behind her hip
#   1 near leg forward, legs closing, near hand at her side
#   2 passing: near leg under her, FAR knee coming forward
#   3 far leg forward (widest), near fist in front of her chest
#   4 far leg forward, legs closing, near fist still in front
#   5 passing: far leg under her, NEAR knee coming forward
#   6 near leg reaching forward, near fist swinging back
# Before using any new sheet, check every frame for which leg and which arm is
# forward, and order them as above: GPT returned these as 1,2,7,4,5,3,8 with
# the two passing frames swapped, which made the legs jump once per stride.
# Slot 7 is a spare near-leg-forward pose and is not used.
# Near-leg stance is frames 6,0,1 plus passing 2 (four frames); far-leg stance
# is 3,4 plus passing 5 (three), so those three are held 4/3 as long.
RUN_ORDER = [0, 1, 2, 3, 4, 5, 6]
RUN_WEIGHTS = [1.0, 1.0, 1.0, 4 / 3, 4 / 3, 4 / 3, 1.0]
RUN_CYCLE = 2.0 * RUN_STEP / RUN_SPEED
assert math.isclose(RUN_SPEED * RUN_CYCLE, 2.0 * RUN_STEP,
                    rel_tol=1e-12, abs_tol=1e-12)


def avatar_frames():
    """Cut the supplied-character pose sheet into foot-anchored SVG images."""
    global _AVATAR
    if _AVATAR is not None:
        return _AVATAR
    _AVATAR = []
    try:
        import base64, io
        from PIL import Image, ImageChops, ImageOps
        src = Image.open(AVATAR_SHEET_PATH).convert("RGBA")
    except Exception as exc:
        print("avatar skipped:", exc)
        return _AVATAR

    cw, ch = src.width // AVATAR_COLS, src.height // AVATAR_ROWS
    if cw * AVATAR_COLS != src.width or ch * AVATAR_ROWS != src.height:
        raise ValueError("runner avatar sheet must contain equal 4x4 cells")
    if cw != int(AVATAR_CELL) or ch != int(AVATAR_CELL):
        raise ValueError(f"runner avatar cells must be {int(AVATAR_CELL)}px square")

    # Consecutive run frames must never be identical, or that leg would hang.
    for a, b in zip(RUN_ORDER, RUN_ORDER[1:] + RUN_ORDER[:1]):
        fa = src.crop(((a % 4) * cw, (a // 4) * ch, (a % 4 + 1) * cw, (a // 4 + 1) * ch))
        fb = src.crop(((b % 4) * cw, (b // 4) * ch, (b % 4 + 1) * cw, (b // 4 + 1) * ch))
        if ImageChops.difference(fa, fb).getbbox() is None:
            raise ValueError(f"runner frames {a} and {b} are identical")

    for i in range(AVATAR_COLS * AVATAR_ROWS):
        col, row = i % AVATAR_COLS, i // AVATAR_COLS
        cell = src.crop((col * cw, row * ch, (col + 1) * cw, (row + 1) * ch))
        box = cell.getchannel("A").getbbox()
        if box is None:
            raise ValueError(f"runner avatar frame {i} is empty")
        x0, y0 = max(0, box[0] - 2), max(0, box[1] - 2)
        x1, y1 = min(cw, box[2] + 2), min(ch, box[3] + 2)
        crop = cell.crop((x0, y0, x1, y1))
        flat = crop.convert("RGB").quantize(
            colors=160, method=Image.Quantize.FASTOCTREE).convert("RGBA")
        flat.putalpha(crop.getchannel("A"))
        buf = io.BytesIO()
        flat.save(buf, "PNG", optimize=True)
        fid = f"avatar{i}"
        _USED[fid] = ("data:image/png;base64," +
                      base64.b64encode(buf.getvalue()).decode(), crop.width, crop.height)
        centre = ((box[0] + box[2]) / 2.0) - x0
        feet = box[3] - y0
        _AVATAR.append((fid, crop.width, crop.height, centre, feet))
    return _AVATAR


def avatar_frame(i, baseline):
    """One pose centred on x=0 with its lowest visible pixel on the baseline."""
    got = avatar_frames()
    if not got:
        return ""
    fid, _, _, centre, feet = got[i]
    return (f'<use xlink:href="#sp-{fid}" style="image-rendering:auto"'
            f' transform="translate({-centre * AVATAR_SCALE:.3f}'
            f' {baseline - feet * AVATAR_SCALE:.3f}) scale({AVATAR_SCALE:.6f})"/>')


def avatar_run(cycle, baseline):
    """One full stride per leg, in RUN_ORDER (see the notes above it)."""
    return flipbook([avatar_frame(i, baseline) for i in RUN_ORDER], cycle,
                    weights=RUN_WEIGHTS)


# v9 sheet: 9 rising with an arm up, 10 the head-butt (held across the moment
# of impact so the hit reads clearly), 11 falling, 12 the landing squash.
AIR_POSES = [9, 10, 10, 11, 11, 11, 12]


def girl_runner(jumps, T, baseline=6.0):
    """Her whole flipbook, built rather than cut: a walk whose legs genuinely
    alternate, with the jump held over the top of it for each square she opens."""
    wins = [(j["t0"], j["resume"]) for j in jumps]
    run = bob(avatar_run(RUN_CYCLE, baseline), RUN_CYCLE / 2.0, RUN_BOUNCE)
    air = ""
    for jump in jumps:
        t0, hit, t1, resume = (jump[k] for k in ("t0", "hit", "t1", "resume"))
        rise_reach = t0 + jump["t_up"] * 0.42
        fall_tuck = hit + jump["t_down"] * 0.16
        fall_open = hit + jump["t_down"] * 0.42
        fall_extend = hit + jump["t_down"] * 0.72
        edges = [t0, rise_reach, hit, fall_tuck, fall_open,
                 fall_extend, t1, resume]
        for pose, a, b in zip(jump.get("poses", AIR_POSES), edges, edges[1:]):
            air += sequence([avatar_frame(pose, baseline)], a, b, T)
    return gate(run, wins, T) + air


# ---------------------------------------------------------------- timed visibility helpers
def _ep_windows(intervals, T):
    """Discrete 0/1 opacity values+keyTimes: visible inside the intervals (mod T)."""
    marks = []
    for a, b in intervals:
        a, b = a % T, b % T
        if a <= b:
            marks.append((a, b))
        else:
            marks += [(0.0, b), (a, T)]
    marks.sort()
    times, vals = [0.0], ["0"]
    for a, b in marks:
        times += [a, b]
        vals += ["1", "0"]
    times.append(T)
    vals.append(vals[-1])
    return _keys(vals, times, T)


def _ep_shown(svg, intervals, T):
    v, k = _ep_windows(intervals, T)
    return (f'<g opacity="0"><animate attributeName="opacity" dur="{T:.3f}s"'
            f' repeatCount="indefinite" calcMode="discrete" values="{v}"'
            f' keyTimes="{k}"/>{svg}</g>')



if __name__ == "__main__":
    data = collect()
    try:
        g = graph()
    except Exception as exc:                 # never fail the whole build on one API hiccup
        print("graphql skipped:", exc)
        g = {}
    out_dir = os.path.dirname(OUT) or "."
    os.makedirs(out_dir, exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(build(data, g))
    # One file per project, because the README wraps each in its own link.
    cards = build_project_cards(data["index"])
    for name, svg in cards.items():
        open(os.path.join(out_dir, name), "w", encoding="utf-8").write(svg)
    # ...and the same nine inlined into a page, where the arcs are elements.
    open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8").write(
        build_pages(data["index"], cards))
    # The ring is silent; the languages ride in the card's own tooltip.
    _write_readme_titles(data["index"])
    if g.get("weeks"):
        # Every sprite revision gets a fresh URL so GitHub's image proxy cannot
        # keep serving a superseded gait after the output branch is rebuilt.
        open(os.path.join(out_dir, "runner-v27.svg"), "w", encoding="utf-8").write(
            build_runner_panel(g["weeks"], total=g.get("contributions")))
        print("wrote runner-v27.svg")
    else:
        print("no calendar data - runner panel skipped")
    # The playable game, served by Pages at /play/: the page, the art it
    # draws with, and her contribution levels for it to build the world from.
    import shutil
    play = os.path.join(out_dir, "play")
    os.makedirs(os.path.join(play, "assets"), exist_ok=True)
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    shutil.copy(os.path.join(root, "game", "index.html"), os.path.join(play, "index.html"))
    for name in ("runner-avatar-sheet-v9.png", "turtle-sheet-v1.png", "snake-sheet-v1.png",
                 "leaf-sheet-v1.png", "blockcoin-sheet-v1.png"):
        shutil.copy(os.path.join(_ASSETS, name), os.path.join(play, "assets", name))
    if g.get("weeks"):
        json.dump({"levels": _levels(g["weeks"])},
                  open(os.path.join(play, "contrib.json"), "w"))
    print("wrote play/")
    print("panels:", data["repos"], "repos,", data["deployed"], "live,", g.get("contributions"), "contributions")
