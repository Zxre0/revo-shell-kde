#!/usr/bin/env bash
# revo-shell on KDE — user part (no sudo). Run inside a Plasma Wayland session after
# setup-root.sh + reboot. Everything it changes is backed up first; undo with ./restore.sh.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="$HERE/backup/$STAMP"
CFG="${XDG_CONFIG_HOME:-$HOME/.config}"
KW="kwriteconfig6 --file kwinrc"
say() { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }

kwin_effects() {
    gdbus call --session --dest org.kde.KWin --object-path /Effects \
        --method org.freedesktop.DBus.Properties.Get org.kde.kwin.Effects listOfEffects
}

# ── preflight ────────────────────────────────────────────────────────────────
[[ "${XDG_SESSION_TYPE:-}" == wayland && "${XDG_CURRENT_DESKTOP:-}" == *KDE* ]] \
    || { echo "Run this inside a KDE Plasma Wayland session."; exit 1; }
[[ -x /usr/local/bin/qs ]] || { echo "Quickshell not found in /usr/local — run ./setup-root.sh first."; exit 1; }
EFFECTS="$(kwin_effects)"
grep -q "'glass'" <<<"$EFFECTS" || warn "Glass KWin effect not found (setup-root.sh, then reboot) — continuing without liquid glass"
grep -q "shapecorners" <<<"$EFFECTS" || warn "Rounded-corners effect not found — continuing without it"

# shells/ = upstream eqsh + macos at the pinned commit + patches/kde-port.patch
[[ -d "$HERE/shells" ]] || "$HERE/fetch-shells.sh"

# ── backup ───────────────────────────────────────────────────────────────────
say "Backing up current Plasma/KWin config → $BACKUP"
mkdir -p "$BACKUP"
for f in kwinrc kwinrulesrc kdeglobals plasmashellrc plasma-org.kde.plasma.desktop-appletsrc; do
    [[ -f "$CFG/$f" ]] && cp -a "$CFG/$f" "$BACKUP/"
done
for s in eqsh macos; do
    if [[ -e "$CFG/quickshell/$s" && ! -L "$CFG/quickshell/$s" ]]; then
        mkdir -p "$BACKUP/quickshell" && mv "$CFG/quickshell/$s" "$BACKUP/quickshell/"
    fi
done
kreadconfig6 --file kdeglobals --group General --key ColorScheme >"$BACKUP/colorscheme" || true

# ── shells ───────────────────────────────────────────────────────────────────
say "Deploying macos + eqsh shells → $CFG/quickshell (symlinked to $HERE/shells)"
mkdir -p "$CFG/quickshell"
ln -sfn "$HERE/shells/eqsh" "$CFG/quickshell/eqsh"
ln -sfn "$HERE/shells/macos" "$CFG/quickshell/macos"

avatar="/var/lib/AccountsService/icons/$USER"
[[ -r "$avatar" ]] || avatar="$HERE/shells/macos/assets/user.jpg"
python3 - "$HERE/shells/macos/userconfig.json" "$avatar" <<'EOF'
import json, sys
p, avatar = sys.argv[1], sys.argv[2]
cfg = json.load(open(p))
cfg["avatarPath"] = avatar
json.dump(cfg, open(p, "w"), indent=4)
EOF

say "Installing SF Pro fonts"
mkdir -p "$HOME/.local/share/fonts/revo-sf"
find "$HERE/shells/eqsh/media/fonts" -name '*.otf' -exec cp -n {} "$HOME/.local/share/fonts/revo-sf/" \;
fc-cache -f "$HOME/.local/share/fonts/revo-sf" >/dev/null

say "Wallpapers → ~/Pictures/Wallpapers"
mkdir -p "$HOME/Pictures"
if [[ ! -e "$HOME/Pictures/Wallpapers" ]]; then
    ln -s "$HERE/wallpapers" "$HOME/Pictures/Wallpapers"
else
    warn "~/Pictures/Wallpapers already exists — left alone (revo wallpapers are in $HERE/wallpapers)"
fi
plasma-apply-wallpaperimage "$HERE/shells/macos/assets/wall.jpg" >/dev/null || true

# ── KWin: liquid glass, corners, motion ──────────────────────────────────────
say "Configuring KWin effects (Glass liquid glass, rounded corners, Revo Motion, Magic Lamp)"
mkdir -p "$HOME/.local/share/kwin/effects"
ln -sfn "$HERE/kwin/revo-motion" "$HOME/.local/share/kwin/effects/revo-motion"

# Glass replaces KWin's blur/contrast; translucency weakens it (per Glass README)
$KW --group Plugins --key blurEnabled false
$KW --group Plugins --key contrastEnabled false
$KW --group Plugins --key translucencyEnabled false
$KW --group Plugins --key glassEnabled true
$KW --group Plugins --key kwin4_effect_shapecornersEnabled true
# window open/close: Hyprland "wind" slide instead of scale/glide; minimize: genie (Magic Lamp)
$KW --group Plugins --key scaleEnabled false
$KW --group Plugins --key glideEnabled false
$KW --group Plugins --key revo-motionEnabled true
$KW --group Plugins --key magiclampEnabled true
$KW --group Plugins --key squashEnabled false
$KW --group Plugins --key slideEnabled true

# Glass ≈ hyprliquid (highlight_style 4, no dispersion) on the shell + Hyprland blur
# (size 8, passes 3) behind translucent windows
G="$KW --group Effect-blurplus"
$G --key BlurStrength 8
$G --key DockBlurStrength 4
$G --key NoiseStrength 0
$G --key DockNoiseStrength 0
$G --key Saturation 1.2
$G --key Brightness 1.0
$G --key Contrast 1.0
$G --key RefractionStrength 12
$G --key RefractionEdgeSize 3
$G --key RefractionNormalPow 6
$G --key RefractionRGBFringing 0
$G --key RefractionOffsetStrength 8
$G --key RefractionBevelIntensity 10
$G --key PhysicallyBasedRefraction true
$G --key BodyRefraction true
$G --key BodyRefractionReach 40
$G --key BodyRefractionStrength 25
$G --key EdgeLighting true
$G --key EdgeLightingDock true
$G --key RimSpecular true
$G --key RimSpecularScale 10
$G --key RimAdaptToRefraction true
$G --key UseDeclaredCornerRadius true
$G --key TopCornerRadius 14
$G --key BottomCornerRadius 14
$G --key MenuCornerRadius 12
# force-blur every translucent window (Hyprland: blur + ignore_opacity) except the shell,
# whose surfaces declare exact glass regions via ext-background-effect
$G --key BlurMatching false
$G --key BlurNonMatching true
# (+ xwaylandvideobridge: an invisible helper window for X11 screen sharing)
$G --key WindowClasses "$(printf 'quickshell\nqs\nxwaylandvideobridge')"
$G --key BlurDecorations true
$G --key BlurMenus true
$G --key BlurDocks false
$G --key TransparentBlur true

# Hyprland: rounding 14, col.active_border rgba(ffffff10), soft shadow
R="$KW --group Round-Corners"
$R --key Exclusions xwaylandvideobridge
$R --key Size 14
$R --key InactiveCornerRadius 14
$R --key OutlineThickness 1
$R --key InactiveOutlineThickness 1
$R --key ActiveOutlineUseCustom true
$R --key InactiveOutlineUseCustom true
$R --key OutlineColor "255,255,255"
$R --key InactiveOutlineColor "255,255,255"
$R --key ActiveOutlineAlpha 16
$R --key InactiveOutlineAlpha 0
$R --key ShadowSize 25
$R --key InactiveShadowSize 18
$R --key ActiveShadowAlpha 64
$R --key InactiveShadowAlpha 40

# Super opens Launchpad. Plasma 6 handles bare Meta as a kglobalaccel shortcut (Kickoff's),
# not through kwinrc ModifierOnlyShortcuts: move Kickoff to Alt+F1 only and give Meta to the
# bridge's "revo-launcher" KWin shortcut (registered when the bridge script loads).
KGA="gdbus call --session --dest org.kde.kglobalaccel --object-path /kglobalaccel --method org.kde.KGlobalAccel"
$KGA.setForeignShortcut "['plasmashell','activate application launcher','plasmashell','Activate Application Launcher']" \
    "[150994992]" >/dev/null || true   # Alt+F1

# macOS traffic lights: RevoTahoe Aurorae decoration (aurorae/generate.py). Red close,
# yellow minimize, green full screen (the "keep below" slot, turned into full screen by the
# bridge's KWin script); double-click the title bar to maximize, Ctrl+Meta+F leaves full screen
mkdir -p "$HOME/.local/share/aurorae/themes"
ln -sfn "$HERE/aurorae/RevoTahoe" "$HOME/.local/share/aurorae/themes/RevoTahoe"
D="$KW --notify --group org.kde.kdecoration2"
$D --key library org.kde.kwin.aurorae
$D --key theme __aurorae__svg__RevoTahoe
$D --key ButtonsOnLeft XIB
$D --key ButtonsOnRight ""
$D --key BorderSize None
$D --key BorderSizeAuto false
$KW --group Windows --key TitlebarDoubleClickCommand Maximize

# same lights on GTK client-side decorations (GTK apps). GTK4 reads gtk.css; GTK3's
# KDE decorations module outranks gtk.css, so the bridge daemon keeps an import in
# gtk-3.0/window_decorations.css (KDE rewrites that file). The daemon also pins GTK's button
# layout to close,minimize,maximize (KDE would drop maximize: it can't map our green slot).
for v in gtk-3.0 gtk-4.0; do
    mkdir -p "$CFG/$v"
    ln -sfn "$HERE/aurorae/gtk/revo-titlebuttons" "$CFG/$v/revo-titlebuttons"
    ln -sfn "$HERE/aurorae/gtk/revo-titlebuttons.css" "$CFG/$v/revo-titlebuttons.css"
done
grep -qs "revo-titlebuttons.css" "$CFG/gtk-4.0/gtk.css" || printf "\n@import 'revo-titlebuttons.css';\n" >>"$CFG/gtk-4.0/gtk.css"
# Firefox / LibreWolf / Waterfox draw their own buttons: userChrome.css in every profile
# (restart the browser to see them)
"$HERE/bin/revo-firefox-theme" install

# window opacity (opaque when focused or fullscreen, 85% otherwise) is applied by the bridge's
# KWin script; remove the fixed window rule older installs created
RULE=revo-shell-opacity
rules="$(kreadconfig6 --file kwinrulesrc --group General --key rules)"
if [[ ",$rules," == *",$RULE,"* ]]; then
    rules="$(tr ',' '\n' <<<"$rules" | grep -vx "$RULE" | paste -sd, -)"
    kwriteconfig6 --file kwinrulesrc --group General --key rules "$rules"
    kwriteconfig6 --file kwinrulesrc --group General --key count \
        "$(( $(kreadconfig6 --file kwinrulesrc --group General --key count --default 1) - 1 ))"
    kwriteconfig6 --file kwinrulesrc --group "$RULE" --key Description --delete
    sed -i "/^\[$RULE\]/,/^\[/{/^\[$RULE\]/d;/^\[/!d}" "$CFG/kwinrulesrc"
fi

plasma-apply-colorscheme BreezeDark >/dev/null || true

gdbus call --session --dest org.kde.KWin --object-path /KWin --method org.kde.KWin.reconfigure >/dev/null

# ── Plasma panel → revo top bar + dock ───────────────────────────────────────
say "Removing Plasma panels (the revo top bar + dock replace them; backed up)"
gdbus call --session --dest org.kde.plasmashell --object-path /PlasmaShell \
    --method org.kde.PlasmaShell.evaluateScript 'panels().forEach(function (p) { p.remove(); })' >/dev/null || true
# the panel's system tray hosted Plasma's notification server; restart so it lets go of
# org.freedesktop.Notifications and the shell's macOS notifications take over
systemctl --user restart plasma-plasmashell.service
sleep 3

# ── autostart + launch ──────────────────────────────────────────────────────
say "Autostart + launch"
mkdir -p "$CFG/autostart"
cat >"$CFG/autostart/revo-shell-kde.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=revo-shell
Comment=macOS-style revo-shell (Quickshell) on KDE Plasma
Exec=$HERE/bin/revo-shell-kde
X-KDE-autostart-phase=2
NoDisplay=true
EOF
mkdir -p "$CFG/systemd/user"
ln -sfn "$HERE/kde-bridge/revo-kwin-bridge.service" "$CFG/systemd/user/revo-kwin-bridge.service"
systemctl --user daemon-reload
mkdir -p "$HOME/.local/bin"
ln -sfn "$HERE/bin/revo-shell-kde" "$HOME/.local/bin/revo-shell-kde"

setsid "$HERE/bin/revo-shell-kde" >"${XDG_RUNTIME_DIR}/revo-shell.log" 2>&1 < /dev/null &
sleep 4
$KGA.setForeignShortcut "['kwin','revo-launcher','KWin','revo-shell: Launchpad']" \
    "[16777250, 301989920]" >/dev/null || true   # Meta, Meta+Shift+Space
owner="$(gdbus call --session --dest org.freedesktop.DBus --object-path /org/freedesktop/DBus \
    --method org.freedesktop.DBus.GetConnectionUnixProcessID org.freedesktop.Notifications 2>/dev/null | grep -oE '[0-9]+' | head -1 || true)"
echo "    notifications served by: $( [[ -n "$owner" ]] && ps -o comm= -p "$owner" || echo none )"

echo
say "Done. Log out and back in once so KWin picks up every effect cleanly."
echo "    Shell log:   ${XDG_RUNTIME_DIR}/revo-shell.log   (restart: revo-shell-kde)"
echo "    Shortcuts:   Super / Meta+Shift+Space Launchpad · Meta+Space Spotlight · Meta+C Control Center"
echo "                 Meta+N Notifications · Meta+Shift+E Session · Meta+Alt+Esc Force Quit"
echo "    Undo all:    $HERE/restore.sh $STAMP"
