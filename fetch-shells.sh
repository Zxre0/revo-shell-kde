#!/usr/bin/env bash
# Build shells/ (eqsh + macos, KDE port) and wallpapers/ from upstream revo-shell.
#
# This repo doesn't redistribute upstream's code or assets (no upstream license; bundled
# SF Pro fonts, icons and wallpapers belong to others). Instead it pins the upstream commit
# the port was made against and applies patches/kde-port.patch on top.
#
#   ./fetch-shells.sh            create shells/ (and wallpapers/) if missing
#   ./fetch-shells.sh --force    rebuild shells/ from scratch (local edits are lost)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
UPSTREAM_URL="https://github.com/vzbc/revo-shell"
UPSTREAM_REV="72f7113c9530577acff57778246b0583324c3774"
SRC="$HERE/build/revo-shell-upstream"
DEST="${SHELLS_DIR:-$HERE/shells}"

if [[ -d "$DEST" && "${1:-}" != "--force" ]]; then
    echo "$DEST already exists (use --force to rebuild it)"
    exit 0
fi

echo "==> Fetching upstream revo-shell @ ${UPSTREAM_REV:0:7}"
mkdir -p "$HERE/build"
[[ -d "$SRC/.git" ]] || git clone -q --filter=blob:none --no-checkout "$UPSTREAM_URL" "$SRC"
git -C "$SRC" fetch -q origin
git -C "$SRC" sparse-checkout set quickshell/eqsh quickshell/macos wallpapers
git -C "$SRC" checkout -q "$UPSTREAM_REV"

echo "==> Assembling $DEST"
rm -rf "$DEST"
mkdir -p "$DEST"
cp -a "$SRC/quickshell/eqsh" "$SRC/quickshell/macos" "$DEST/"
# upstream's macos shell borrows eqsh files through absolute links into the author's home
# (/home/revo/.config/quickshell/eqsh/...): make them relative
( cd "$DEST" && find macos -type l | while read -r l; do
    t="$(readlink "$l")"
    [[ "$t" == /home/revo/.config/quickshell/* ]] || continue
    ln -sfn "$(realpath -m --relative-to="$DEST/$(dirname "$l")" "$DEST/${t#/home/revo/.config/quickshell/}")" "$l"
done )

git -C "$DEST" init -q
git -C "$DEST" add -A
git -C "$DEST" -c user.name=revo-kde -c user.email=revo-kde@localhost commit -qm "upstream eqsh+macos @ ${UPSTREAM_REV:0:7}"
git -C "$DEST" apply --binary "$HERE/patches/kde-port.patch"
git -C "$DEST" add -A
git -C "$DEST" -c user.name=revo-kde -c user.email=revo-kde@localhost commit -qm "KDE Plasma port (patches/kde-port.patch)"

if [[ ! -d "$HERE/wallpapers" ]]; then
    echo "==> Wallpapers"
    cp -a "$SRC/wallpapers" "$HERE/wallpapers"
fi
echo "Done: $DEST"
