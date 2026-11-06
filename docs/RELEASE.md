Edición HD corregida sobre Kubuntu 26.04.1, con iconos reparados, indicadores Breeze, ajustes de sesión Wayland y configuración táctil. El nombre público de la ISO cambió; su contenido es el mismo que el de la imagen corregida validada.

### Descargar y reconstruir la ISO

1. Descarga las tres partes `.part001`, `.part002`, `.part003`, `SHA256SUMS`, `SHA256SUMS.parts` y `unir_iso.py` en la misma carpeta.
2. Ejecuta `python unir_iso.py` (en Windows también puedes usar `py unir_iso.py`). Requiere Python 3 y aproximadamente 11,2 GB libres para partes e ISO.
3. El script comprueba las partes y el SHA-256 final. Graba la ISO reconstruida como imagen de disco completa en la USB. No grabes las partes por separado.

Archivo final: `hannah-montana-os-26.04.1-2026-amd64.iso` · 5.554.634.752 bytes.

SHA-256:

```text
0e8320f72fbbd5a646f155ad03944cd74ac4404cf83d6e5a4686eb59a8641668
```

### Instalación y validación

El instalador requiere 30 GiB de almacenamiento y 4 GiB de RAM. Se probó el Live con BIOS y UEFI, aplicaciones y entrada táctil virtual en QEMU/KVM. El usuario confirmó el funcionamiento y que AHCI resolvió la detección del SSD.

Es posible convivir con Windows; prepara Windows antes de cambiar RAID/RST a AHCI y conserva sus particiones. La instalación completa, el dual boot, Secure Boot en firmware físico y una pantalla táctil física siguen pendientes de validación. Qt Quick se configura por software para compatibilidad y puede afectar el rendimiento.

Consulta el README y los informes del repositorio para más detalles. Proyecto comunitario no oficial; los recursos de terceros conservan sus respectivos derechos.
