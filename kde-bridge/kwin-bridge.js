// revo KWin bridge — pushes the window list to org.revo.KWinBridge on every change.
// Stands in for wlr-foreign-toplevel / Hyprland IPC, which KWin does not expose.
// Loaded by revo-kwin-bridge.py through org.kde.KWin /Scripting.

function isTask(w) {
    // the shell's own layer surfaces count as normal windows in KWin (namespace → type)
    if (!w || /^(quickshell|qs)$/i.test(String(w.resourceClass)))
        return false;
    return w.normalWindow && !w.skipTaskbar && !w.specialWindow;
}

function snapshot(w) {
    var area = workspace.clientArea(KWin.MaximizeArea, w);
    var g = w.frameGeometry;
    return {
        id: String(w.internalId),
        appId: String(w.desktopFileName || w.resourceClass || ""),
        resourceClass: String(w.resourceClass || ""),
        title: String(w.caption || ""),
        pid: w.pid || 0,
        activated: w === workspace.activeWindow,
        minimized: !!w.minimized,
        fullscreen: !!w.fullScreen,
        maximized: !!(area && g.width >= area.width && g.height >= area.height),
        screen: w.output ? String(w.output.name) : "",
        desktops: (w.desktops || []).map(function (d) { return String(d.id); }),
        onAllDesktops: !!w.onAllDesktops
    };
}

function push() {
    var list = workspace.windowList().filter(isTask).map(snapshot);
    var state = {
        windows: list,
        activeId: workspace.activeWindow ? String(workspace.activeWindow.internalId) : "",
        currentDesktop: workspace.currentDesktop ? String(workspace.currentDesktop.id) : "",
        activeScreen: workspace.activeScreen ? String(workspace.activeScreen.name) : ""
    };
    callDBus("org.revo.KWinBridge", "/", "org.revo.KWinBridge", "update", JSON.stringify(state));
}

function watch(w) {
    if (!w) return;
    ["captionChanged", "minimizedChanged", "fullScreenChanged", "frameGeometryChanged",
     "outputChanged", "desktopsChanged", "skipTaskbarChanged"].forEach(function (sig) {
        if (w[sig]) w[sig].connect(push);
    });
}

workspace.windowList().forEach(watch);
workspace.windowAdded.connect(function (w) { watch(w); push(); });
workspace.windowRemoved.connect(push);
workspace.windowActivated.connect(push);
workspace.currentDesktopChanged.connect(push);
push();

// macOS-style shortcuts → the shell's command channel (ShellController reads /tmp/macos_cmd).
// Rebindable under System Settings → Shortcuts → KWin.
[
    ["spotlight", "Spotlight", "Meta+Space"],
    ["launcher", "Launchpad", "Meta"],
    ["controlcenter", "Control Center", "Meta+C"],
    ["notifications", "Notification Center", "Meta+N"],
    ["session", "Session Menu", "Meta+Shift+E"],
    ["forcequit", "Force Quit Applications", "Meta+Alt+Esc"]
].forEach(function (s) {
    registerShortcut("revo-" + s[0], "revo-shell: " + s[1], s[2], function () {
        callDBus("org.revo.KWinBridge", "/", "org.revo.KWinBridge", "command", s[0]);
    });
});
