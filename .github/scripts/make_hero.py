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
    <stop offset="0" stop-color="#7FEFC8"><animate attributeName="stop-color" values="#7FEFC8;#74D2FB;#C0A2FF;#7FEFC8" dur="14s" repeatCount="indefinite"/></stop>
    <stop offset="0.55" stop-color="#74D2FB"><animate attributeName="stop-color" values="#74D2FB;#C0A2FF;#7FEFC8;#74D2FB" dur="14s" repeatCount="indefinite"/></stop>
    <stop offset="1" stop-color="#C0A2FF"><animate attributeName="stop-color" values="#C0A2FF;#7FEFC8;#74D2FB;#C0A2FF" dur="14s" repeatCount="indefinite"/></stop>
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
OUT = os.path.join(ROOT, "assets", "hero-v13.svg")

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


def bez(p0, p1, p2, p3, steps=90):
    """A cubic, for the one curve in the set - the git branch."""
    out = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def ring(d, cx, cy, r, w):
    stroke(d, arc(cx, cy, r), w, closed=True)


def poly(d, pts):
    d.polygon(to_px(pts), fill=255)


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
# The run of the working day: open the terminal, write it, build it with a
# framework, check it against the design, bundle it, commit it, automate round
# it, put the data somewhere, ship it.  Figma sits mid-set rather than first
# because the avatar hands straight over to whatever opens the loop, and that
# wants to be the work itself.  Every mark has to survive being redrawn as 1550
# dots, and that test shapes how each one is drawn.  Fine detail does not
# survive it - the Octocat loses its silhouette, so GitHub is the branch
# glyph.  Nor does a mark that only works in colour, which is why the Figma
# pieces below are inset apart: at full size they touch, and in one colour
# that fuses them into a slab.
#
# Some tools have no mark anyone reads out of context at all.  That is the
# honest position for WAHA, Railway and n8n, so automation is a plain gear and
# those three are named outright in the caption under it, where they are read
# rather than guessed.
#
# Most of these are stroked, which holds their weight even.  The two solids -
# the Vite bolt and the Vercel triangle - are shapes that lose their identity
# as outlines: an outlined triangle is a generic delta, not the Vercel mark.
# Both are small enough that 1550 dots still read as a solid; a fill across
# the whole box would thin out to a haze.
def sym_figma():
    """The Figma mark, where a screen is settled before any of it is built.

    Five shapes on a 2x3 grid: three down the left, a lobe top right, a loose
    circle in the middle and another at the foot.  The real mark has them
    touching, which in one colour fuses the whole left column into a slab.
    Insetting each piece puts the gaps back, and it is the five-piece
    arrangement that identifies it once the colour is gone.
    """
    im, d = raster()
    s, ox, oy, g = 1.12, 28.7, 18.0, 0.9          # logo units are 38 x 57

    def at(x, y):
        return ox + x * s, oy + y * s

    def blob(cx, cy, r):
        (x, y), rr = at(cx, cy), (r - g) * s
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=255)

    def half(x0, y0, side):
        """One cell of the grid, with its outer edge rounded to a semicircle."""
        blob(x0 + 9.5, y0 + 9.5, 9.5)
        a, b = at(x0 + (9.5 if side < 0 else g), y0 + g)
        c, e = at(x0 + (19 - g if side < 0 else 9.5), y0 + 19 - g)
        d.rectangle([a, b, c, e], fill=255)

    half(0, 0, -1)          # top left, rounded left
    half(19, 0, +1)         # top right, rounded right
    half(0, 19, -1)         # middle left, rounded left
    blob(28.5, 28.5, 9.5)   # the loose circle, middle right
    blob(9.5, 47.5, 9.5)    # and the foot
    return im


def sym_term():
    """>_ - Claude Code and Codex, where most of the day actually starts."""
    im, d = raster()
    stroke(d, rrect(8, 20, 84, 60, 9), 3.6, closed=True)
    stroke(d, [(28, 40), (44, 53), (28, 66)], 5.0)
    stroke(d, [(52, 66), (74, 66)], 5.0)
    return im


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


def sym_vite():
    """Vite's bolt: the build step under every one of those games."""
    im, d = raster()
    poly(d, [(62, 8), (30, 54), (46, 54), (38, 92), (72, 44), (54, 44)])
    return im


def sym_git():
    """The branch glyph: git, and the GitHub the whole README lives on."""
    im, d = raster()
    stroke(d, [(33, 30), (33, 74)], 4.2)                      # the trunk
    stroke(d, bez((33, 58), (33, 42), (52, 34), (67, 34)), 4.2)  # and the branch
    for c in ((33, 22), (33, 82), (75, 34)):
        disc(d, c[0], c[1], 8.0)
    return im


def sym_gear():
    """Automation: the n8n and WAHA flows, and the CI that runs the rest."""
    im, d = raster()
    teeth, r_out, r_in = 8, 40.0, 30.0
    pts = []
    for i in range(teeth):
        a = 360.0 * i / teeth
        pts += arc(50, 50, r_out, a - 13, a + 13, 10)
        pts += arc(50, 50, r_in, a + 19, a + 360.0 / teeth - 19, 10)
    poly(d, pts)
    punch(d, 50, 50, 14.0)
    return im


def sym_data():
    """Postgres behind the automations, IndexedDB inside the games."""
    im, d = raster()
    rx, ry = 29.0, 10.5

    def front(y):
        """The near half of the ellipse at this height - the visible curve."""
        return [(50 + rx * math.cos(math.radians(a)), y + ry * math.sin(math.radians(a)))
                for a in range(0, 181, 3)]

    stroke(d, ellipse_path(50, 27, rx, ry, 0), 3.8, closed=True)   # the lid
    for y in (45, 62):
        stroke(d, front(y), 3.8)                                   # the courses
    stroke(d, front(73), 3.8)                                      # and the base
    stroke(d, [(50 - rx, 27), (50 - rx, 73)], 3.8)                 # the sides
    stroke(d, [(50 + rx, 27), (50 + rx, 73)], 3.8)
    return im


def sym_ship():
    """The Vercel triangle: nearly every game in the README ships there."""
    im, d = raster()
    poly(d, [(50, 19), (89, 77), (11, 77)])
    return im


# Each mark carries the line that appears under the panel while it is on
# screen, so TOOLCHAIN.SCAN reads as a caption rather than an unrelated
# ticker.  It is also where the tools with no usable mark get named outright:
# the gear is n8n, WAHA and Railway, and the triangle is both hosts.
#
# The third field is the colour the whole dot cloud takes while that mark is
# up.  Each is its tool's own, lifted toward the light end - a brand colour
# picked for white backgrounds goes muddy on a near-black panel, and Postgres
# navy in particular disappears into it.  They are also ordered so no two
# neighbours land on the same part of the wheel, which is why GitHub is the
# near-white break between Vite's amber and n8n's pink rather than git orange.
SYMBOLS = [
    (sym_term, "claude code · codex", "#E8865F"),      # Claude coral
    (sym_code, "html · css · javascript", "#F7DF1E"),  # JavaScript yellow
    (sym_react, "react · typescript", "#61DAFB"),      # React cyan
    (sym_figma, "figma", "#A259FF"),                        # Figma purple
    (sym_vite, "vite", "#FFC016"),                          # Vite amber
    (sym_git, "git · github", "#E6EDF3"),              # GitHub near-white
    (sym_gear, "n8n · waha · railway", "#EA4B71"),  # n8n pink
    (sym_data, "postgres · indexeddb", "#6BA6E8"),     # Postgres blue, lifted
    (sym_ship, "vercel · netlify", "#00E5C7"),         # Netlify teal
]
IDLE = "standby"                # shown while the avatar, not a symbol, is up
HOME = "#CFF3FF"                # the cloud's colour while it is her face


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
            # The second copy of each symbol drifts a hair off the first, so
            # the hold breathes instead of freezing dead still.
            stops.append((q[0] + RNG.uniform(-1.1, 1.1), q[1] + RNG.uniform(-1.1, 1.1)))
        stops += [p, p]

        j = RNG.uniform(-0.009, 0.009)
        ks = [K[0]] + [k + j for k in K[1:-1]] + [K[-1]]
        vals = ";".join(f"{fmt(x)} {fmt(y)}" for x, y in stops)
        href = "#e" if RNG.random() < 0.085 else "#d"
        out.append(
            f'<use href="{href}"><animateTransform attributeName="transform"'
            f' type="translate" values="{vals}" keyTimes="{ktimes(ks)}" dur="{LOOP}s"'
            f' begin="{BEGIN}s" repeatCount="indefinite" calcMode="spline"'
            f' keySplines="{splines(ks)}"/></use>')
    return out


def tints():
    """The cloud's colour at each stop: home, each mark twice, home again."""
    out = [HOME, HOME]
    for _, _, colour in SYMBOLS:
        out += [colour, colour]
    return ";".join(out + [HOME, HOME])


def ticker_svg():
    """The TOOLCHAIN.SCAN line, cut to the same clock as the symbols.

    It used to run its own 20s loop against the panel's 30s one, so the name
    underneath drifted against the shape above it and only agreed by accident.
    Both now come off K, so a label is up exactly while its mark is.
    """
    lead, tail = 0.45 / LOOP, 0.35 / LOOP        # a beat either side of the hold
    out = [f'<text x="60" y="650" font-size="13" fill="#31514c">&#9656; {IDLE}'
           f'<animate attributeName="opacity" values="1;1;0;0;1;1"'
           f' keyTimes="{ktimes([0, F_REST, F_SYM1, F_BACK, F_BACK + 0.4 / LOOP, 1])}"'
           f' dur="{LOOP}s" begin="{BEGIN}s" repeatCount="indefinite"/></text>']
    for i, (_, label, colour) in enumerate(SYMBOLS):
        on, off = K[2 + 2 * i], K[3 + 2 * i]
        kt = [0, on - lead, on + 0.10 / LOOP, off, off + tail, 1]
        # The caption takes the mark's colour too, so the line under the panel
        # and the cloud above it are visibly the same thing.
        out.append(
            f'<text x="60" y="650" font-size="13" fill="{colour}" opacity="0">'
            f'&#9656; {label}<animate attributeName="opacity" values="0;0;1;1;0;0"'
            f' keyTimes="{ktimes(kt)}" dur="{LOOP}s" begin="{BEGIN}s"'
            f' repeatCount="indefinite"/></text>')
    return out


def main():
    im = Image.open(MASK).convert("L")
    pts = mask_points(im)
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)

    home = sample_tone(pts, N_PARTICLES)
    shapes = [place(fn(), N_PARTICLES) for fn, _, _ in SYMBOLS]

    kt_p = [0, F_REST, F_SYM1, F_HOME - 0.22 * RETURN / LOOP, F_HOME,
            F_HOME + 0.28 * SETTLE / LOOP, 1]
    # Fragments travel far enough to clear the face; the clip keeps the ones
    # that overshoot from spilling onto the SYSTEM.INFO column next door.
    body = [
        '<g clip-path="url(#pan)">',
        '<g transform="translate(44.0 115.1) scale(1.604)" shape-rendering="crispEdges">',
        *tiles_svg(pts, cx, cy),
        '</g>',
        '',
        '<g transform="translate(44.0 115.1) scale(1.604)" shape-rendering="crispEdges"'
        f' opacity="0" fill="{HOME}">'
        f'<animate attributeName="opacity" values="0;0;1;1;1;0;0" keyTimes="{ktimes(kt_p)}"'
        f' dur="{LOOP}s" begin="{BEGIN}s" repeatCount="indefinite"'
        f' calcMode="spline" keySplines="{splines(kt_p)}"/>'
        # One fill animation on the group recolours all of the dots at once,
        # because #d and #e declare no fill of their own and inherit it.  It
        # runs on the same stops as the movement, so a mark's colour arrives
        # exactly as its shape does.
        f'<animate attributeName="fill" values="{tints()}" keyTimes="{ktimes(K)}"'
        f' dur="{LOOP}s" begin="{BEGIN}s" repeatCount="indefinite"'
        f' calcMode="spline" keySplines="{splines(K)}"/>',
        *particles_svg(home, shapes),
        '</g>',
        '</g>',
    ]

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(HEAD)
        f.write("\n".join(body))
        f.write("\n")
        f.write(TAIL.replace("<!--TICKER-->", "\n".join(ticker_svg())))
    print(f"{OUT}  {os.path.getsize(OUT) / 1024:.0f} KB  "
          f"{len(pts)} avatar px, {N_PARTICLES} particles, "
          f"{len(SYMBOLS)} symbols, {LOOP:.1f}s loop")


if __name__ == "__main__":
    main()
