# revo-shell-kde

The macOS-style **revo-shell** rice ([vzbc/revo-shell](https://github.com/vzbc/revo-shell),
built for Hyprland) ported to **KDE Plasma 6 on Wayland**. It includes the top bar, dock,
Launchpad (with type-to-search), Control Center and notifications, real refracting liquid
glass, and Hyprland-style window animations.

Tested on Fedora 44 with Plasma 6.7.

## Install

```bash
git clone https://github.com/Zxre0/revo-shell-kde ~/revo-kde
cd ~/revo-kde
./setup-root.sh      # sudo: upgrade, build Quickshell v0.3.2 + Glass KWin effect, deps
# reboot, log into Plasma (Wayland)
./install-user.sh    # fetch + patch the shell, configure KWin, swap the Plasma panel
```

Everything `install-user.sh` changes is backed up to `backup/`. Undo it all with `./restore.sh`.
After a `dnf upgrade` that bumps Qt or KWin, run `./setup-root.sh --rebuild`. Both builds use
private APIs and must match the installed versions exactly.

To put the shell on a monitor other than KDE's primary one, run `REVO_SCREEN=DP-1 revo-shell-kde`.

## Shortcuts

| Key | Action |
|---|---|
| Super / Meta+Shift+Space | Launchpad (start typing to search, Enter launches the top hit) |
| Meta+Space | Spotlight |
| Meta+C | Control Center |
| Meta+N | Notification Center |
| Meta+Shift+E | Session menu |
| Meta+Alt+Esc | Force Quit |
| Ctrl+Meta+F | Toggle full screen (the way out, since full-screen windows have no title bar) |

You can rebind these under System Settings → Shortcuts → KWin ("revo-shell: …").

## How the Hyprland pieces map to KDE

| Hyprland | KDE port |
|---|---|
| `hyprliquid` liquid glass on dock / eqsh popovers / launchpad | Quickshell `BackgroundEffect` blur regions + [Glass](https://github.com/4v3ngR/kwin-effects-glass) KWin effect (refraction, edge lighting, specular rim) |
| `decoration.blur`, 92/85 % opacity, rounding 14, faint border | Glass force-blur, opacity set by the bridge's KWin script (focused and fullscreen windows opaque, others 85 %), [KDE-Rounded-Corners](https://github.com/matinlotfali/KDE-Rounded-Corners) |
| `windowsIn/Out … slide` with `winIn`/`winOut` beziers | `kwin/revo-motion`: slide from the nearest edge, OutBack / InBack |
| genie minimize (needs Hyprland screencopy) | KWin Magic Lamp |
| `hyprbars` traffic lights | `aurorae/`: RevoTahoe decoration (red close, yellow minimize, green full screen, hover glyphs), matching GTK CSS for GTK apps, and a `userChrome.css` for Firefox / LibreWolf / Waterfox (installed by `bin/revo-firefox-theme`; restart the browser once) |
| `Hyprland.toplevels`, `ToplevelManager`, `hyprctl clients` | `kde-bridge/`: KWin script → `revo-kwin-bridge.py` (systemd user service) → `KdeToplevels` QML singleton, plus a `hyprctl` shim on the shell's PATH only |
| `HyprlandFocusGrab` | transparent click-catcher layer |
| ext-session-lock screen | KDE's screen locker |
| Hyprland keybinds | KWin shortcuts registered by the bridge |
| `kitty` terminal | Konsole styled as macOS Terminal (`konsole/`): Apple System Colors palette, SF Mono, no toolbars, Tahoe-style pill tabs with a "+" button that continue the title bar |

## Layout

| Path | What |
|---|---|
| `setup-root.sh` | system deps, Quickshell + Glass builds, rounded-corners COPR |
| `install-user.sh` / `restore.sh` | apply / undo the rice for the current user |
| `fetch-shells.sh` | builds `shells/` from upstream at a pinned commit + `patches/kde-port.patch` |
| `patches/kde-port.patch` | every change to upstream's `eqsh` + `macos` shells |
| `kde-bridge/` | KWin script, bridge daemon + service, `hyprctl` shim |
| `kwin/revo-motion/` | window open/close animation effect |
| `aurorae/` | `generate.py` → RevoTahoe title bar theme + GTK title-button CSS |
| `bin/revo-shell-kde` | launcher (bridge + Quickshell) |
| `konsole/`, `bin/revo-konsole-theme` | macOS Terminal profile, colour scheme and tab style for Konsole |
| `bin/revo-firefox-theme` | add / remove the traffic-light `userChrome.css` in Firefox-family profiles |

## Credits and licensing

The shell itself (`eqsh`, `macos`), its fonts, icons and wallpapers come from
[vzbc/revo-shell](https://github.com/vzbc/revo-shell) and aren't redistributed here.
`fetch-shells.sh` downloads them from upstream. The files in this repo are MIT
licensed (see `LICENSE`).
