#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import socket
import time
from collections import defaultdict

import cv2

from camera import open_camera
from config import settings
from event_manager import EventManager
from face_detector import FaceDetector
from logger import setup_logging
from recognizer import TemplateFaceRecognizer
from stream_server import FrameStore, start_stream_server

from telegram_management import (
    AdministrativeActionManager,
    SystemMonitor,
    TelegramAccessController,
    TelegramCommandHandler,
    TelegramManager,
    TelegramNotifier,
)


def draw_label(frame, x, y, w, h, name, confidence):
    """
    Dibuja el rectángulo y la etiqueta del reconocimiento facial.
    """

    if name != "Desconocido":
        color = (0, 220, 0)
    else:
        color = (0, 0, 255)

    cv2.rectangle(
        frame,
        (x, y),
        (x + w, y + h),
        color,
        2,
    )

    label = "{} ({:.1f}%)".format(
        name,
        confidence * 100.0,
    )

    label_top = max(0, y - 28)
    label_width = max(210, w)

    cv2.rectangle(
        frame,
        (x, label_top),
        (x + label_width, y),
        color,
        -1,
    )

    cv2.putText(
        frame,
        label,
        (x + 5, y - 7),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (255, 255, 255),
        2,
    )


def create_directories():
    """
    Crea los directorios requeridos por la aplicación.
    """

    directories = (
        settings.faces_dir,
        settings.events_dir,
        os.path.dirname(settings.log_file),
    )

    for directory in directories:
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)


def main():
    """
    Punto de entrada principal de Jetson Nano Vision.
    """

    log = setup_logging(
        settings.log_file,
        settings.log_level,
    )

    create_directories()

    log.info("Iniciando Jetson Nano Vision v2.")

    # ---------------------------------------------------------
    # Detector facial
    # ---------------------------------------------------------

    detector = FaceDetector(
        settings.haar_model,
        settings.detection_scale_factor,
        settings.detection_min_neighbors,
        settings.detection_min_size,
    )

    # ---------------------------------------------------------
    # Reconocedor facial
    # ---------------------------------------------------------

    recognizer = TemplateFaceRecognizer(
        settings.faces_dir,
        settings.face_width,
        settings.face_height,
        settings.recognition_threshold,
    )

    # ---------------------------------------------------------
    # Gestor de eventos
    # ---------------------------------------------------------

    events = EventManager(
        settings.events_dir,
        settings.event_cooldown_seconds,
        settings.event_retention_days,
    )

    events.cleanup()

    # ---------------------------------------------------------
    # Almacenamiento del último frame
    # ---------------------------------------------------------

    store = FrameStore(
        settings.stream_jpeg_quality,
        settings.stream_max_fps,
    )

    # ---------------------------------------------------------
    # Notificaciones Telegram
    # ---------------------------------------------------------

    notifier = TelegramNotifier(
        enabled=settings.telegram_enabled,
        bot_token=settings.telegram_bot_token,
        notification_chat_ids=(
            settings.telegram_notification_chat_ids
        ),
        timeout_seconds=settings.telegram_timeout_seconds,
        retry_count=settings.telegram_retry_count,
    )

    # ---------------------------------------------------------
    # Control de acceso Telegram
    # ---------------------------------------------------------

    access = TelegramAccessController(
        admin_chat_ids=settings.telegram_admin_chat_ids,
        user_chat_ids=settings.telegram_user_chat_ids,
    )

    # ---------------------------------------------------------
    # Monitor del sistema
    # ---------------------------------------------------------

    monitor = SystemMonitor(
        service_name=settings.systemd_service_name,
        faces_directory=settings.faces_dir,
        events_directory=settings.events_dir,
    )

    # ---------------------------------------------------------
    # Administrador de acciones críticas
    # ---------------------------------------------------------

    action_manager = AdministrativeActionManager(
        confirmation_timeout=(
            settings.telegram_reboot_confirm_timeout
        )
    )

    # ---------------------------------------------------------
    # Comandos Telegram
    # ---------------------------------------------------------

    command_handler = TelegramCommandHandler(
        notifier=notifier,
        access=access,
        monitor=monitor,
        action_manager=action_manager,
        frame_store=store,
        faces_dir=settings.faces_dir,
        events_dir=settings.events_dir,
        service_name=settings.systemd_service_name,
        reboot_enabled=settings.telegram_reboot_enabled,
    )

    # ---------------------------------------------------------
    # Bot Telegram
    # ---------------------------------------------------------

    telegram_manager = TelegramManager(
        enabled=settings.telegram_enabled,
        commands_enabled=settings.telegram_commands_enabled,
        bot_token=settings.telegram_bot_token,
        poll_timeout=settings.telegram_poll_timeout,
        notifier=notifier,
        access=access,
        command_handler=command_handler,
    )

    # ---------------------------------------------------------
    # Servidor web de streaming
    # ---------------------------------------------------------

    server = None

    if settings.stream_enabled:
        server = start_stream_server(
            settings.stream_host,
            settings.stream_port,
            store,
        )

        log.info(
            "Streaming disponible en http://%s:%s/",
            settings.stream_host,
            settings.stream_port,
        )

    # ---------------------------------------------------------
    # Cámara
    # ---------------------------------------------------------

    camera = open_camera(settings)

    # ---------------------------------------------------------
    # Datos del sistema
    # ---------------------------------------------------------

    hostname = socket.gethostname()

    counters = defaultdict(int)

    last_frame_time = time.time()
    fps = 0.0
    last_recognition = None

    # ---------------------------------------------------------
    # Iniciar Telegram
    # ---------------------------------------------------------

    telegram_manager.start()

    if notifier.validate():
        notifier.send_startup(hostname)

    # ---------------------------------------------------------
    # Bucle principal
    # ---------------------------------------------------------

    try:
        while True:
            ok, frame = camera.read()

            if not ok or frame is None:
                log.warning(
                    "Fallo de cámara: %s",
                    camera.last_error,
                )

                camera.release()

                time.sleep(
                    settings.camera_reconnect_seconds
                )

                camera = open_camera(settings)

                continue

            # -------------------------------------------------
            # Cálculo de FPS
            # -------------------------------------------------

            now = time.time()

            delta = max(
                0.0001,
                now - last_frame_time,
            )

            current_fps = 1.0 / delta

            if fps == 0:
                fps = current_fps
            else:
                fps = (
                    fps * 0.9
                    + current_fps * 0.1
                )

            last_frame_time = now

            # -------------------------------------------------
            # Conversión a escala de grises
            # -------------------------------------------------

            gray = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2GRAY,
            )

            # -------------------------------------------------
            # Detección facial
            # -------------------------------------------------

            faces = detector.detect(gray)

            active_names = set()

            # -------------------------------------------------
            # Reconocimiento facial
            # -------------------------------------------------

            for x, y, w, h in faces:
                crop = gray[
                    y:y + h,
                    x:x + w
                ]

                name, confidence = recognizer.predict(crop)

                active_names.add(name)

                counters[name] += 1

                if name != "Desconocido":
                    required = (
                        settings.recognition_confirm_frames
                    )
                else:
                    required = (
                        settings.unknown_confirm_frames
                    )

                draw_label(
                    frame,
                    x,
                    y,
                    w,
                    h,
                    name,
                    confidence,
                )

                # ---------------------------------------------
                # Confirmación del reconocimiento
                # ---------------------------------------------

                if counters[name] >= required:
                    should_save = (
                        name != "Desconocido"
                        or settings.save_unknown_events
                    )

                    if should_save:
                        path = events.save(
                            name,
                            confidence,
                            frame,
                        )

                        if path:
                            last_recognition = {
                                "name": name,
                                "confidence": round(
                                    confidence,
                                    4,
                                ),
                                "time": time.strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            }

                            # Enviar únicamente reconocimientos
                            # conocidos por Telegram.
                            if name != "Desconocido":
                                notifier.send_recognition(
                                    image_path=path,
                                    name=name,
                                    confidence=confidence,
                                    hostname=hostname,
                                )

                    counters[name] = 0

            # -------------------------------------------------
            # Reiniciar contadores de rostros ausentes
            # -------------------------------------------------

            for known_name in list(counters.keys()):
                if known_name not in active_names:
                    counters[known_name] = 0

            # -------------------------------------------------
            # Información visual sobre el frame
            # -------------------------------------------------

            cv2.putText(
                frame,
                "FPS: {:.1f}".format(fps),
                (15, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 255, 255),
                2,
            )

            cv2.putText(
                frame,
                "Rostros: {}".format(len(faces)),
                (15, 58),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 255, 255),
                2,
            )

            # -------------------------------------------------
            # Actualizar streaming y estado
            # -------------------------------------------------

            store.update(
                frame,
                {
                    "ok": True,
                    "fps": round(fps, 1),
                    "faces": len(faces),
                    "last_recognition": last_recognition,
                },
            )

            # -------------------------------------------------
            # Ventana local
            # -------------------------------------------------

            if settings.display_enabled:
                cv2.imshow(
                    settings.display_window_name,
                    frame,
                )

                key = cv2.waitKey(1) & 0xFF

                if key == ord("q"):
                    break

    except KeyboardInterrupt:
        log.info(
            "Interrupción recibida desde el teclado."
        )

    except Exception:
        log.exception(
            "Error inesperado en el bucle principal."
        )

    finally:
        # -----------------------------------------------------
        # Detener Telegram
        # -----------------------------------------------------

        try:
            telegram_manager.stop()

        except Exception:
            log.exception(
                "Error deteniendo el bot Telegram."
            )

        # -----------------------------------------------------
        # Liberar cámara
        # -----------------------------------------------------

        try:
            camera.release()

        except Exception:
            log.exception(
                "Error liberando la cámara."
            )

        # -----------------------------------------------------
        # Detener servidor web
        # -----------------------------------------------------

        if server is not None:
            try:
                server.shutdown()
                server.server_close()

            except Exception:
                log.exception(
                    "Error deteniendo el servidor web."
                )

        # -----------------------------------------------------
        # Cerrar ventanas de OpenCV
        # -----------------------------------------------------

        try:
            cv2.destroyAllWindows()

        except Exception:
            log.exception(
                "Error cerrando las ventanas de OpenCV."
            )

        log.info("Aplicación detenida.")


if __name__ == "__main__":
    main()
