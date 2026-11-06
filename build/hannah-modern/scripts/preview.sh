#!/bin/bash
# Native Qt/Plasma rendering under Xvfb, using the host kernel (no VM).
# No physical disk devices or host display sockets are passed into this container.
set -euo pipefail
root=/data/hannah-modern/rootfs
logs=/data/hannah-modern/logs
art=/data/hannah-modern/artifacts
cleanup() {
    if [ -n "${session_pid:-}" ]; then kill "$session_pid" 2>/dev/null || true; fi
    if [ -n "${xvfb_pid:-}" ]; then kill "$xvfb_pid" 2>/dev/null || true; fi
    umount "$root/tmp/.X11-unix" 2>/dev/null || true
    umount "$root/proc" 2>/dev/null || true
}
trap cleanup EXIT
mkdir -p "$root/proc" "$root/tmp/.X11-unix"
mount -t proc proc "$root/proc"
Xvfb :99 -screen 0 1440x1000x24 -ac -nolisten tcp > "$logs/xvfb.log" 2>&1 &
xvfb_pid=$!
sleep 1
mount --bind /tmp/.X11-unix "$root/tmp/.X11-unix"
mkdir -p "$root/tmp/hannah-preview-home" "$root/tmp/hannah-runtime"
chmod 700 "$root/tmp/hannah-runtime"
cp -a "$root/etc/skel/." "$root/tmp/hannah-preview-home/"
rm -rf "$root/tmp/hannah-preview-home/.cache" "$root/tmp/hannah-preview-home/.local" \
    "$root/tmp/hannah-preview-home/.config/plasma-org.kde.plasma.desktop-appletsrc"
chroot "$root" env HOME=/tmp/hannah-preview-home USER=root LANG=C.UTF-8 \
    XDG_RUNTIME_DIR=/tmp/hannah-runtime XDG_CONFIG_DIRS=/etc/xdg:/usr/share/kubuntu-default-settings/kf5-settings \
    XDG_MENU_PREFIX=plasma- XDG_DATA_DIRS=/usr/local/share:/usr/share:/var/lib/snapd/desktop \
    XDG_SESSION_TYPE=wayland XDG_CURRENT_DESKTOP=KDE KDE_FULL_SESSION=true \
    DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 KWIN_COMPOSE=Q \
    dbus-run-session -- kwin_wayland --x11-display :99 --width 1366 --height 768 \
    --no-lockscreen --xwayland --exit-with-session plasmashell \
    > "$logs/plasma-preview.log" 2>&1 &
session_pid=$!
sleep 20
xwd -display :99 -root -silent -out "$art/desktop-native.xwd"
magick "$art/desktop-native.xwd" -crop 1366x768+0+0 +repage "$art/desktop-native.png"
kill "$session_pid" 2>/dev/null || true
wait "$session_pid" 2>/dev/null || true
pkill -TERM -x kwin_wayland 2>/dev/null || true
sleep 2
# Test the two separate UI entry points in the same isolated X server.
timeout 15 chroot "$root" env HOME=/tmp/hannah-preview-home LANG=C.UTF-8 \
    DISPLAY=:99 QT_QPA_PLATFORM=xcb QT_QUICK_BACKEND=software QT_QPA_PLATFORMTHEME=kde \
    sddm-greeter-qt6 --test-mode --theme /usr/share/sddm/themes/hannah-montana \
    > "$logs/sddm-preview.log" 2>&1 &
greeter_pid=$!
sleep 8
xwd -display :99 -root -silent -out "$art/login-native.xwd"
magick "$art/login-native.xwd" "$art/login-native.png"
wait "$greeter_pid" || true
timeout 16 chroot "$root" env HOME=/tmp/hannah-preview-home LANG=C.UTF-8 \
    DISPLAY=:99 QT_QPA_PLATFORM=xcb QT_QUICK_BACKEND=software QT_QPA_PLATFORMTHEME=kde \
    calamares -d > "$logs/calamares-preview.log" 2>&1 &
installer_pid=$!
sleep 8
xwd -display :99 -root -silent -out "$art/installer-native.xwd"
magick "$art/installer-native.xwd" "$art/installer-native.png"
wait "$installer_pid" || true
timeout 14 chroot "$root" env HOME=/tmp/hannah-preview-home LANG=C.UTF-8 \
    DISPLAY=:99 QT_QPA_PLATFORM=xcb QT_QUICK_BACKEND=software QT_QPA_PLATFORMTHEME=kde \
    dbus-run-session -- plasma-welcome --pages 00-HannahMontana > "$logs/welcome-preview.log" 2>&1 &
welcome_pid=$!
sleep 7
xwd -display :99 -root -silent -out "$art/welcome-native.xwd"
magick "$art/welcome-native.xwd" "$art/welcome-native.png"
wait "$welcome_pid" || true
printf 'Native rendering previews saved in %s\n' "$art"
