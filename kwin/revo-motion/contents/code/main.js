"use strict";

// revo-motion — revo-shell's Hyprland window animations for KWin.
//
// Hyprland (hypr/configs/animations.conf):
//   bezier = winIn,  0.1, 1.1, 0.1, 1.1      animation = windowsIn,  1, 6, winIn,  slide
//   bezier = winOut, 0.3, -0.3, 0, 1         animation = windowsOut, 1, 5, winOut, slide
//   animation = fadeIn, 1, 1.73, ...         animation = fadeOut, 1, 1.46, ...
// Speeds are in deciseconds. "slide" moves the window in from / out to the nearest screen
// edge; winIn overshoots (≈ OutBack) and winOut pulls back first (≈ InBack).

var revoMotion = {
    loadConfig: function () {
        revoMotion.inDuration = animationTime(600);
        revoMotion.outDuration = animationTime(500);
        revoMotion.fadeInDuration = animationTime(173);
        revoMotion.fadeOutDuration = animationTime(146);
    },

    isMotionWindow: function (window) {
        // same heuristics as KWin's scale effect: plasmashell only for its decorated dialogs
        if (window.windowClass == "plasmashell plasmashell" || window.windowClass == "plasmashell org.kde.plasmashell")
            return window.hasDecoration;
        // the shell's layer surfaces ("macos:dock" etc.) map to normal windows in KWin;
        // they animate themselves in QML
        if (/(^|\s)(quickshell|qs)(\s|$)/i.test(window.windowClass))
            return false;
        if (window.popupWindow || window.lockScreen || window.outline || !window.managed)
            return false;
        if (window.desktopWindow || window.dock || window.splash || window.notification
            || window.criticalNotification || window.onScreenDisplay)
            return false;
        return window.normalWindow || window.dialog;
    },

    // translation that puts the window just past the screen edge nearest to its centre
    edgeOffset: function (window) {
        var g = window.geometry;
        var s = window.screen ? window.screen.geometry : g;
        var cx = g.x + g.width / 2, cy = g.y + g.height / 2;
        var dLeft = cx - s.x, dRight = s.x + s.width - cx;
        var dTop = cy - s.y, dBottom = s.y + s.height - cy;
        var m = Math.min(dLeft, dRight, dTop, dBottom);
        if (m === dLeft) return { value1: -(g.x + g.width - s.x), value2: 0 };
        if (m === dRight) return { value1: s.x + s.width - g.x, value2: 0 };
        if (m === dTop) return { value1: 0, value2: -(g.y + g.height - s.y) };
        return { value1: 0, value2: s.y + s.height - g.y };
    },

    setupForcedRoles: function (window) {
        window.setData(Effect.WindowForceBackgroundContrastRole, true);
        window.setData(Effect.WindowForceBlurRole, true);
    },

    cleanupForcedRoles: function (window) {
        window.setData(Effect.WindowForceBackgroundContrastRole, null);
        window.setData(Effect.WindowForceBlurRole, null);
    },

    slotWindowAdded: function (window) {
        if (effects.hasActiveFullScreenEffect || !window.visible || !revoMotion.isMotionWindow(window))
            return;
        if (!effect.grab(window, Effect.WindowAddedGrabRole))
            return;
        revoMotion.setupForcedRoles(window);
        window.revoInAnimation = animate({
            window: window,
            curve: QEasingCurve.OutBack,
            duration: revoMotion.inDuration,
            animations: [
                { type: Effect.Translation, from: revoMotion.edgeOffset(window), to: { value1: 0, value2: 0 } },
                { type: Effect.Opacity, from: 0, to: 1, duration: revoMotion.fadeInDuration, curve: QEasingCurve.Linear }
            ]
        });
    },

    slotWindowClosed: function (window) {
        if (effects.hasActiveFullScreenEffect || !revoMotion.isMotionWindow(window))
            return;
        if (!effect.grab(window, Effect.WindowClosedGrabRole))
            return;
        if (window.revoInAnimation) {
            cancel(window.revoInAnimation);
            delete window.revoInAnimation;
        }
        revoMotion.setupForcedRoles(window);
        window.revoOutAnimation = animate({
            window: window,
            curve: QEasingCurve.InBack,
            duration: revoMotion.outDuration,
            animations: [
                { type: Effect.Translation, from: { value1: 0, value2: 0 }, to: revoMotion.edgeOffset(window) },
                { type: Effect.Opacity, from: 1, to: 0, delay: revoMotion.outDuration - revoMotion.fadeOutDuration,
                  duration: revoMotion.fadeOutDuration, curve: QEasingCurve.Linear }
            ]
        });
    },

    slotWindowDataChanged: function (window, role) {
        if (role === Effect.WindowAddedGrabRole) {
            if (window.revoInAnimation && effect.isGrabbed(window, role)) {
                cancel(window.revoInAnimation);
                delete window.revoInAnimation;
                revoMotion.cleanupForcedRoles(window);
            }
        } else if (role === Effect.WindowClosedGrabRole) {
            if (window.revoOutAnimation && effect.isGrabbed(window, role)) {
                cancel(window.revoOutAnimation);
                delete window.revoOutAnimation;
                revoMotion.cleanupForcedRoles(window);
            }
        }
    },

    init: function () {
        revoMotion.loadConfig();
        effect.configChanged.connect(revoMotion.loadConfig);
        effect.animationEnded.connect(revoMotion.cleanupForcedRoles);
        effects.windowAdded.connect(revoMotion.slotWindowAdded);
        effects.windowClosed.connect(revoMotion.slotWindowClosed);
        effects.windowDataChanged.connect(revoMotion.slotWindowDataChanged);
    }
};

revoMotion.init();
