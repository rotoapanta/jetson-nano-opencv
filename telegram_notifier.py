#!/usr/bin/env python3
from __future__ import print_function
import logging, time
from datetime import datetime
import requests

LOG = logging.getLogger("jetson-vision.telegram")

class TelegramNotifier(object):
    def __init__(self, enabled, bot_token, chat_id,
                 timeout_seconds=10, retry_count=3):
        self.enabled = bool(enabled)
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout_seconds = int(timeout_seconds)
        self.retry_count = int(retry_count)

    def validate(self):
        return bool(self.enabled and self.bot_token and self.chat_id)

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
            confidence=confidence * 100.0,
            date=now.strftime("%d/%m/%Y"),
            time=now.strftime("%H:%M:%S"),
            hostname=hostname
        )
        url = "https://api.telegram.org/bot{}/sendPhoto".format(self.bot_token)
        for attempt in range(1, self.retry_count + 1):
            try:
                with open(image_path, "rb") as image:
                    response = requests.post(
                        url,
                        data={"chat_id": self.chat_id, "caption": caption},
                        files={"photo": image},
                        timeout=self.timeout_seconds
                    )
                if response.ok:
                    LOG.info("Notificación Telegram enviada.")
                    return True
                LOG.warning("Telegram HTTP %s: %s",
                            response.status_code, response.text[:300])
            except Exception as exc:
                LOG.warning("Telegram intento %s/%s: %s",
                            attempt, self.retry_count, exc)
            time.sleep(min(5, attempt * 2))
        return False
