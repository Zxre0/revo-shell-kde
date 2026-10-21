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

// Hyprland's active_opacity 0.92 / inactive_opacity 0.85, but opaque in fullscreen
// (a KWin window rule can't make that exception)
function applyOpacity(w) {
    // skip-taskbar windows are helpers (e.g. xwaylandvideobridge keeps itself invisible
    // through its own opacity) and the shell's layer surfaces
    if (!w || !w.normalWindow || w.skipTaskbar || /^(quickshell|qs)$/i.test(String(w.resourceClass)))
        return;
    w.opacity = w.fullScreen ? 1.0 : (w === workspace.activeWindow ? 0.92 : 0.85);
}

function applyOpacityAll() {
    workspace.windowList().forEach(applyOpacity);
}

// The RevoTahoe decoration's green light sits in the "keep below" button slot (KDE has no
// full-screen button): turn that toggle into full screen, like the macOS green button.
function greenLight(w) {
    if (!w.keepBelow)
        return;
    w.keepBelow = false;
    if (w.fullScreenable)
        w.fullScreen = !w.fullScreen;
}

function watch(w) {
    if (!w) return;
    if (w.keepBelowChanged) w.keepBelowChanged.connect(function () { greenLight(w); });
    if (w.fullScreenChanged) w.fullScreenChanged.connect(function () { applyOpacity(w); });
    ["captionChanged", "minimizedChanged", "fullScreenChanged", "frameGeometryChanged",
     "outputChanged", "desktopsChanged", "skipTaskbarChanged"].forEach(function (sig) {
        if (w[sig]) w[sig].connect(push);
    });
}

workspace.windowList().forEach(watch);
workspace.windowAdded.connect(function (w) { watch(w); applyOpacity(w); push(); });
workspace.windowRemoved.connect(push);
workspace.windowActivated.connect(function () { applyOpacityAll(); push(); });
workspace.currentDesktopChanged.connect(push);
applyOpacityAll();
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

// macOS ⌃⌘F: the way back out of full screen (full-screen windows have no title bar)
registerShortcut("revo-fullscreen", "revo-shell: Toggle Full Screen", "Ctrl+Meta+F", function () {
    var w = workspace.activeWindow;
    if (w && w.fullScreenable)
        w.fullScreen = !w.fullScreen;
});
