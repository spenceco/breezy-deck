#!/bin/bash
# Install (or update) the Breezy Desktop helpers for this user. Safe to re-run.
#   ./install.sh           command, service, launchers, shortcuts, KDE settings
#   ./install.sh --steam   also install the Deck's desktop button layout
#                          (closes Steam for a moment and starts it again)
set -euo pipefail

# VS Code's terminal runs in a Flatpak sandbox: run on the host instead.
if [[ -f /.flatpak-info ]]; then
    exec flatpak-spawn --host --directory="$HOME" "$(readlink -f "$0")" "$@"
fi

repo=$(dirname "$(readlink -f "$0")")
bin=$HOME/.local/bin/breezy
apps=$HOME/.local/share/applications
units=$HOME/.config/systemd/user
steam=$HOME/.local/share/Steam
step() { echo "== $*"; }

step "Command: $bin"
mkdir -p "$(dirname "$bin")"
ln -sfn "$repo/bin/breezy" "$bin"
# The separate scripts this replaces.
rm -f "$HOME"/.local/bin/breezy_{auto_screens,layout,recenter,rotate}

step "Launchers"
mkdir -p "$apps"
for f in "$repo"/applications/*.desktop; do
    sed "s|@BREEZY@|$bin|" "$f" > "$apps/$(basename "$f")"
done
update-desktop-database "$apps" 2>/dev/null || true
kbuildsycoca6 >/dev/null 2>&1 || true

step "Service: breezy-auto-screens"
mkdir -p "$units"
cp "$repo/systemd/breezy-auto-screens.service" "$units/"
systemctl --user daemon-reload
systemctl --user enable breezy-auto-screens.service >/dev/null 2>&1
# Restart only when it changed: a restart briefly turns the Deck's screen on,
# which shuffles windows.
stamp=$HOME/.cache/breezy-deck.stamp
sum=$(cat "$repo/systemd/breezy-auto-screens.service" "$repo/libexec/auto-screens" | sha1sum)
if ! systemctl --user is-active -q breezy-auto-screens.service || [[ $(cat "$stamp" 2>/dev/null) != "$sum" ]]; then
    systemctl --user restart breezy-auto-screens.service
fi
echo "$sum" > "$stamp"

step "Service: breezy-taps (double-tap the glasses)"
cp "$repo/systemd/breezy-taps.service" "$units/"
systemctl --user daemon-reload
systemctl --user enable breezy-taps.service >/dev/null 2>&1
systemctl --user restart breezy-taps.service
# The driver's tap gesture is off by default.
"$HOME/.local/bin/xr_driver_cli" --multi-tap >/dev/null 2>&1 || echo "   Couldn't turn on the driver's multi-tap (xr_driver_cli --multi-tap)."

step "Shortcuts"
# Qt key codes: Meta 0x10000000, Ctrl 0x04000000, Alt 0x08000000.
META_CTRL_SPACE=335544352 PAUSE=16777224 META_PAUSE=285212680
META_CTRL_ALT_RIGHT=486539284 META_CTRL_ALT_LEFT=486539282 SCROLL_LOCK=16777254
SHIFT_META_CTRL_ALT_RIGHT=520093716 SHIFT_META_CTRL_ALT_LEFT=520093714  # + Shift 0x02000000
META_CTRL_ALT_SCROLL_LOCK=486539302 SHIFT_CTRL_ALT_SCROLL_LOCK=251658278
accel() {
    gdbus call --session --dest org.kde.kglobalaccel --object-path /kglobalaccel \
        --method "org.kde.KGlobalAccel.$1" "${@:2}" >/dev/null
}
keys() {  # keys <component> <action> <component name> <action name> <code>...
    local id="[\"$1\",\"$2\",\"$3\",\"$4\"]" list="" k
    for k in "${@:5}"; do list+="([$k, 0, 0, 0],), "; done
    accel doRegister "$id"
    accel setForeignShortcutKeys "$id" "[${list%, }]"
}
# Keys move between actions here, so actions giving keys up come first.
# Recenter is Breezy's own action (double-tapping the glasses also recenters).
keys kwin Recenter KWin Recenter $META_CTRL_SPACE
# Cursor to the middle screen. The Deck's layout sends Ctrl+Alt+Scroll Lock
# when L4 or L5 is let go; with the other one still held (L4 sends Shift, L5
# Meta), that's L4 + L5.
keys breezy-deck-center.desktop _launch "Cursor to Middle Screen (Glasses)" Launch \
    $META_CTRL_ALT_SCROLL_LOCK $SHIFT_CTRL_ALT_SCROLL_LOCK
# Rotate: L5 + D-pad sends Meta+Ctrl+Alt+arrow; L3 sends Pause (Meta+Pause in
# case L5 is held) and R3 Scroll Lock.
keys breezy-deck-rotate-right.desktop _launch "Rotate Glasses Screens Right" Launch $META_CTRL_ALT_RIGHT $SCROLL_LOCK
keys breezy-deck-rotate-left.desktop _launch "Rotate Glasses Screens Left" Launch $META_CTRL_ALT_LEFT $PAUSE $META_PAUSE
# Swap is rotate's keys plus Shift: on the Deck, L4 (Shift) + L5 + D-pad.
keys breezy-deck-swap-right.desktop _launch "Swap Window Right (Glasses)" Launch $SHIFT_META_CTRL_ALT_RIGHT
keys breezy-deck-swap-left.desktop _launch "Swap Window Left (Glasses)" Launch $SHIFT_META_CTRL_ALT_LEFT
# Earlier versions: launchers under other names (KDE caches a launcher's
# command until logout, so new names were needed) and a KWin script whose
# shortcuts went stale on reload. Free their keys.
for old in breezy-rotate-right.desktop breezy-rotate-left.desktop; do
    accel setForeignShortcutKeys "[\"$old\",\"_launch\",\"\",\"\"]" "[]" || true
    accel unregister "$old" _launch || true
    kwriteconfig6 --file kglobalshortcutsrc --group services --group "$old" --key _launch --delete
done
rm -f "$apps"/breezy-{recenter,rotate-right,rotate-left}.desktop
accel unregister kwin "Breezy: Rotate screens right" || true
accel unregister kwin "Breezy: Rotate screens left" || true
kwriteconfig6 --file kwinrc --group Plugins --key breezyrotatescreensEnabled --delete
rm -rf "$HOME/.local/share/kwin/scripts/breezyrotatescreens"

# KDE only activates command shortcuts when you log in; ones added during the
# session are saved but ignore key presses until then.
for component in rotate_right swap_right center; do
    active=$(qdbus6 org.kde.kglobalaccel /component/breezy_deck_${component}_desktop \
        org.kde.kglobalaccel.Component.isActive 2>/dev/null || echo false)
    if [[ $active != true ]]; then
        echo "   Log out and back in once to activate the rotate, swap and center shortcuts (L3, R3, L4/L5 + D-pad, L4 + L5)."
        break
    fi
done

step "KDE settings"
# Locking when the screens turn off made clicks vanish: the lock screen isn't
# shown in the glasses but takes every click. Screens also went off after 60 s.
for group in AC Battery LowBattery; do
    kwriteconfig6 --file powerdevilrc --group $group --group Display --key LockBeforeTurnOffDisplay false
done
for group in Battery LowBattery; do
    kwriteconfig6 --file powerdevilrc --group $group --group Display --key TurnOffDisplayIdleTimeoutSec 600
done
qdbus6 org.kde.Solid.PowerManagement /org/kde/Solid/PowerManagement \
    org.kde.Solid.PowerManagement.refreshStatus >/dev/null 2>&1 || true
# No resistance when the cursor crosses between screens.
kwriteconfig6 --file kwinrc --group EdgeBarrier --key EdgeBarrier 0
kwriteconfig6 --file kwinrc --group EdgeBarrier --key CornerBarrier false
# KWin window rules that put windows on the middle (third) screen. KWin numbers
# screens in the order they appeared: the glasses' own first, then the four
# virtual ones (the Deck's screen is off), so the middle one is 2. Without the
# glasses there is no third screen and KWin ignores the rules.
kw() { kwriteconfig6 --file kwinrulesrc --group "$rule" --key "$@"; }
add_rule() {  # after the rule's keys are written; KWin uses the first matching rule
    local rules
    rules=$(kreadconfig6 --file kwinrulesrc --group General --key rules)
    if [[ ,$rules, != *,$rule,* ]]; then
        rules=${rules:+$rules,}$rule
        kwriteconfig6 --file kwinrulesrc --group General --key rules "$rules"
        kwriteconfig6 --file kwinrulesrc --group General --key count "$(tr , '\n' <<< "$rules" | wc -l)"
    fi
}
# Steam's on-screen keyboard opens at the bottom of the first (leftmost) screen.
rule=breezy-deck-keyboard
kw Description "Steam keyboard on the middle screen (breezy-deck)"
kw wmclass steam; kw wmclassmatch 1  # 1 = exact match
kw title "Steam Input On-screen Keyboard"; kw titlematch 1
kw screen 2; kw screenrule 2  # 2 = force
add_rule
# Apps that pick their own position (X11 ones like Discord and Steam) opened on
# the leftmost screen. Every program's main window opens on the middle screen:
# KWin ignores the position the app asks for (or the screen rule loses to it)
# and places the window itself. "Apply initially" only places it there, so
# rotate can still move it; dialogs (not normal windows) still open by their
# parent.
rule=breezy-deck-open-middle
kw Description "Open programs on the middle screen (breezy-deck)"
kw types 1  # normal windows
kw ignoregeometry true; kw ignoregeometryrule 2  # 2 = force
kw screen 2; kw screenrule 3  # 3 = apply initially
add_rule
qdbus6 org.kde.KWin /KWin reconfigure >/dev/null 2>&1 || true

if [[ ${1:-} == --steam ]]; then
    step "Steam desktop layout (L3/R3 and L5 + D-pad rotate, L4 + L5 center)"
    configs=$(ls -d "$steam/steamapps/common/Steam Controller Configs"/*/config | head -1)
    was_running=0
    if pgrep -x steam >/dev/null; then
        was_running=1
        "$steam/steam.sh" -shutdown >/dev/null 2>&1 &
        for _ in $(seq 60); do pgrep -x steam >/dev/null || break; sleep 1; done
        pgrep -x steam >/dev/null && { echo "Steam didn't close; try again" >&2; exit 1; }
    fi
    mkdir -p "$configs/413080"
    cp "$repo/steam/desktop_layout.vdf" "$configs/413080/controller_neptune.vdf"
    # Select it as the Deck's desktop layout.
    configset="$configs/configset_controller_neptune.vdf"
    [[ -f $configset ]] || printf '"controller_config"\n{\n}\n' > "$configset"
    if ! grep -q '"413080"' "$configset"; then
        python3 - "$configset" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read().rstrip()
s = s[:-1] + '\t"413080"\n\t{\n\t\t"autosave"\t\t"1"\n\t}\n}\n'
open(p, "w").write(s)
PY
    fi
    if (( was_running )); then
        systemd-run --user --unit="breezy-steam-restart-$RANDOM" "$steam/steam.sh" -steamdeck -silent >/dev/null 2>&1
    fi
else
    echo "(Steam button layout not touched; run ./install.sh --steam to install it)"
fi

# Desktop Breezy can only send commands (like Recenter) to the glasses driver
# if this file is writable; the root-run Decky plugin creates it at boot.
if [[ ! -f /etc/tmpfiles.d/xr-driver-control.conf ]]; then
    cat <<'EOF'

One step needs your password. In Konsole run:
  echo 'f /dev/shm/xr_driver_control 0666 root root -' | sudo tee /etc/tmpfiles.d/xr-driver-control.conf
  sudo chmod 666 /dev/shm/xr_driver_control
EOF
fi
echo "Done."
