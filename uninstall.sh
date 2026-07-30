#!/usr/bin/env bash
set -euo pipefail
sudo systemctl disable --now jetson-vision.service 2>/dev/null || true
sudo rm -f /etc/systemd/system/jetson-vision.service
sudo systemctl daemon-reload
echo "Servicio eliminado. El proyecto y los datos se conservaron."
