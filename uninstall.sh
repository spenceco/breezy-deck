#!/bin/bash
# Remove what install.sh set up. Your saved window layout
# (~/.config/breezy-layout.json) is kept.
#   ./uninstall.sh           command, service, launchers, shortcuts, KDE settings
#   ./uninstall.sh --steam   also switch the Deck back to Steam's default
#                            desktop button layout (restarts Steam)
set -uo pipefail

if [[ -f /.flatpak-info ]]; then
    exec flatpak-spawn --host --directory="$HOME" "$(readlink -f "$0")" "$@"
fi

steam=$HOME/.local/share/Steam
step() { echo "== $*"; }

step "Service"
systemctl --user disable --now breezy-auto-screens.service 2>/dev/null
rm -f "$HOME/.config/systemd/user/breezy-auto-screens.service"
systemctl --user disable --now breezy-taps.service 2>/dev/null
rm -f "$HOME/.config/systemd/user/breezy-taps.service"
systemctl --user daemon-reload
kscreen-doctor output.eDP-1.enable >/dev/null 2>&1

step "Shortcuts"
accel() {
    gdbus call --session --dest org.kde.kglobalaccel --object-path /kglobalaccel \
        --method "org.kde.KGlobalAccel.$1" "${@:2}" >/dev/null 2>&1
}
for launcher in breezy-deck-{rotate,swap}-{right,left}.desktop breezy-deck-center.desktop \
        breezy-deck-background-{next,prev}.desktop breezy-deck-screenshot.desktop; do
    accel setForeignShortcutKeys "[\"$launcher\",\"_launch\",\"\",\"\"]" "[]"
    accel unregister "$launcher" _launch
    kwriteconfig6 --file kglobalshortcutsrc --group services --group "$launcher" --key _launch --delete
done
rm -f "$HOME/.cache/breezy-deck.stamp"
# Recenter back to Breezy's own default, Meta+Ctrl+Space.
accel setForeignShortcutKeys '["kwin","Recenter","KWin","Recenter"]' '[([335544352, 0, 0, 0],)]'

step "Command and launchers"
rm -f "$HOME/.local/bin/breezy" "$HOME"/.local/share/applications/breezy-deck-{recenter,center,rotate-right,rotate-left,swap-right,swap-left,background-next,background-prev,screenshot}.desktop
kbuildsycoca6 >/dev/null 2>&1

step "KDE settings back to defaults"
for group in AC Battery LowBattery; do
    kwriteconfig6 --file powerdevilrc --group $group --group Display --key LockBeforeTurnOffDisplay --delete
    kwriteconfig6 --file powerdevilrc --group $group --group Display --key TurnOffDisplayIdleTimeoutSec --delete
done
kwriteconfig6 --file kwinrc --group EdgeBarrier --key EdgeBarrier --delete
kwriteconfig6 --file kwinrc --group EdgeBarrier --key CornerBarrier --delete
kwriteconfig6 --file kwinrc --group Effect-breezy_desktop --key CurvedDisplay --delete
sed -i 's/^curved_display=.*/curved_display=false/' "$HOME/.config/xr_driver/config.ini" 2>/dev/null
# The background lines patched into Breezy's scene (gone after the next login).
sed -i -e '/breezy-deck: starfield/,/breezy-deck: starfield background loaded/d' \
    -e '/breezy-deck: background {/,/breezy-deck: background }/d' -e '/breezy-deck: background$/d' \
    "$HOME/.local/share/kwin/effects/breezy_desktop/qml/main.qml" 2>/dev/null
rm -rf "$HOME/.local/share/breezy-deck/background" "$HOME/.config/breezy-background"
# The window rules (Steam keyboard, programs opening on the middle screen).
rules=$(kreadconfig6 --file kwinrulesrc --group General --key rules | tr , '\n' |
    grep -vxE 'breezy-deck-(keyboard|open-middle)')
kwriteconfig6 --file kwinrulesrc --group General --key rules "$(paste -sd, <<< "$rules")"
kwriteconfig6 --file kwinrulesrc --group General --key count "$(grep -c . <<< "$rules")"
for rule in breezy-deck-keyboard breezy-deck-open-middle; do
    for key in Description wmclass wmclassmatch title titlematch types ignoregeometry ignoregeometryrule screen screenrule; do
        kwriteconfig6 --file kwinrulesrc --group $rule --key $key --delete
    done
done
qdbus6 org.kde.KWin /KWin reconfigure >/dev/null 2>&1

if [[ ${1:-} == --steam ]]; then
    step "Steam default desktop layout"
    configs=$(ls -d "$steam/steamapps/common/Steam Controller Configs"/*/config | head -1)
    was_running=0
    if pgrep -x steam >/dev/null; then
        was_running=1
        "$steam/steam.sh" -shutdown >/dev/null 2>&1 &
        for _ in $(seq 60); do pgrep -x steam >/dev/null || break; sleep 1; done
    fi
    rm -f "$configs/413080/controller_neptune.vdf"
    python3 - "$configs/configset_controller_neptune.vdf" <<'PY'
import re, sys
p = sys.argv[1]
try:
    s = open(p).read()
except FileNotFoundError:
    sys.exit()
open(p, "w").write(re.sub(r'\t"413080"\n\t\{[^}]*\}\n', "", s))
PY
    (( was_running )) && systemd-run --user --unit="breezy-steam-restart-$RANDOM" "$steam/steam.sh" -steamdeck -silent >/dev/null 2>&1
fi

cat <<'EOF'
Done. To also drop the driver-file fix (needs your password):
  sudo rm /etc/tmpfiles.d/xr-driver-control.conf
EOF
