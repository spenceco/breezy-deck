# breezy-deck

Helpers for using XR glasses with [Breezy Desktop](https://github.com/wheaney/breezy-desktop)
on a Steam Deck in desktop mode (KDE Plasma, Wayland). Built for VITURE Beast
glasses, but nothing here is specific to them.

## What you get

| Feature | How to trigger it |
|---|---|
| Recenter the view | **L5 + X** (hold the lower-left back button), **double-tap the glasses** (two quick knocks on the frame), `Meta+Ctrl+Space`, the *Recenter Glasses* launcher, or `breezy recenter` |
| Rotate the screens (every window moves one screen over, wrapping round; the cursor returns to the middle screen) | **R3 / L3** (right/left stick click), **L5 + D-pad right/left** (hold the lower-left back button), `Scroll Lock` / `Pause`, `Meta+Ctrl+Alt+Right/Left`, or `breezy rotate right\|left` |
| Cursor back to the middle screen (focuses the topmost window there; does nothing if that screen is empty) | **L4 + L5** (both left back buttons; it happens when you let go), **double-tap the glasses** (after recentering), or `breezy center` |
| Swap the active window with its neighbour (it moves one screen over and the windows there take its place; then, as after rotate, the cursor and focus return to the middle screen) | **L4 + L5 + D-pad right/left** (both left back buttons), `Shift+Meta+Ctrl+Alt+Right/Left`, or `breezy swap right\|left` |
| Change the background behind the screens (starfield, matrix, cyberpunk, nature, vaporwave, none) | **L5 + D-pad up/down**, or `breezy background next\|prev\|<name>` |
| Widget strip floating above the middle screen: clock, calendar, media player, CPU, memory, battery (KDE desktop widgets on a short virtual screen; rotate, swap and center leave it alone) | automatic when the glasses connect, or `breezy widgets` |
| Screenshot of what the glasses show, saved to `~/Pictures/Glasses` | **L5 + A**, `Meta+Ctrl+Alt+S`, or `breezy screenshot` |
| More or fewer screens: 1, 3 or 5, always one more or one fewer on each side so the middle screen stays straight ahead (windows on a removed screen move one screen inwards). The glasses start with 1 (their own screen); the panel is on the middle one | **L5 + Y** (more) / **L5 + B** (fewer), `Meta+Ctrl+Alt+PgUp/PgDn`, or `breezy screens more\|less` |
| Deck's own screen turned off while the glasses are connected (it isn't shown in them, so the cursor got lost there); left on if only their USB is connected (e.g. a dock whose USB-C port carries no video) | automatic |
| Save which window is on which screen, and put them back (opening missing apps) | `breezy layout save`, then `breezy layout restore` when you want it |
| A stereo 3D scene (a side-by-side cut-out in a 360° room, e.g. the [skybox viewer](https://github.com/spenceco/stereo-skybox-viewer)) that you look around in with your head, in the glasses' 3D mode. See [Throne viewer](#throne-viewer-stereo-3d-with-head-tracking) | `Meta+Ctrl+Alt+T` (again to leave), the *Throne Viewer* launcher, or `breezy throne` |

Other fixes it applies:

- **No screen lock when the screens turn off**, and screens stay on for 10
  minutes instead of 60 seconds on battery. The lock screen isn't visible in
  the glasses but takes every click, which looked like the mouse stopped
  working.
- **No edge barrier** between screens.
- **A background behind the screens** instead of see-through black:
  starfield (default), matrix, cyberpunk, nature or vaporwave, switched live
  with **L5 + D-pad up/down** or `breezy background <name>` (`list`, `next`,
  `prev`, `none`). install.sh patches
  Breezy's scene (`qml/main.qml`) to show whatever image is in
  `~/.local/share/breezy-deck/background`; the patch itself only takes effect
  after a login (KWin keeps compiled QML until then). Re-run install.sh after
  a Breezy update, which replaces the file. The images are 360° panoramas
  made by `backgrounds/make-*.py` (Pillow and numpy; starfield needs neither).
- **Curved screens**: Breezy's Curved Display is on, so each screen bends
  around you as well as the row of screens wrapping round.
- **Steam's on-screen keyboard opens on the middle screen** (a KWin window
  rule) instead of the leftmost one. The rule names the glasses' own screen,
  which `breezy screens` keeps in the middle.
- **Programs open on the middle screen.** Apps that choose their own position
  (X11 ones like Discord and Steam) opened on the leftmost screen. A KWin
  window rule makes KWin ignore the position they ask for and open them on the
  middle screen; dialogs still open next to their window, and rotate still
  moves windows as usual.

## Install

```
git clone <this repo> ~/breezy-deck
~/breezy-deck/install.sh --steam
```

`--steam` installs the Deck's desktop button layout (L3, R3, L4 and L5 as above;
everything else is Steam's default). It closes Steam for a moment. Leave it
off to keep your own Steam layout.

The install script prints one command to run with `sudo` if it's still
needed: Breezy's Recenter can only reach the glasses driver if
`/dev/shm/xr_driver_control` is writable, and the Decky XR Gaming plugin
creates it as root-only at every boot.

After the first install, **log out and back in once**: KDE only activates
shortcuts that run commands (rotate, swap, center) at login. Until then they are saved but
ignore key presses.

Run `install.sh` again after changing anything here. `uninstall.sh` (with
`--steam` to also restore Steam's default layout) removes it all.

## The `breezy` command

```
breezy recenter
breezy center
breezy rotate right|left
breezy swap right|left
breezy layout save|restore|place|show  # ~/.config/breezy-layout.json
breezy background [list|<name>|none|next|prev]
breezy widgets
breezy screenshot
breezy screens more|less|arrange
breezy screens add [n] [w] [h] | list | remove <id>
breezy throne [<viewer-url>|stop]  # stereo viewer in the glasses, head-tracked
breezy auto-screens                 # run by the breezy-auto-screens service
breezy taps                         # run by the breezy-taps service
```

Works from VS Code's (sandboxed) terminal too.

## Throne viewer (stereo 3D with head tracking)

Breezy draws its scene from one camera, so in the glasses' side-by-side 3D
mode nothing inside it (screens or background) can be stereo. `breezy throne`
hands the glasses' screen to the stereo skybox viewer instead, and feeds it
the head pose Breezy would have used:

1. Saves your window layout and how many screens you have, stops
   breezy-auto-screens and unloads Breezy's KWin effect (which removes its
   virtual screens), keeping the Deck's screen off.
2. Starts `libexec/throne-server` on 127.0.0.1:8770. It serves the viewer
   (fetched from the address you gave and cached in `~/.cache/breezy-throne`,
   so it works offline once seen) and streams the glasses' orientation from
   the driver's `/dev/shm/breezy_desktop_imu`, decoded and converted exactly
   as Breezy does, as Server-Sent Events on `/pose`. `/status` shows the
   decoded block.
3. Opens it fullscreen in Firefox (own profile, kiosk mode; Chrome, Chromium
   or Brave if there's no Firefox).

It switches the glasses to 3D by itself. The XR driver can't: it forces a
Beast into 2D whenever it connects (and the glasses' buttons are dead while
it runs). So while the viewer is open the driver is stopped and
`libexec/throne-glasses` drives the glasses through VITURE's own SDK (the
`libglasses.so` the driver installed): it turns off the glasses' own
anchoring, switches them to 3D side-by-side, and writes their head tracking
in the driver's format for throne-server. On the way out it puts the glasses
back as they were and the driver takes over again. If that fails, the driver
comes back and the viewer runs in 2D (`$XDG_RUNTIME_DIR/breezy-throne/glasses.log`
says why).

In 3D a Beast wants a 3840x1080 picture, and it gives up on 3D within about
a second if it isn't getting one: far too fast for KWin, which only learns of
the wide mode from the glasses as they switch. So the Deck has to offer that
mode all along: once per boot, run

    sudo ~/breezy-deck/libexec/throne-edid

It gives the kernel a copy of the glasses' EDID with 3840x1080@60 added (a
debugfs override: a reboot or `sudo .../throne-edid reset` undoes it).
throne then switches to the wide picture on the glasses' first display change
and back to 1920x1080 on the way out. Without it, throne says so and the
glasses stay in 2D. If head tracking doesn't come back afterwards, replug the
glasses: a change of picture size sometimes leaves them deaf to USB.

In the viewer the camera follows your head (with Breezy's look-ahead), the
field of view is the glasses' own. Double-click (trackpad) cycles 2D, 3D
(half side-by-side) and 3D (full side-by-side) if the mode is wrong. R, Space or Enter
recenters, H opens the settings panel, Ctrl+Q leaves. Leaving
loads Breezy again, adds the screens back and puts the windows back.

First time: `breezy throne <viewer-url>` (the address is kept in
`~/.config/breezy-throne-url`). After that, `Meta+Ctrl+Alt+T` or the launcher.
To always open in one environment, put its name (as in the viewer's
Environment menu, e.g. `Backyard patio (3D)`) in `~/.config/breezy-throne-env`.

## Layout of this repo

- `bin/breezy`: the command; each subcommand is a script in `libexec/`
- `systemd/`: the user services that set up the screens and follow the glasses' double-taps
- `applications/`: launchers (the rotate, swap and center ones are what the shortcuts run)
- `steam/desktop_layout.vdf`: Steam's default Deck desktop layout with
  L3 = Pause, R3 = Scroll Lock, L4 = Shift, L5 = Meta, and, while L5 is held,
  D-pad = Ctrl+Alt+arrows, A = Ctrl+Alt+S, X = Ctrl+Space (recenter),
  Y = Ctrl+Alt+PgUp and B = Ctrl+Alt+PgDn (Steam Input mode shifts). Letting
  go of L4 or L5 also sends Ctrl+Alt+Scroll Lock; with the other still held
  (adding Meta or Shift) that's the L4 + L5 shortcut. It fires on release so
  that L4 + L5 + D-pad (swap) still swaps the active window.
- `install.sh`, `uninstall.sh`

## Notes

- Shortcuts that run commands, not KWin scripts: a KWin script's shortcuts
  stop working if the script is reloaded until you log out.
- KDE caches a launcher's command until logout, so changing the `Exec` line of
  a launcher only takes effect after logging out (or under a new file name).
- The glasses' own buttons can't recenter on the desktop: the XR driver
  doesn't read them (holding the button only recenters in VITURE's own app).
  Double-tap recentering isn't detected on the VITURE Beast either.
