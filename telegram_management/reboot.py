#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestión segura de acciones administrativas.

Compatible con Python 3.6.
"""

import logging
import threading
import time


LOGGER = logging.getLogger("jetson-vision.telegram.reboot")


ACTION_REBOOT = "reboot"
ACTION_RESTART_SERVICE = "restart_service"


class AdministrativeActionManager(object):
    """Gestiona solicitudes administrativas pendientes."""

    def __init__(self, confirmation_timeout=30):
        self.confirmation_timeout = max(
            int(confirmation_timeout),
            5,
        )

        self._pending = {}
        self._lock = threading.Lock()

    def request_reboot(self, chat_id):
        """Registra una solicitud de reinicio."""
        chat_id = int(chat_id)

        with self._lock:
            self._pending[chat_id] = {
                "action": ACTION_REBOOT,
                "created_at": time.time(),
            }

        LOGGER.warning(
            "Reinicio solicitado por CHAT_ID %s",
            chat_id,
        )

        return (
            "⚠️ REINICIO SOLICITADO\n\n"
            "La Jetson Nano se reiniciará completamente.\n\n"
            "Para confirmar escriba:\n"
            "/confirmar_reboot\n\n"
            "Para cancelar:\n"
            "/cancelar\n\n"
            "La solicitud caduca en {} segundos."
        ).format(self.confirmation_timeout)

    def confirm_reboot(self, chat_id):
        """
        Confirma una solicitud.

        Retorna:
            (True, ACTION_REBOOT, mensaje)
            (False, None, mensaje)
        """
        chat_id = int(chat_id)

        with self._lock:
            request = self._pending.get(chat_id)

            if request is None:
                return (
                    False,
                    None,
                    "No existe una solicitud de reinicio pendiente.",
                )

            elapsed = time.time() - request["created_at"]

            if elapsed > self.confirmation_timeout:
                del self._pending[chat_id]

                return (
                    False,
                    None,
                    "La solicitud de reinicio ha caducado.",
                )

            if request["action"] != ACTION_REBOOT:
                del self._pending[chat_id]

                return (
                    False,
                    None,
                    "La solicitud pendiente no corresponde a un reinicio.",
                )

            del self._pending[chat_id]

        LOGGER.warning(
            "Reinicio confirmado por CHAT_ID %s",
            chat_id,
        )

        return (
            True,
            ACTION_REBOOT,
            "✅ Reinicio confirmado. La Jetson Nano se reiniciará.",
        )

    def cancel(self, chat_id):
        """Cancela la solicitud pendiente del chat."""
        chat_id = int(chat_id)

        with self._lock:
            existed = chat_id in self._pending

            if existed:
                del self._pending[chat_id]

        if existed:
            LOGGER.info(
                "Acción administrativa cancelada por CHAT_ID %s",
                chat_id,
            )

            return True, "✅ Operación cancelada."

        return False, "No existe una operación pendiente."

    def has_pending_action(self, chat_id):
        """Indica si el chat tiene una acción vigente."""
        chat_id = int(chat_id)

        with self._lock:
            request = self._pending.get(chat_id)

            if request is None:
                return False

            elapsed = time.time() - request["created_at"]

            if elapsed > self.confirmation_timeout:
                del self._pending[chat_id]
                return False

            return True

    def clear_expired(self):
        """Elimina solicitudes caducadas."""
        now = time.time()
        expired = []

        with self._lock:
            for chat_id, request in self._pending.items():
                if now - request["created_at"] > self.confirmation_timeout:
                    expired.append(chat_id)

            for chat_id in expired:
                del self._pending[chat_id]

        return len(expired)
