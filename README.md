# Jetson Nano OpenCV Vision v2

Proyecto completo para Jetson Nano + IMX219, compatible con:

- JetPack 4.6.6 / L4T R32.7.6
- Ubuntu 18.04
- Python 3.6
- OpenCV 3.2 sin GStreamer integrado
- GStreamer vía PyGObject

## Mejoras principales

- Conversión BGRx a BGR respetando el `stride` real.
- Reconexión automática de cámara.
- Reconocimiento confirmado durante varios frames.
- Cooldown por persona para evitar eventos duplicados.
- Streaming MJPEG estable con FPS y calidad configurables.
- `/health`, `/snapshot.jpg` y `/stream.mjpg`.
- Telegram con foto, nombre, confianza, fecha y hora.
- Logs rotativos.
- Servicio `systemd`.
- Configuración centralizada en `.env`.

## Instalación

```bash
cd ~/Documentos/Projects
unzip jetson-nano-opencv.zip
cd jetson-nano-opencv
chmod +x install.sh
./install.sh
```

## Migrar los 30 rostros de Roberto

```bash
cp -a \
  ~/Documentos/Projects/jetson-nano-opencv/data/faces/. \
  ~/Documentos/Projects/jetson-nano-opencv/data/faces/
```

## Prueba obligatoria de cámara

```bash
source jetson-nano-opencv-env/bin/activate
python3 scripts/test_camera.py
```

Debe verse limpia, sin ruido, bandas ni colores corruptos.

## Ejecutar manualmente

```bash
python3 main.py
```

Abrir:

```text
http://192.168.100.41:8080/
```

Estado:

```text
http://192.168.100.41:8080/health
```

Captura JPEG:

```text
http://192.168.100.41:8080/snapshot.jpg
```

## Registrar otra persona

```bash
python3 collect_faces.py --name Nombre --samples 30
```

## Telegram

Editar `.env`:

```env
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=TOKEN
TELEGRAM_CHAT_ID=CHAT_ID
```

## Servicio automático

```bash
sudo systemctl start jetson-vision
sudo systemctl status jetson-vision
journalctl -u jetson-vision -f
```

## Validación antes de reemplazar la versión funcional

1. Cámara sin corrupción durante 10 minutos.
2. Streaming visible desde la laptop.
3. Reconocimiento correcto de Roberto.
4. Persona no registrada mostrada como `Desconocido`.
5. Sin duplicar eventos durante el cooldown.
6. Telegram con fotografía.
7. Recuperación tras reiniciar el servicio.
8. Recuperación tras reiniciar `nvargus-daemon`.

Conserve la versión anterior hasta completar estas pruebas.
