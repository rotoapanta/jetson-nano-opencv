#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Funciones auxiliares para Telegram Management.

Compatible con Python 3.6.
"""

from datetime import datetime


def format_bytes(value):
    """Convierte bytes a un formato legible."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "N/D"

    units = ["B", "KB", "MB", "GB", "TB"]
    index = 0

    while value >= 1024.0 and index < len(units) - 1:
        value /= 1024.0
        index += 1

    if index == 0:
        return "{:.0f} {}".format(value, units[index])

    return "{:.2f} {}".format(value, units[index])


def format_seconds(seconds):
    """Convierte segundos a días, horas, minutos y segundos."""
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return "N/D"

    if seconds < 0:
        seconds = 0

    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []

    if days:
        parts.append("{} día{}".format(days, "" if days == 1 else "s"))

    if hours:
        parts.append("{} hora{}".format(hours, "" if hours == 1 else "s"))

    if minutes:
        parts.append(
            "{} minuto{}".format(minutes, "" if minutes == 1 else "s")
        )

    if seconds or not parts:
        parts.append(
            "{} segundo{}".format(seconds, "" if seconds == 1 else "s")
        )

    return ", ".join(parts)


def format_datetime(value=None, date_format="%d/%m/%Y %H:%M:%S"):
    """Formatea una fecha y hora."""
    if value is None:
        value = datetime.now()

    if isinstance(value, datetime):
        return value.strftime(date_format)

    try:
        return datetime.fromtimestamp(float(value)).strftime(date_format)
    except (TypeError, ValueError, OSError):
        return str(value)


def percentage(used, total):
    """Calcula un porcentaje de forma segura."""
    try:
        used = float(used)
        total = float(total)

        if total <= 0:
            return 0.0

        return (used / total) * 100.0

    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def truncate_text(text, max_length=3500):
    """Recorta texto para evitar exceder los límites de Telegram."""
    if text is None:
        return ""

    text = str(text)

    if len(text) <= max_length:
        return text

    return text[:max_length - 3] + "..."


def safe_username(user):
    """Obtiene un nombre legible desde un usuario de Telegram."""
    if not isinstance(user, dict):
        return "desconocido"

    username = user.get("username")

    if username:
        return "@{}".format(username)

    first_name = user.get("first_name", "")
    last_name = user.get("last_name", "")

    full_name = "{} {}".format(first_name, last_name).strip()

    return full_name or "desconocido"


def parse_int_list(value):
    """
    Convierte una cadena separada por comas en una lista de enteros.

    Ejemplo:
        "123,456,789" -> [123, 456, 789]
    """
    result = []

    if value is None:
        return result

    if isinstance(value, (list, tuple, set)):
        values = value
    else:
        values = str(value).split(",")

    for item in values:
        try:
            text = str(item).strip()

            if not text:
                continue

            number = int(text)

            if number not in result:
                result.append(number)

        except (TypeError, ValueError):
            continue

    return result
