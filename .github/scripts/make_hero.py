#!/usr/bin/env python3
"""Builds the hero panel: the avatar, and the particle morph that carries it
through four symbols and back.

The VISUAL.MAP panel has two layers that hand off to each other:

  tiles      the avatar itself, cut into a grid of fragments.  Each fragment
             is one <path> of stipple pixels, so the resting portrait is the
             full-density image, not a thinned-out cloud of dots.
  particles  ~1700 dots that live at avatar pixels, then travel through
             </>, the React mark, a gamepad and the Vercel triangle -
             write it, build it, play it, ship it.

The handoff is the whole point.  The fragments fly apart along the vector
from the centre of the face while the particles light up on the pixels they
were sampled from, so the avatar visibly comes apart into the dots that
become the symbol, instead of one image cross-fading into another.  The
return runs the same move backwards and lands the particles back on their
own pixels just as the fragments settle, so the loop closes without a seam.

Run it from the repo root:  python .github/scripts/make_hero.py
"""
import math
import os
import random

from PIL import Image, ImageDraw

HEAD = """<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="706" viewBox="0 0 1180 706"
     font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
     role="img" aria-label="Ananya Goswami, senior product associate">
<defs>
  <linearGradient id="ink" x1="0" y1="0" x2="0" y2="1" gradientUnits="objectBoundingBox">
    <stop offset="0" stop-color="#9BE7C4"><animate attributeName="stop-color" values="#9BE7C4;#8FD4F5;#B9A7FA;#9BE7C4" dur="12s" repeatCount="indefinite"/></stop>
    <stop offset="0.55" stop-color="#8FD4F5"><animate attributeName="stop-color" values="#8FD4F5;#B9A7FA;#9BE7C4;#8FD4F5" dur="12s" repeatCount="indefinite"/></stop>
    <stop offset="1" stop-color="#B9A7FA"><animate attributeName="stop-color" values="#B9A7FA;#9BE7C4;#8FD4F5;#B9A7FA" dur="12s" repeatCount="indefinite"/></stop>
  </linearGradient>
  <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#00FF9C" stop-opacity=".75"/><stop offset="1" stop-color="#22D3EE" stop-opacity=".55"/>
  </linearGradient>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#04070a"/><stop offset="0.55" stop-color="#060e12"/><stop offset="1" stop-color="#04090c"/>
  </linearGradient>
  <radialGradient id="glowA"><stop offset="0" stop-color="#00FF9C" stop-opacity=".14"/><stop offset="1" stop-color="#00FF9C" stop-opacity="0"/></radialGradient>
  <radialGradient id="glowB"><stop offset="0" stop-color="#22D3EE" stop-opacity=".12"/><stop offset="1" stop-color="#22D3EE" stop-opacity="0"/></radialGradient>
  <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#7fffd4" fill-opacity=".03"/></pattern>
  <pattern id="grid" width="34" height="34" patternUnits="userSpaceOnUse"><path d="M34 0H0V34" fill="none" stroke="#00FF9C" stroke-opacity=".04"/></pattern>
  <rect id="d" width="1.25" height="1.25" fill="#CFF3FF"/>
  <rect id="e" width="1.9" height="1.9" fill="#9BE7C4"/>
  <clipPath id="pan"><rect x="39" y="89" width="440" height="580" rx="8"/></clipPath>
</defs>
<style>.rv { opacity: 1 }</style>

<rect width="1180" height="706" rx="16" fill="url(#bg)"/>
<rect width="1180" height="706" rx="16" fill="url(#grid)"/>
<ellipse cx="250" cy="300" rx="330" ry="280" fill="url(#glowA)"/>
<ellipse cx="960" cy="480" rx="360" ry="260" fill="url(#glowB)"/>

<rect x="1" y="1" width="1178" height="44" rx="16" fill="#080f12"/><rect x="1" y="30" width="1178" height="16" fill="#080f12"/>
<circle cx="30" cy="23" r="6" fill="#ff5f57"/><circle cx="52" cy="23" r="6" fill="#febc2e"/><circle cx="74" cy="23" r="6" fill="#28c840"/>
<text x="590" y="28" font-size="13" text-anchor="middle" fill="#5c7a74">goswamiananya54@gmail.com - % ./profile.sh --live</text>
<line x1="1" y1="45" x2="1179" y2="45" stroke="#00FF9C" stroke-opacity=".2"/>

<text x="44" y="80" font-size="12" letter-spacing="3" fill="#3f5f58">VISUAL.MAP</text>
<rect x="38" y="88" width="442" height="582" rx="8" fill="#030a08" stroke="url(#edge)" stroke-width="1.4"/>

"""

TAIL = """
<rect x="46" y="610" width="426" height="46" fill="#030a08" fill-opacity=".88"/>
<line x1="46" y1="610" x2="472" y2="610" stroke="#00FF9C" stroke-opacity=".18"/>
<text x="60" y="630" font-size="11" letter-spacing="2.4" fill="#31514c">TOOLCHAIN.SCAN</text>
<text x="60" y="650" font-size="13" fill="#00FF9C" opacity="0">&#9656; figma<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.0000;0.0125;0.0875;0.1000;1" dur="20.0s" begin="0s" repeatCount="indefinite"/></text>
<text x="60" y="650" font-size="13" fill="#00FF9C" opacity="0">&#9656; vite<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.1000;0.1125;0.1875;0.2000;1" dur="20.0s" begin="0s" repeatCount="indefinite"/></text>
<text x="60" y="650" font-size="13" fill="#00FF9C" opacity="0">&#9656; react<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.2000;0.2125;0.2875;0.3000;1" dur="20.0s" begin="0s" repeatCount="indefinite"/></text>
<text x="60" y="650" font-size="13" fill="#00FF9C" opacity="0">&#9656; n8n<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.3000;0.3125;0.3875;0.4000;1" dur="20.0s" begin="0s" repeatCount="indefinite"/></text>
<text x="60" y="650" font-size="13" fill="#00FF9C" opacity="0">&#9656; waha<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.4000;0.4125;0.4875;0.5000;1" dur="20.0s" begin="0s" repeatCount="indefinite"/></text>
<text x="60" y="650" font-size="13" fill="#00FF9C" opacity="0">&#9656; railway<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.5000;0.5125;0.5875;0.6000;1" dur="20.0s" begin="0s" repeatCount="indefinite"/></text>
<text x="60" y="650" font-size="13" fill="#00FF9C" opacity="0">&#9656; postgres<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.6000;0.6125;0.6875;0.7000;1" dur="20.0s" begin="0s" repeatCount="indefinite"/></text>
<text x="60" y="650" font-size="13" fill="#00FF9C" opacity="0">&#9656; claude api<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.7000;0.7125;0.7875;0.8000;1" dur="20.0s" begin="0s" repeatCount="indefinite"/></text>
<text x="60" y="650" font-size="13" fill="#00FF9C" opacity="0">&#9656; vercel<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.8000;0.8125;0.8875;0.9000;1" dur="20.0s" begin="0s" repeatCount="indefinite"/></text>
<text x="60" y="650" font-size="13" fill="#00FF9C" opacity="0">&#9656; netlify<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.9000;0.9125;0.9875;1.0000;1" dur="20.0s" begin="0s" repeatCount="indefinite"/></text>

<text x="500" y="80" font-size="12" letter-spacing="3" fill="#3f5f58">SYSTEM.INFO</text>
<text x="1140" y="80" font-size="12" text-anchor="end" letter-spacing="1.5" fill="#00FF9C">● LIVE
  <animate attributeName="opacity" values="1;.35;1" dur="2.6s" repeatCount="indefinite"/></text>
<rect x="500" y="102" width="330" height="26" rx="6" fill="#0d1a17" stroke="#00FF9C" stroke-opacity=".35"/>
<text x="512" y="120" font-size="13" fill="#00FF9C">goswamiananya54@gmail.com</text>
<line x1="500" y1="150" x2="1140" y2="150" stroke="#00FF9C" stroke-opacity=".12"/>
<text x="500" y="172" font-size="12" letter-spacing="2" fill="#31514c">$ whoami --verbose</text>

<text opacity="0" x="500" y="190" font-size="14" xml:space="preserve"><tspan fill="#22D3EE">Subject</tspan><tspan fill="#31514c"> ..................................................... </tspan><tspan fill="#F2FBF8" font-weight="600">Ananya Goswami</tspan><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.106;0.161;1" dur="9.0s" begin="0s" fill="freeze"/></text>
<text opacity="0" x="500" y="214" font-size="14" xml:space="preserve"><tspan fill="#22D3EE">Role</tspan><tspan fill="#31514c"> .............................................. </tspan><tspan fill="#00FF9C" font-weight="600">Senior Product Associate</tspan><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.123;0.178;1" dur="9.0s" begin="0s" fill="freeze"/></text>
<text opacity="0" x="500" y="238" font-size="14" xml:space="preserve"><tspan fill="#22D3EE">Team</tspan><tspan fill="#31514c"> ...................................... </tspan><tspan fill="#CFEAE3" font-weight="600">Game Development, ConveGenius AI</tspan><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.140;0.196;1" dur="9.0s" begin="0s" fill="freeze"/></text>
<text opacity="0" x="500" y="262" font-size="14" xml:space="preserve"><tspan fill="#22D3EE">Origin</tspan><tspan fill="#31514c"> ........................................................ </tspan><tspan fill="#CFEAE3" font-weight="600">Noida, India</tspan><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.157;0.213;1" dur="9.0s" begin="0s" fill="freeze"/></text>
<text opacity="0" x="500" y="286" font-size="14" xml:space="preserve"><tspan fill="#22D3EE">Education</tspan><tspan fill="#31514c"> ..................... </tspan><tspan fill="#CFEAE3" font-weight="600">BSc Programming and Data Science, IIT Madras</tspan><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.174;0.230;1" dur="9.0s" begin="0s" fill="freeze"/></text>
<text opacity="0" x="500" y="310" font-size="14" xml:space="preserve"><tspan fill="#22D3EE">Status</tspan><tspan fill="#31514c"> ................................. </tspan><tspan fill="#22D3EE" font-weight="600">Prototyping + Shipping + Automating</tspan><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.192;0.247;1" dur="9.0s" begin="0s" fill="freeze"/></text>
<text opacity="0" x="500" y="334" font-size="14" xml:space="preserve"><tspan fill="#22D3EE">ToolChain</tspan><tspan fill="#31514c"> ............................. </tspan><tspan fill="#CFEAE3" font-weight="600">VS Code, Figma, Git, Vercel, Netlify</tspan><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.209;0.264;1" dur="9.0s" begin="0s" fill="freeze"/></text>
<text opacity="0" x="500" y="368" font-size="14" xml:space="preserve"><tspan fill="#22D3EE">Core.Lang</tspan><tspan fill="#31514c"> .................................... </tspan><tspan fill="#CFEAE3" font-weight="600">JavaScript, HTML, CSS, Python</tspan><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.226;0.282;1" dur="9.0s" begin="0s" fill="freeze"/></text>
<text opacity="0" x="500" y="392" font-size="14" xml:space="preserve"><tspan fill="#22D3EE">Core.Frontend</tspan><tspan fill="#31514c"> ...................................... </tspan><tspan fill="#CFEAE3" font-weight="600">React, Vite, vanilla JS</tspan><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.243;0.299;1" dur="9.0s" begin="0s" fill="freeze"/></text>
<text opacity="0" x="500" y="416" font-size="14" xml:space="preserve"><tspan fill="#22D3EE">Core.Automation</tspan><tspan fill="#31514c"> ......................................... </tspan><tspan fill="#CFEAE3" font-weight="600">n8n, WAHA, Railway</tspan><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.261;0.316;1" dur="9.0s" begin="0s" fill="freeze"/></text>
<text opacity="0" x="500" y="440" font-size="14" xml:space="preserve"><tspan fill="#22D3EE">Core.Data</tspan><tspan fill="#31514c"> .............................................. </tspan><tspan fill="#CFEAE3" font-weight="600">Postgres, IndexedDB</tspan><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.278;0.333;1" dur="9.0s" begin="0s" fill="freeze"/></text>
<text opacity="0" x="500" y="464" font-size="14" xml:space="preserve"><tspan fill="#22D3EE">Core.AI</tspan><tspan fill="#31514c"> ......................................................... </tspan><tspan fill="#CFEAE3" font-weight="600">Claude API</tspan><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.295;0.351;1" dur="9.0s" begin="0s" fill="freeze"/></text>
<text opacity="0" x="500" y="488" font-size="14" xml:space="preserve"><tspan fill="#22D3EE">Ships</tspan><tspan fill="#31514c"> .................................... </tspan><tspan fill="#00FF9C" font-weight="600">15+ browser games, Classes 6 to 9</tspan><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.312;0.368;1" dur="9.0s" begin="0s" fill="freeze"/></text>
<text class="rv" x="500" y="522" font-size="14" fill="#3f5f58">- Contact ......................................................................<animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.329;0.385;1" dur="9.0s" begin="0s" fill="freeze"/></text>
<text opacity="0" x="500" y="546" font-size="14" xml:space="preserve"><tspan fill="#22D3EE">Grid.Mail</tspan><tspan fill="#31514c"> ........................................ </tspan><tspan fill="#CFEAE3" font-weight="600">goswamiananya54@gmail.com</tspan><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.343;0.398;1" dur="9.0s" begin="0s" fill="freeze"/></text>
<text opacity="0" x="500" y="570" font-size="14" xml:space="preserve"><tspan fill="#22D3EE">Grid.Portfolio</tspan><tspan fill="#31514c"> ........................................ </tspan><tspan fill="#22D3EE" font-weight="600">g-ananya.netlify.app</tspan><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.360;0.416;1" dur="9.0s" begin="0s" fill="freeze"/></text>
<text opacity="0" x="500" y="594" font-size="14" xml:space="preserve"><tspan fill="#22D3EE">Grid.LinkedIn</tspan><tspan fill="#31514c"> .................................................... </tspan><tspan fill="#CFEAE3" font-weight="600">ananyagos</tspan><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.377;0.433;1" dur="9.0s" begin="0s" fill="freeze"/></text>
<text opacity="0" x="500" y="618" font-size="14" xml:space="preserve"><tspan fill="#22D3EE">Grid.GitHub</tspan><tspan fill="#31514c"> ................................................ </tspan><tspan fill="#CFEAE3" font-weight="600">@ananya-goswami</tspan><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.394;0.450;1" dur="9.0s" begin="0s" fill="freeze"/></text>

<text opacity="0" x="500" y="658" font-size="13" fill="#3ddc97">▸ projects, games and automations below
  <animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.451;0.99;1" dur="9.0s" begin="0s" fill="freeze"/></text>
<rect x="830" y="646" width="9" height="15" fill="#00FF9C">
  <animate attributeName="opacity" values="1;1;0;0" dur="1.05s" begin="0s" repeatCount="indefinite"/></rect>

<rect width="1180" height="706" rx="16" fill="url(#scan)"/>
<rect x="1" y="1" width="1178" height="704" rx="16" fill="none" stroke="#00FF9C" stroke-opacity=".3"/>
</svg>
"""


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MASK = os.path.join(ROOT, "assets", "portrait-mask.png")
OUT = os.path.join(ROOT, "assets", "hero-v13.svg")

RNG = random.Random(7)

# ---------------------------------------------------------------- timeline
# One loop, as fractions of LOOP.  The panel rests on the avatar for the
# first 14% and the last 12%; everything between is the morph.
LOOP = 30.0                     # seconds for the whole avatar -> symbols -> avatar cycle
BEGIN = 4.6                     # the loop starts after the intro has drawn the avatar
K = [0.000,                     # rest
     0.140, 0.205,              # come apart -> first symbol
     0.300, 0.365,              # -> second
     0.460, 0.525,              # -> third
     0.620, 0.685,              # -> fourth
     0.790, 0.880,              # -> back to the avatar
     1.000]
EASE = ".42 0 .18 1"            # one ease-in-out, reused on every segment

N_PARTICLES = 1700
TILE_COLS, TILE_ROWS = 12, 15

# The symbols are drawn in a 0..100 box and then mapped into the avatar's own
# coordinate space, so a particle's trip from face to symbol stays short.
SYM_CX, SYM_CY = 134.0, 146.0
SYM_W, SYM_H = 196.0, 166.0


# ------------------------------------------------------------------ raster
# Symbols are drawn eight times up and the points are picked off the result, so
# a diagonal edge lands on a smooth line of dots rather than a visible stair.
UP = 8.0
CANVAS = int(100 * UP)


def raster():
    """A canvas to draw one symbol on, plus its drawing context."""
    im = Image.new("L", (CANVAS, CANVAS), 0)
    return im, ImageDraw.Draw(im)


def to_px(pts):
    """0..100 design units -> pixels on the canvas."""
    return [(x * UP, y * UP) for x, y in pts]


def stroke(d, pts, w, closed=False):
    """A round-capped, round-joined stroke, laid down as a run of discs.

    Pillow's `line` gives square ends and mitres that notch where two thick
    strokes meet, and both show up badly once the shape is only 1700 dots.
    Stamping a disc along the path costs nothing here and leaves every end and
    corner clean.
    """
    p = to_px(pts)
    if closed:
        p = p + [p[0]]
    r = w * UP / 2.0
    for (x0, y0), (x1, y1) in zip(p, p[1:]):
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / (r * 0.35) + 1))
        for i in range(n + 1):
            t = i / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            d.ellipse([x - r, y - r, x + r, y + r], fill=255)


def disc(d, cx, cy, r):
    (x, y), rr = to_px([(cx, cy)])[0], r * UP
    d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=255)


def arc(cx, cy, r, a0=0, a1=360, steps=240):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / steps)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / steps)))
            for i in range(steps + 1)]


def ellipse_path(cx, cy, rx, ry, tilt, steps=260):
    """One tilted ellipse - the orbit in the React mark."""
    ca, sa = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    out = []
    for i in range(steps + 1):
        t = 2 * math.pi * i / steps
        x, y = rx * math.cos(t), ry * math.sin(t)
        out.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return out


def ring(d, cx, cy, r, w):
    stroke(d, arc(cx, cy, r), w, closed=True)


def poly(d, pts):
    d.polygon(to_px(pts), fill=255)


def rrect(x, y, w, h, r):
    """Outline of a rounded rectangle as a point list."""
    pts = []
    for cx, cy, a0 in ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0),
                       (x + r, y + h - r, 90), (x + r, y + r, 180)):
        for i in range(19):
            a = math.radians(a0 + i * 5)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def mask_points(im):
    px = im.load()
    w, h = im.size
    return [(x, y) for y in range(h) for x in range(w) if px[x, y]]


# ----------------------------------------------------------------- symbols
# Write it, build it, play it, ship it - the four marks are the shortest true
# account of the work, and each one has to survive being redrawn as 1700 dots.
# That rules out anything that leans on colour to be read (the Figma mark) or
# on fine detail (the Octocat), and it rules out a symbol nobody would place
# out of context, which is what sank the mortarboard and the node graph.
# Three of the four are stroked, which holds their weight even.  The Vercel
# mark is the exception: it is a solid triangle and drawing it as an outline
# turns it into a generic delta, so it is filled.  It gets away with it
# because a triangle covers only half its box, which keeps the 1700 dots
# close enough together to still read as a solid.  A larger fill would thin
# out to a haze at this count.
def sym_code():
    """</> - the games are hand-written HTML, CSS and JavaScript."""
    im, d = raster()
    stroke(d, [(35, 27), (15, 50), (35, 73)], 5.6)
    stroke(d, [(58, 19), (42, 81)], 5.6)
    stroke(d, [(65, 27), (85, 50), (65, 73)], 5.6)
    return im


def sym_react():
    """The React mark: what the bigger builds are put together with."""
    im, d = raster()
    for tilt in (0, 60, 120):
        stroke(d, ellipse_path(50, 50, 42, 16, tilt), 3.4, closed=True)
    disc(d, 50, 50, 6.4)
    return im


def sym_gamepad():
    """15+ browser games running in classrooms - the day job."""
    im, d = raster()
    stroke(d, rrect(13, 31, 74, 38, 18), 4.6, closed=True)
    stroke(d, [(26, 50), (40, 50)], 4.2)              # d-pad, across
    stroke(d, [(33, 43), (33, 57)], 4.2)              # d-pad, down
    disc(d, 64, 44, 4.8)
    disc(d, 75, 55, 4.8)
    return im


def sym_ship():
    """The Vercel triangle: nearly every game in the README ships there."""
    im, d = raster()
    poly(d, [(50, 19), (89, 77), (11, 77)])
    return im


SYMBOLS = [sym_code, sym_react, sym_gamepad, sym_ship]


# ---------------------------------------------------------------- sampling
def scatter(pts, n):
    """n points spread evenly over a mask, by best-candidate sampling.

    Picking at random clumps, and a clump inside a 6px stroke reads as noise
    rather than a line.  Each new point is the furthest of a few candidates
    from everything placed so far, which is enough to keep the spacing even
    without the cost of a full relaxation.
    """
    cell = max(2.0, math.sqrt(len(pts) / max(n, 1)) * 1.6)
    grid, out = {}, []
    for _ in range(n):
        best, best_d = None, -1.0
        for _ in range(16):
            c = pts[RNG.randrange(len(pts))]
            gx, gy = int(c[0] / cell), int(c[1] / cell)
            near = 1e9
            for ax in (gx - 1, gx, gx + 1):
                for ay in (gy - 1, gy, gy + 1):
                    for p in grid.get((ax, ay), ()):
                        dd = (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2
                        if dd < near:
                            near = dd
            if near > best_d:
                best, best_d = c, near
        out.append(best)
        grid.setdefault((int(best[0] / cell), int(best[1] / cell)), []).append(best)
    return out


def sample_tone(pts, n):
    """n points drawn straight from the avatar's own pixels.

    The avatar is a dither, so how densely its pixels sit already carries the
    tone.  Taking them uniformly keeps that: the cheek stays bright and the
    hair stays dark, and the cloud still reads as her face on the way out.
    """
    return [pts[i] for i in RNG.sample(range(len(pts)), n)]


def polar_rank(pts, sectors=96):
    """Order points by angle around their own centre, then by radius.

    Every shape is ordered the same way and particle number r takes rank r in
    all of them, so the cloud rotates into each symbol instead of shuffling
    through itself.  Without this a particle on the left of the face can be
    assigned a target on the right, and 1700 of those crossing at once is the
    scribble the old panel showed mid-morph.
    """
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)

    def key(i):
        dx, dy = pts[i][0] - cx, pts[i][1] - cy
        a = math.atan2(dy, dx) + math.pi
        return (int(a / (2 * math.pi) * sectors), dx * dx + dy * dy)

    return sorted(range(len(pts)), key=key)


def place(im, n):
    """A symbol's mask -> n points, in the avatar's coordinate space."""
    pts = mask_points(im)
    pts = scatter(pts, n)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    s = min(SYM_W / max(x1 - x0, 1), SYM_H / max(y1 - y0, 1))
    mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    return [(SYM_CX + (x - mx) * s, SYM_CY + (y - my) * s) for x, y in pts]


# ------------------------------------------------------------------ output
def fmt(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def ktimes(ks):
    return ";".join(f"{k:.4f}".rstrip("0").rstrip(".") for k in ks)


def splines(n):
    return ";".join([EASE] * n)


def tiles_svg(pts, cx, cy):
    """The avatar, cut into fragments that fly apart and come back."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    tw = (x1 - x0 + 1) / TILE_COLS
    th = (y1 - y0 + 1) / TILE_ROWS

    cells = {}
    for x, y in pts:
        cells.setdefault((min(int((x - x0) / tw), TILE_COLS - 1),
                          min(int((y - y0) / th), TILE_ROWS - 1)), []).append((x, y))

    order = sorted(cells)
    RNG.shuffle(order)
    out = []
    for i, key in enumerate(order):
        cell = cells[key]
        d = "".join(f"M{x} {y}h1v1h-1z" for x, y in cell)

        # Fly out along the line from the centre of the face, further the
        # further out the fragment already is, so the avatar opens up rather
        # than scattering in place.
        mx = sum(p[0] for p in cell) / len(cell)
        my = sum(p[1] for p in cell) / len(cell)
        dx, dy = mx - cx, my - cy
        dist = math.hypot(dx, dy) or 1.0
        reach = min(18.0 + dist * 0.34, 62.0)
        ox = dx / dist * reach + RNG.uniform(-6, 6)
        oy = dy / dist * reach + RNG.uniform(-6, 6) - 5.0

        # A little per-fragment slack on the timing keeps the break-up from
        # happening on one frame, which is what made it read as a cross-fade.
        j = RNG.uniform(-0.011, 0.011)
        kt_t = [0, K[1] + j, K[2] + j, 0.820 + j, K[10] + j, 1]
        kt_o = [0, K[1] + j, 0.200 + j, 0.868 + j, 0.912 + j, 1]

        begin_in = 0.25 + i * 0.012
        out.append(
            f'<g opacity="0">'
            f'<animate attributeName="opacity" values="0;1" dur="0.7s" begin="{begin_in:.2f}s"'
            f' fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="{EASE}"/>'
            f'<animateTransform attributeName="transform" type="translate"'
            f' values="{fmt(ox)} {fmt(oy)};0 0" dur="0.9s" begin="{begin_in:.2f}s"'
            f' fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="{EASE}"/>'
            f'<animate attributeName="opacity" values="1;1;0;0;1;1" keyTimes="{ktimes(kt_o)}"'
            f' dur="{LOOP}s" begin="{BEGIN}s" repeatCount="indefinite"'
            f' calcMode="spline" keySplines="{splines(5)}"/>'
            f'<animateTransform attributeName="transform" type="translate"'
            f' values="0 0;0 0;{fmt(ox)} {fmt(oy)};{fmt(ox)} {fmt(oy)};0 0;0 0"'
            f' keyTimes="{ktimes(kt_t)}" dur="{LOOP}s" begin="{BEGIN}s" repeatCount="indefinite"'
            f' calcMode="spline" keySplines="{splines(5)}"/>'
            f'<path d="{d}" fill="url(#ink)"/></g>')
    return out


def particles_svg(home, shapes):
    """The dots: avatar pixel -> each symbol in turn -> the same pixel back."""
    rank_home = polar_rank(home)
    rank_sym = [polar_rank(s) for s in shapes]

    out = []
    for r in range(len(home)):
        p = home[rank_home[r]]
        stops = [p, p]
        for s, rk in zip(shapes, rank_sym):
            q = s[rk[r]]
            stops.append(q)
            # The second copy of each symbol drifts a hair off the first, so a
            # three-second hold breathes instead of freezing dead still.
            stops.append((q[0] + RNG.uniform(-1.1, 1.1), q[1] + RNG.uniform(-1.1, 1.1)))
        stops += [p, p]

        j = RNG.uniform(-0.009, 0.009)
        ks = [K[0]] + [k + j for k in K[1:-1]] + [K[11]]
        vals = ";".join(f"{fmt(x)} {fmt(y)}" for x, y in stops)
        href = "#e" if RNG.random() < 0.085 else "#d"
        out.append(
            f'<use href="{href}"><animateTransform attributeName="transform"'
            f' type="translate" values="{vals}" keyTimes="{ktimes(ks)}" dur="{LOOP}s"'
            f' begin="{BEGIN}s" repeatCount="indefinite" calcMode="spline"'
            f' keySplines="{splines(11)}"/></use>')
    return out


def main():
    im = Image.open(MASK).convert("L")
    pts = mask_points(im)
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)

    home = sample_tone(pts, N_PARTICLES)
    shapes = [place(fn(), N_PARTICLES) for fn in SYMBOLS]

    kt_p = [0, K[1], 0.205, 0.855, K[10], 0.910, 1]
    # Fragments travel far enough to clear the face; the clip keeps the ones
    # that overshoot from spilling onto the SYSTEM.INFO column next door.
    body = [
        '<g clip-path="url(#pan)">',
        '<g transform="translate(44.0 115.1) scale(1.604)" shape-rendering="crispEdges">',
        *tiles_svg(pts, cx, cy),
        '</g>',
        '',
        '<g transform="translate(44.0 115.1) scale(1.604)" shape-rendering="crispEdges"'
        ' opacity="0">'
        f'<animate attributeName="opacity" values="0;0;1;1;1;0;0" keyTimes="{ktimes(kt_p)}"'
        f' dur="{LOOP}s" begin="{BEGIN}s" repeatCount="indefinite"'
        f' calcMode="spline" keySplines="{splines(6)}"/>',
        *particles_svg(home, shapes),
        '</g>',
        '</g>',
    ]

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(HEAD)
        f.write("\n".join(body))
        f.write("\n")
        f.write(TAIL)
    print(f"{OUT}  {os.path.getsize(OUT) / 1024:.0f} KB  "
          f"{len(pts)} avatar px, {N_PARTICLES} particles, {TILE_COLS * TILE_ROWS} fragments")


if __name__ == "__main__":
    main()
