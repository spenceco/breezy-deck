# Sourced by rotate and swap.
# run_kwin_script NAME: run the JavaScript on stdin, after kwin-helpers.js, as
# a one-off KWin script, so there is no long-lived script to go stale.
run_kwin_script() {
    local script id
    script=$(mktemp --suffix=.js)
    cat "$(dirname "${BASH_SOURCE[0]}")/kwin-helpers.js" - > "$script"
    kwin /Scripting org.kde.kwin.Scripting.unloadScript "$1" >/dev/null
    id=$(kwin /Scripting org.kde.kwin.Scripting.loadScript "$script" "$1" | grep -oE '[0-9]+')
    kwin "/Scripting/Script$id" org.kde.kwin.Script.run >/dev/null
    sleep 1  # time for the moved windows to redraw (see focusAndFollow)
    kwin /Scripting org.kde.kwin.Scripting.unloadScript "$1" >/dev/null
    rm -f "$script"
}

kwin() { gdbus call --session --dest org.kde.KWin --object-path "$1" --method "$2" "${@:3}"; }
