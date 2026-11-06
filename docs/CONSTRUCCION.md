# Construcción y procedencia

Los directorios de `build/` conservan los scripts originales de cada etapa; no constituyen un constructor autónomo reproducible desde un clon limpio. No se ha reconstruido la ISO durante su publicación en GitHub: únicamente se renombró la imagen corregida, conservando su SHA-256.

## Estructura esperada

Los scripts históricos utilizan rutas bajo `/data` dentro de Docker. El directorio de trabajo del proyecto se monta en `/data` y contiene las ISOs de origen y los directorios `hannah-modern`, `hannah-hd`, `hannah-upscale` y `hannah-repair`. Copia los scripts de cada etapa a esos directorios si preparas un entorno separado.

Se necesitan la ISO de Kubuntu 26.04.1 amd64 y la edición original de Hannah Montana Linux. Los scripts de modernización usan el nombre `hannah_montana_linux_x86_basic_edition.iso`; el archivo local original también se ha conservado con el nombre `hannaa-montana-old.iso`. Verifica las sumas indicadas en `build/hannah-modern/scripts/build.sh` antes de usar las entradas.

Dependencias generales: Docker, Python 3, Pillow, squashfs-tools, xorriso, cpio y zstd. Los Dockerfiles históricos documentan los paquetes adicionales. Para las pruebas de arranque se utilizaron QEMU/KVM y OVMF.

## Etapas

1. `hannah-modern/scripts/`: extracción, personalización inicial, initrd, empaquetado y comprobación de la edición desktop.
2. `hannah-upscale/`: herramientas y scripts del reescalado. Los modelos y recursos generados no se incluyen. La reparación final de los iconos utiliza RGBA original con Lanczos en lugar de mezclar RGB generado y alfa antiguo.
3. `hannah-hd/scripts/`: incorporación de fondos y recursos HD. Requiere el resultado de las etapas anteriores.
4. `hannah-repair/scripts/`: reparación final sobre una copia de la raíz y del árbol ISO HD, conservando permisos y enlaces. Orden: `repair.py`, `touch.py`, `panel.py`, preparación del initrd, `package_iso.py` y `validate.py`.

La reparación requiere `hannah-modern/original-root`, el manifiesto `hannah-upscale/artifacts/enhancement-manifest.json`, `hannah-repair/rootfs`, `hannah-repair/iso` y `hannah-repair/artifacts/initrd-report.json`, además de las dependencias de las etapas previas. Estos datos de trabajo no están incluidos. No ejecutes los scripts sobre el sistema anfitrión ni sobre una raíz instalada: modifican árboles extraídos y algunos limpian directorios temporales de esos árboles.

Los scripts históricos generan y verifican el nombre `hannah-montana-os-26.04.1-hd-fixed-amd64.iso`. El nombre público se cambió después a `hannah-montana-os-26.04.1-2026-amd64.iso` sin cambiar su contenido. Los informes históricos conservan el nombre utilizado durante la validación.

## Publicación

`tools/preparar_release.py ISO DIRECTORIO` verifica la suma de la imagen, la divide en partes de 1.900.000.000 bytes y genera las sumas. `tools/publicar_release.sh DIRECTORIO` crea una release en borrador, sube los archivos y la publica al terminar. Requiere GitHub CLI autenticado con permiso de escritura. Los scripts no agregan las imágenes al historial Git.
