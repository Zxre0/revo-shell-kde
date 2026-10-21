#!/usr/bin/env python3
"""revo KWin bridge daemon.

Owns org.revo.KWinBridge on the session bus:
  update(json)        called by kwin-bridge.js; state is written (coalesced) to
                      $XDG_RUNTIME_DIR/revo-kwin/windows.json for Quickshell to watch
  command(cmd)        shell command from a KWin shortcut → /tmp/macos_cmd (read by ShellController)
  (also pins GTK's button layout and keeps the traffic-light CSS imported for GTK/Firefox)
  superKey()          Super tapped alone (kwinrc ModifierOnlyShortcuts) → opens Launchpad
  action(id, verb)    activate | close | minimize | unminimize | toggleMinimize |
                      maximize | unmaximize | fullscreen | unfullscreen
                      runs a one-shot KWin script against the window with that internalId
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import Gio, GLib

HERE = os.path.dirname(os.path.realpath(__file__))
BRIDGE_JS = os.path.join(HERE, "kwin-bridge.js")
RUNTIME = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "revo-kwin")
STATE_FILE = os.path.join(RUNTIME, "windows.json")
BRIDGE_NAME = "revo-kwin-bridge"
CONFIG = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
# KDE's GTK3 window-decorations module loads this file above gtk.css priority and rewrites
# it on colour/decoration changes; our traffic-light CSS has to be imported from it
GTK3_DECO_CSS = os.path.join(CONFIG, "gtk-3.0", "window_decorations.css")
GTK3_IMPORT = "@import 'revo-titlebuttons.css';"
# KDE derives GTK's button layout from kwinrc and drops the "keep below" slot that holds our
# green light (XIB → close,minimize), so client-side decorations (Firefox, GTK apps) would
# lose maximize. Pin the macOS order everywhere GTK and Firefox read it.
GTK_LAYOUT = "close,minimize,maximize:"
GTK_SETTINGS_INI = [os.path.join(CONFIG, v, "settings.ini") for v in ("gtk-3.0", "gtk-4.0")]
XSETTINGSD_CONF = os.path.join(CONFIG, "xsettingsd", "xsettingsd.conf")

ACTIONS = {
    "activate": "w.minimized = false; workspace.activeWindow = w;",
    "close": "w.closeWindow();",
    "minimize": "w.minimized = true;",
    "unminimize": "w.minimized = false; workspace.activeWindow = w;",
    "toggleMinimize": "if (w.minimized || w !== workspace.activeWindow) { w.minimized = false; workspace.activeWindow = w; } else { w.minimized = true; }",
    "maximize": "w.setMaximize(true, true);",
    "unmaximize": "w.setMaximize(false, false);",
    "fullscreen": "w.fullScreen = true;",
    "unfullscreen": "w.fullScreen = false;",
}


def scripting():
    return dbus.Interface(
        dbus.SessionBus().get_object("org.kde.KWin", "/Scripting"),
        "org.kde.kwin.Scripting",
    )


def run_kwin_script(path, name):
    s = scripting()
    if s.isScriptLoaded(name):
        s.unloadScript(name)
    # loadScript is overloaded (s / ss): pick the two-argument form explicitly
    dbus.SessionBus().call_blocking("org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting",
                                    "loadScript", "ss", (path, name))
    s.start()


class Bridge(dbus.service.Object):
    def __init__(self, bus):
        super().__init__(bus, "/")
        self._pending = None
        self._timer = 0

    @dbus.service.method("org.revo.KWinBridge", in_signature="s")
    def update(self, payload):
        self._pending = str(payload)
        if not self._timer:
            self._timer = GLib.timeout_add(40, self._flush)

    def _flush(self):
        self._timer = 0
        data, self._pending = self._pending, None
        if data is None:
            return False
        fd, tmp = tempfile.mkstemp(dir=RUNTIME, prefix=".windows.")
        with os.fdopen(fd, "w") as f:
            f.write(data)
        os.replace(tmp, STATE_FILE)
        return False

    @dbus.service.method("org.revo.KWinBridge", in_signature="ss")
    def action(self, window_id, verb):
        body = ACTIONS.get(str(verb))
        if body is None:
            raise dbus.exceptions.DBusException("unknown action: %s" % verb)
        name = "revo-action-" + uuid.uuid4().hex[:8]
        js = (
            "var w = workspace.windowList().filter(function (x) { return String(x.internalId) === %s; })[0];\n"
            "if (w) { %s }\n" % (json.dumps(str(window_id)), body)
        )
        path = os.path.join(RUNTIME, name + ".js")
        with open(path, "w") as f:
            f.write(js)
        run_kwin_script(path, name)
        # one-shot: unload once KWin has run it
        GLib.timeout_add(500, self._cleanup, name, path)

    def _cleanup(self, name, path):
        try:
            scripting().unloadScript(name)
        except dbus.DBusException:
            pass
        try:
            os.unlink(path)
        except OSError:
            pass
        return False

    @dbus.service.method("org.revo.KWinBridge", in_signature="s")
    def command(self, cmd):
        # same channel the Hyprland binds used (scripts/macos_lock.sh etc.)
        with open("/tmp/macos_cmd", "w") as f:
            f.write(str(cmd) + "\n")

    @dbus.service.method("org.revo.KWinBridge")
    def superKey(self):
        # no-argument entry point for KWin's [ModifierOnlyShortcuts] (Meta tapped alone)
        self.command("launcher")

    @dbus.service.method("org.revo.KWinBridge")
    def resync(self):
        run_kwin_script(BRIDGE_JS, BRIDGE_NAME)


def ensure_gtk_traffic_lights(*_):
    if not os.path.exists(os.path.join(CONFIG, "gtk-3.0", "revo-titlebuttons.css")):
        return
    try:
        with open(GTK3_DECO_CSS) as f:
            css = f.read()
    except FileNotFoundError:
        css = ""
    if GTK3_IMPORT in css:
        return
    with open(GTK3_DECO_CSS, "w") as f:
        f.write(GTK3_IMPORT + "\n" + css)


def _rewrite(path, pattern, line):
    try:
        with open(path) as f:
            text = f.read()
    except FileNotFoundError:
        return False
    new = re.sub(pattern, line, text, flags=re.M)
    if new == text:
        return False
    with open(path, "w") as f:
        f.write(new)
    return True


def ensure_gtk_layout(*_):
    for ini in GTK_SETTINGS_INI:
        _rewrite(ini, r"^gtk-decoration-layout=.*$", "gtk-decoration-layout=" + GTK_LAYOUT)
    if _rewrite(XSETTINGSD_CONF, r"^Gtk/DecorationLayout .*$", 'Gtk/DecorationLayout "%s"' % GTK_LAYOUT):
        os.system("pkill -HUP -x xsettingsd")
    wm = Gio.Settings.new("org.gnome.desktop.wm.preferences")
    if wm.get_string("button-layout") != GTK_LAYOUT:
        wm.set_string("button-layout", GTK_LAYOUT)
        Gio.Settings.sync()


def watch_file(path, callback):
    monitor = Gio.File.new_for_path(path).monitor_file(Gio.FileMonitorFlags.WATCH_MOVES, None)
    # let KDE finish writing before checking
    monitor.connect("changed", lambda *a: GLib.timeout_add(300, lambda: callback() and False))
    return monitor


def main():
    os.makedirs(RUNTIME, exist_ok=True)
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    if bus.name_has_owner("org.revo.KWinBridge"):
        print("revo-kwin-bridge already running", file=sys.stderr)
        return 0
    name = dbus.service.BusName("org.revo.KWinBridge", bus, do_not_queue=True)  # noqa: F841
    bridge = Bridge(bus)
    ensure_gtk_traffic_lights()
    ensure_gtk_layout()
    monitors = [watch_file(GTK3_DECO_CSS, ensure_gtk_traffic_lights)]  # noqa: F841
    monitors += [watch_file(p, ensure_gtk_layout) for p in GTK_SETTINGS_INI + [XSETTINGSD_CONF]]
    wm = Gio.Settings.new("org.gnome.desktop.wm.preferences")
    wm.connect("changed::button-layout", lambda *a: GLib.timeout_add(300, lambda: ensure_gtk_layout() and False))
    # traffic lights for Firefox profiles created since the last login
    subprocess.run([os.path.join(HERE, "..", "bin", "revo-firefox-theme"), "install"],
                   stdout=subprocess.DEVNULL, check=False)
    # (re)load the KWin side so it pushes a full snapshot to us right away
    GLib.idle_add(lambda: bridge.resync() and False)
    GLib.MainLoop().run()


if __name__ == "__main__":
    sys.exit(main())
