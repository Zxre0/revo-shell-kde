#!/usr/bin/env bash
# Undo install-user.sh: restore the backed-up Plasma/KWin config and stop revo-shell.
#   ./restore.sh            restore the newest backup
#   ./restore.sh <stamp>    restore backup/<stamp>
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CFG="${XDG_CONFIG_HOME:-$HOME/.config}"
STAMP="${1:-$(ls -1 "$HERE/backup" 2>/dev/null | sort | tail -1)}"
BACKUP="$HERE/backup/$STAMP"
[[ -n "$STAMP" && -d "$BACKUP" ]] || { echo "No backup found in $HERE/backup"; exit 1; }
echo "Restoring from $BACKUP"

rm -f "$CFG/autostart/revo-shell-kde.desktop" "$HOME/.local/bin/revo-shell-kde"
/usr/local/bin/qs kill -p "$CFG/quickshell/macos" >/dev/null 2>&1 || true
systemctl --user stop revo-kwin-bridge.service 2>/dev/null || true
rm -f "$CFG/systemd/user/revo-kwin-bridge.service"
systemctl --user daemon-reload
gdbus call --session --dest org.kde.KWin --object-path /Scripting \
    --method org.kde.kwin.Scripting.unloadScript revo-kwin-bridge >/dev/null 2>&1 || true
# the bridge script managed window opacity: put every window back to opaque
reset_js="$(mktemp --suffix=.js)"
echo 'workspace.windowList().forEach(function (w) { w.opacity = 1.0; });' >"$reset_js"
KS="gdbus call --session --dest org.kde.KWin --object-path /Scripting --method org.kde.kwin.Scripting"
$KS.loadScript "$reset_js" revo-opacity-reset >/dev/null 2>&1 && $KS.start >/dev/null 2>&1 || true
sleep 0.5
$KS.unloadScript revo-opacity-reset >/dev/null 2>&1 || true
rm -f "$reset_js"

"$HERE/bin/revo-konsole-theme" remove || true
for f in kwinrc kwinrulesrc kdeglobals plasmashellrc plasma-org.kde.plasma.desktop-appletsrc konsolerc; do
    [[ -f "$BACKUP/$f" ]] && cp -a "$BACKUP/$f" "$CFG/$f"
done
rm -f "$HOME/.local/share/kwin/effects/revo-motion"
rm -f "$HOME/.local/share/aurorae/themes/RevoTahoe"
for v in gtk-3.0 gtk-4.0; do
    rm -f "$CFG/$v/revo-titlebuttons" "$CFG/$v/revo-titlebuttons.css"
    sed -i "/@import 'revo-titlebuttons.css';/d" "$CFG/$v/gtk.css" "$CFG/$v/window_decorations.css" 2>/dev/null || true
done
"$HERE/bin/revo-firefox-theme" remove || true
# let KDE recompute GTK's button layout from the restored kwinrc (the bridge pinned it)
K="gdbus call --session --dest org.kde.kded6 --object-path /kded --method org.kde.kded6"
$K.unloadModule gtkconfig >/dev/null 2>&1 || true
$K.loadModule gtkconfig >/dev/null 2>&1 || true
for s in eqsh macos; do
    [[ -L "$CFG/quickshell/$s" ]] && rm "$CFG/quickshell/$s"
    [[ -e "$BACKUP/quickshell/$s" ]] && mv "$BACKUP/quickshell/$s" "$CFG/quickshell/"
done
[[ -L "$HOME/Pictures/Wallpapers" ]] && rm "$HOME/Pictures/Wallpapers"
scheme="$(cat "$BACKUP/colorscheme" 2>/dev/null || true)"
[[ -n "$scheme" ]] && plasma-apply-colorscheme "$scheme" >/dev/null || true

# give Super back to Plasma's application launcher (Meta, Alt+F1)
gdbus call --session --dest org.kde.kglobalaccel --object-path /kglobalaccel \
    --method org.kde.KGlobalAccel.setForeignShortcut \
    "['plasmashell','activate application launcher','plasmashell','Activate Application Launcher']" \
    "[16777250, 150994992]" >/dev/null || true

gdbus call --session --dest org.kde.KWin --object-path /KWin --method org.kde.KWin.reconfigure >/dev/null
systemctl --user restart plasma-plasmashell.service
echo "Restored. Log out and back in to fully reset KWin effects."
