# breezy-deck

Helpers for using XR glasses with [Breezy Desktop](https://github.com/wheaney/breezy-desktop)
on a Steam Deck in desktop mode (KDE Plasma, Wayland). Built for VITURE Beast
glasses, but nothing here is specific to them.

## What you get

| Feature | How to trigger it |
|---|---|
| Recenter the view | **L3** (left stick click), `Meta+Ctrl+Space`, `Pause`, the *Recenter Glasses* launcher, or `breezy recenter` |
| Rotate the screens (every window moves one screen over, wrapping round; the cursor returns to the middle screen) | **R3** (right stick click) or `Meta+Ctrl+Alt+Right` for right; `Meta+Ctrl+Alt+Left` for left; `breezy rotate right\|left` |
| Five screens set up automatically when the glasses connect (the glasses' own screen plus four virtual ones), panel on the middle one | automatic (`breezy-auto-screens` service) |
| Deck's own screen turned off while the glasses are connected (it isn't shown in them, so the cursor got lost there) | automatic |
| Saved window layout restored when the glasses connect | `breezy layout save` once, then automatic |

Other fixes it applies:

- **No screen lock when the screens turn off**, and screens stay on for 10
  minutes instead of 60 seconds on battery. The lock screen isn't visible in
  the glasses but takes every click, which looked like the mouse stopped
  working.
- **No edge barrier** between screens.
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

`--steam` installs the Deck's desktop button layout (L3 and R3 as above;
everything else is Steam's default). It closes Steam for a moment. Leave it
off to keep your own Steam layout.

The install script prints one command to run with `sudo` if it's still
needed: Breezy's Recenter can only reach the glasses driver if
`/dev/shm/xr_driver_control` is writable, and the Decky XR Gaming plugin
creates it as root-only at every boot.

After the first install, **log out and back in once**: KDE only activates
shortcuts that run commands (rotate) at login. Until then they are saved but
ignore key presses.

Run `install.sh` again after changing anything here. `uninstall.sh` (with
`--steam` to also restore Steam's default layout) removes it all.

## The `breezy` command

```
breezy recenter
breezy rotate right|left
breezy layout save|restore|show     # ~/.config/breezy-layout.json
breezy screens add [n] [w] [h] | list | remove <id>
breezy auto-screens                 # run by the service
```

Works from VS Code's (sandboxed) terminal too.

## Layout of this repo

- `bin/breezy`: the command; each subcommand is a script in `libexec/`
- `systemd/`: the user service that sets up the screens
- `applications/`: launchers (the rotate ones are what the shortcuts run)
- `steam/desktop_layout.vdf`: Steam's default Deck desktop layout with
  L3 = Pause and R3 = Scroll Lock
- `install.sh`, `uninstall.sh`

## Notes

- Shortcuts that run commands, not KWin scripts: a KWin script's shortcuts
  stop working if the script is reloaded until you log out.
- KDE caches a launcher's command until logout, so changing the `Exec` line of
  a launcher only takes effect after logging out (or under a new file name).
- The glasses' own buttons can't recenter on the desktop: the XR driver
  doesn't read them (holding the button only recenters in VITURE's own app).
  Double-tap recentering isn't detected on the VITURE Beast either.
