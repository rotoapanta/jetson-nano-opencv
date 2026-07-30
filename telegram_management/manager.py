#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import logging
import threading
import time

import requests

from telegram_management.helpers import safe_username


LOG = logging.getLogger("jetson-vision.telegram.manager")


class TelegramManager(object):
    """Recibe y procesa comandos del bot en un hilo independiente."""

    def __init__(
        self,
        enabled,
        commands_enabled,
        bot_token,
        poll_timeout,
        notifier,
        access,
        command_handler,
    ):
        self.enabled = bool(enabled)
        self.commands_enabled = bool(commands_enabled)
        self.bot_token = str(bot_token or "").strip()
        self.poll_timeout = max(int(poll_timeout), 1)
        self.notifier = notifier
        self.access = access
        self.command_handler = command_handler

        self._offset = 0
        self._stop_event = threading.Event()
        self._thread = None

    def validate(self):
        return bool(
            self.enabled
            and self.commands_enabled
            and self.bot_token
        )

    def start(self):
        if not self.validate():
            LOG.info("Comandos Telegram deshabilitados.")
            return False

        if self._thread is not None and self._thread.is_alive():
            return True

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._polling_loop,
            name="telegram-command-bot",
        )

        self._thread.daemon = True
        self._thread.start()

        LOG.info("Bot de comandos Telegram iniciado.")

        return True

    def stop(self):
        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(
                timeout=self.poll_timeout + 2
            )

        LOG.info("Bot de comandos Telegram detenido.")

    def _get_updates(self):
        url = (
            "https://api.telegram.org/bot{}/getUpdates"
        ).format(self.bot_token)

        response = requests.get(
            url,
            params={
                "offset": self._offset,
                "timeout": self.poll_timeout,
                "allowed_updates": '["message"]',
            },
            timeout=self.poll_timeout + 5,
        )

        response.raise_for_status()

        payload = response.json()

        if not payload.get("ok"):
            raise RuntimeError(
                "Telegram respondió ok=false"
            )

        return payload.get("result", [])

    def _polling_loop(self):
        while not self._stop_event.is_set():
            try:
                updates = self._get_updates()

                for update in updates:
                    update_id = update.get("update_id")

                    if update_id is not None:
                        self._offset = max(
                            self._offset,
                            int(update_id) + 1,
                        )

                    self._process_update(update)

            except requests.exceptions.ReadTimeout:
                continue

            except requests.exceptions.RequestException as exc:
                LOG.warning(
                    "Error de comunicación getUpdates: %s",
                    exc,
                )

                self._stop_event.wait(5)

            except Exception:
                LOG.exception(
                    "Error inesperado procesando Telegram."
                )

                self._stop_event.wait(3)

    def _process_update(self, update):
        message = update.get("message")

        if not isinstance(message, dict):
            return

        text = message.get("text")

        if not text or not str(text).strip().startswith("/"):
            return

        chat = message.get("chat") or {}
        user = message.get("from") or {}

        chat_id = chat.get("id")

        if chat_id is None:
            return

        command = self.access.normalize_command(text)

        if not self.access.is_authorized(chat_id):
            LOG.warning(
                "Acceso Telegram no autorizado: chat_id=%s, usuario=%s, comando=%s",
                chat_id,
                safe_username(user),
                command,
            )

            return

        if not self.access.can_execute(chat_id, command):
            LOG.warning(
                "Permiso Telegram denegado: chat_id=%s, rol=%s, comando=%s",
                chat_id,
                self.access.describe_role(chat_id),
                command,
            )

            self.notifier.send_message(
                chat_id,
                "⛔ No tiene permisos para ejecutar este comando.",
            )

            return

        LOG.info(
            "Comando Telegram: chat_id=%s, rol=%s, comando=%s",
            chat_id,
            self.access.describe_role(chat_id),
            command,
        )

        self.command_handler.execute(
            chat_id,
            command,
        )
