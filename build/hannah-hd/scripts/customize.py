#!/usr/bin/env python3
"""Build the Hannah Montana artwork package and customize a Kubuntu live tree.

Run as root INSIDE the builder container. Only paths beneath the workspace change.
The 2009 ISO is a source of artwork, never of executable code or repositories.
"""
from pathlib import Path
from PIL import Image
import configparser
import gzip
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import textwrap
import yaml

B = Path(sys.argv[1] if len(sys.argv) > 1 else '/data/hannah-modern')
R = B / 'rootfs'
O = B / 'original-root'
P = B / 'artwork-package'
THEME = 'org.hannahmontana.desktop'
WALL = '/usr/share/wallpapers/HannahMontana3/contents/images/1024x768.png'
assert (R / 'usr/bin/calamares').is_file()
assert (O / 'usr/share/wallpapers/hannah_montana_3.png').is_file()
if P.exists():
    shutil.rmtree(P)
P.mkdir()

def write(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(data).lstrip('\n'))
    path.chmod(mode)

def put(path, data, mode=0o644):
    write(P / path.lstrip('/'), data, mode)

def cp(src, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)

def tree(src, dest):
    shutil.copytree(src, dest, symlinks=True, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('.DS_Store', '*~'))

def ini(path):
    c = configparser.ConfigParser(interpolation=None, strict=False)
    c.optionxform = str
    c.read(path)
    return c

def saveini(path, c):
    s = io.StringIO()
    c.write(s, space_around_delimiters=False)
    write(path, s.getvalue())

def meta(identifier, name, structure=None):
    data = {'KPlugin': {'Id': identifier, 'Name': name,
            'Description': 'Original Hannah Montana Linux artwork adapted to Plasma 6',
            'Version': '26.04.1', 'Authors': [{'Name': 'Hannah Montana Linux Project (original artwork)'}]}}
    if structure:
        data['KPackageStructure'] = structure
    return json.dumps(data, ensure_ascii=False, indent=2) + '\n'

# Every original wallpaper remains available, with its original pixels.
for n in range(1, 6):
    src = next((O / 'usr/share/wallpapers').glob(f'hannah_montana_{n}.*'))
    im = Image.open(src)
    dest = P / f'usr/share/wallpapers/HannahMontana{n}'
    cp(src, dest / f'contents/images/{im.width}x{im.height}{src.suffix}')
    put(f'/usr/share/wallpapers/HannahMontana{n}/metadata.json',
        meta(f'HannahMontana{n}', f'Hannah Montana {n}'))
    thumb = im.copy()
    thumb.thumbnail((600, 400))
    thumb.save(dest / 'contents/screenshot.png')
    cp(src, P / 'usr/share/wallpapers' / src.name)

icons = P / 'usr/share/icons/hannah_montana'
tree(O / 'usr/share/icons/hannah_montana', icons)
c = ini(icons / 'index.theme')
c['Icon Theme']['Name'] = 'Hannah Montana'
c['Icon Theme']['Comment'] = 'Original Hannah Montana Linux icons, with modern application aliases'
c['Icon Theme']['Inherits'] = 'breeze,hicolor'
saveini(icons / 'index.theme', c)
aliases = {'org.kde.dolphin': 'system-file-manager', 'org.kde.konsole': 'konsole',
           'org.kde.kate': 'accessories-text-editor', 'org.kde.discover': 'system-software-install',
           'org.kde.okular': 'okular', 'systemsettings': 'preferences-system',
           'firefox_firefox': 'firefox', 'start-here-hannah': 'start-here',
           'distributor-logo-hannah': 'start-here', 'calamares': 'system-software-install'}
for size in ['16x16', '22x22', '32x32', '48x48', '64x64', '128x128']:
    for alias, source in aliases.items():
        found = list((icons / size).glob(f'*/{source}.png'))
        if found and found[0].is_file() and not (icons / size / 'apps' / f'{alias}.png').exists():
            cp(found[0], icons / size / 'apps' / f'{alias}.png')

# Old Plasma SVGs retain their shape, texture and colors. Missing modern
# elements use the supported Oxygen style shipped in the same base image.
style = P / 'usr/share/plasma/desktoptheme/hannah_montana'
tree(O / 'usr/share/kde4/apps/desktoptheme/hannah_montana', style)
(style / 'metadata.desktop').unlink(missing_ok=True)
put('/usr/share/plasma/desktoptheme/hannah_montana/metadata.json',
    json.dumps({**json.loads(meta('hannah_montana', 'Hannah Montana')),
                'X-Plasma-API': '5.0'}, indent=2) + '\n')
put('/usr/share/plasma/desktoptheme/hannah_montana/plasmarc', '''
    [Settings]
    FallbackTheme=oxygen
    [Wallpaper]
    defaultWallpaperTheme=HannahMontana3
    defaultFileSuffix=.png
    defaultWidth=1024
    defaultHeight=768
    [BlurBehindEffect]
    enabled=false
    [ContrastEffect]
    enabled=false
''')

# Complete the sparse original application palette with contemporary roles.
colors = ini(R / 'usr/share/color-schemes/Oxygen.colors')
old = ini(O / 'etc/skel/.kde/share/config/kdeglobals')
for section in old.sections():
    if section.startswith('Colors:') or section == 'WM':
        if not colors.has_section(section):
            colors.add_section(section)
        colors[section].update(old[section])
colors['General']['Name'] = 'Hannah Montana'
colors['General']['ColorScheme'] = 'HannahMontana'
colors['Colors:Window']['ForegroundNormal'] = '0,0,0'
colors['Colors:View']['ForegroundNormal'] = '0,0,0'
colors['Colors:Selection']['ForegroundNormal'] = '255,248,209'
colors['WM']['activeForeground'] = '255,248,209'
colors['WM']['inactiveBackground'] = '154,110,189'
saveini(P / 'usr/share/color-schemes/HannahMontana.colors', colors)

global_config = ini(R / 'usr/share/kubuntu-default-settings/kf5-settings/kdeglobals')
for section in colors.sections():
    if section.startswith('Colors:') or section == 'WM':
        if not global_config.has_section(section):
            global_config.add_section(section)
        global_config[section].update(colors[section])
global_config['General']['ColorScheme'] = 'HannahMontana'
global_config['KDE'].update({'LookAndFeelPackage': THEME, 'widgetStyle': 'oxygen',
                           'AutomaticLookAndFeel': 'false',
                           'DefaultLightLookAndFeel': THEME,
                           'DefaultDarkLookAndFeel': THEME})
global_config['Icons'] = {'Theme': 'hannah_montana'}
for dest in ['etc/xdg/kdeglobals', 'etc/skel/.config/kdeglobals',
             'var/lib/sddm/.config/kdeglobals']:
    saveini(P / dest, global_config)

for base in ['/etc/xdg', '/etc/skel/.config']:
    put(base + '/plasmarc', '[Theme]\nname=hannah_montana\n')
    put(base + '/ksplashrc', f'[KSplash]\nEngine=KSplashQML\nTheme={THEME}\n')
    put(base + '/kscreenlockerrc', f'''
        [Greeter]
        [Greeter][Wallpaper][org.kde.image][General]
        Image=file://{WALL}
        PreviewImage=file://{WALL}
        DynamicMode=0
        FillMode=1
        Color=108,38,207
    ''')
    put(base + '/kwinrc', '''
        [Desktops]
        Number=4
        Rows=1
        [org.kde.kdecoration2]
        library=org.kde.oxygen
        [Windows]
        RollOverDesktops=true
    ''')

look = P / f'usr/share/plasma/look-and-feel/{THEME}'
put(f'/usr/share/plasma/look-and-feel/{THEME}/metadata.json',
    meta(THEME, 'Hannah Montana OS', 'Plasma/LookAndFeel'))
put(f'/usr/share/plasma/look-and-feel/{THEME}/contents/defaults', f'''
    [kdeglobals][KDE]
    widgetStyle=oxygen
    [kdeglobals][General]
    ColorScheme=HannahMontana
    [kdeglobals][Icons]
    Theme=hannah_montana
    [plasmarc][Theme]
    name=hannah_montana
    [kcminputrc][Mouse]
    cursorTheme=breeze_cursors
    [kwinrc][org.kde.kdecoration2]
    library=org.kde.oxygen
    [Wallpaper]
    Image=HannahMontana3
    [KSplash]
    Theme={THEME}
''')
put(f'/usr/share/plasma/look-and-feel/{THEME}/contents/layouts/org.kde.plasma.desktop-layout.js', '''
    var plasma = getApiVersion(1);
    if (panels().length === 0) {
        var panel = new Panel;
        panel.location = 'bottom';
        panel.height = Math.max(38, Math.round(gridUnit * 2.5));
        panel.floating = false;
        var launcher = panel.addWidget('org.kde.plasma.kickoff');
        launcher.currentConfigGroup = ['General'];
        launcher.writeConfig('icon', 'start-here-hannah');
        launcher.currentConfigGroup = ['Shortcuts'];
        launcher.writeConfig('global', 'Alt+F1');
        var quick = panel.addWidget('org.kde.plasma.icon');
        quick.writeConfig('url', 'file:///usr/share/applications/org.kde.dolphin.desktop');
        var tasks = panel.addWidget('org.kde.plasma.taskmanager');
        tasks.currentConfigGroup = ['General'];
        tasks.writeConfig('showOnlyCurrentDesktop', true);
        panel.addWidget('org.kde.plasma.pager');
        panel.addWidget('org.kde.plasma.showdesktop');
        panel.addWidget('org.kde.plasma.systemtray');
        panel.addWidget('org.kde.plasma.digitalclock');
    }
    var ds = desktopsForActivity(currentActivity());
    for (var i = 0; i < ds.length; ++i) {
        ds[i].wallpaperPlugin = 'org.kde.image';
        ds[i].currentConfigGroup = ['Wallpaper', 'org.kde.image', 'General'];
        ds[i].writeConfig('Image', 'file:///usr/share/wallpapers/HannahMontana3/contents/images/1024x768.png');
        ds[i].writeConfig('FillMode', 1);
        ds[i].writeConfig('Color', '#6c26cf');
    }
''')
# Keep the supported Plasma 6 lock screen and task switchers.
for name in ['lockscreen', 'windowswitcher', 'desktopswitcher', 'logout', 'systemdialog']:
    src = R / 'usr/share/plasma/look-and-feel/org.kde.breeze.desktop/contents' / name
    if src.exists():
        tree(src, look / 'contents' / name)
cp(O / 'usr/share/kde4/apps/ksplash/Themes/hannah_montana/1600x1200/background.png',
   look / 'contents/splash/background.png')
put(f'/usr/share/plasma/look-and-feel/{THEME}/contents/splash/Splash.qml', '''
    import QtQuick
    Rectangle {
        id: root
        property int stage: 0
        color: '#6c26cf'
        Image { anchors.fill: parent; source: 'background.png'; fillMode: Image.PreserveAspectFit }
        Rectangle {
            width: Math.min(parent.width * 0.4, 360); height: 5
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom; anchors.bottomMargin: parent.height * 0.08
            color: '#6820d4'
            Rectangle {
                width: parent.width * Math.min(1, root.stage / 6); height: parent.height
                color: '#5fe835'
                Behavior on width { NumberAnimation { duration: 250 } }
            }
        }
    }
''')
cp(O / 'usr/share/kde4/apps/ksplash/Themes/hannah_montana/Preview.png',
   look / 'contents/previews/splash.png')
cp(O / 'usr/share/wallpapers/hannah_montana_3.png', look / 'contents/previews/fullscreenpreview.jpg')
# A real JPEG for tools that select the decoder by extension.
Image.open(O / 'usr/share/wallpapers/hannah_montana_3.png').convert('RGB').save(
    look / 'contents/previews/fullscreenpreview.jpg', quality=90)
cp(look / 'contents/previews/fullscreenpreview.jpg', look / 'contents/previews/preview.png')
Image.open(O / 'usr/share/wallpapers/hannah_montana_3.png').save(look / 'contents/previews/preview.png')

# Reuse supported SDDM components with the actual 2009 login background/logo.
sddm = P / 'usr/share/sddm/themes/hannah-montana'
tree(R / 'usr/share/sddm/themes/breeze', sddm)
kdm = O / 'usr/share/kde4/apps/kdm/themes/hannah_montana'
cp(kdm / 'background.svg', sddm / 'background.svg')
cp(kdm / 'branding-icon.png', sddm / 'logo.png')
put('/usr/share/sddm/themes/hannah-montana/theme.conf', '''
    [General]
    showlogo=shown
    showClock=true
    logo=/usr/share/sddm/themes/hannah-montana/logo.png
    type=image
    color=#6c26cf
    fontSize=10
    background=/usr/share/sddm/themes/hannah-montana/background.svg
    needsFullUserModel=false
''')
q = sddm / 'Main.qml'
q.write_text(q.read_text().replace('Kirigami.Theme.inherit: false', '''Kirigami.Theme.inherit: false
    Kirigami.Theme.backgroundColor: "#6c26cf"
    Kirigami.Theme.textColor: "#fff8d1"
    Kirigami.Theme.highlightColor: "#6820d4"
    Kirigami.Theme.highlightedTextColor: "#fff8d1"'''))
c = ini(sddm / 'metadata.desktop')
c['SddmGreeterTheme']['Name'] = 'Hannah Montana'
c['SddmGreeterTheme']['Description'] = 'Original Hannah Montana Linux artwork on the Plasma 6 greeter'
c['SddmGreeterTheme']['Theme-Id'] = 'hannah-montana'
saveini(sddm / 'metadata.desktop', c)
put('/etc/sddm.conf.d/90-hannah-montana.conf', '''
    [Theme]
    Current=hannah-montana
    CursorTheme=breeze_cursors
''')

# Native two-step Plymouth keeps password prompts and disk-encryption support.
# Only the generic spinner is reused; branding comes from the original ISO.
ply = P / 'usr/share/plymouth/themes/hannah-montana'
tree(R / 'usr/share/plymouth/themes/spinner', ply)
(ply / 'spinner.plymouth').unlink()
c = ini(R / 'usr/share/plymouth/themes/kubuntu-logo/kubuntu-logo.plymouth')
c['Plymouth Theme']['Name'] = 'Hannah Montana OS'
c['Plymouth Theme']['Description'] = 'Hannah Montana Linux original artwork'
c['two-step'].update({'ImageDir': '/usr/share/plymouth/themes/hannah-montana',
    'BackgroundStartColor': '0x6c26cf', 'BackgroundEndColor': '0x42116b',
    'ProgressBarForegroundColor': '0x5fe835', 'WatermarkVerticalAlignment': '.32',
    'DialogVerticalAlignment': '.65'})
for sec in ['boot-up', 'shutdown', 'reboot']:
    c[sec]['UseFirmwareBackground'] = 'false'
saveini(ply / 'hannah-montana.plymouth', c)
im = Image.open(kdm / 'branding-icon.png').convert('RGBA')
im.thumbnail((480, 200))
(ply / 'watermark.png').unlink(missing_ok=True)
im.save(ply / 'watermark.png')
put('/etc/plymouth/plymouthd.conf.d/90-hannah-montana.conf',
    '[Daemon]\nTheme=hannah-montana\n')
put('/etc/default/grub.d/90-hannah-montana.cfg', '''
    GRUB_DISTRIBUTOR="Hannah Montana OS"
    GRUB_BACKGROUND="/usr/share/wallpapers/hannah_montana_3.png"
    GRUB_COLOR_NORMAL="white/black"
    GRUB_COLOR_HIGHLIGHT="yellow/magenta"
''')

logo_src = next((icons / '128x128').glob('*/start-here.png'))
cp(logo_src, P / 'usr/share/pixmaps/hannah-montana.png')
put('/etc/xdg/kcm-about-distrorc', '''
    [General]
    LogoPath=/usr/share/pixmaps/hannah-montana.png
    Name=Hannah Montana OS
    UseOSReleaseVersion=false
    Version=26.04.1 (Kubuntu LTS base)
    Website=https://hannahmontana.sourceforge.net/
''')
put('/usr/share/hannah-montana/os-release', '''
    PRETTY_NAME="Hannah Montana OS 26.04.1 (Kubuntu LTS)"
    NAME="Hannah Montana OS"
    VERSION_ID="26.04"
    VERSION="26.04.1 LTS (Resolute Raccoon)"
    VERSION_CODENAME=resolute
    ID=ubuntu
    ID_LIKE=debian
    UBUNTU_CODENAME=resolute
    HOME_URL="https://hannahmontana.sourceforge.net/"
    SUPPORT_URL="https://help.ubuntu.com/"
    BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
    LOGO=hannah-montana
    VARIANT="Hannah Montana OS community remix"
    VARIANT_ID=hannah-montana
''')
put('/usr/share/doc/hannah-montana-artwork/README.es.txt', '''
    Hannah Montana OS 26.04.1 - adaptación comunitaria

    Base: Kubuntu 26.04.1 amd64. Arte: ISO original Hannah Montana Linux (2009).
    Tema global: Hannah Montana OS. Iconos: Hannah Montana. Estilo: Oxygen.
    Los cinco fondos originales están disponibles en Configurar escritorio.
    Los repositorios y el ID de Ubuntu se conservan para recibir actualizaciones.
    No se incluyen ejecutables, controladores ni repositorios obsoletos de 2009.

    Para instalar: arrancar el USB en UEFI y abrir «Instalar Hannah Montana OS».
    Para controladores propietarios: Preferencias del sistema > Controladores
    adicionales. Con Secure Boot puede ser necesario inscribir una clave MOK.
    La compatibilidad concreta debe comprobarse en el equipo de destino.

    Esta adaptación no es una publicación oficial de Kubuntu ni del proyecto
    original. Los recursos gráficos conservan sus autores y derechos originales.
''')
# Preserve original theme metadata and configuration as provenance, not active code.
for src, name in [(O / 'usr/share/kde4/apps/desktoptheme/hannah_montana/metadata.desktop', 'original-theme.desktop'),
                  (O / 'etc/skel/.kde/share/config/kdeglobals', 'original-kdeglobals'),
                  (O / 'usr/share/icons/hannah_montana/index.theme', 'original-icons.theme')]:
    cp(src, P / 'usr/share/doc/hannah-montana-artwork' / name)
tree(O / 'usr/share/sounds', P / 'usr/share/hannah-montana/original-sounds')
for base in ['/etc/xdg', '/etc/skel/.config']:
    put(base + '/plasma_workspace.notifyrc', '''
        [Event/startkde]
        Action=Sound
        Sound=/usr/share/hannah-montana/original-sounds/KDE-Sys-Log-In.ogg
        [Event/exitkde]
        Action=Sound
        Sound=/usr/share/hannah-montana/original-sounds/KDE-Sys-Log-Out.ogg
    ''')
put('/usr/share/applications/hannah-montana-guide.desktop', '''
    [Desktop Entry]
    Type=Application
    Name=Hannah Montana OS — Guide
    Name[es]=Hannah Montana OS — Guía
    Exec=xdg-open /usr/share/doc/hannah-montana-artwork/README.es.txt
    Icon=distributor-logo-hannah
    Categories=Documentation;
    Terminal=false
''')
put('/usr/share/plasma/plasma-welcome/extra-pages/00-HannahMontana.qml', '''
    import QtQuick
    import QtQuick.Layouts
    import org.kde.plasma.welcome
    Page {
        heading: qsTr("Welcome to Hannah Montana OS")
        description: qsTr("The original Hannah Montana Linux look, on the Kubuntu 26.04 LTS base. Your original wallpapers, purple icons and sounds are ready. Use System Settings to customize your desktop and Discover to install software and updates.")
        Image {
            anchors.fill: parent
            source: "/usr/share/wallpapers/hannah_montana_1.png"
            fillMode: Image.PreserveAspectFit
        }
    }
''')

put('/DEBIAN/control', '''
    Package: hannah-montana-artwork
    Version: 26.04.1-1
    Architecture: all
    Maintainer: Hannah Montana OS local remix <root@localhost>
    Section: x11
    Priority: optional
    Depends: plasma-desktop, kde-style-oxygen-qt6, kwin-decoration-oxygen, plasma-theme-oxygen, oxygen-sounds, sddm-theme-breeze, plymouth-theme-spinner
    Description: Original Hannah Montana Linux artwork adapted to Plasma 6
     Includes original wallpapers, icons and desktop artwork, a Plasma 6 global
     theme, an SDDM login screen and Plymouth branding for the Kubuntu LTS base.
''')
put('/DEBIAN/postinst', '''
    #!/bin/sh
    set -e
    if [ "$1" = configure ]; then
        if [ ! -e /usr/lib/os-release.kubuntu ]; then
            cp -p /usr/lib/os-release /usr/lib/os-release.kubuntu
        fi
        dpkg-divert --package hannah-montana-artwork --add --no-rename \
            --divert /usr/lib/os-release.kubuntu /usr/lib/os-release
        install -m 644 /usr/share/hannah-montana/os-release /usr/lib/os-release
        dpkg-divert --package hannah-montana-artwork --add --rename \
            --divert /usr/share/doc/hannah-montana-artwork/01-Kubuntu.qml.original \
            /usr/share/plasma/plasma-welcome/extra-pages/01-Kubuntu.qml
        update-alternatives --install /usr/share/plymouth/themes/default.plymouth \
            default.plymouth /usr/share/plymouth/themes/hannah-montana/hannah-montana.plymouth 250
        update-alternatives --set default.plymouth \
            /usr/share/plymouth/themes/hannah-montana/hannah-montana.plymouth
    fi
''', 0o755)
put('/DEBIAN/postrm', '''
    #!/bin/sh
    set -e
    if [ "$1" = remove ] || [ "$1" = purge ]; then
        dpkg-divert --package hannah-montana-artwork --remove --rename \
            --divert /usr/share/doc/hannah-montana-artwork/01-Kubuntu.qml.original \
            /usr/share/plasma/plasma-welcome/extra-pages/01-Kubuntu.qml
        update-alternatives --remove default.plymouth \
            /usr/share/plymouth/themes/hannah-montana/hannah-montana.plymouth || true
        if [ -e /usr/lib/os-release.kubuntu ]; then
            dpkg-divert --package hannah-montana-artwork --remove --no-rename \
                --divert /usr/lib/os-release.kubuntu /usr/lib/os-release
            mv /usr/lib/os-release.kubuntu /usr/lib/os-release
        fi
    fi
''', 0o755)
# Files already owned by Kubuntu must not conflict in dpkg. The about module
# override is an explicit local configuration change, applied below instead.
about = (P / 'etc/xdg/kcm-about-distrorc').read_text()
(P / 'etc/xdg/kcm-about-distrorc').unlink()
for path in P.rglob('*'):
    if not path.is_symlink():
        os.chown(path, 0, 0)
        if path.is_dir():
            path.chmod(0o755)
deb = B / 'artifacts/hannah-montana-artwork_26.04.1-1_all.deb'
subprocess.run(['dpkg-deb', '--root-owner-group', '--build', str(P), str(deb)], check=True)
cp(deb, R / 'tmp/hannah-montana-artwork.deb')
subprocess.run(['chroot', str(R), 'dpkg', '-i', '/tmp/hannah-montana-artwork.deb'], check=True)
(R / 'tmp/hannah-montana-artwork.deb').unlink()
write(R / 'etc/xdg/kcm-about-distrorc', about)

# The live prompt has Kubuntu artwork compiled into the binary. Start the
# complete Plasma desktop directly, retaining SDDM's expected live session name.
write(R / 'usr/libexec/start-kubuntu-live-env', '''
    #!/bin/sh
    export XDG_SESSION_CLASS=user
    export XDG_SESSION_DESKTOP=KDE
    export DESKTOP_SESSION=plasma
    export QT_QPA_PLATFORMTHEME=kde
    exec /usr/bin/startplasma-wayland
''', 0o755)
q = R / 'usr/share/wayland-sessions/kubuntu-live-environment.desktop'
q.write_text(q.read_text().replace('Kubuntu', 'Hannah Montana OS'))
desktop = R / 'usr/share/applications/kubuntu-calamares.desktop'
c = ini(desktop)
for key in list(c['Desktop Entry']):
    if key.startswith('Name') or key.startswith('GenericName'):
        c['Desktop Entry'][key] = 'Install Hannah Montana OS 26.04.1'
c['Desktop Entry']['Name[es]'] = 'Instalar Hannah Montana OS 26.04.1'
c['Desktop Entry']['Icon'] = 'distributor-logo-hannah'
saveini(desktop, c)
for p in (R / 'etc/skel/Desktop').glob('*'):
    if p.is_symlink() and ('kfocus' in p.name or 'kubuntu' in p.name):
        p.unlink()

# Keep the validated install sequence and Ubuntu EFI bootloader ID intact.
# The EFI path MUST stay ubuntu for the signed GRUB/shim packages.
settings = R / 'etc/calamares/settings.conf'
cfg = yaml.safe_load(settings.read_text())
cfg['branding'] = 'hannah-montana'
cfg['prompt-install'] = False
settings.write_text(yaml.safe_dump(cfg, sort_keys=False))
branding = R / 'etc/calamares/branding/hannah-montana'
branding.mkdir(exist_ok=True)
bcfg = yaml.safe_load((R / 'etc/calamares/branding/kubuntu/branding.desc').read_text())
bcfg['componentName'] = 'hannah-montana'
bcfg['strings'].update({'productName': 'Hannah Montana OS',
    'shortProductName': 'Hannah Montana OS', 'version': '26.04.1',
    'shortVersion': '26.04.1', 'versionedName': 'Hannah Montana OS 26.04.1',
    'shortVersionedName': 'Hannah Montana OS 26.04.1',
    'bootloaderEntryName': 'Hannah Montana OS',
    'productUrl': 'https://hannahmontana.sourceforge.net/',
    'supportUrl': 'https://help.ubuntu.com/'})
bcfg['style'] = {'SidebarBackground': '#6c26cf', 'SidebarText': '#fff8d1',
                 'SidebarTextCurrent': '#5fe835'}
(branding / 'branding.desc').write_text(yaml.safe_dump(bcfg, sort_keys=False))
for name in ['logo.png', 'icon.png']:
    cp(kdm / 'branding-icon.png', branding / name)
cp(O / 'usr/share/wallpapers/hannah_montana_1.png', branding / 'welcome.png')
slides = []
for n in range(1, 6):
    src = next((O / 'usr/share/wallpapers').glob(f'hannah_montana_{n}.*'))
    cp(src, branding / src.name)
    slides.append(f'''    Slide {{
        Image {{ anchors.fill: parent; source: "{src.name}"; fillMode: Image.PreserveAspectFit }}
    }}''')
write(branding / 'show.qml', '''
    import QtQuick 2.0
    import calamares.slideshow 1.0
    Presentation {
        id: presentation
        Timer { interval: 12000; running: presentation.activatedInCalamares; repeat: true
            onTriggered: presentation.goToNextSlide() }
''' + '\n'.join(slides) + '\n}\n')
welcome = R / 'etc/calamares/modules/welcome.conf'
cfg = yaml.safe_load(welcome.read_text().replace('\t', ' '))
cfg.pop('showDonateUrl', None)
cfg['requirements']['requiredStorage'] = 30
cfg['requirements']['requiredRam'] = 4
welcome.write_text(yaml.safe_dump(cfg, sort_keys=False))

# A graphical installer should use the Wayland session actually shipped in 26.04.
dm = R / 'etc/calamares/modules/displaymanager.conf'
cfg = yaml.safe_load(dm.read_text())
cfg['defaultDesktopEnvironment'] = {'executable': 'startplasma-wayland',
                                     'desktopFile': 'plasma'}
dm.write_text(yaml.safe_dump(cfg, sort_keys=False))
launcher = R / 'usr/bin/calamares-launch-normal'
text = launcher.read_text()
if 'export QT_QPA_PLATFORMTHEME=kde' not in text:
    launcher.write_text(text.replace("export BROWSER=", "export QT_QPA_PLATFORMTHEME=kde\nexport BROWSER="))

# Record exact file hashes of the original art copied to the new system.
provenance = {}
for src in (O / 'usr/share/wallpapers').glob('hannah_montana_*'):
    provenance[str(src.relative_to(O))] = hashlib.sha256(src.read_bytes()).hexdigest()
for src in (O / 'usr/share/icons/hannah_montana').rglob('*'):
    if src.is_file() and not src.is_symlink() and src.name not in ['index.theme', '.DS_Store'] and not src.name.endswith('~'):
        provenance[str(src.relative_to(O))] = hashlib.sha256(src.read_bytes()).hexdigest()
(B / 'artifacts/original-artwork-sha256.json').write_text(json.dumps(provenance, indent=2))
print(f'Customized {R}; artwork package: {deb}; {len(provenance)} source artwork hashes recorded')
