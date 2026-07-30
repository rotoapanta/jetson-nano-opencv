#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Monitoreo básico de la Jetson Nano.

No depende directamente de Telegram.
Compatible con Python 3.6.
"""

import os
import shutil
import socket
import subprocess
import time

from telegram_management.helpers import (
    format_bytes,
    format_seconds,
    percentage,
)


class SystemMonitor(object):
    """Obtiene información del sistema operativo y la aplicación."""

    def __init__(
        self,
        service_name="jetson-vision.service",
        faces_directory="data/faces",
        events_directory="data/events",
    ):
        self.service_name = service_name
        self.faces_directory = faces_directory
        self.events_directory = events_directory
        self.application_start_time = time.time()

    @staticmethod
    def _run_command(command):
        try:
            output = subprocess.check_output(
                command,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )

            return output.strip()

        except (subprocess.CalledProcessError, OSError):
            return None

    @staticmethod
    def get_temperature():
        """Obtiene la temperatura térmica principal disponible."""
        thermal_base = "/sys/class/thermal"

        try:
            zones = sorted(
                name for name in os.listdir(thermal_base)
                if name.startswith("thermal_zone")
            )
        except OSError:
            return None

        preferred = []
        remaining = []

        for zone in zones:
            zone_path = os.path.join(thermal_base, zone)

            try:
                with open(os.path.join(zone_path, "type"), "r") as file_obj:
                    zone_type = file_obj.read().strip().lower()
            except OSError:
                zone_type = ""

            item = (zone_path, zone_type)

            if any(
                word in zone_type
                for word in ("cpu", "gpu", "soc", "thermal")
            ):
                preferred.append(item)
            else:
                remaining.append(item)

        for zone_path, zone_type in preferred + remaining:
            try:
                with open(os.path.join(zone_path, "temp"), "r") as file_obj:
                    raw_value = float(file_obj.read().strip())

                if raw_value > 1000:
                    raw_value /= 1000.0

                if -20.0 <= raw_value <= 150.0:
                    return {
                        "value": raw_value,
                        "zone": zone_type or os.path.basename(zone_path),
                    }

            except (OSError, TypeError, ValueError):
                continue

        return None

    @staticmethod
    def get_memory():
        """Obtiene información de memoria desde /proc/meminfo."""
        values = {}

        try:
            with open("/proc/meminfo", "r") as file_obj:
                for line in file_obj:
                    key, value = line.split(":", 1)
                    number = value.strip().split()[0]
                    values[key] = int(number) * 1024
        except (OSError, ValueError, IndexError):
            return None

        total = values.get("MemTotal", 0)
        available = values.get("MemAvailable", values.get("MemFree", 0))
        used = max(total - available, 0)

        return {
            "total": total,
            "used": used,
            "available": available,
            "percent": percentage(used, total),
        }

    @staticmethod
    def get_disk(path="/"):
        """Obtiene información de almacenamiento."""
        try:
            usage = shutil.disk_usage(path)
        except OSError:
            return None

        return {
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": percentage(usage.used, usage.total),
        }

    @staticmethod
    def get_system_uptime():
        """Obtiene el tiempo desde el arranque del sistema."""
        try:
            with open("/proc/uptime", "r") as file_obj:
                return float(file_obj.read().split()[0])
        except (OSError, ValueError, IndexError):
            return None

    def get_application_uptime(self):
        """Obtiene el tiempo activo de esta instancia."""
        return max(time.time() - self.application_start_time, 0)

    @staticmethod
    def get_load_average():
        """Obtiene la carga promedio del sistema."""
        try:
            load_1, load_5, load_15 = os.getloadavg()

            return {
                "1min": load_1,
                "5min": load_5,
                "15min": load_15,
            }
        except (AttributeError, OSError):
            return None

    @staticmethod
    def get_ip_address():
        """Obtiene la dirección IP principal."""
        connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            connection.connect(("8.8.8.8", 80))
            return connection.getsockname()[0]
        except OSError:
            try:
                return socket.gethostbyname(socket.gethostname())
            except OSError:
                return "N/D"
        finally:
            connection.close()

    def get_service_status(self):
        """Comprueba el estado del servicio systemd."""
        result = self._run_command([
            "systemctl",
            "is-active",
            self.service_name,
        ])

        if result == "active":
            return "Activo"

        if result:
            return result.capitalize()

        return "No disponible"

    def count_registered_people(self):
        """Cuenta carpetas de personas registradas."""
        try:
            return sum(
                1
                for name in os.listdir(self.faces_directory)
                if os.path.isdir(os.path.join(self.faces_directory, name))
            )
        except OSError:
            return 0

    def count_events(self):
        """Cuenta archivos almacenados en el directorio de eventos."""
        count = 0

        if not os.path.isdir(self.events_directory):
            return count

        for root, directories, files in os.walk(self.events_directory):
            del directories

            for filename in files:
                if filename.lower().endswith(
                    (".jpg", ".jpeg", ".png")
                ):
                    count += 1

        return count

    def build_status_message(self, camera_status=None):
        """Construye el mensaje general del sistema."""
        temperature = self.get_temperature()
        memory = self.get_memory()
        disk = self.get_disk("/")
        system_uptime = self.get_system_uptime()
        application_uptime = self.get_application_uptime()
        load = self.get_load_average()

        lines = [
            "🖥 ESTADO DE JETSON VISION",
            "",
            "Servicio: {}".format(self.get_service_status()),
            "Dirección IP: {}".format(self.get_ip_address()),
        ]

        if camera_status is not None:
            lines.append(
                "Cámara: {}".format(
                    "Disponible" if camera_status else "No disponible"
                )
            )

        if temperature:
            lines.append(
                "Temperatura: {:.1f} °C ({})".format(
                    temperature["value"],
                    temperature["zone"],
                )
            )
        else:
            lines.append("Temperatura: N/D")

        if memory:
            lines.append(
                "RAM: {} / {} ({:.1f} %)".format(
                    format_bytes(memory["used"]),
                    format_bytes(memory["total"]),
                    memory["percent"],
                )
            )
        else:
            lines.append("RAM: N/D")

        if disk:
            lines.append(
                "Disco: {} / {} ({:.1f} %)".format(
                    format_bytes(disk["used"]),
                    format_bytes(disk["total"]),
                    disk["percent"],
                )
            )
        else:
            lines.append("Disco: N/D")

        if load:
            lines.append(
                "Carga: {:.2f}, {:.2f}, {:.2f}".format(
                    load["1min"],
                    load["5min"],
                    load["15min"],
                )
            )

        if system_uptime is not None:
            lines.append(
                "Uptime Jetson: {}".format(
                    format_seconds(system_uptime)
                )
            )

        lines.append(
            "Uptime aplicación: {}".format(
                format_seconds(application_uptime)
            )
        )

        lines.extend([
            "Personas registradas: {}".format(
                self.count_registered_people()
            ),
            "Eventos almacenados: {}".format(
                self.count_events()
            ),
        ])

        return "\n".join(lines)

    def build_uptime_message(self):
        """Construye únicamente el mensaje de uptime."""
        system_uptime = self.get_system_uptime()
        application_uptime = self.get_application_uptime()

        return (
            "⏱ TIEMPO DE FUNCIONAMIENTO\n\n"
            "Jetson Nano: {}\n"
            "Jetson Vision: {}".format(
                format_seconds(system_uptime)
                if system_uptime is not None
                else "N/D",
                format_seconds(application_uptime),
            )
        )
