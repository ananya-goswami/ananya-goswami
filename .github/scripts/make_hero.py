#!/usr/bin/env python3
"""Builds the hero panel: the avatar, and the particle morph that carries it
through the toolchain and back.

The VISUAL.MAP panel has two layers that hand off to each other:

  tiles      the avatar itself, cut into a grid of fragments.  Each fragment
             is one <path> of stipple pixels, so the resting portrait is the
             full-density image, not a thinned-out cloud of dots.
  particles  ~1550 dots that live at avatar pixels, then travel through the
             marks in SYMBOLS - the run of a working day, from the terminal
             the morning opens in to the deploy it ends with.

Each mark carries its own caption, and the TOOLCHAIN.SCAN line under the
panel is generated from the same key times, so the name on screen is always
the name of the shape above it.

The handoff is the whole point.  The fragments fly apart along the vector
from the centre of the face while the particles light up on the pixels they
were sampled from, so the avatar visibly comes apart into the dots that
become the symbol, instead of one image cross-fading into another.  The
return runs the same move backwards and lands the particles back on their
own pixels just as the fragments settle, so the loop closes without a seam.

Run it from the repo root:  python .github/scripts/make_hero.py

Bump the filename in OUT, and the readme with it, on any change anyone is
meant to see.  GitHub serves README images through camo, which caches them by
URL, so republishing to the same path leaves everyone looking at the first
version that was ever fetched - no amount of pushing shifts it.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

HEAD = """<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="706" viewBox="0 0 1180 706"
     font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
     role="img" aria-label="Ananya Goswami, senior product associate">
<defs>
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
  <rect id="d" width="1.25" height="1.25"/>
  <rect id="e" width="2" height="2" fill-opacity=".45"/>
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
<!--TICKER-->

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
REF = os.path.join(ROOT, "assets", "portrait-colour.png")
OUT = os.path.join(ROOT, "assets", "hero-v21.svg")

RNG = random.Random(7)

# ---------------------------------------------------------------- timeline
# Seconds, in the order they happen.  The loop length and every key time fall
# out of these, so adding or dropping a symbol needs no other edit - which is
# the point, because the set is the part most likely to change.
BEGIN = 4.6                     # the loop starts after the intro has drawn the avatar
REST = 4.5                      # the avatar sits, whole, at the top of the loop
DISSOLVE = 1.6                  # it comes apart and the dots take the first symbol
HOLD = 2.15                     # each symbol is held this long
MORPH = 1.15                    # and takes this long to become the next
RETURN = 1.8                    # the dots fly home to their own pixels
SETTLE = 1.5                    # the avatar is whole again before the loop repeats
EASE = ".4 0 .2 1"              # one ease-in-out, reused on every segment; it is
                                # repeated once per segment per element, so the
                                # short spelling is worth ~100KB on the file

N_PARTICLES = 1550
N_INKS = 64                     # colours the painted avatar is cut down to; at 28
                                # median-cut spent them all on skin and flattened
                                # her mouth into a grey
N_DOT_TONES = 4                 # and the far coarser set the dots use
TILE_COLS, TILE_ROWS = 12, 15

# The symbols are drawn in a 0..100 box and then mapped into the avatar's own
# coordinate space, so a particle's trip from face to symbol stays short.
PANEL = (38, 88, 442, 582)      # the VISUAL.MAP box, in panel coordinates
PANEL_BG = "#030a08"            # and what it is filled with, so the occluder matches
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


def stroke(d, pts, w, closed=False, ink=1):
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
            d.ellipse([x - r, y - r, x + r, y + r], fill=ink)


def disc(d, cx, cy, r, ink=1):
    (x, y), rr = to_px([(cx, cy)])[0], r * UP
    d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=ink)


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


def bez(p0, p1, p2, p3, steps=90):
    """A cubic, for the one curve in the set - the git branch."""
    out = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def ring(d, cx, cy, r, w, ink=1):
    stroke(d, arc(cx, cy, r), w, closed=True, ink=ink)


def poly(d, pts, ink=1):
    d.polygon(to_px(pts), fill=ink)


def punch(d, cx, cy, r):
    """Erase a disc - how the gear gets its bore."""
    (x, y), rr = to_px([(cx, cy)])[0], r * UP
    d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=0)


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
# The run of the working day: write it, build it with a framework, check it
# against the design, bundle it, commit it, automate round it, put the data
# somewhere, ship it - and the terminal it is all driven from, which closes
# the loop and hands back to her.  Neither Figma nor the terminal opens the
# set, because the avatar hands straight over to the first mark and that
# wants to be the work rather than a tool.  Every mark has to survive being redrawn as 1550
# dots, and that test shapes how each one is drawn.  Fine detail does not
# survive it - the Octocat loses its silhouette, so GitHub is the branch
# glyph.  Some tools have no mark anyone reads out of context at all, which is
# the honest position for WAHA, Railway and n8n, so automation is a plain gear
# and those three are named outright in the caption under it.
#
# Each function draws its regions with ink=1, 2, 3... and returns the colours
# those inks stand for, so a mark can carry its real palette rather than one
# flat tint.  Every colour here is the tool's own, lifted toward the light end
# where it has to be: a brand colour chosen for a white page goes muddy on a
# near-black panel, and Postgres navy disappears into it outright.
#
# Most marks are stroked, which holds their weight even.  The two solids - the
# Vite bolt and the Vercel triangle - lose their identity as outlines, since an
# outlined triangle is a generic delta rather than the Vercel mark.  Both are
# small enough that 1550 dots still read solid; a fill across the whole box
# would thin out to a haze.
def sym_figma():
    """The Figma mark, where a screen is settled before any of it is built.

    Five shapes on a 2x3 grid, in its five official colours and their official
    places: three down the left, a lobe top right, a loose circle in the middle
    and another at the foot.  The real mark has them touching, which fuses the
    left column into a slab; insetting each piece puts the gaps back.
    """
    im, d = raster()
    s, ox, oy, g = 1.12, 28.7, 18.0, 0.9          # logo units are 38 x 57

    def at(x, y):
        return ox + x * s, oy + y * s

    def blob(cx, cy, r, ink):
        (x, y), rr = at(cx, cy), (r - g) * s
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=ink)

    def half(x0, y0, side, ink):
        """One cell of the grid, with its outer edge rounded to a semicircle."""
        blob(x0 + 9.5, y0 + 9.5, 9.5, ink)
        a, b = at(x0 + (9.5 if side < 0 else g), y0 + g)
        c, e = at(x0 + (19 - g if side < 0 else 9.5), y0 + 19 - g)
        d.rectangle([a, b, c, e], fill=ink)

    half(0, 0, -1, 1)           # top left
    half(19, 0, +1, 2)          # top right
    half(0, 19, -1, 3)          # middle left
    blob(28.5, 28.5, 9.5, 4)    # the loose circle, middle right
    blob(9.5, 47.5, 9.5, 5)     # and the foot
    return im, ["#F24E1E", "#A259FF", "#FF7262", "#1ABCFE", "#0ACF83"]


def sym_term():
    """>_ - Claude Code and Codex, where most of the day actually starts."""
    im, d = raster()
    stroke(d, rrect(8, 20, 84, 60, 9), 3.6, closed=True, ink=1)
    stroke(d, [(28, 40), (44, 53), (28, 66)], 5.0, ink=2)
    stroke(d, [(52, 66), (74, 66)], 5.0, ink=2)
    return im, ["#D97757", "#F4A88C"]           # Claude coral, and its light tint


def sym_code():
    """</> - the games are hand-written HTML, CSS and JavaScript.

    Three strokes, so each takes one of the three languages' own colours.
    """
    im, d = raster()
    stroke(d, [(35, 27), (15, 50), (35, 73)], 5.6, ink=1)
    stroke(d, [(58, 19), (42, 81)], 5.6, ink=2)
    stroke(d, [(65, 27), (85, 50), (65, 73)], 5.6, ink=3)
    return im, ["#E34F26", "#1572B6", "#F7DF1E"]   # HTML5, CSS3, JavaScript


def sym_react():
    """The React mark: what the bigger builds are put together with."""
    im, d = raster()
    for tilt in (0, 60, 120):
        stroke(d, ellipse_path(50, 50, 42, 16, tilt), 3.4, closed=True, ink=1)
    disc(d, 50, 50, 6.4, ink=2)
    return im, ["#61DAFB", "#3178C6"]           # React cyan, TypeScript blue


def sym_vite():
    """Vite's bolt inside its shield: the build step under every game."""
    im, d = raster()
    stroke(d, [(13, 17), (50, 89), (87, 17)], 4.6, ink=1)          # the shield
    poly(d, [(59, 26), (37, 55), (49, 55), (43, 80), (65, 49), (53, 49)], ink=2)  # the bolt
    return im, ["#BD34FE", "#FFD028"]           # Vite purple, Vite yellow


def sym_git():
    """The branch glyph: git, and the GitHub the whole README lives on."""
    im, d = raster()
    stroke(d, [(33, 30), (33, 74)], 4.2, ink=1)                      # the trunk
    stroke(d, bez((33, 58), (33, 42), (52, 34), (67, 34)), 4.2, ink=1)  # the branch
    for c in ((33, 22), (33, 82), (75, 34)):
        disc(d, c[0], c[1], 8.0, ink=2)                              # and the commits
    return im, ["#F05133", "#E6EDF3"]           # git orange, GitHub near-white


def sym_gear():
    """Automation: the n8n and WAHA flows, and the CI that runs the rest."""
    im, d = raster()
    teeth, r_out, r_in = 8, 40.0, 30.0
    pts = []
    for i in range(teeth):
        a = 360.0 * i / teeth
        pts += arc(50, 50, r_out, a - 13, a + 13, 10)
        pts += arc(50, 50, r_in, a + 19, a + 360.0 / teeth - 19, 10)
    poly(d, pts, ink=1)
    punch(d, 50, 50, 14.0)
    return im, ["#EA4B71"]                      # n8n pink


def sym_data():
    """Postgres behind the automations, IndexedDB inside the games."""
    im, d = raster()
    rx, ry = 29.0, 10.5

    def front(y):
        """The near half of the ellipse at this height - the visible curve."""
        return [(50 + rx * math.cos(math.radians(a)), y + ry * math.sin(math.radians(a)))
                for a in range(0, 181, 3)]

    for y in (45, 62):
        stroke(d, front(y), 3.8, ink=1)                            # the courses
    stroke(d, front(73), 3.8, ink=1)                               # and the base
    stroke(d, [(50 - rx, 27), (50 - rx, 73)], 3.8, ink=1)          # the sides
    stroke(d, [(50 + rx, 27), (50 + rx, 73)], 3.8, ink=1)
    stroke(d, ellipse_path(50, 27, rx, ry, 0), 3.8, closed=True, ink=2)   # the lid
    return im, ["#4A8BC9", "#7FB3E0"]           # Postgres blue, lifted off navy


def sym_ship():
    """The Vercel triangle: nearly every game in the README ships there."""
    im, d = raster()
    poly(d, [(50, 19), (89, 77), (11, 77)], ink=1)
    return im, ["#FFFFFF"]                      # Vercel is black on white, so white here


# Each mark carries the line that appears under the panel while it is on
# screen, so TOOLCHAIN.SCAN reads as a caption rather than an unrelated ticker.
# It is also where the tools with no usable mark get named outright.
DIM = "#31514c"                 # the separator between tools in a caption
SYMBOLS = [
    (sym_code, [("html", "#E34F26"), (" \u00b7 ", DIM), ("css", "#4A9BE0"),
                (" \u00b7 ", DIM), ("javascript", "#F7DF1E")]),
    (sym_react, [("react", "#61DAFB"), (" \u00b7 ", DIM), ("typescript", "#5A9BE0")]),
    (sym_figma, [("figma", "#A259FF")]),
    (sym_vite, [("vite", "#FFD028")]),
    (sym_git, [("git", "#F05133"), (" \u00b7 ", DIM), ("github", "#E6EDF3")]),
    (sym_gear, [("n8n", "#EA4B71"), (" \u00b7 ", DIM), ("waha", "#25D366"),
                (" \u00b7 ", DIM), ("railway", "#B49BEA")]),
    (sym_data, [("postgres", "#4A8BC9"), (" \u00b7 ", DIM), ("indexeddb", "#7FB3E0")]),
    (sym_ship, [("vercel", "#FFFFFF"), (" \u00b7 ", DIM), ("netlify", "#00C7B7")]),
    (sym_term, [("claude code", "#D97757"), (" \u00b7 ", DIM), ("codex", "#C9CDD4")]),
]
# Shown while the avatar, rather than a mark, is up.  A machine word like
# "standby" reads as the panel waiting for something; this is the line her
# own README opens with, so the rest is what she builds it with.
IDLE = [("classroom idea", "#9BE7C4"), (" → ", "#31514c"),
        ("prototype", "#22D3EE"), (" → ", "#31514c"),
        ("shipped", "#00FF9C")]


# ------------------------------------------------------------------ colour
# The avatar is coloured from the photo it was dithered out of, not from a
# palette anyone guessed at.  assets/portrait-colour.png is her GitHub avatar
# resampled onto the stipple's own grid - found by correlating the two, which
# lines up at 0.87 - so this only has to read a colour per pixel.
#
# What it does have to do is fix the brightness.  How densely the dots sit is
# already the tone of the photo, so painting them in the photo's own luminance
# squares it: hair at a tenth brightness drawn a tenth as densely disappears,
# and the face goes to paper.  That is what made the earlier pass look like a
# ghost.  The curve below flattens luminance hard - LO is the floor even pure
# black is lifted to - and keeps the hue and saturation untouched, so density
# carries the shading and the photo carries the colour.
LO, HI, GAMMA, SAT = 0.22, 1.0, 0.52, 1.10

# Placed against the recovered tone, and kept light: the photo already has her
# make-up in it, so these only lift what is there.  The eyes are the exception
# worth the trouble - both sit in shadow, and at this dot size they close up to
# a smudge without a brighter white and a catchlight.
EYES = ((134, 137, 17, 5.6), (187, 137, 13.5, 5.4))
CHEEKS = ((107, 166), (191, 159))
MOUTH = (161, 198, 30, 13)      # found from the lip-coloured pixels themselves,
                                # not by eye: her head is turned, so the mouth sits
                                # right of centre and lower than it looks
SCLERA = (238, 245, 255)
GLINT = (255, 255, 255)
BLUSH = (232, 126, 120)
LIPS = (252, 116, 158)          # a rose that still reads as pink beside the skin;
                                # both clamp red at 255 once lifted, so the tint has
                                # to carry in green and blue or it vanishes


def _smooth(a):
    a = 0.0 if a < 0 else (1.0 if a > 1 else a)
    return a * a * (3 - 2 * a)


def _mix(base, top, w):
    if w <= 0:
        return base
    return tuple(base[c] + (top[c] - base[c]) * w for c in range(3))


def _ell(x, y, cx, cy, rx, ry, feather=0.18):
    d = math.hypot((x - cx) / rx, (y - cy) / ry)
    return _smooth((1.0 + feather - d) / feather)


def paint(mask, pts):
    """A colour for every lit pixel of the portrait."""
    ref = Image.open(REF).convert("RGB").load()
    out = {}
    for x, y in pts:
        r, g, b = ref[x, y]

        # Her hair is shot against a lilac backdrop and the fine strands let it
        # through, so the avatar is violet where the cut-out the stipple came
        # from is hair.  The density there is a real highlight and worth
        # keeping; only the colour is wrong.
        #
        # Two casts to catch, and both have to miss the navy of the jacket and
        # the warmth of her skin.  Lilac leaves green the darkest channel, which
        # skin never does (blue is) and navy never does (red is).  The paler
        # wash at the crown is blue-led but bright and almost grey, where the
        # jacket is blue-led and dark.  Caught pixels lose the cast and some of
        # the lift, so the crown reads as sheen on black hair rather than a halo.
        # Her mouth is exempt.  Rose has green as its darkest channel just as
        # lilac does, so the first test catches her lips too and flattens them
        # to grey, which against warm skin reads as blue.  Telling the two
        # apart by how far red runs ahead of blue does fix the mouth, but it
        # then lets warm mid-dark hair through as well - and lifting a dark
        # brown only makes a lighter brown, which is salmon.  The mouth is one
        # small place in a known spot, so excluding it there is the honest fix.
        mx, mn = max(r, g, b), min(r, g, b)
        lit = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
        mouth = _ell(x, y, *MOUTH, 0.30) > 0.3
        if (not mouth and g < r and g < b) or (b >= r and b >= g and lit > 0.28
                                               and (mx - mn) / max(mx, 1) < 0.50):
            v = lit * 255.0 * 0.76
            r, g, b = v * 1.06, v * 0.97, v * 0.93

        lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
        k = (LO + (HI - LO) * (max(lum, 0.0) ** GAMMA)) / max(lum, 0.004)
        c = [r * k, g * k, b * k]
        grey = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
        c = [grey + (v - grey) * SAT for v in c]

        # Lips.  The photo has them barely a shade off the skin around them, so
        # they read as nothing but a dark line at this dot size.  Which pixels
        # are lip is decided by colour rather than by the ellipse alone: lips
        # run redder than the skin beside them, about 0.52 green-to-red against
        # 0.63, so the ellipse says where to look and the ratio says what to
        # tint.  That keeps the chin and the philtrum out of it.
        if mouth:
            w = _ell(x, y, *MOUTH, 0.30) * _smooth((0.615 - g / max(r, 1)) / 0.090)
            c = _mix(c, LIPS, w * 0.72)

        for cx, cy in CHEEKS:
            c = _mix(c, BLUSH, _ell(x, y, cx, cy, 26, 21, 0.9) * 0.10)

        for cx, cy, rx, ry in EYES:
            eye = _ell(x, y, cx, cy, rx, ry, 0.13)
            if eye <= 0:
                continue
            iris = _ell(x, y, cx, cy, 6.0, 5.2, 0.22)
            c = _mix(c, SCLERA, eye * (1 - iris) * 0.55)
            c = _mix(c, GLINT, _ell(x, y, cx + 2.4, cy - 1.5, 1.9, 1.6, 0.5) * 0.85)

        out[(x, y)] = tuple(max(0, min(255, int(round(v)))) for v in c)
    return out


def quantize(colours, n):
    """Cut the painted pixels down to n inks.

    Every distinct colour would mean its own <path> inside every fragment it
    touches.  Quantising first keeps that to a handful per fragment, and at
    this dot size the banding it introduces is invisible.
    """
    keys = list(colours)
    strip = Image.new("RGB", (len(keys), 1))
    strip.putdata([colours[k] for k in keys])
    pal = strip.quantize(colors=n, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    table = pal.getpalette()
    inks = ["#%02X%02X%02X" % tuple(table[i * 3:i * 3 + 3]) for i in range(n)]
    idx = list(pal.getdata()) if not hasattr(pal, "get_flattened_data") else list(pal.get_flattened_data())
    return inks, {k: idx[i] for i, k in enumerate(keys)}


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
    """A symbol's mask -> n points in the avatar's space, each with its ink.

    The ink is the pixel's own value on the canvas, so a dot keeps whichever
    region of the mark it was sampled from and can be coloured by it.
    """
    pts = scatter(mask_points(im), n)
    ink = im.load()
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    s = min(SYM_W / max(x1 - x0, 1), SYM_H / max(y1 - y0, 1))
    mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    return [(SYM_CX + (x - mx) * s, SYM_CY + (y - my) * s, ink[x, y] - 1) for x, y in pts]


# ------------------------------------------------------------------ output
def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fmt(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def ktimes(ks):
    return ";".join(f"{k:.4f}".rstrip("0").rstrip(".") for k in ks)


def splines(kts):
    return ";".join([EASE] * (len(kts) - 1))


# The loop, laid out once from the durations above.  K is the stop list the
# particles use - rest, then each symbol twice (arrive, then hold out), then
# home - and the named fractions are the moments the two layers hand over.
LOOP = REST + DISSOLVE + len(SYMBOLS) * HOLD + (len(SYMBOLS) - 1) * MORPH + RETURN + SETTLE
F_REST = REST / LOOP                            # the avatar starts to come apart
F_SYM1 = (REST + DISSOLVE) / LOOP               # the first symbol is formed
F_BACK = (LOOP - SETTLE - RETURN) / LOOP        # the dots set off home
F_HOME = (LOOP - SETTLE) / LOOP                 # and land on their own pixels


def _stops():
    ks, t = [0.0], REST + DISSOLVE
    ks.append(F_REST)
    for i in range(len(SYMBOLS)):
        if i:
            t += MORPH
        ks.append(t / LOOP)                     # this symbol is formed
        t += HOLD
        ks.append(t / LOOP)                     # and has been held
    ks.append(F_HOME)
    ks.append(1.0)
    return ks


K = _stops()


COMET_PERIOD = 30.0             # the whole procession repeats on this
COMET_GAP = 3.0                 # and one sets off every this many seconds
COMET_TINTS = ("ice", "mint", "iris")


def comet_defs():
    """One reusable comet, drawn head at the origin with its tail along -x.

    The tail is a filled taper, not a stroked line.  A constant-width stroke
    with a gradient on it reads as a laser: the edge stays hard all the way out
    and the head sits on it like a bead.  This one is two quadratics meeting at
    a point, so it is widest at the head and fades to nothing, and the head is a
    tight core rather than a blob.

    The glow is two gradients rather than a blur filter.  A feGaussianBlur on
    ten moving groups is re-rasterised every frame for something that is never
    more than a few pixels across; a radial halo behind the head and a linear
    fade down the tail cost nothing and render the same everywhere.

    The tail gradient is in user space, not on the bounding box: the tail is a
    horizontal line, so its box has no height, and a bounding-box gradient on
    that is undefined and drops out in some renderers.
    """
    out = ['<radialGradient id="halo">'
           '<stop offset="0" stop-color="#FFFFFF" stop-opacity=".95"/>'
           '<stop offset="0.18" stop-color="#EAF7FF" stop-opacity=".55"/>'
           '<stop offset="0.45" stop-color="#A8DBFF" stop-opacity=".17"/>'
           '<stop offset="1" stop-color="#7FB8FF" stop-opacity="0"/></radialGradient>']
    for name, mid, far in (("ice", "#CFF3FF", "#7FD8FF"),
                           ("mint", "#B8F5D8", "#4FE0A8"),
                           ("iris", "#DCCFFF", "#9B7FF0")):
        out.append(
            f'<linearGradient id="t{name}" gradientUnits="userSpaceOnUse"'
            f' x1="-100" y1="0" x2="0" y2="0">'
            f'<stop offset="0" stop-color="{far}" stop-opacity="0"/>'
            f'<stop offset="0.45" stop-color="{far}" stop-opacity=".09"/>'
            f'<stop offset="0.78" stop-color="{mid}" stop-opacity=".28"/>'
            f'<stop offset="0.95" stop-color="{mid}" stop-opacity=".60"/>'
            f'<stop offset="1" stop-color="#F2FBFF" stop-opacity=".88"/></linearGradient>')
        out.append(
            f'<g id="c{name}">'
            f'<path d="M0 -1.45Q-30 -0.85 -100 0Q-30 0.85 0 1.45Z" fill="url(#t{name})"/>'
            f'<circle r="4.1" fill="url(#halo)"/>'
            f'<circle r="0.95" fill="#FFFFFF"/></g>')
    return out


def comets_svg():
    """A procession of them, one setting off every COMET_GAP seconds.

    Depth is carried by three things at once, because scale alone reads as a
    near comet that happens to be small: a far one is also dimmer and slower,
    since parallax is what actually says how distant something is.  One is
    deliberately much larger than the rest so the stream has an event in it.
    """
    cx, cy, reach = 259.0, 379.0, 430.0
    n = int(round(COMET_PERIOD / COMET_GAP))
    out = []
    for i in range(n):
        big = (i == 3)
        if big:
            scale, alpha, cross = 1.75, 1.0, 5.5
        else:
            # most sit far back; a couple come closer
            z = RNG.choice([0.34, 0.40, 0.46, 0.52, 0.60, 0.72, 0.95, 1.20])
            scale, alpha = z, min(0.95, 0.30 + 0.62 * z)
            # The far ones take longest to cross.  That is the parallax: they
            # are the same distance across the panel either way, so the only
            # thing that can say they are further off is taking longer over it.
            cross = 11.5 - 5.0 * min(z, 1.2) / 1.2

        # Right to left, on one heading.  The earlier spread ran from 158 to 202
        # degrees, which is left-and-down for half of them and left-and-up for
        # the other half - two directions, however narrow the band.  A meteor
        # shower is parallel; these are too, give or take three degrees.
        ang = math.radians(RNG.uniform(165, 171))
        dx, dy = math.cos(ang), math.sin(ang)
        off = RNG.uniform(-250, 250)
        px, py = -dy * off, dx * off
        x0, y0 = cx + px - dx * reach, cy + py - dy * reach
        x1, y1 = cx + px + dx * reach, cy + py + dy * reach

        begin = i * COMET_GAP + RNG.uniform(-0.25, 0.25)
        a = cross / COMET_PERIOD
        tint = COMET_TINTS[i % len(COMET_TINTS)]
        out.append(
            f'<g opacity="0">'
            # Every one of these has to be a fraction of the crossing, not of the
            # period.  A fixed fade-in put keyTimes out of order once the cross
            # was short, and an out-of-order list makes the whole animation
            # invalid - the comets simply never appeared.
            f'<animate attributeName="opacity" values="0;{alpha:.2f};{alpha:.2f};0;0"'
            f' keyTimes="0;{a * 0.12:.4f};{a * 0.74:.4f};{a:.4f};1" dur="{COMET_PERIOD}s"'
            f' begin="{begin:.2f}s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate"'
            f' values="{x0:.0f} {y0:.0f};{x1:.0f} {y1:.0f};{x1:.0f} {y1:.0f}"'
            f' keyTimes="0;{a:.4f};1" dur="{COMET_PERIOD}s" begin="{begin:.2f}s"'
            f' repeatCount="indefinite"/>'
            f'<use href="#c{tint}" transform="rotate({math.degrees(ang):.1f})'
            f' scale({scale:.2f})"/></g>')
    return out


def space_svg():
    """A quiet starfield behind her, and a comet through it now and then.

    Panel coordinates, not the avatar's, so this sits under both layers and
    needs no transform.  Stars are given their own periods and offsets rather
    than a shared one: a field that pulses together reads as a flicker, and the
    point is that it should barely be noticed.  Nothing is drawn over the face
    itself - the stipple is dense there and a star behind it only muddies her -
    so the field thins out toward the middle.
    """
    out = []
    cx, cy = 259.0, 380.0                       # roughly where her head sits
    for _ in range(190):
        x = RNG.uniform(PANEL[0] + 4, PANEL[0] + PANEL[2] - 4)
        y = RNG.uniform(PANEL[1] + 4, PANEL[1] + PANEL[3] - 4)
        # thin the field out over her, and keep it off the caption bar
        near = math.hypot((x - cx) / 150.0, (y - cy) / 210.0)
        if near < 1.0 and RNG.random() > near * near * 0.7:
            continue
        if y > 596:
            continue
        r = RNG.choice([0.5, 0.5, 0.6, 0.7, 0.7, 0.9, 1.1])
        hi = RNG.uniform(0.30, 0.85) * (0.6 if r < 0.6 else 1.0)
        lo = hi * RNG.uniform(0.15, 0.45)
        dur = RNG.uniform(2.4, 7.5)
        col = RNG.choice(["#CFF3FF", "#CFF3FF", "#9BE7C4", "#B9A7FA", "#FFFFFF"])
        out.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{col}" opacity="{lo:.2f}">'
            f'<animate attributeName="opacity" values="{lo:.2f};{hi:.2f};{lo:.2f}"'
            f' dur="{dur:.1f}s" begin="-{RNG.uniform(0, dur):.1f}s"'
            f' repeatCount="indefinite"/></circle>')

    return out


def occluder_svg(mask):
    """A solid silhouette of her, in the panel's own colour, under the stipple.

    The stipple only covers about a sixth of the pixels it spans, so anything
    drawn behind her shows through the gaps - a comet crossing behind her hair
    reads as crossing over it.  Being behind in document order is not enough;
    something has to actually stop the light.

    It is filled with the panel background, so it is invisible except for what
    it hides, and it fades on the same beats as the fragments.  It has to: left
    solid through the symbols it would punch a person-shaped hole in the sky,
    and comets would wink out crossing an empty panel.

    Emitted as horizontal runs rather than per pixel - a filled shape is a
    handful of spans per row instead of a few hundred rects.
    """
    px = mask.load()
    W, H = mask.size
    blur = mask.filter(ImageFilter.GaussianBlur(3.0)).load()

    runs, solid = [], 0
    for y in range(H):
        x = 0
        while x < W:
            if px[x, y] or blur[x, y] > 9:       # a dot, or dots close by
                x0 = x
                gap = 0
                while x < W and gap < 3:         # bridge the dither's own gaps
                    if px[x, y] or blur[x, y] > 9:
                        gap = 0
                    else:
                        gap += 1
                    x += 1
                x1 = x - gap
                if x1 > x0:
                    runs.append(f"M{x0} {y}h{x1 - x0}v1h-{x1 - x0}z")
                    solid += x1 - x0
            else:
                x += 1

    kt = [0, F_REST, F_REST + 0.72 * DISSOLVE / LOOP,
          F_HOME - 0.30 * RETURN / LOOP, F_HOME + 0.34 * SETTLE / LOOP, 1]
    return [f'<g transform="translate(44.0 115.1) scale(1.604)" shape-rendering="crispEdges">'
            f'<path d="{"".join(runs)}" fill="{PANEL_BG}">'
            f'<animate attributeName="opacity" values="1;1;0;0;1;1" keyTimes="{ktimes(kt)}"'
            f' dur="{LOOP}s" begin="{BEGIN}s" repeatCount="indefinite"'
            f' calcMode="spline" keySplines="{splines(kt)}"/></path></g>'], len(runs), solid


def tiles_svg(pts, cx, cy, inks, ink_of):
    """The avatar, cut into fragments that fly apart and come back.

    A fragment is one <g> carrying the animation, with one <path> inside per
    ink it contains.  Keeping the animation on the group is what makes the
    colour affordable: the paths multiply, the four animations do not.
    """
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
        by_ink = {}
        for p in cell:
            by_ink.setdefault(ink_of[p], []).append(p)
        paths = "".join(
            '<path d="%s" fill="%s"/>' % ("".join(f"M{x} {y}h1v1h-1z" for x, y in ps), inks[k])
            for k, ps in sorted(by_ink.items()))

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
        j = RNG.uniform(-0.009, 0.009)
        kt_t = [0, F_REST + j, F_SYM1 + j, F_BACK + j, F_HOME + j, 1]
        # A fragment is all but gone before it has finished travelling, and on
        # the way back it is lit again as it arrives, so the crossfade with the
        # particles happens where both are in the same place.
        kt_o = [0, F_REST + j, F_REST + 0.75 * DISSOLVE / LOOP + j,
                F_HOME - 0.30 * RETURN / LOOP + j, F_HOME + 0.30 * SETTLE / LOOP + j, 1]

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
            f' calcMode="spline" keySplines="{splines(kt_o)}"/>'
            f'<animateTransform attributeName="transform" type="translate"'
            f' values="0 0;0 0;{fmt(ox)} {fmt(oy)};{fmt(ox)} {fmt(oy)};0 0;0 0"'
            f' keyTimes="{ktimes(kt_t)}" dur="{LOOP}s" begin="{BEGIN}s" repeatCount="indefinite"'
            f' calcMode="spline" keySplines="{splines(kt_t)}"/>'
            f'{paths}</g>')
    return out


def particles_svg(home, home_ink, shapes, palettes):
    """The dots: avatar pixel -> each mark in turn -> the same pixel back.

    Colour is carried by grouping rather than per dot.  A dot's colour at every
    stop is fixed once its rank is, so dots that share a whole colour sequence
    share a <g> and one <animate> recolours all of them.  Because the marks'
    regions fall in roughly contiguous bands of polar rank, the number of
    distinct sequences stays in the dozens rather than the product of the
    region counts - a per-dot fill animation would cost several hundred KB.
    """
    rank_home = polar_rank(home)
    rank_sym = [polar_rank(s) for s in shapes]

    groups = {}
    for r in range(len(home)):
        h = home_ink[rank_home[r]]
        seq = tuple(palettes[k][shapes[k][rank_sym[k][r]][2]] for k in range(len(shapes)))
        groups.setdefault((h,) + seq, []).append(r)

    out = []
    for key, ranks in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        h, seq = key[0], key[1:]
        vals = ";".join([h, h] + [c for col in seq for c in (col, col)] + [h, h])
        dots = []
        for r in ranks:
            p = home[rank_home[r]]
            stops = [p, p]
            for k, s in enumerate(shapes):
                q = s[rank_sym[k][r]][:2]
                stops.append(q)
                # The second copy of each mark drifts a hair off the first, so
                # the hold breathes instead of freezing dead still.
                stops.append((q[0] + RNG.uniform(-1.1, 1.1), q[1] + RNG.uniform(-1.1, 1.1)))
            stops += [p, p]

            j = RNG.uniform(-0.009, 0.009)
            ks = [K[0]] + [k + j for k in K[1:-1]] + [K[-1]]
            vs = ";".join(f"{fmt(x)} {fmt(y)}" for x, y in stops)
            href = "#e" if RNG.random() < 0.085 else "#d"
            dots.append(
                f'<use href="{href}"><animateTransform attributeName="transform"'
                f' type="translate" values="{vs}" keyTimes="{ktimes(ks)}" dur="{LOOP}s"'
                f' begin="{BEGIN}s" repeatCount="indefinite" calcMode="spline"'
                f' keySplines="{splines(ks)}"/></use>')
        out.append(
            f'<g fill="{h}"><animate attributeName="fill" values="{vals}"'
            f' keyTimes="{ktimes(K)}" dur="{LOOP}s" begin="{BEGIN}s" repeatCount="indefinite"'
            f' calcMode="spline" keySplines="{splines(K)}"/>' + "".join(dots) + '</g>')
    return out, len(groups)


def ticker_svg():
    """The TOOLCHAIN.SCAN line, cut to the same clock as the marks.

    It used to run its own 20s loop against the panel's 30s one, so the name
    underneath drifted against the shape above it and only agreed by accident.
    Both now come off K, so a caption is up exactly while its mark is.  Each
    tool in a caption is set in its own colour, which is also where the ones
    with no symbol of their own - WAHA, Railway, Netlify - get to show theirs.
    """
    lead, tail = 0.45 / LOOP, 0.35 / LOOP        # a beat either side of the hold
    idle = "".join(f'<tspan fill="{c}">{esc(t)}</tspan>' for t, c in IDLE)
    out = [f'<text x="60" y="650" font-size="13" xml:space="preserve">'
           f'<tspan fill="#31514c">&#9656; </tspan>{idle}'
           f'<animate attributeName="opacity" values="1;1;0;0;1;1"'
           f' keyTimes="{ktimes([0, F_REST, F_SYM1, F_BACK, F_BACK + 0.4 / LOOP, 1])}"'
           f' dur="{LOOP}s" begin="{BEGIN}s" repeatCount="indefinite"/></text>']
    for i, (_, caption) in enumerate(SYMBOLS):
        on, off = K[2 + 2 * i], K[3 + 2 * i]
        kt = [0, on - lead, on + 0.10 / LOOP, off, off + tail, 1]
        spans = "".join(f'<tspan fill="{c}">{esc(t)}</tspan>' for t, c in caption)
        out.append(
            f'<text x="60" y="650" font-size="13" opacity="0" xml:space="preserve">'
            f'<tspan fill="#31514c">&#9656; </tspan>{spans}'
            f'<animate attributeName="opacity" values="0;0;1;1;0;0"'
            f' keyTimes="{ktimes(kt)}" dur="{LOOP}s" begin="{BEGIN}s"'
            f' repeatCount="indefinite"/></text>')
    return out


def main():
    mask = Image.open(MASK).convert("L")
    pts = mask_points(mask)
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)

    painted = paint(mask, pts)
    inks, ink_of = quantize(painted, N_INKS)

    home = sample_tone(pts, N_PARTICLES)
    # The dots take the colour of the pixel they came off, cut to a few tones.
    # Every extra tone multiplies the number of colour groups, and a handful is
    # enough for the cloud to resolve into a face rather than a pale smear.
    tones, tone_of = quantize({p: painted[p] for p in home}, N_DOT_TONES)
    home_ink = [tones[tone_of[p]] for p in home]

    built = [fn() for fn, _ in SYMBOLS]
    shapes = [place(im, N_PARTICLES) for im, _ in built]
    palettes = [pal for _, pal in built]

    kt_p = [0, F_REST, F_SYM1, F_HOME - 0.22 * RETURN / LOOP, F_HOME,
            F_HOME + 0.28 * SETTLE / LOOP, 1]
    dots, n_groups = particles_svg(home, home_ink, shapes, palettes)
    occ, n_runs, n_solid = occluder_svg(mask)
    # Fragments travel far enough to clear the face; the clip keeps the ones
    # that overshoot from spilling onto the SYSTEM.INFO column next door.
    body = [
        '<defs>' + ''.join(comet_defs()) + '</defs>',
        '<g clip-path="url(#pan)">',
        *space_svg(),
        *comets_svg(),
        *occ,
        '<g transform="translate(44.0 115.1) scale(1.604)" shape-rendering="crispEdges">',
        *tiles_svg(pts, cx, cy, inks, ink_of),
        '</g>',
        '',
        '<g transform="translate(44.0 115.1) scale(1.604)" shape-rendering="crispEdges"'
        ' opacity="0">'
        f'<animate attributeName="opacity" values="0;0;1;1;1;0;0" keyTimes="{ktimes(kt_p)}"'
        f' dur="{LOOP}s" begin="{BEGIN}s" repeatCount="indefinite"'
        f' calcMode="spline" keySplines="{splines(kt_p)}"/>',
        *dots,
        '</g>',
        '</g>',
    ]

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(HEAD)
        f.write("\n".join(body))
        f.write("\n")
        f.write(TAIL.replace("<!--TICKER-->", "\n".join(ticker_svg())))
    print(f"{OUT}  {os.path.getsize(OUT) / 1024:.0f} KB  "
          f"{len(pts)} avatar px in {N_INKS} inks, {N_PARTICLES} particles in "
          f"{n_groups} colour groups, {len(SYMBOLS)} symbols, {LOOP:.1f}s loop")


if __name__ == "__main__":
    main()
