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
// (scripts can't warp the cursor; KWin's MoveMouseToFocus can). A Wayland
// window only lands on its new screen once the app redraws there; moving the
// mouse before that would put it where the window was.
function focusAndFollow(w, screen) {
    workspace.activeWindow = w;
    const g = screen.geometry;
    const arrived = () => {
        const f = w.frameGeometry, cx = f.x + f.width / 2;
        return cx >= g.x && cx < g.x + g.width;
    };
    const moveMouse = () => {
        if (!arrived()) return;
        w.frameGeometryChanged.disconnect(moveMouse);
        callDBus("org.kde.kglobalaccel", "/component/kwin", "org.kde.kglobalaccel.Component",
                 "invokeShortcut", "MoveMouseToFocus");
    };
    w.frameGeometryChanged.connect(moveMouse);
    moveMouse();  // X11 windows have moved already
}
