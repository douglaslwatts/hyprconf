!#/bin/bash

WAYBAR_CONFIGS="${HOME}/.config/waybar/config ${HOME}/.config/waybar/style.css"

trap "killall waybar" EXIT

while true; do
    waybar & disown
    inotifywait -e create,modify $WAYBAR_CONFIGS
    killall waybar
done

