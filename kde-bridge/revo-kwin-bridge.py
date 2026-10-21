#!/usr/bin/env python3
"""revo KWin bridge daemon.

Owns org.revo.KWinBridge on the session bus:
  update(json)        called by kwin-bridge.js; state is written (coalesced) to
                      $XDG_RUNTIME_DIR/revo-kwin/windows.json for Quickshell to watch
  command(cmd)        shell command from a KWin shortcut → /tmp/macos_cmd (read by ShellController)
  superKey()          Super tapped alone (kwinrc ModifierOnlyShortcuts) → opens Launchpad
  action(id, verb)    activate | close | minimize | unminimize | toggleMinimize |
                      maximize | unmaximize | fullscreen | unfullscreen
                      runs a one-shot KWin script against the window with that internalId
"""
import json
import os
import sys
import tempfile
import uuid

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

HERE = os.path.dirname(os.path.realpath(__file__))
BRIDGE_JS = os.path.join(HERE, "kwin-bridge.js")
RUNTIME = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "revo-kwin")
STATE_FILE = os.path.join(RUNTIME, "windows.json")
BRIDGE_NAME = "revo-kwin-bridge"

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


def main():
    os.makedirs(RUNTIME, exist_ok=True)
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    if bus.name_has_owner("org.revo.KWinBridge"):
        print("revo-kwin-bridge already running", file=sys.stderr)
        return 0
    name = dbus.service.BusName("org.revo.KWinBridge", bus, do_not_queue=True)  # noqa: F841
    bridge = Bridge(bus)
    # (re)load the KWin side so it pushes a full snapshot to us right away
    GLib.idle_add(lambda: bridge.resync() and False)
    GLib.MainLoop().run()


if __name__ == "__main__":
    sys.exit(main())
