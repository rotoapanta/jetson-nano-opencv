#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_dotenv(path):
    """
    Carga variables desde un archivo .env.

    No sobrescribe variables que ya existan en el entorno.
    """

    if not os.path.isfile(path):
        return

    with open(path, "r") as handle:
        for raw_line in handle:
            line = raw_line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            if "=" not in line:
                continue

            key, value = line.split("=", 1)

            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key and key not in os.environ:
                os.environ[key] = value


def _get(name, default=None):
    """
    Obtiene una variable de entorno.
    """

    return os.environ.get(name, default)


def _get_int(name, default):
    """
    Obtiene una variable de entorno como entero.
    """

    try:
        return int(_get(name, str(default)))

    except (TypeError, ValueError):
        return int(default)


def _get_float(name, default):
    """
    Obtiene una variable de entorno como número decimal.
    """

    try:
        return float(_get(name, str(default)))

    except (TypeError, ValueError):
        return float(default)


def _get_bool(name, default):
    """
    Obtiene una variable de entorno como booleano.
    """

    value = _get(
        name,
        "true" if default else "false"
    )

    return str(value).strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
        "si",
        "sí",
    )


def _get_int_list(name, default=""):
    """
    Obtiene una lista de enteros separados por comas.

    Ejemplo:

        TELEGRAM_ADMIN_CHAT_IDS=123456789,987654321

    Resultado:

        [123456789, 987654321]
    """

    value = _get(name, default)
    result = []

    if value is None:
        return result

    if isinstance(value, (list, tuple, set)):
        values = value
    else:
        values = str(value).split(",")

    for item in values:
        item = str(item).strip()

        if not item:
            continue

        try:
            number = int(item)

            if number not in result:
                result.append(number)

        except (TypeError, ValueError):
            continue

    return result


def _path(name, default):
    """
    Devuelve una ruta absoluta.

    Si el valor configurado es relativo, se construye desde BASE_DIR.
    """

    value = _get(name, default)

    if os.path.isabs(value):
        return value

    return os.path.join(BASE_DIR, value)


# Cargar variables del archivo .env
_load_dotenv(
    os.path.join(BASE_DIR, ".env")
)


class Settings(object):
    """
    Configuración central de Jetson Nano Vision.
    """

    # ---------------------------------------------------------
    # Rutas principales
    # ---------------------------------------------------------

    base_dir = BASE_DIR

    # ---------------------------------------------------------
    # Cámara CSI
    # ---------------------------------------------------------

    camera_sensor_id = _get_int(
        "CAMERA_SENSOR_ID",
        0
    )

    camera_capture_width = _get_int(
        "CAMERA_CAPTURE_WIDTH",
        1920
    )

    camera_capture_height = _get_int(
        "CAMERA_CAPTURE_HEIGHT",
        1080
    )

    camera_output_width = _get_int(
        "CAMERA_OUTPUT_WIDTH",
        960
    )

    camera_output_height = _get_int(
        "CAMERA_OUTPUT_HEIGHT",
        540
    )

    camera_framerate = _get_int(
        "CAMERA_FRAMERATE",
        30
    )

    camera_flip_method = _get_int(
        "CAMERA_FLIP_METHOD",
        0
    )

    camera_read_timeout_seconds = _get_float(
        "CAMERA_READ_TIMEOUT_SECONDS",
        3.0
    )

    camera_reconnect_seconds = _get_float(
        "CAMERA_RECONNECT_SECONDS",
        3.0
    )

    # ---------------------------------------------------------
    # Modelos y datos
    # ---------------------------------------------------------

    haar_model = _path(
        "HAAR_MODEL",
        "models/haarcascade_frontalface_default.xml"
    )

    faces_dir = _path(
        "FACES_DIR",
        "data/faces"
    )

    events_dir = _path(
        "EVENTS_DIR",
        "data/events"
    )

    # ---------------------------------------------------------
    # Detección facial
    # ---------------------------------------------------------

    face_width = _get_int(
        "FACE_WIDTH",
        160
    )

    face_height = _get_int(
        "FACE_HEIGHT",
        160
    )

    detection_scale_factor = _get_float(
        "DETECTION_SCALE_FACTOR",
        1.15
    )

    detection_min_neighbors = _get_int(
        "DETECTION_MIN_NEIGHBORS",
        5
    )

    detection_min_size = _get_int(
        "DETECTION_MIN_SIZE",
        80
    )

    # ---------------------------------------------------------
    # Reconocimiento facial
    # ---------------------------------------------------------

    recognition_threshold = _get_float(
        "RECOGNITION_THRESHOLD",
        0.72
    )

    recognition_confirm_frames = _get_int(
        "RECOGNITION_CONFIRM_FRAMES",
        3
    )

    unknown_confirm_frames = _get_int(
        "UNKNOWN_CONFIRM_FRAMES",
        5
    )

    # ---------------------------------------------------------
    # Eventos
    # ---------------------------------------------------------

    event_cooldown_seconds = _get_int(
        "EVENT_COOLDOWN_SECONDS",
        60
    )

    event_retention_days = _get_int(
        "EVENT_RETENTION_DAYS",
        30
    )

    save_unknown_events = _get_bool(
        "SAVE_UNKNOWN_EVENTS",
        False
    )

    # ---------------------------------------------------------
    # Streaming web
    # ---------------------------------------------------------

    stream_enabled = _get_bool(
        "STREAM_ENABLED",
        True
    )

    stream_host = _get(
        "STREAM_HOST",
        "0.0.0.0"
    )

    stream_port = _get_int(
        "STREAM_PORT",
        8080
    )

    stream_jpeg_quality = _get_int(
        "STREAM_JPEG_QUALITY",
        80
    )

    stream_max_fps = _get_float(
        "STREAM_MAX_FPS",
        12.0
    )

    # ---------------------------------------------------------
    # Pantalla local
    # ---------------------------------------------------------

    display_enabled = _get_bool(
        "DISPLAY_ENABLED",
        True
    )

    display_window_name = _get(
        "DISPLAY_WINDOW_NAME",
        "Jetson Nano Vision v2"
    )

    # ---------------------------------------------------------
    # Telegram
    # ---------------------------------------------------------

    telegram_enabled = _get_bool(
        "TELEGRAM_ENABLED",
        False
    )

    telegram_commands_enabled = _get_bool(
        "TELEGRAM_COMMANDS_ENABLED",
        True
    )

    telegram_bot_token = _get(
        "TELEGRAM_BOT_TOKEN",
        ""
    )

    # Compatibilidad temporal con la configuración antigua.
    telegram_chat_id = _get(
        "TELEGRAM_CHAT_ID",
        ""
    )

    # Administradores del bot.
    #
    # Si TELEGRAM_ADMIN_CHAT_IDS no existe,
    # se usa temporalmente TELEGRAM_CHAT_ID.
    telegram_admin_chat_ids = _get_int_list(
        "TELEGRAM_ADMIN_CHAT_IDS",
        telegram_chat_id
    )

    # Usuarios normales.
    telegram_user_chat_ids = _get_int_list(
        "TELEGRAM_USER_CHAT_IDS",
        ""
    )

    # Destinatarios de notificaciones automáticas.
    #
    # Por ejemplo:
    # - reconocimiento facial;
    # - inicio del sistema;
    # - futuras alertas.
    telegram_notification_chat_ids = _get_int_list(
        "TELEGRAM_NOTIFICATION_CHAT_IDS",
        telegram_chat_id
    )

    telegram_timeout_seconds = _get_int(
        "TELEGRAM_TIMEOUT_SECONDS",
        10
    )

    telegram_retry_count = _get_int(
        "TELEGRAM_RETRY_COUNT",
        3
    )

    telegram_poll_timeout = _get_int(
        "TELEGRAM_POLL_TIMEOUT",
        20
    )

    telegram_reboot_enabled = _get_bool(
        "TELEGRAM_REBOOT_ENABLED",
        False
    )

    telegram_reboot_confirm_timeout = _get_int(
        "TELEGRAM_REBOOT_CONFIRM_TIMEOUT",
        30
    )

    # ---------------------------------------------------------
    # Servicio systemd
    # ---------------------------------------------------------

    systemd_service_name = _get(
        "SYSTEMD_SERVICE_NAME",
        "jetson-vision.service"
    )

    # ---------------------------------------------------------
    # Logging
    # ---------------------------------------------------------

    log_level = _get(
        "LOG_LEVEL",
        "INFO"
    )

    log_file = _path(
        "LOG_FILE",
        "logs/jetson-vision.log"
    )


settings = Settings()
