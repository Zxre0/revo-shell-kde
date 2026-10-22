#!/usr/bin/env python3
"""Generate the Finder look for Dolphin.

  finder/RevoFinder/        icon theme (inherits breeze-dark), used by Dolphin only
                            (dolphinrc [Icons] Theme): macOS Tahoe-style blue folders with
                            embossed glyphs, and grey glyphs for disks and the trash
  finder/sidebar/           revo-finder-*.svg: blue SF Symbols-style sidebar glyphs,
                            installed into hicolor so file dialogs in every app find them
  finder/RevoFinder.colors  Finder dark palette: chrome continues the RevoTahoe title bar,
                            #1e1e1e content, macOS selection blue

All artwork here is original (drawn from scratch), not Apple's.
Run: python3 finder/generate.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
THEME = os.path.join(HERE, "RevoFinder")
SIDEBAR = os.path.join(HERE, "sidebar")

ACCENT = "#3b99fc"        # sidebar glyphs (macOS dark accent, a touch lighter for 16 px)
DEVICE = "#98989d"        # Finder draws disks / trash in grey
EMBOSS = "#2a78c9"        # glyph pressed into the folder front

# 24x24 outline glyphs (stroked), in the spirit of SF Symbols
GLYPHS = {
    "home": "M4,11 L12,4.2 L20,11 M6.2,9.4 V19.5 H17.8 V9.4 M10.2,19.5 V14.2 H13.8 V19.5",
    "desktop": "M5,4.5 H19 A2,2 0 0 1 21,6.5 V14.5 A2,2 0 0 1 19,16.5 H5 A2,2 0 0 1 3,14.5 V6.5 A2,2 0 0 1 5,4.5 Z "
               "M9,20 H15 M12,16.5 V20",
    "documents": "M7,3.5 H13.5 L18,8 V19 A1.5,1.5 0 0 1 16.5,20.5 H7.5 A1.5,1.5 0 0 1 6,19 V5 A1.5,1.5 0 0 1 7.5,3.5 Z "
                 "M13.5,3.5 V8 H18 M9,12.5 H15 M9,16 H15",
    "downloads": "M12,3.5 A8.5,8.5 0 1 1 11.99,3.5 Z M12,7.5 V16 M8.5,12.5 L12,16 L15.5,12.5",
    "music": "M9,17.5 V6.2 L19,4 V15.5 M9,17.5 A2.2,2.2 0 1 1 4.6,17.5 A2.2,2.2 0 1 1 9,17.5 Z "
             "M19,15.5 A2.2,2.2 0 1 1 14.6,15.5 A2.2,2.2 0 1 1 19,15.5 Z",
    "pictures": "M5.5,5 H18.5 A2,2 0 0 1 20.5,7 V17 A2,2 0 0 1 18.5,19 H5.5 A2,2 0 0 1 3.5,17 V7 A2,2 0 0 1 5.5,5 Z "
                "M10.5,10 A1.6,1.6 0 1 1 7.3,10 A1.6,1.6 0 1 1 10.5,10 Z M4,17 L9.5,12.5 L13,15.5 L16,13 L20.2,16.6",
    "videos": "M5.5,5 H18.5 A2,2 0 0 1 20.5,7 V17 A2,2 0 0 1 18.5,19 H5.5 A2,2 0 0 1 3.5,17 V7 A2,2 0 0 1 5.5,5 Z "
              "M7.5,5 V19 M16.5,5 V19 M3.5,9.7 H7.5 M3.5,14.3 H7.5 M16.5,9.7 H20.5 M16.5,14.3 H20.5",
    "public": "M12,9 A3,3 0 1 1 6,9 A3,3 0 1 1 12,9 Z M3.5,19 C3.5,16 6,14 9,14 C12,14 14.5,16 14.5,19 "
              "M18.9,9.5 A2.4,2.4 0 1 1 14.1,9.5 A2.4,2.4 0 1 1 18.9,9.5 Z M16,14.1 C18.6,14.1 20.5,15.9 20.5,18.5",
    "templates": "M7,3.5 H13.5 L18,8 V19 A1.5,1.5 0 0 1 16.5,20.5 H7.5 A1.5,1.5 0 0 1 6,19 V5 A1.5,1.5 0 0 1 7.5,3.5 Z "
                 "M13.5,3.5 V8 H18 M9,13 H15 M12,10 V16",
    "trash": "M4.5,6.5 H19.5 M9.5,6.5 V4.8 A0.8,0.8 0 0 1 10.3,4 H13.7 A0.8,0.8 0 0 1 14.5,4.8 V6.5 "
             "M6.3,6.5 L7.3,19.2 A1.4,1.4 0 0 0 8.7,20.5 H15.3 A1.4,1.4 0 0 0 16.7,19.2 L17.7,6.5 M10,10 V16.5 M14,10 V16.5",
    "network": "M12,3.5 A8.5,8.5 0 1 1 11.99,3.5 Z M12,3.5 C9.3,6 8.5,9 8.5,12 C8.5,15 9.3,18 12,20.5 "
               "C14.7,18 15.5,15 15.5,12 C15.5,9 14.7,6 12,3.5 Z M3.5,12 H20.5 M5,7.8 H19 M5,16.2 H19",
    "recent": "M12,3.5 A8.5,8.5 0 1 1 11.99,3.5 Z M12,7.2 V12 L15.3,14",
    "drive": "M6,7 H18 A2.5,2.5 0 0 1 20.5,9.5 V14.5 A2.5,2.5 0 0 1 18,17 H6 A2.5,2.5 0 0 1 3.5,14.5 V9.5 A2.5,2.5 0 0 1 6,7 Z "
             "M6.8,12 H11 M16.5,11.1 A0.9,0.9 0 1 1 16.49,11.1 Z",
    "external": "M6,9 H18 A2.5,2.5 0 0 1 20.5,11.5 V15.5 A2.5,2.5 0 0 1 18,18 H6 A2.5,2.5 0 0 1 3.5,15.5 V11.5 A2.5,2.5 0 0 1 6,9 Z "
                "M6.8,13.5 H11 M12,3.5 L15,6.5 H9 Z",
    "folder": "M3.5,18.5 V6.5 A1.5,1.5 0 0 1 5,5 H9.5 L11.5,7 H19 A1.5,1.5 0 0 1 20.5,8.5 V18.5 A1.5,1.5 0 0 1 19,20 H5 "
              "A1.5,1.5 0 0 1 3.5,18.5 Z M3.5,10 H20.5",
    "applications": "M6,4 H9 A2,2 0 0 1 11,6 V9 A2,2 0 0 1 9,11 H6 A2,2 0 0 1 4,9 V6 A2,2 0 0 1 6,4 Z "
                    "M15,4 H18 A2,2 0 0 1 20,6 V9 A2,2 0 0 1 18,11 H15 A2,2 0 0 1 13,9 V6 A2,2 0 0 1 15,4 Z "
                    "M6,13 H9 A2,2 0 0 1 11,15 V18 A2,2 0 0 1 9,20 H6 A2,2 0 0 1 4,18 V15 A2,2 0 0 1 6,13 Z "
                    "M15,13 H18 A2,2 0 0 1 20,15 V18 A2,2 0 0 1 18,20 H15 A2,2 0 0 1 13,18 V15 A2,2 0 0 1 15,13 Z",
    "cloud": "M7.2,18.5 H17 A3.8,3.8 0 0 0 17.6,10.95 A5.6,5.6 0 0 0 6.8,10.6 A4,4 0 0 0 7.2,18.5 Z",
}


def glyph_svg(name, color, size=24, width=1.7):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24">'
            f'<path d="{GLYPHS[name]}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'stroke-linecap="round" stroke-linejoin="round"/></svg>\n')


def folder_svg(emboss=None):
    """macOS Tahoe-style folder on a 64 px canvas: darker back panel with a tab, a lighter
    front panel with a soft top highlight, and an optional glyph pressed into the front."""
    g = ""
    if emboss:
        # glyph 24 → 22 px, centred on the front panel; a light lower edge sells the emboss
        tf = "translate(21,26) scale(0.92)"
        g = (f'<path d="{GLYPHS[emboss]}" transform="translate(0,0.8) {tf}" fill="none" stroke="#c6e6ff" '
             f'stroke-opacity="0.55" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/>'
             f'<path d="{GLYPHS[emboss]}" transform="{tf}" fill="none" stroke="{EMBOSS}" stroke-opacity="0.9" '
             f'stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
<defs>
<linearGradient id="back" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3fa3f5"/><stop offset="1" stop-color="#2386e6"/></linearGradient>
<linearGradient id="front" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7cc9fc"/><stop offset="1" stop-color="#55aef5"/></linearGradient>
</defs>
<path d="M8,9 H22.5 A3,3 0 0 1 25,10.3 L27.2,13.5 H56 A4,4 0 0 1 60,17.5 V50 A4,4 0 0 1 56,54 H8 A4,4 0 0 1 4,50 V13 A4,4 0 0 1 8,9 Z" fill="url(#back)"/>
<rect x="4" y="18.5" width="56" height="37" rx="4" fill="#1d6fc4" opacity="0.35"/>
<rect x="4" y="18" width="56" height="37" rx="4" fill="url(#front)"/>
<path d="M8,18.6 H56" stroke="#b5e2ff" stroke-width="1.2" stroke-linecap="round" opacity="0.9"/>
{g}</svg>
'''


# folder art (Dolphin's view): icon name → embossed glyph
FOLDERS = {
    "folder": None, "inode-directory": None, "folder-open": None, "folder-blue": None,
    "user-home": "home", "folder-home": "home",
    "user-desktop": "desktop", "folder-desktop": "desktop",
    "folder-documents": "documents", "folder-download": "downloads", "folder-downloads": "downloads",
    "folder-music": "music", "folder-sound": "music",
    "folder-pictures": "pictures", "folder-image": "pictures", "folder-images": "pictures",
    "folder-videos": "videos", "folder-video": "videos",
    "folder-publicshare": "public", "folder-public": "public",
    "folder-templates": "templates", "folder-cloud": "cloud", "folder-network": "network",
    "folder-recent": "recent",
}
# grey device glyphs (Finder's sidebar Locations section); also used in the view, rarely
DEVICES = {
    "drive-harddisk": "drive", "drive-harddisk-root": "drive", "drive-harddisk-solidstate": "drive",
    "drive-removable-media": "external", "drive-removable-media-usb": "external",
    "drive-removable-media-usb-pendrive": "external", "media-flash": "external",
    "user-trash": "trash", "user-trash-full": "trash",
}
# blue sidebar glyphs for Places bookmarks (install-time: bookmarks are pointed at these)
SIDEBAR_GLYPHS = ["home", "desktop", "documents", "downloads", "music", "pictures", "videos",
                  "public", "templates", "trash", "network", "recent", "folder", "applications", "cloud"]

INDEX = """[Icon Theme]
Name=Revo Finder
Comment=macOS Finder-style folders for Dolphin (revo-shell-kde)
Inherits=breeze-dark,hicolor
Directories=places/scalable,devices/scalable,emblems/scalable

[places/scalable]
Size=64
MinSize=8
MaxSize=512
Type=Scalable
Context=Places

[devices/scalable]
Size=24
MinSize=8
MaxSize=512
Type=Scalable
Context=Devices

[emblems/scalable]
Size=16
MinSize=8
MaxSize=512
Type=Scalable
Context=Emblems
"""

COLORS_ROLE = """BackgroundAlternate={alt}
BackgroundNormal={bg}
DecorationFocus=10,132,255
DecorationHover=10,132,255
ForegroundActive=10,132,255
ForegroundInactive=152,152,157
ForegroundLink=10,132,255
ForegroundNegative=255,69,58
ForegroundNeutral=255,159,10
ForegroundNormal={fg}
ForegroundPositive=50,215,75
ForegroundVisited=191,90,242
"""
CHROME = "39,44,49"   # RevoTahoe title bar, so title bar + toolbar + sidebar read as one
ROLES = {
    "Button": dict(bg="52,57,62", alt="0,88,208", fg="236,236,236"),
    "Complementary": dict(bg=CHROME, alt="0,88,208", fg="236,236,236"),
    "Header": dict(bg=CHROME, alt=CHROME, fg="236,236,236"),
    "Header][Inactive": dict(bg=CHROME, alt=CHROME, fg="236,236,236"),
    "Selection": dict(bg="0,88,208", alt="0,70,170", fg="255,255,255"),
    "Tooltip": dict(bg="44,44,46", alt="30,30,30", fg="236,236,236"),
    "View": dict(bg="30,30,30", alt="36,36,38", fg="236,236,236"),
    "Window": dict(bg=CHROME, alt="46,51,56", fg="236,236,236"),
}
COLORS_TAIL = """
[ColorEffects:Disabled]
Color=56,56,56
ColorAmount=0
ColorEffect=0
ContrastAmount=0.65
ContrastEffect=1
IntensityAmount=0.1
IntensityEffect=2

[ColorEffects:Inactive]
ChangeSelectionColor=true
Color=112,111,110
ColorAmount=0.025
ColorEffect=2
ContrastAmount=0.1
ContrastEffect=2
Enable=false
IntensityAmount=0
IntensityEffect=0

[General]
ColorScheme=RevoFinder
Name=RevoFinder
shadeSortColumn=false

[KDE]
contrast=4

[WM]
activeBackground=39,44,49
activeBlend=252,252,252
activeForeground=252,252,252
inactiveBackground=39,44,49
inactiveBlend=161,169,177
inactiveForeground=161,169,177
"""


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


write(os.path.join(THEME, "index.theme"), INDEX)
for name, emboss in FOLDERS.items():
    write(os.path.join(THEME, "places", "scalable", name + ".svg"), folder_svg(emboss))
for name, g in DEVICES.items():
    write(os.path.join(THEME, "devices", "scalable", name + ".svg"), glyph_svg(g, DEVICE))
# Finder doesn't badge disks: no orange "unmounted" emblem over the drive glyphs
write(os.path.join(THEME, "emblems", "scalable", "emblem-unmounted.svg"),
      '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"/>\n')
for g in SIDEBAR_GLYPHS:
    write(os.path.join(SIDEBAR, f"revo-finder-{g}.svg"), glyph_svg(g, ACCENT))
write(os.path.join(HERE, "RevoFinder.colors"),
      "".join(f"[Colors:{role}]\n" + COLORS_ROLE.format(**c) + "\n" for role, c in ROLES.items()) + COLORS_TAIL)
print("wrote", THEME, SIDEBAR, os.path.join(HERE, "RevoFinder.colors"))
