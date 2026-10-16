// Shared by the rotate and swap KWin scripts (put in front of each one).

// The glasses' screens, left to right. The Deck's own screen (eDP) is left out.
const screens = workspace.screens
    .filter(s => !s.name.startsWith("eDP"))
    .sort((a, b) => a.geometry.x - b.geometry.x || a.geometry.y - b.geometry.y);

// Shown on the current virtual desktop.
function shown(w) {
    return !w.minimized && (w.onAllDesktops || w.desktops.includes(workspace.currentDesktop));
}

// Activate w, which is being moved to screen, and move the cursor onto it
// (scripts can't warp the cursor; KWin's MoveMouseToFocus moves it to the
// active window). Wait until w is both there and active: a Wayland window only
// lands on its new screen once the app redraws there, and an X11 window only
// becomes active once X confirms the focus. Moving the mouse earlier put it
// where the window was, or on the previously active window.
function focusAndFollow(w, screen) {
    const g = screen.geometry;
    const ready = () => {
        const f = w.frameGeometry, cx = f.x + f.width / 2;
        return cx >= g.x && cx < g.x + g.width && workspace.activeWindow === w;
    };
    const moveMouse = () => {
        if (!ready()) return;
        w.frameGeometryChanged.disconnect(moveMouse);
        workspace.windowActivated.disconnect(moveMouse);
        callDBus("org.kde.kglobalaccel", "/component/kwin", "org.kde.kglobalaccel.Component",
                 "invokeShortcut", "MoveMouseToFocus");
    };
    w.frameGeometryChanged.connect(moveMouse);
    workspace.windowActivated.connect(moveMouse);
    workspace.activeWindow = w;
    moveMouse();  // already there and active (X11 moves, Wayland focus)
}

// Cursor and focus to the middle screen: focusAndFollow the topmost shown
// window of windows (those that end up on the middle screen).
function focusMiddle(windows) {
    const middle = screens[Math.floor(screens.length / 2)];
    const stack = workspace.stackingOrder;
    for (let i = stack.length - 1; i >= 0; i--) {
        if (windows.includes(stack[i]) && shown(stack[i])) {
            focusAndFollow(stack[i], middle);
            return;
        }
    }
}
