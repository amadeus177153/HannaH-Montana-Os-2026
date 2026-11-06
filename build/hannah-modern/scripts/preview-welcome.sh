#!/bin/bash
set -euo pipefail
root=/data/hannah-modern/rootfs
art=/data/hannah-modern/artifacts
logs=/data/hannah-modern/logs
Xvfb :99 -screen 0 1100x850x24 -ac -nolisten tcp > "$logs/welcome-xvfb.log" 2>&1 &
xpid=$!
trap 'kill "$xpid" 2>/dev/null || true; umount "$root/tmp/.X11-unix" 2>/dev/null || true' EXIT
sleep 1
mkdir -p "$root/tmp/.X11-unix" "$root/tmp/hannah-welcome-home"
mount --bind /tmp/.X11-unix "$root/tmp/.X11-unix"
timeout 14 chroot "$root" env HOME=/tmp/hannah-welcome-home LANG=C.UTF-8 \
    DISPLAY=:99 QT_QPA_PLATFORM=xcb QT_QUICK_BACKEND=software QT_QPA_PLATFORMTHEME=kde \
    dbus-run-session -- plasma-welcome --pages 00-HannahMontana \
    > "$logs/welcome-preview.log" 2>&1 &
wpid=$!
sleep 8
xwd -display :99 -root -silent -out "$art/welcome-native.xwd"
magick "$art/welcome-native.xwd" "$art/welcome-native.png"
wait "$wpid" || true
