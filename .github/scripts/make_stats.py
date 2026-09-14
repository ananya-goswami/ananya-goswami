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
    langs = {}
    for r in own:
        try:
            for lang, b in api(r["languages_url"]).items():
                langs[lang] = langs.get(lang, 0) + b
        except Exception:
            pass
    deployed = [r for r in own if (r.get("homepage") or "").strip()]
    return {
        "repos": len(own),
        "deployed": len(deployed),
        "langs": sorted(langs.items(), key=lambda kv: -kv[1])[:3],
        "total_bytes": sum(langs.values()) or 1,
    }


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(d):
    W, H = 1000, 268
    tiles = [
        (f"{d['repos']}", "REPOS"),
        (f"{d['deployed']}", "LIVE BUILDS"),
        ("6-9", "CLASSES SERVED"),
        ("HI/EN", "BILINGUAL BY DEFAULT"),
    ]
    tw, gap, x0 = 224, 20, 28
    tile_svg = ""
    for i, (val, label) in enumerate(tiles):
        x = x0 + i * (tw + gap)
        tile_svg += f'''
  <g class="fade d{i + 1}">
    <rect x="{x}" y="72" width="{tw}" height="92" rx="14" fill="#141024" stroke="#8B5CF6" stroke-opacity=".32"/>
    <text x="{x + tw / 2:.0f}" y="122" text-anchor="middle" font-size="36" font-weight="700" fill="url(#numG)">{val}</text>
    <text x="{x + tw / 2:.0f}" y="146" text-anchor="middle" font-size="11" letter-spacing="2.2" fill="#8b86a8" font-weight="600">{label}</text>
  </g>'''

    colors = ["#8B5CF6", "#22D3EE", "#F0ABFC"]
    bar_w, bar_x, bar_y = 944, 28, 196
    seg_svg, leg_svg, cursor, lx = "", "", 0.0, 28
    for i, (lang, b) in enumerate(d["langs"]):
        frac = b / d["total_bytes"]
        w = max(frac * bar_w, 4)
        seg_svg += f'''
    <rect class="grow g{i}" x="{bar_x + cursor:.1f}" y="{bar_y}" width="{w:.1f}" height="15" rx="7.5" fill="{colors[i]}"/>'''
        cursor += w + 3
        pct = f"{frac * 100:.0f}%"
        leg_svg += f'''
    <circle cx="{lx}" cy="{bar_y + 42}" r="4.5" fill="{colors[i]}"/>
    <text x="{lx + 13}" y="{bar_y + 46}" font-size="13" fill="#b9b3d6">{esc(lang)} {pct}</text>'''
        lx += 34 + len(lang) * 7.6 + len(pct) * 8

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="High scores">
<defs>
  <linearGradient id="panelG" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#0c0a16"/><stop offset="100%" stop-color="#120d24"/>
  </linearGradient>
  <linearGradient id="numG" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#FFFFFF"/><stop offset="100%" stop-color="#A78BFA"/>
  </linearGradient>
  <linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="#ffffff" stop-opacity="0"/>
    <stop offset="50%" stop-color="#ffffff" stop-opacity=".07"/>
    <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
  <clipPath id="panelClip"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18"/></clipPath>
</defs>
<style>
  text {{ font-family: "Segoe UI", Ubuntu, "Helvetica Neue", Arial, sans-serif; }}
  .mono {{ font-family: ui-monospace, "SF Mono", Consolas, monospace; }}
  .fade {{ opacity: 0; animation: up .8s cubic-bezier(.2,.7,.3,1) forwards; }}
  @keyframes up {{ from {{ opacity: 0; transform: translateY(12px); }} to {{ opacity: 1; transform: translateY(0); }} }}
  .d1 {{ animation-delay: .10s }} .d2 {{ animation-delay: .22s }}
  .d3 {{ animation-delay: .34s }} .d4 {{ animation-delay: .46s }} .d5 {{ animation-delay: .60s }}
  .grow {{ transform-box: view-box; transform-origin: 28px 0; animation: grow 1.1s cubic-bezier(.2,.8,.3,1) forwards; }}
  @keyframes grow {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
  .g0 {{ animation-delay: .55s }} .g1 {{ animation-delay: .70s }} .g2 {{ animation-delay: .85s }}
  .sweep {{ transform-box: view-box; animation: sweep 7s ease-in-out infinite; }}
  @keyframes sweep {{ 0% {{ transform: translateX(-160px); }} 60%, 100% {{ transform: translateX(1100px); }} }}
  .blip {{ animation: blip 1.9s ease-in-out infinite; }}
  @keyframes blip {{ 0%, 100% {{ opacity: .25 }} 50% {{ opacity: 1 }} }}
</style>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18" fill="url(#panelG)" stroke="#8B5CF6" stroke-opacity=".38"/>
<g clip-path="url(#panelClip)"><rect class="sweep" x="0" y="0" width="150" height="{H}" fill="url(#shine)"/></g>
<circle class="blip" cx="34" cy="38" r="5" fill="#22D3EE"/>
<text x="50" y="44" font-size="17" font-weight="700" letter-spacing="4" fill="#E9E3FF">HIGH SCORES</text>
<text class="mono" x="{W - 28}" y="43" text-anchor="end" font-size="11" letter-spacing="1.4" fill="#6f6a8c">REBUILT DAILY FROM THE GITHUB API</text>
{tile_svg}
  <g class="fade d5">
    <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="15" rx="7.5" fill="#1b1630"/>{seg_svg}{leg_svg}
  </g>
</svg>
'''


if __name__ == "__main__":
    data = collect()
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    open(OUT, "w").write(build(data))
    print("wrote", OUT, data["repos"], "repos,", data["deployed"], "live builds,", data["langs"])
