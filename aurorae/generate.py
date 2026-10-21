#!/usr/bin/env python3
"""Generate the RevoTahoe Aurorae window decoration (macOS Tahoe traffic lights).

Reference: macOS Tahoe dark mode window chrome.
  - 13 px lights on a 20 px pitch, first centre 20 px from the left edge, title bar 32 px
  - close #FF5F57 / ring #E0443E, minimize #FEBC2E / #DEA123, zoom #28C840 / #1AAB29
  - unfocused windows: grey lights; hovering any light shows all three glyphs
    (x, -, two fullscreen triangles), as on macOS
The green light lives in Aurorae's "keepbelow" slot (B): KDE has no fullscreen button, so
the revo KWin bridge turns that toggle into fullscreen (kde-bridge/kwin-bridge.js).

Run: python3 aurorae/generate.py   → writes aurorae/RevoTahoe/
"""
import os

NAME = "RevoTahoe"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), NAME)

TITLEBAR = "#272c31"      # Breeze Dark title bar (kdeglobals [WM] activeBackground)
TITLEBAR_INACTIVE = "#272c31"
BOX = 20                  # button box (ButtonWidth/Height)
R = 6.5                   # light radius → 13 px

LIGHTS = {
    # file: (fill, ring, pressed fill, glyph colour, glyph)
    "close": ("#ff5f57", "#e0443e", "#c9433c", "#4d0000", "x"),
    "minimize": ("#febc2e", "#dea123", "#d29a1c", "#985712", "-"),
    "keepbelow": ("#28c840", "#1aab29", "#1e9a33", "#0b650d", "fullscreen"),
    # not on KDE title bars (green = keepbelow → full screen), but KDE renders these into
    # the GTK client-side-decoration assets, where green has to be maximize / restore
    "maximize": ("#28c840", "#1aab29", "#1e9a33", "#0b650d", "fullscreen"),
    "restore": ("#28c840", "#1aab29", "#1e9a33", "#0b650d", "unfullscreen"),
}
INACTIVE = ("#4b4f54", "#41454a")


def glyph(kind, color):
    c = BOX / 2
    if kind == "x":
        d = 2.6
        return (f'<path d="M{c-d},{c-d} L{c+d},{c+d} M{c+d},{c-d} L{c-d},{c+d}" '
                f'stroke="{color}" stroke-width="1.35" stroke-linecap="round" fill="none" opacity="0.85"/>')
    if kind == "-":
        d = 3.2
        return (f'<path d="M{c-d},{c} L{c+d},{c}" stroke="{color}" stroke-width="1.5" '
                f'stroke-linecap="round" fill="none" opacity="0.85"/>')
    if kind == "unfullscreen":
        # exit full screen: the two triangles point back to the centre
        a, b = 0.5, 3.6
        return (f'<path d="M{c-a},{c-a} L{c-b},{c-a} L{c-a},{c-b} Z M{c+a},{c+a} L{c+b},{c+a} L{c+a},{c+b} Z" '
                f'fill="{color}" opacity="0.85"/>')
    # macOS fullscreen: two right triangles pointing to opposite corners
    a, b = 3.1, -0.1
    return (f'<path d="M{c-a},{c-a} L{c+b},{c-a} L{c-a},{c+b} Z M{c+a},{c+a} L{c-b},{c+a} L{c+a},{c-b} Z" '
            f'fill="{color}" opacity="0.85"/>')


def light(gid, fill, ring, inner=""):
    c = BOX / 2
    return (f'<g id="{gid}">'
            f'<rect x="0" y="0" width="{BOX}" height="{BOX}" fill="none" stroke="none" opacity="0"/>'
            f'<circle cx="{c}" cy="{c}" r="{R - 0.25}" fill="{fill}" stroke="{ring}" stroke-width="0.5"/>'
            f'{inner}</g>')


def button_svg(fill, ring, pressed, gcolor, kind):
    g = glyph(kind, gcolor)
    parts = [
        light("active-center", fill, ring),
        light("hover-center", fill, ring, g),
        light("pressed-center", pressed, ring, g),
        light("inactive-center", *INACTIVE),
        light("hover-inactive-center", fill, ring, g),
        light("pressed-inactive-center", pressed, ring, g),
        light("deactivated-center", *INACTIVE),
        light("deactivated-inactive-center", *INACTIVE),
    ]
    # Aurorae looks elements up by id; stack them in one 20x20 canvas
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{BOX}" height="{BOX}" '
            f'viewBox="0 0 {BOX} {BOX}">' + "".join(parts) + "</svg>\n")


def frame(prefix, color):
    """FrameSvg pieces: 1 px corners/edges around a centre. With BorderSize=None only the
    title bar (part of the centre) is visible; the window's rounding comes from the
    rounded-corners KWin effect."""
    s, m = 1, 10  # edge size, centre size
    cells = {
        "topleft": (0, 0, s, s), "top": (s, 0, m, s), "topright": (s + m, 0, s, s),
        "left": (0, s, s, m), "center": (s, s, m, m), "right": (s + m, s, s, m),
        "bottomleft": (0, s + m, s, s), "bottom": (s, s + m, m, s), "bottomright": (s + m, s + m, s, s),
    }
    return "".join(f'<rect id="{prefix}-{k}" x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"/>'
                   for k, (x, y, w, h) in cells.items())


def decoration_svg():
    total = 12
    body = (frame("decoration", TITLEBAR) + frame("decoration-inactive", TITLEBAR_INACTIVE)
            )  # no "mask": a square blur region pokes out past the rounded corners
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="{total}" '
            f'viewBox="0 0 {total} {total}">{body}</svg>\n')


RC = f"""[General]
TitleAlignment=Center
TitleVerticalAlignment=Center
Animation=120
ActiveTextColor=255,255,255,220
InactiveTextColor=255,255,255,110
UseTextShadow=false
ButtonGroupHover=true
LeftButtons=XIB
RightButtons=
Shadow=false

[Layout]
BorderLeft=0
BorderRight=0
BorderBottom=0
TitleEdgeTop=0
TitleEdgeBottom=0
TitleEdgeLeft=10
TitleEdgeRight=10
TitleEdgeTopMaximized=0
TitleEdgeBottomMaximized=0
TitleEdgeLeftMaximized=10
TitleEdgeRightMaximized=10
TitleBorderLeft=12
TitleBorderRight=12
TitleHeight=32
ButtonWidth={BOX}
ButtonHeight={BOX}
ButtonSpacing=0
ButtonMarginTop=6
ButtonMarginTopMaximized=6
ExplicitButtonSpacer=10
"""

METADATA = f"""[Desktop Entry]
Name=Revo Tahoe
Comment=macOS Tahoe traffic lights for revo-shell-kde (green = full screen)
X-KDE-PluginInfo-Name={NAME}
X-KDE-PluginInfo-Author=revo-shell-kde
X-KDE-PluginInfo-Website=https://github.com/Zxre0/revo-shell-kde
X-KDE-PluginInfo-Version=1.0
X-KDE-PluginInfo-License=MIT
"""

os.makedirs(OUT, exist_ok=True)
for name, (fill, ring, pressed, gcolor, kind) in LIGHTS.items():
    with open(os.path.join(OUT, f"{name}.svg"), "w") as f:
        f.write(button_svg(fill, ring, pressed, gcolor, kind))
with open(os.path.join(OUT, "decoration.svg"), "w") as f:
    f.write(decoration_svg())
with open(os.path.join(OUT, f"{NAME}rc"), "w") as f:
    f.write(RC)
with open(os.path.join(OUT, "metadata.desktop"), "w") as f:
    f.write(METADATA)
print("wrote", OUT)


# ── GTK client-side decorations (Firefox, GTK3/4 apps) ──────────────────────
# KDE's GTK sync can only render Breeze buttons, so ship our own images + CSS.
# GTK has no full-screen button: there green = maximize.
# KDE's window-decorations GTK module loads its Breeze button CSS at the same (user)
# priority after gtk.css, so every selector carries :not(#revo) to win on specificity.
GTK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gtk")
os.makedirs(os.path.join(GTK, "revo-titlebuttons"), exist_ok=True)


def single(fill, ring, inner=""):
    c = BOX / 2
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{BOX}" height="{BOX}" viewBox="0 0 {BOX} {BOX}">'
            f'<circle cx="{c}" cy="{c}" r="{R - 0.25}" fill="{fill}" stroke="{ring}" stroke-width="0.5"/>'
            f'{inner}</svg>\n')


BASES = ("headerbar button.titlebutton:not(#revo)", ".titlebar button.titlebutton:not(#revo)",
         "windowcontrols > button:not(#revo)")
css = ["/* revo-shell-kde: macOS traffic lights for GTK client-side decorations (generated) */",
       ", ".join(BASES) + " {",
       "  min-width: 20px; min-height: 20px; margin: 0; padding: 0; border: none; box-shadow: none;",
       "  border-radius: 9999px; background-color: transparent; background-repeat: no-repeat;",
       "  background-position: center; background-size: 20px 20px; color: transparent; -gtk-icon-shadow: none; }",
       ", ".join(b + " image" for b in BASES) + " {",
       "  opacity: 0; }"]
gtk_lights = {"close": LIGHTS["close"], "minimize": LIGHTS["minimize"], "maximize": LIGHTS["maximize"]}
for name, (fill, ring, pressed, gcolor, kind) in gtk_lights.items():
    states = {
        "normal": single(fill, ring),
        "hover": single(fill, ring, glyph(kind, gcolor)),
        "active": single(pressed, ring, glyph(kind, gcolor)),
        "backdrop": single(*INACTIVE),
    }
    for st, svg in states.items():
        with open(os.path.join(GTK, "revo-titlebuttons", f"{name}-{st}.svg"), "w") as f:
            f.write(svg)
    sel = lambda pseudo: ", ".join(f"{base}.{name}{pseudo}" for base in BASES)
    # macOS shows every glyph when the pointer is over the button group
    group_hover = ", ".join(f"{g}:hover button.titlebutton:not(#revo).{name}" for g in ("headerbar", ".titlebar")) + \
        f", windowcontrols:hover > button:not(#revo).{name}"
    css += [f"{sel('')} {{ background-image: url('revo-titlebuttons/{name}-normal.svg'); }}",
            f"{group_hover}, {sel(':hover')} {{ background-image: url('revo-titlebuttons/{name}-hover.svg'); }}",
            f"{sel(':active')} {{ background-image: url('revo-titlebuttons/{name}-active.svg'); }}",
            f"{sel(':backdrop')} {{ background-image: url('revo-titlebuttons/{name}-backdrop.svg'); }}",
            f"{sel(':backdrop:hover')} {{ background-image: url('revo-titlebuttons/{name}-hover.svg'); }}"]
with open(os.path.join(GTK, "revo-titlebuttons.css"), "w") as f:
    f.write("\n".join(css) + "\n")
print("wrote", GTK)
