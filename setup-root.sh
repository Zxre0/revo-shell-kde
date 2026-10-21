#!/usr/bin/env bash
# revo-shell on KDE — system part (needs sudo).
#
#   ./setup-root.sh            full setup: upgrade Fedora, install deps, build Quickshell + Glass
#   ./setup-root.sh --rebuild  only rebuild Quickshell + Glass (run after a dnf upgrade that
#                              bumps Qt or KWin — both use private APIs and must match exactly)
#
# What gets installed:
#   - Quickshell v0.3.2 from source → /usr/local  (Fedora's package predates BackgroundEffect,
#     which the KDE port uses for per-surface liquid-glass blur regions)
#   - "Glass" KWin effect from source (blur + refraction + edge lighting; liquid glass on KDE)
#   - KDE-Rounded-Corners KWin effect (upstream COPR; 14px corners + outline like the Hyprland config)
#   - runtime tools the macos/eqsh shell calls
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BUILD="$HERE/build"
QS_TAG="v0.3.2"
mkdir -p "$BUILD"

fetch() { # fetch <url> <dir> [tag]
    if [[ -d "$2/.git" ]]; then
        git -C "$2" fetch -q --tags origin
    else
        git clone -q "$1" "$2"
    fi
    if [[ -n "${3:-}" ]]; then git -C "$2" checkout -q "$3"; else git -C "$2" pull -q --ff-only; fi
}

build_quickshell() {
    echo "==> Building Quickshell $QS_TAG"
    sudo dnf -y builddep quickshell || true   # needs source repos; explicit list below covers it
    sudo dnf -y install ninja-build cmake gcc-c++ qt6-qtbase-private-devel qt6-qtshadertools-devel \
        qt6-qtwayland-devel qt6-qtdeclarative-devel qt6-qtsvg-devel wayland-devel wayland-protocols-devel \
        cli11-devel spirv-tools pkgconf-pkg-config vulkan-headers libxcb-devel jemalloc-devel pipewire-devel pam-devel polkit-devel glib2-devel libdrm-devel mesa-libgbm-devel
    fetch https://git.outfoxxed.me/quickshell/quickshell.git "$BUILD/quickshell" "$QS_TAG"
    rm -rf "$BUILD/quickshell/build"
    cmake -S "$BUILD/quickshell" -B "$BUILD/quickshell/build" -G Ninja \
        -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_INSTALL_PREFIX=/usr/local \
        -DCRASH_HANDLER=OFF -DDISTRIBUTOR="revo-kde (source build)"
    cmake --build "$BUILD/quickshell/build"
    sudo cmake --install "$BUILD/quickshell/build"
}

build_glass() {
    echo "==> Building the Glass KWin effect"
    sudo dnf -y install cmake extra-cmake-modules gcc-c++ kwin-devel kf6-kwindowsystem-devel \
        plasma-workspace-devel libplasma-devel qt6-qtbase-private-devel qt6-qtbase-devel \
        kf6-knotifications-devel kf6-kio-devel kf6-kcrash-devel kf6-ki18n-devel kf6-kguiaddons-devel \
        libepoxy-devel kf6-kglobalaccel-devel kf6-kcmutils-devel kf6-kconfigwidgets-devel \
        kf6-kdeclarative-devel kdecoration-devel wayland-devel libdrm-devel
    fetch https://github.com/4v3ngR/kwin-effects-glass "$BUILD/kwin-effects-glass"
    rm -rf "$BUILD/kwin-effects-glass/build"
    cmake -S "$BUILD/kwin-effects-glass" -B "$BUILD/kwin-effects-glass/build" -DCMAKE_INSTALL_PREFIX=/usr
    make -C "$BUILD/kwin-effects-glass/build" -j"$(nproc)"
    sudo make -C "$BUILD/kwin-effects-glass/build" install
}

if [[ "${1:-}" == "--rebuild" ]]; then
    build_quickshell
    build_glass
    echo "Rebuilt. Log out and back in (KWin loads effects at startup)."
    exit 0
fi

echo "==> [1/4] Upgrading system (Glass must be built against the KWin you will run)"
sudo dnf -y upgrade --refresh

echo "==> [2/4] Runtime tools + rounded corners effect"
sudo dnf -y install dnf-plugins-core
sudo dnf -y copr enable matinlotfali/KDE-Rounded-Corners
sudo dnf -y install kwin-effect-roundcorners \
    qt6-qt5compat qt6-qtmultimedia qt6-qtsvg qt6-qtimageformats qt6-qtwayland \
    cliphist wl-clipboard brightnessctl playerctl ddcutil fd-find \
    pipewire-utils wireplumber NetworkManager bluez python3-dbus python3-gobject fira-code-fonts git

echo "==> [3/4]"; build_quickshell
echo "==> [4/4]"; build_glass

echo
echo "Done. REBOOT now (new KWin + Qt), log back into Plasma (Wayland), then run:"
echo "    $HERE/install-user.sh"
