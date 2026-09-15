#!/usr/bin/env python3
"""Builds an arcade-style HIGH SCORES panel (dist/stats.svg) from live GitHub data."""
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
      contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount } } }
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
    return {
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
  <path d="M500 58c-4 7 2 9 0 14-3-2-9 3-4 9 3 4 10 4 12-1 2-5-4-8-4-13 0-3-2-6-4-9z" fill="#9BE7C4">
    <animate attributeName="opacity" values="1;.45;1" dur="2.4s" repeatCount="indefinite"/>
  </path>
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


SNAKE_PALETTE = {
    "--cb": "#0e1a1f",      # cell border
    "--cs": "#C4A8FF",      # the snake, violet so it reads over the grid
    "--ce": "#0c171c",      # empty cell
    "--c0": "#0c171c",
    "--c1": "#1b5f4f",      # contribution ramp: teal -> mint -> cyan
    "--c2": "#2b9a7a",
    "--c3": "#56D6A8",
    "--c4": "#8FE9F5",
}


def build_snake_panel(src_path, out_path):
    """Recolour the generated snake and sit it inside a matching terminal panel."""
    import re
    svg = open(src_path).read()

    def repalette(m):
        return "".join(f"{k}:{v};" for k, v in SNAKE_PALETTE.items()).rstrip(";")
    svg = re.sub(r"(?<=:root\{)[^}]*", repalette, svg, count=1)
    # a soft glow on the snake body and rounder cells
    extra = (".s{filter:drop-shadow(0 0 4px #C4A8FF) drop-shadow(0 0 9px rgba(196,168,255,.45))}"
             ".c{rx:3.5px;ry:3.5px}"
             ".c.c3,.c.c4{filter:drop-shadow(0 0 3px rgba(143,233,245,.55))}")
    svg = svg.replace("</style>", extra + "</style>", 1)

    head = re.match(r"<svg[^>]*>", svg).group(0)
    vw = float(re.search(r'width="([0-9.]+)"', head).group(1))
    vh = float(re.search(r'height="([0-9.]+)"', head).group(1))

    W = 1000
    inner_w = W - 64
    k = inner_w / vw
    inner_h = (vh - 34) * k
    H = int(inner_h + 52)

    inner = re.sub(r"^<svg[^>]*>", "", svg, count=1)[: -len("</svg>")]
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', head).group(1).split()]
    vb[3] -= 34                      # the source leaves an empty band under the grid
    view = " ".join(f"{v:g}" for v in vb)

    panel = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="contribution snake">
<defs>
  <linearGradient id="sbg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#04070a"/><stop offset="60%" stop-color="#060e12"/><stop offset="100%" stop-color="#04090c"/>
  </linearGradient>
  <radialGradient id="sglow"><stop offset="0%" stop-color="#9BE7C4" stop-opacity=".12"/><stop offset="100%" stop-color="#9BE7C4" stop-opacity="0"/></radialGradient>
  <pattern id="sscan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#7fffd4" fill-opacity=".028"/></pattern>
  <clipPath id="swin"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14"/></clipPath>
</defs>
<style>.smono {{ font-family: ui-monospace, "SF Mono", "JetBrains Mono", Consolas, monospace; }}
  .spulse {{ animation: spulse 3.6s ease-in-out infinite; }}
  @keyframes spulse {{ 0%,100% {{ opacity: .45 }} 50% {{ opacity: 1 }} }}</style>
<rect width="{W}" height="{H}" rx="14" fill="url(#sbg)"/>
<ellipse cx="500" cy="{H}" rx="520" ry="200" fill="url(#sglow)"/>
<svg x="32" y="26" width="{inner_w}" height="{inner_h:.0f}" viewBox="{view}" preserveAspectRatio="xMidYMid meet">
{inner}
</svg>
<g clip-path="url(#swin)"><rect width="{W}" height="{H}" fill="url(#sscan)"/></g>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="none" stroke="#9BE7C4" stroke-opacity=".26"/>
</svg>
'''
    open(out_path, "w").write(panel)
    return W, H


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
    for src, dst in (("snake-dark.svg", "snake-panel-v2.svg"),):
        p = os.path.join(out_dir, src)
        if os.path.exists(p):
            build_snake_panel(p, os.path.join(out_dir, dst))
            print("wrote", dst)
    print("panels:", data["repos"], "repos,", data["deployed"], "live,", g.get("contributions"), "contributions")
