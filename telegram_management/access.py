#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Control de acceso para Telegram.

Roles:
- Usuario
- Administrador
- No autorizado

Compatible con Python 3.6.
"""

import logging


LOGGER = logging.getLogger("jetson-vision.telegram.access")


ROLE_ADMIN = "admin"
ROLE_USER = "user"
ROLE_UNAUTHORIZED = "unauthorized"


USER_COMMANDS = {
    "/start",
    "/ayuda",
    "/estado",
    "/foto",
    "/eventos",
    "/ultimo_evento",
    "/personas",
    "/uptime",
}


ADMIN_COMMANDS = USER_COMMANDS.union({
    "/reiniciar_servicio",
    "/reboot",
    "/confirmar_reboot",
    "/cancelar",
})


class TelegramAccessController(object):
    """Controla usuarios, administradores y permisos."""

    def __init__(self, admin_chat_ids=None, user_chat_ids=None):
        self.admin_chat_ids = self._normalize_ids(admin_chat_ids)
        self.user_chat_ids = self._normalize_ids(user_chat_ids)

        # Evita duplicados: un administrador no necesita aparecer como usuario.
        self.user_chat_ids.difference_update(self.admin_chat_ids)

        LOGGER.info(
            "Telegram: %d administrador(es), %d usuario(s)",
            len(self.admin_chat_ids),
            len(self.user_chat_ids),
        )

    @staticmethod
    def _normalize_ids(chat_ids):
        """
        Convierte distintos formatos en un conjunto de enteros.

        Ejemplos:
            123456789
            "123456789"
            "123456789,987654321"
            [123456789, 987654321]
        """
        normalized = set()

        if chat_ids is None:
            return normalized

        if isinstance(chat_ids, (int, float)):
            chat_ids = [chat_ids]

        elif isinstance(chat_ids, str):
            chat_ids = chat_ids.split(",")

        for value in chat_ids:
            try:
                text = str(value).strip()

                if not text:
                    continue

                normalized.add(int(text))

            except (TypeError, ValueError):
                LOGGER.warning(
                    "CHAT_ID inválido ignorado: %r",
                    value,
                )

        return normalized

    @staticmethod
    def normalize_command(command):
        """
        Normaliza comandos como:

            /estado
            /estado@MiBot
            /estado argumento
        """
        if not command:
            return ""

        command = str(command).strip().split()[0].lower()

        if "@" in command:
            command = command.split("@", 1)[0]

        return command

    def get_role(self, chat_id):
        """Devuelve admin, user o unauthorized."""
        try:
            chat_id = int(chat_id)
        except (TypeError, ValueError):
            return ROLE_UNAUTHORIZED

        if chat_id in self.admin_chat_ids:
            return ROLE_ADMIN

        if chat_id in self.user_chat_ids:
            return ROLE_USER

        return ROLE_UNAUTHORIZED

    def is_authorized(self, chat_id):
        """Comprueba si el chat está autorizado."""
        return self.get_role(chat_id) != ROLE_UNAUTHORIZED

    def is_admin(self, chat_id):
        """Comprueba si el chat pertenece a un administrador."""
        return self.get_role(chat_id) == ROLE_ADMIN

    def can_execute(self, chat_id, command):
        """Comprueba si el chat puede ejecutar el comando."""
        role = self.get_role(chat_id)
        command = self.normalize_command(command)

        if role == ROLE_ADMIN:
            return command in ADMIN_COMMANDS

        if role == ROLE_USER:
            return command in USER_COMMANDS

        return False

    def get_allowed_commands(self, chat_id):
        """Devuelve los comandos disponibles para el chat."""
        role = self.get_role(chat_id)

        if role == ROLE_ADMIN:
            return sorted(ADMIN_COMMANDS)

        if role == ROLE_USER:
            return sorted(USER_COMMANDS)

        return []

    def describe_role(self, chat_id):
        """Devuelve el nombre legible del rol."""
        role = self.get_role(chat_id)

        if role == ROLE_ADMIN:
            return "Administrador"

        if role == ROLE_USER:
            return "Usuario"

        return "No autorizado"

    def build_help_message(self, chat_id):
        """Genera el mensaje de ayuda según el rol."""
        role = self.get_role(chat_id)

        if role == ROLE_ADMIN:
            return (
                "🤖 JETSON VISION\n\n"
                "Rol: Administrador\n\n"
                "Consultas:\n"
                "/estado - Estado general del sistema\n"
                "/foto - Obtener una fotografía actual\n"
                "/eventos - Consultar eventos recientes\n"
                "/ultimo_evento - Enviar el último evento\n"
                "/personas - Listar personas registradas\n"
                "/uptime - Tiempo de funcionamiento\n\n"
                "Administración:\n"
                "/reiniciar_servicio - Reiniciar Jetson Vision\n"
                "/reboot - Solicitar reinicio de la Jetson\n"
                "/confirmar_reboot - Confirmar el reinicio\n"
                "/cancelar - Cancelar una acción pendiente\n"
                "/ayuda - Mostrar esta ayuda"
            )

        if role == ROLE_USER:
            return (
                "🤖 JETSON VISION\n\n"
                "Rol: Usuario\n\n"
                "/estado - Estado general del sistema\n"
                "/foto - Obtener una fotografía actual\n"
                "/eventos - Consultar eventos recientes\n"
                "/ultimo_evento - Enviar el último evento\n"
                "/personas - Listar personas registradas\n"
                "/uptime - Tiempo de funcionamiento\n"
                "/ayuda - Mostrar esta ayuda"
            )

        return "⛔ Acceso no autorizado."
