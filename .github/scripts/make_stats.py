#!/usr/bin/env python3
"""Builds an arcade-style HIGH SCORES panel (dist/stats.svg) from live GitHub data."""
import json
import os
import urllib.request

USER = "ananya-goswami"
OUT = os.environ.get("STATS_OUT", "dist/stats.svg")
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


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(d):
    W, H = 1000, 300
    langs = d["langs"]
    rows = [
        ("PUBLIC REPOS", str(d["repos"])),
        ("LIVE BUILDS", str(d["deployed"])),
        ("CLASSES SERVED", "6 to 9"),
        ("LANGUAGES", "hi / en, bilingual by default"),
    ]
    body, y = "", 96
    for label, val in rows:
        dots = "." * max(2, 26 - len(label))
        body += (f'<text class="mono" x="34" y="{y}" font-size="14.5" fill="#4e6b66" xml:space="preserve">'
                 f'{label} {dots} <tspan fill="#E8FFF6" font-weight="700">{esc(val)}</tspan></text>\n')
        y += 26

    y += 14
    body += (f'<text class="mono" x="34" y="{y}" font-size="14.5" fill="#3ddc97" fill-opacity=".75" '
             f'xml:space="preserve">$ gh api /languages</text>\n')
    y += 28
    colors = ["#00FF9C", "#22D3EE", "#7CF3D0"]
    for i, (lang, b) in enumerate(langs):
        frac = b / d["total_bytes"]
        filled = int(round(frac * 34))
        bar = "\u2588" * filled + "\u2591" * (34 - filled)
        pct = f"{frac * 100:.0f}%"
        name = (esc(lang) + " " * 12)[:12]
        body += (f'<text class="mono" x="34" y="{y}" font-size="14.5" fill="{colors[i]}" xml:space="preserve">'
                 f'{name}<tspan fill="#8fb3ad">{pct:>4}</tspan>  {bar}</text>\n')
        y += 25

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="high scores">
<defs>
  <linearGradient id="bgG" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#04070a"/><stop offset="60%" stop-color="#060d10"/><stop offset="100%" stop-color="#04090c"/>
  </linearGradient>
  <radialGradient id="glowA"><stop offset="0%" stop-color="#00FF9C" stop-opacity=".13"/><stop offset="100%" stop-color="#00FF9C" stop-opacity="0"/></radialGradient>
  <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
    <rect width="4" height="1" fill="#7fffd4" fill-opacity=".03"/>
  </pattern>
  <clipPath id="win"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="12"/></clipPath>
</defs>
<style>
  .mono {{ font-family: ui-monospace, "SF Mono", "JetBrains Mono", Consolas, monospace; }}
  .car {{ animation: blink 1.05s steps(1) infinite; }}
  @keyframes blink {{ 0%,48% {{ opacity: 1 }} 49%,100% {{ opacity: 0 }} }}
  .pulse {{ animation: pulse 3.6s ease-in-out infinite; }}
  @keyframes pulse {{ 0%,100% {{ opacity: .45 }} 50% {{ opacity: 1 }} }}
</style>
<rect width="{W}" height="{H}" rx="12" fill="url(#bgG)"/>
<ellipse cx="820" cy="250" rx="320" ry="200" fill="url(#glowA)"/>
<rect x="1" y="1" width="{W - 2}" height="30" rx="12" fill="#0a1114"/>
<rect x="1" y="20" width="{W - 2}" height="11" fill="#0a1114"/>
<circle cx="24" cy="16" r="4.5" fill="#ff5f57"/><circle cx="40" cy="16" r="4.5" fill="#febc2e"/><circle cx="56" cy="16" r="4.5" fill="#28c840"/>
<text class="mono" x="78" y="21" font-size="12" fill="#4e6b66">ananya@github:~/stats</text>
<text class="mono pulse" x="{W - 24}" y="21" font-size="12" text-anchor="end" fill="#00FF9C">rebuilt daily</text>
<line x1="1" y1="31" x2="{W - 1}" y2="31" stroke="#00FF9C" stroke-opacity=".18"/>
<text class="mono" x="34" y="66" font-size="14.5" fill="#3ddc97" fill-opacity=".75" xml:space="preserve">$ gh api /users/ananya-goswami</text>
{body}<rect class="car" x="34" y="{y - 12}" width="8" height="15" fill="#00FF9C"/>
<g clip-path="url(#win)"><rect width="{W}" height="{H}" fill="url(#scan)"/></g>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="12" fill="none" stroke="#00FF9C" stroke-opacity=".26"/>
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
<circle cx="26" cy="17" r="4.5" fill="#ff5f57"/><circle cx="43" cy="17" r="4.5" fill="#febc2e"/><circle cx="60" cy="17" r="4.5" fill="#28c840"/>
<text class="mono" x="84" y="22" font-size="12" fill="#4e6b66">ananya@github: ~/projects</text>
<line x1="1" y1="33" x2="{W - 1}" y2="33" stroke="#00FF9C" stroke-opacity=".18"/>
<text class="mono" x="26" y="68" font-size="14" fill="#3ddc97" fill-opacity=".8" xml:space="preserve">$ ls ~/projects --featured</text>
<rect class="car" x="232" y="56" width="8" height="15" fill="#00FF9C" fill-opacity=".8"/>
{cards}
<g clip-path="url(#win)"><rect width="{W}" height="{H}" fill="url(#scan)"/></g>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14" fill="none" stroke="#00FF9C" stroke-opacity=".26"/>
</svg>
'''


if __name__ == "__main__":
    data = collect()
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    open(OUT, "w").write(build(data))
    open(os.path.join(os.path.dirname(OUT) or ".", "projects.svg"), "w").write(build_projects(data["index"]))
    print("wrote panels:", data["repos"], "repos,", data["deployed"], "live builds")
