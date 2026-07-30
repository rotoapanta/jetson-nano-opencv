#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import json
import logging
import threading
import time

from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

import cv2
import numpy as np


LOG = logging.getLogger("jetson-vision.stream-server")


class FrameStore(object):
    """
    Almacena el último frame JPEG y el estado actual del sistema.
    """

    def __init__(self, jpeg_quality=80, max_fps=12.0):
        self.condition = threading.Condition()
        self.jpeg = None
        self.sequence = 0
        self.jpeg_quality = int(jpeg_quality)
        self.max_fps = float(max_fps)
        self.last_encode = 0.0

        self.status = {
            "ok": True,
            "fps": 0.0,
            "faces": 0,
            "last_recognition": None
        }

    def update(self, frame, status=None):
        """
        Convierte el frame a JPEG y notifica a los clientes conectados.
        """
        now = time.time()

        if (
            self.max_fps > 0
            and now - self.last_encode < 1.0 / self.max_fps
        ):
            if status:
                self.status.update(status)

            return False

        if frame is None or not isinstance(frame, np.ndarray):
            return False

        ok, encoded = cv2.imencode(
            ".jpg",
            frame,
            [
                int(cv2.IMWRITE_JPEG_QUALITY),
                self.jpeg_quality
            ]
        )

        if not ok:
            LOG.warning("No se pudo codificar el frame como JPEG.")
            return False

        with self.condition:
            self.jpeg = encoded.tobytes()
            self.sequence += 1
            self.last_encode = now

            if status:
                self.status.update(status)

            self.condition.notify_all()

        return True

    def wait(self, last_sequence, timeout=2.0):
        """
        Espera hasta que exista un frame nuevo.
        """
        with self.condition:
            if self.sequence == last_sequence:
                self.condition.wait(timeout)

            return self.sequence, self.jpeg

    def snapshot(self):
        """
        Devuelve el último frame JPEG disponible.
        """
        with self.condition:
            return self.jpeg

    def status_json(self):
        """
        Devuelve el estado del sistema en formato JSON.
        """
        with self.condition:
            return json.dumps(
                self.status
            ).encode("utf-8")


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """
    Servidor HTTP que atiende cada cliente en un hilo separado.
    """

    daemon_threads = True
    allow_reuse_address = True


def make_handler(store):
    """
    Crea el manejador HTTP asociado al almacenamiento de frames.
    """

    class Handler(BaseHTTPRequestHandler):

        def log_message(self, format_string, *args):
            """
            Evita los mensajes HTTP estándar en consola.
            """
            return

        def handle(self):
            """
            Captura desconexiones que suceden antes o durante
            el procesamiento de una petición HTTP.
            """
            try:
                BaseHTTPRequestHandler.handle(self)

            except (
                BrokenPipeError,
                ConnectionResetError,
                ConnectionAbortedError
            ):
                LOG.info(
                    "Cliente desconectado del stream: %s",
                    self._client_ip()
                )

            except OSError as exc:
                # errno 32  = Broken pipe
                # errno 54  = Connection reset by peer, algunos sistemas
                # errno 104 = Connection reset by peer, Linux
                if getattr(exc, "errno", None) in (32, 54, 104):
                    LOG.info(
                        "Cliente desconectado del stream: %s",
                        self._client_ip()
                    )
                    return

                LOG.exception(
                    "Error de comunicación con el cliente %s",
                    self._client_ip()
                )

            except Exception:
                LOG.exception(
                    "Error inesperado atendiendo al cliente %s",
                    self._client_ip()
                )

        def _client_ip(self):
            """
            Obtiene de forma segura la IP del cliente.
            """
            try:
                return self.client_address[0]
            except Exception:
                return "desconocido"

        def _headers(self, code, content_type, length=None):
            """
            Envía las cabeceras HTTP.
            """
            self.send_response(code)
            self.send_header(
                "Content-Type",
                content_type
            )
            self.send_header(
                "Cache-Control",
                "no-store, no-cache, must-revalidate"
            )
            self.send_header(
                "Pragma",
                "no-cache"
            )

            if length is not None:
                self.send_header(
                    "Content-Length",
                    str(length)
                )

            self.end_headers()

        def _write_response(self, payload):
            """
            Envía una respuesta corta manejando la desconexión
            del cliente de forma limpia.
            """
            try:
                self.wfile.write(payload)
                self.wfile.flush()
                return True

            except (
                BrokenPipeError,
                ConnectionResetError,
                ConnectionAbortedError
            ):
                LOG.info(
                    "Cliente desconectado: %s",
                    self._client_ip()
                )
                return False

            except OSError as exc:
                if getattr(exc, "errno", None) in (32, 54, 104):
                    LOG.info(
                        "Cliente desconectado: %s",
                        self._client_ip()
                    )
                    return False

                raise

        def do_HEAD(self):
            """
            Atiende solicitudes HEAD.
            """
            if self.path in (
                "/",
                "/stream.mjpg",
                "/snapshot.jpg",
                "/health"
            ):
                self._headers(
                    200,
                    "text/plain; charset=utf-8"
                )
            else:
                self.send_error(404)

        def do_GET(self):
            """
            Atiende la página, el stream, la captura y el estado.
            """

            if self.path == "/":
                self._serve_home()
                return

            if self.path == "/health":
                self._serve_health()
                return

            if self.path == "/snapshot.jpg":
                self._serve_snapshot()
                return

            if self.path == "/stream.mjpg":
                self._serve_stream()
                return

            self.send_error(404)

        def _serve_home(self):
            """
            Muestra la página principal.
            """
            page = (
                "<!doctype html>"
                "<html lang='es'>"
                "<head>"
                "<meta charset='utf-8'>"
                "<meta name='viewport' "
                "content='width=device-width,initial-scale=1'>"
                "<title>Jetson Nano Vision v2</title>"
                "</head>"
                "<body style='margin:0;background:#111;color:#fff;"
                "font-family:Arial;text-align:center'>"
                "<h2>Jetson Nano Vision v2</h2>"
                "<img src='/stream.mjpg' "
                "style='width:100%;max-width:960px;height:auto'>"
                "<p>"
                "<a style='color:#8fd3ff' "
                "href='/snapshot.jpg'>Captura</a>"
                " · "
                "<a style='color:#8fd3ff' "
                "href='/health'>Estado</a>"
                "</p>"
                "</body>"
                "</html>"
            ).encode("utf-8")

            self._headers(
                200,
                "text/html; charset=utf-8",
                len(page)
            )

            self._write_response(page)

        def _serve_health(self):
            """
            Entrega el estado en formato JSON.
            """
            payload = store.status_json()

            self._headers(
                200,
                "application/json; charset=utf-8",
                len(payload)
            )

            self._write_response(payload)

        def _serve_snapshot(self):
            """
            Entrega el último frame como imagen JPEG.
            """
            jpeg = store.snapshot()

            if not jpeg:
                self.send_error(
                    503,
                    "No hay frame disponible"
                )
                return

            self._headers(
                200,
                "image/jpeg",
                len(jpeg)
            )

            self._write_response(jpeg)

        def _serve_stream(self):
            """
            Entrega el video mediante MJPEG.
            """
            self._headers(
                200,
                "multipart/x-mixed-replace; boundary=frame"
            )

            client_ip = self._client_ip()
            sequence = -1

            LOG.info(
                "Cliente conectado al stream: %s",
                client_ip
            )

            try:
                while True:
                    sequence, jpeg = store.wait(sequence)

                    if not jpeg:
                        time.sleep(0.05)
                        continue

                    header = (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n"
                        b"Content-Length: "
                        + str(len(jpeg)).encode("ascii")
                        + b"\r\n\r\n"
                    )

                    self.wfile.write(header)
                    self.wfile.write(jpeg)
                    self.wfile.write(b"\r\n")
                    self.wfile.flush()

            except (
                BrokenPipeError,
                ConnectionResetError,
                ConnectionAbortedError
            ):
                LOG.info(
                    "Cliente desconectado del stream: %s",
                    client_ip
                )

            except OSError as exc:
                if getattr(exc, "errno", None) in (32, 54, 104):
                    LOG.info(
                        "Cliente desconectado del stream: %s",
                        client_ip
                    )
                    return

                LOG.exception(
                    "Error transmitiendo el stream al cliente %s",
                    client_ip
                )

            except Exception:
                LOG.exception(
                    "Error inesperado transmitiendo el stream "
                    "al cliente %s",
                    client_ip
                )

    return Handler


def start_stream_server(host, port, store):
    """
    Inicia el servidor HTTP en un hilo independiente.
    """
    server = ThreadedHTTPServer(
        (host, int(port)),
        make_handler(store)
    )

    thread = threading.Thread(
        target=server.serve_forever
    )

    thread.daemon = True
    thread.start()

    LOG.info(
        "Servidor de streaming iniciado en http://%s:%s",
        host,
        port
    )

    return server
