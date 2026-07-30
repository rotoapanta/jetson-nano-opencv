#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import logging
import os
import re
import subprocess
from datetime import datetime


LOG = logging.getLogger("jetson-vision.telegram.commands")


EVENT_EXTENSIONS = (".jpg", ".jpeg", ".png")


class TelegramCommandHandler(object):
    """Implementa los comandos disponibles en Telegram."""

    def __init__(
        self,
        notifier,
        access,
        monitor,
        action_manager,
        frame_store,
        faces_dir,
        events_dir,
        service_name="jetson-vision.service",
        reboot_enabled=False,
    ):
        self.notifier = notifier
        self.access = access
        self.monitor = monitor
        self.action_manager = action_manager
        self.frame_store = frame_store
        self.faces_dir = faces_dir
        self.events_dir = events_dir
        self.service_name = service_name
        self.reboot_enabled = bool(reboot_enabled)

    def execute(self, chat_id, command):
        command = self.access.normalize_command(command)

        handlers = {
            "/start": self.cmd_help,
            "/ayuda": self.cmd_help,
            "/estado": self.cmd_status,
            "/foto": self.cmd_photo,
            "/eventos": self.cmd_events,
            "/ultimo_evento": self.cmd_last_event,
            "/personas": self.cmd_people,
            "/uptime": self.cmd_uptime,
            "/reiniciar_servicio": self.cmd_restart_service,
            "/reboot": self.cmd_reboot,
            "/confirmar_reboot": self.cmd_confirm_reboot,
            "/cancelar": self.cmd_cancel,
        }

        handler = handlers.get(command)

        if handler is None:
            self.notifier.send_message(
                chat_id,
                "Comando desconocido. Use /ayuda.",
            )
            return False

        try:
            return handler(chat_id)

        except Exception:
            LOG.exception(
                "Error ejecutando %s para CHAT_ID %s",
                command,
                chat_id,
            )

            self.notifier.send_message(
                chat_id,
                "❌ Se produjo un error procesando el comando.",
            )

            return False

    def cmd_help(self, chat_id):
        return self.notifier.send_message(
            chat_id,
            self.access.build_help_message(chat_id),
        )

    def cmd_status(self, chat_id):
        camera_available = bool(
            self.frame_store is not None
            and self.frame_store.snapshot()
        )

        message = self.monitor.build_status_message(
            camera_status=camera_available
        )

        return self.notifier.send_message(chat_id, message)

    def cmd_photo(self, chat_id):
        if self.frame_store is None:
            return self.notifier.send_message(
                chat_id,
                "📷 La cámara no está disponible.",
            )

        image = self.frame_store.snapshot()

        if not image:
            return self.notifier.send_message(
                chat_id,
                "📷 Todavía no existe una imagen disponible.",
            )

        caption = "📷 Captura actual\n{}".format(
            datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        )

        return self.notifier.send_photo_bytes(
            chat_id,
            image,
            caption=caption,
            filename="jetson_snapshot.jpg",
        )

    def _get_event_files(self):
        events = []

        if not os.path.isdir(self.events_dir):
            return events

        for root, directories, files in os.walk(self.events_dir):
            del directories

            for filename in files:
                if not filename.lower().endswith(EVENT_EXTENSIONS):
                    continue

                path = os.path.join(root, filename)

                try:
                    modified = os.path.getmtime(path)
                except OSError:
                    continue

                events.append((modified, path, filename))

        events.sort(key=lambda item: item[0], reverse=True)

        return events

    @staticmethod
    def _event_description(filename, modified):
        name = os.path.splitext(filename)[0]

        match = re.match(
            r"^(.*?)_(\d{8})_(\d{6})_(\d{3})$",
            name,
        )

        if match:
            person = match.group(1).replace("_", " ")
            date_text = match.group(2)
            time_text = match.group(3)
            confidence = int(match.group(4))

            try:
                event_time = datetime.strptime(
                    date_text + time_text,
                    "%Y%m%d%H%M%S",
                )

                return "{} — {} — {} %".format(
                    person,
                    event_time.strftime("%d/%m/%Y %H:%M:%S"),
                    confidence,
                )

            except ValueError:
                pass

        return "{} — {}".format(
            filename,
            datetime.fromtimestamp(modified).strftime(
                "%d/%m/%Y %H:%M:%S"
            ),
        )

    def cmd_events(self, chat_id):
        events = self._get_event_files()[:10]

        if not events:
            return self.notifier.send_message(
                chat_id,
                "📁 No existen eventos almacenados.",
            )

        lines = ["📁 ÚLTIMOS EVENTOS", ""]

        for index, item in enumerate(events, 1):
            modified, path, filename = item
            del path

            lines.append(
                "{}. {}".format(
                    index,
                    self._event_description(filename, modified),
                )
            )

        return self.notifier.send_message(
            chat_id,
            "\n".join(lines),
        )

    def cmd_last_event(self, chat_id):
        events = self._get_event_files()

        if not events:
            return self.notifier.send_message(
                chat_id,
                "📁 No existen eventos almacenados.",
            )

        modified, path, filename = events[0]

        caption = (
            "📸 ÚLTIMO EVENTO\n\n{}"
        ).format(
            self._event_description(filename, modified)
        )

        return self.notifier.send_photo_path(
            chat_id,
            path,
            caption=caption,
        )

    def cmd_people(self, chat_id):
        people = []

        if os.path.isdir(self.faces_dir):
            for name in sorted(os.listdir(self.faces_dir)):
                directory = os.path.join(self.faces_dir, name)

                if not os.path.isdir(directory):
                    continue

                samples = 0

                try:
                    for filename in os.listdir(directory):
                        if filename.lower().endswith(EVENT_EXTENSIONS):
                            samples += 1
                except OSError:
                    samples = 0

                people.append((name, samples))

        if not people:
            return self.notifier.send_message(
                chat_id,
                "👥 No existen personas registradas.",
            )

        lines = ["👥 PERSONAS REGISTRADAS", ""]

        for index, item in enumerate(people, 1):
            name, samples = item

            lines.append(
                "{}. {} — {} muestra{}".format(
                    index,
                    name,
                    samples,
                    "" if samples == 1 else "s",
                )
            )

        return self.notifier.send_message(
            chat_id,
            "\n".join(lines),
        )

    def cmd_uptime(self, chat_id):
        return self.notifier.send_message(
            chat_id,
            self.monitor.build_uptime_message(),
        )

    def cmd_restart_service(self, chat_id):
        self.notifier.send_message(
            chat_id,
            "🔄 Reiniciando Jetson Vision...",
        )

        try:
            subprocess.Popen([
                "sudo",
                "-n",
                "systemctl",
                "restart",
                self.service_name,
            ])

            return True

        except OSError as exc:
            LOG.error("No se pudo reiniciar el servicio: %s", exc)

            return self.notifier.send_message(
                chat_id,
                "❌ No se pudo solicitar el reinicio del servicio.",
            )

    def cmd_reboot(self, chat_id):
        if not self.reboot_enabled:
            return self.notifier.send_message(
                chat_id,
                "⛔ El reinicio remoto está deshabilitado.",
            )

        return self.notifier.send_message(
            chat_id,
            self.action_manager.request_reboot(chat_id),
        )

    def cmd_confirm_reboot(self, chat_id):
        if not self.reboot_enabled:
            return self.notifier.send_message(
                chat_id,
                "⛔ El reinicio remoto está deshabilitado.",
            )

        confirmed, action, message = (
            self.action_manager.confirm_reboot(chat_id)
        )

        self.notifier.send_message(chat_id, message)

        if not confirmed or action != "reboot":
            return False

        try:
            subprocess.Popen([
                "sudo",
                "-n",
                "systemctl",
                "reboot",
            ])

            return True

        except OSError as exc:
            LOG.error("No se pudo reiniciar la Jetson: %s", exc)

            return self.notifier.send_message(
                chat_id,
                "❌ No se pudo ejecutar el reinicio.",
            )

    def cmd_cancel(self, chat_id):
        success, message = self.action_manager.cancel(chat_id)

        self.notifier.send_message(chat_id, message)

        return success
