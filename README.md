# breezy-deck

Helpers for using XR glasses with [Breezy Desktop](https://github.com/wheaney/breezy-desktop)
on a Steam Deck in desktop mode (KDE Plasma, Wayland). Built for VITURE Beast
glasses, but nothing here is specific to them.

## What you get

| Feature | How to trigger it |
|---|---|
| Recenter the view | **double-tap the glasses** (two quick knocks on the frame), `Meta+Ctrl+Space`, the *Recenter Glasses* launcher, or `breezy recenter` |
| Rotate the screens (every window moves one screen over, wrapping round; the cursor returns to the middle screen) | **R3 / L3** (right/left stick click), **L5 + D-pad right/left** (hold the lower-left back button), `Scroll Lock` / `Pause`, `Meta+Ctrl+Alt+Right/Left`, or `breezy rotate right\|left` |
| Cursor back to the middle screen (focuses the topmost window there; does nothing if that screen is empty) | **L4 + L5** (both left back buttons; it happens when you let go), **double-tap the glasses** (after recentering), or `breezy center` |
| Swap the active window with its neighbour (it moves one screen over and the windows there take its place; then, as after rotate, the cursor and focus return to the middle screen) | **L4 + L5 + D-pad right/left** (both left back buttons), `Shift+Meta+Ctrl+Alt+Right/Left`, or `breezy swap right\|left` |
| Change the background behind the screens (starfield, matrix, cyberpunk, nature, vaporwave, none) | **L5 + D-pad up/down**, or `breezy background next\|prev\|<name>` |
| Five screens set up automatically when the glasses connect (the glasses' own screen plus four virtual ones), panel on the middle one | automatic (`breezy-auto-screens` service) |
| Deck's own screen turned off while the glasses are connected (it isn't shown in them, so the cursor got lost there); left on if only their USB is connected (e.g. a dock whose USB-C port carries no video) | automatic |
| Saved window layout restored when the glasses connect | `breezy layout save` once, then automatic |

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
  rule) instead of the leftmost one.
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
breezy layout save|restore|show     # ~/.config/breezy-layout.json
breezy background [list|<name>|none|next]
breezy screens add [n] [w] [h] | list | remove <id>
breezy auto-screens                 # run by the breezy-auto-screens service
breezy taps                         # run by the breezy-taps service
```

Works from VS Code's (sandboxed) terminal too.

## Layout of this repo

- `bin/breezy`: the command; each subcommand is a script in `libexec/`
- `systemd/`: the user services that set up the screens and follow the glasses' double-taps
- `applications/`: launchers (the rotate, swap and center ones are what the shortcuts run)
- `steam/desktop_layout.vdf`: Steam's default Deck desktop layout with
  L3 = Pause, R3 = Scroll Lock, L4 = Shift, L5 = Meta, and, while L5 is held,
  D-pad = Ctrl+Alt+arrows (a Steam Input mode shift). Letting
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
