#!/usr/bin/env python3
from __future__ import print_function

import logging
import threading
import numpy as np
import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst

Gst.init(None)
LOG = logging.getLogger("jetson-vision.camera")


def build_pipeline(sensor_id, capture_width, capture_height,
                   output_width, output_height, framerate, flip_method):
    return (
        "nvarguscamerasrc sensor-id={sensor_id} ! "
        "video/x-raw(memory:NVMM),"
        "width=(int){capture_width},"
        "height=(int){capture_height},"
        "format=(string)NV12,"
        "framerate=(fraction){framerate}/1 ! "
        "nvvidconv flip-method={flip_method} ! "
        "video/x-raw,"
        "width=(int){output_width},"
        "height=(int){output_height},"
        "format=(string)BGRx ! "
        "appsink name=camera_sink emit-signals=false "
        "sync=false drop=true max-buffers=1"
    ).format(
        sensor_id=sensor_id,
        capture_width=capture_width,
        capture_height=capture_height,
        output_width=output_width,
        output_height=output_height,
        framerate=framerate,
        flip_method=flip_method
    )


class GStreamerCamera(object):
    """Captura BGRx respetando el stride real del buffer."""

    def __init__(self, pipeline_text, timeout_seconds=3.0):
        self.pipeline_text = pipeline_text
        self.timeout_ns = int(timeout_seconds * Gst.SECOND)
        self.pipeline = None
        self.appsink = None
        self.lock = threading.Lock()
        self.opened = False
        self.last_error = None
        self._open()

    def _open(self):
        LOG.info("Pipeline: %s", self.pipeline_text)
        self.pipeline = Gst.parse_launch(self.pipeline_text)
        self.appsink = self.pipeline.get_by_name("camera_sink")
        if self.appsink is None:
            raise RuntimeError("No se encontró appsink camera_sink.")

        result = self.pipeline.set_state(Gst.State.PLAYING)
        if result == Gst.StateChangeReturn.FAILURE:
            self.release()
            raise RuntimeError("GStreamer no pudo iniciar la cámara.")

        result, _, _ = self.pipeline.get_state(5 * Gst.SECOND)
        if result == Gst.StateChangeReturn.FAILURE:
            self.release()
            raise RuntimeError("El pipeline no alcanzó PLAYING.")

        self.opened = True

    def isOpened(self):
        return bool(self.opened and self.pipeline and self.appsink)

    def _read_bus_error(self):
        if self.pipeline is None:
            return None
        bus = self.pipeline.get_bus()
        message = bus.pop_filtered(Gst.MessageType.ERROR)
        if message:
            error, debug = message.parse_error()
            return "{} | {}".format(error, debug)
        return None

    def read(self):
        if not self.isOpened():
            return False, None

        with self.lock:
            sample = self.appsink.emit("try-pull-sample", self.timeout_ns)
            if sample is None:
                self.last_error = self._read_bus_error() or "Timeout esperando frame."
                return False, None

            caps = sample.get_caps()
            structure = caps.get_structure(0)
            width = int(structure.get_value("width"))
            height = int(structure.get_value("height"))

            buffer_obj = sample.get_buffer()
            ok, map_info = buffer_obj.map(Gst.MapFlags.READ)
            if not ok:
                self.last_error = "No se pudo mapear el buffer."
                return False, None

            try:
                raw = np.frombuffer(map_info.data, dtype=np.uint8)
                if height <= 0 or raw.size % height != 0:
                    self.last_error = "Buffer inválido: bytes={} height={}".format(
                        raw.size, height
                    )
                    return False, None

                stride = raw.size // height
                required = width * 4
                if stride < required:
                    self.last_error = "Stride insuficiente: {} < {}".format(
                        stride, required
                    )
                    return False, None

                rows = raw.reshape((height, stride))
                bgrx = rows[:, :required].reshape((height, width, 4))
                frame = bgrx[:, :, :3].copy()
                return True, frame
            finally:
                buffer_obj.unmap(map_info)

    def release(self):
        self.opened = False
        if self.pipeline is not None:
            try:
                self.pipeline.set_state(Gst.State.NULL)
                self.pipeline.get_state(2 * Gst.SECOND)
            except Exception:
                pass
        self.appsink = None
        self.pipeline = None


def open_camera(settings):
    pipeline = build_pipeline(
        settings.camera_sensor_id,
        settings.camera_capture_width,
        settings.camera_capture_height,
        settings.camera_output_width,
        settings.camera_output_height,
        settings.camera_framerate,
        settings.camera_flip_method
    )
    camera = GStreamerCamera(
        pipeline,
        timeout_seconds=settings.camera_read_timeout_seconds
    )
    ok, frame = camera.read()
    if not ok or frame is None:
        error = camera.last_error
        camera.release()
        raise RuntimeError("La cámara no entregó frames: {}".format(error))
    LOG.info("IMX219 abierta: %sx%s", frame.shape[1], frame.shape[0])
    return camera
