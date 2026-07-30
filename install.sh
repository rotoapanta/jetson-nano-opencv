#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/jetson-nano-opencv-env"
TOTAL_STEPS=10
STEP=0

green='\033[0;32m'; yellow='\033[1;33m'
blue='\033[0;34m'; red='\033[0;31m'; none='\033[0m'

next_step() { STEP=$((STEP + 1)); echo; echo -e "${blue}[$STEP/$TOTAL_STEPS] $1${none}"; }
info() { echo -e "${blue}ℹ $1${none}"; }
warning() { echo -e "${yellow}⚠ $1${none}"; }
success() { echo -e "${green}✔ $1${none}"; }
fail() { echo -e "${red}✘ $1${none}"; exit 1; }

cd "$PROJECT_DIR"

next_step "Validando plataforma"
uname -m
python3 --version
test -f /etc/nv_tegra_release || warning "No se detectó L4T."

next_step "Instalando dependencias"
sudo apt update
sudo apt install -y \
  python3 python3-pip python3-venv python3-dev \
  python3-numpy python3-opencv opencv-data \
  python3-gi python3-gst-1.0 \
  gir1.2-gstreamer-1.0 gir1.2-gst-plugins-base-1.0 \
  gstreamer1.0-tools gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good v4l-utils curl

next_step "Creando entorno virtual"
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv --system-site-packages "$VENV_DIR"
fi
"$VENV_DIR/bin/python3" -m pip install --upgrade "pip<22" "setuptools<60" wheel
"$VENV_DIR/bin/pip" install -r requirements.txt

next_step "Creando directorios"
mkdir -p data/faces data/events logs models

next_step "Creando configuración"
if [ ! -f .env ]; then cp .env.example .env; else warning ".env existente conservado"; fi

next_step "Localizando Haar Cascade"
HAAR_DEST="${PROJECT_DIR}/models/haarcascade_frontalface_default.xml"
if [ ! -f "$HAAR_DEST" ]; then
  HAAR_SOURCE="$(find /usr/share /usr/local/share -type f \
    -name haarcascade_frontalface_default.xml 2>/dev/null | head -n 1 || true)"
  [ -n "$HAAR_SOURCE" ] || fail "No se encontró haarcascade_frontalface_default.xml"
  cp "$HAAR_SOURCE" "$HAAR_DEST"
fi
success "Modelo Haar listo"

next_step "Verificando Python, OpenCV y GStreamer"
"$VENV_DIR/bin/python3" - <<'PY'
import cv2, gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst
Gst.init(None)
print("OpenCV:", cv2.__version__)
print("GStreamer Python: OK")
cascade = cv2.CascadeClassifier("models/haarcascade_frontalface_default.xml")
assert not cascade.empty()
print("Haar: OK")
PY

next_step "Verificando nvarguscamerasrc"
gst-inspect-1.0 nvarguscamerasrc >/dev/null
success "nvarguscamerasrc disponible"

next_step "Instalando servicio systemd"
SERVICE_TMP="/tmp/jetson-vision.service"
sed -e "s|__USER__|${USER}|g" \
    -e "s|__PROJECT_DIR__|${PROJECT_DIR}|g" \
    systemd/jetson-vision.service > "$SERVICE_TMP"
sudo cp "$SERVICE_TMP" /etc/systemd/system/jetson-vision.service
sudo systemctl daemon-reload
sudo systemctl enable jetson-vision.service

next_step "Finalizando"
chmod +x install.sh uninstall.sh main.py collect_faces.py scripts/*.sh scripts/*.py
success "Instalación completada"
echo
echo "Migrar rostros anteriores:"
echo "  cp -a ../jetson-nano-opencv/data/faces/. data/faces/"
echo
echo "Probar cámara:"
echo "  source jetson-nano-opencv-env/bin/activate"
echo "  python3 scripts/test_camera.py"
echo
echo "Ejecutar:"
echo "  python3 main.py"
