#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import logging
import os
import time
from datetime import datetime

import requests


LOG = logging.getLogger("jetson-vision.telegram.notifier")


class TelegramNotifier(object):
    """
    Envía mensajes y fotografías mediante la API HTTP de Telegram.

    Compatible con:
    - un CHAT_ID;
    - varios CHAT_ID;
    - respuestas directas a un chat específico;
    - Python 3.6.
    """

    def __init__(
        self,
        enabled,
        bot_token,
        notification_chat_ids=None,
        timeout_seconds=10,
        retry_count=3,
    ):
        self.enabled = bool(enabled)
        self.bot_token = str(bot_token or "").strip()
        self.notification_chat_ids = self._normalize_chat_ids(
            notification_chat_ids
        )
        self.timeout_seconds = int(timeout_seconds)
        self.retry_count = max(int(retry_count), 1)

    @staticmethod
    def _normalize_chat_ids(chat_ids):
        result = []

        if chat_ids is None:
            return result

        if isinstance(chat_ids, (int, float)):
            chat_ids = [chat_ids]

        elif isinstance(chat_ids, str):
            chat_ids = chat_ids.split(",")

        for value in chat_ids:
            try:
                chat_id = int(str(value).strip())

                if chat_id not in result:
                    result.append(chat_id)

            except (TypeError, ValueError):
                LOG.warning("CHAT_ID inválido ignorado: %r", value)

        return result

    def validate(self):
        return bool(self.enabled and self.bot_token)

    def _api_url(self, method):
        return "https://api.telegram.org/bot{}/{}".format(
            self.bot_token,
            method,
        )

    def _request(self, method, data=None, files=None):
        if not self.validate():
            return False, None

        url = self._api_url(method)

        for attempt in range(1, self.retry_count + 1):
            try:
                response = requests.post(
                    url,
                    data=data,
                    files=files,
                    timeout=self.timeout_seconds,
                )

                if response.ok:
                    try:
                        return True, response.json()
                    except ValueError:
                        return True, None

                LOG.warning(
                    "Telegram HTTP %s en %s: %s",
                    response.status_code,
                    method,
                    response.text[:300],
                )

            except Exception as exc:
                LOG.warning(
                    "Telegram %s intento %s/%s: %s",
                    method,
                    attempt,
                    self.retry_count,
                    exc,
                )

            if attempt < self.retry_count:
                time.sleep(min(5, attempt * 2))

        return False, None

    def send_message(self, chat_id, text):
        if not self.validate():
            return False

        try:
            chat_id = int(chat_id)
        except (TypeError, ValueError):
            LOG.warning("CHAT_ID inválido para send_message: %r", chat_id)
            return False

        ok, _ = self._request(
            "sendMessage",
            data={
                "chat_id": chat_id,
                "text": str(text),
                "disable_web_page_preview": "true",
            },
        )

        return ok

    def broadcast_message(self, text):
        success = False

        for chat_id in self.notification_chat_ids:
            if self.send_message(chat_id, text):
                success = True

        return success

    def send_photo_path(self, chat_id, image_path, caption=None):
        if not self.validate():
            return False

        if not image_path or not os.path.isfile(image_path):
            LOG.warning("Imagen no encontrada: %s", image_path)
            return False

        try:
            chat_id = int(chat_id)
        except (TypeError, ValueError):
            return False

        try:
            with open(image_path, "rb") as image:
                ok, _ = self._request(
                    "sendPhoto",
                    data={
                        "chat_id": chat_id,
                        "caption": caption or "",
                    },
                    files={"photo": image},
                )

            return ok

        except OSError as exc:
            LOG.warning("No se pudo abrir %s: %s", image_path, exc)
            return False

    def send_photo_bytes(
        self,
        chat_id,
        image_bytes,
        caption=None,
        filename="snapshot.jpg",
    ):
        if not self.validate() or not image_bytes:
            return False

        try:
            chat_id = int(chat_id)
        except (TypeError, ValueError):
            return False

        files = {
            "photo": (
                filename,
                image_bytes,
                "image/jpeg",
            )
        }

        ok, _ = self._request(
            "sendPhoto",
            data={
                "chat_id": chat_id,
                "caption": caption or "",
            },
            files=files,
        )

        return ok

    def broadcast_photo_path(self, image_path, caption=None):
        success = False

        for chat_id in self.notification_chat_ids:
            if self.send_photo_path(chat_id, image_path, caption):
                success = True

        return success

    def send_recognition(self, image_path, name, confidence, hostname):
        if not self.validate():
            return False

        now = datetime.now()

        caption = (
            "👤 Persona reconocida\n\n"
            "Nombre: {name}\n"
            "Confianza: {confidence:.1f} %\n"
            "Fecha: {date}\n"
            "Hora: {time}\n"
            "Equipo: {hostname}"
        ).format(
            name=name,
            confidence=float(confidence) * 100.0,
            date=now.strftime("%d/%m/%Y"),
            time=now.strftime("%H:%M:%S"),
            hostname=hostname,
        )

        result = self.broadcast_photo_path(
            image_path=image_path,
            caption=caption,
        )

        if result:
            LOG.info(
                "Notificación de reconocimiento enviada a %d chat(s).",
                len(self.notification_chat_ids),
            )

        return result

    def send_startup(self, hostname):
        now = datetime.now()

        message = (
            "✅ JETSON VISION INICIADO\n\n"
            "Equipo: {hostname}\n"
            "Fecha: {date}\n"
            "Hora: {time}\n"
            "Estado: operativo"
        ).format(
            hostname=hostname,
            date=now.strftime("%d/%m/%Y"),
            time=now.strftime("%H:%M:%S"),
        )

        return self.broadcast_message(message)

    def send_shutdown(self, hostname):
        now = datetime.now()

        message = (
            "⛔ JETSON VISION DETENIDO\n\n"
            "Equipo: {hostname}\n"
            "Fecha: {date}\n"
            "Hora: {time}"
        ).format(
            hostname=hostname,
            date=now.strftime("%d/%m/%Y"),
            time=now.strftime("%H:%M:%S"),
        )

        return self.broadcast_message(message)
