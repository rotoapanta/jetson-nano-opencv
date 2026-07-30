#!/usr/bin/env python3
from __future__ import print_function
import logging, os, re, time
from datetime import datetime, timedelta
import cv2

LOG = logging.getLogger("jetson-vision.events")

def safe_name(value):
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value))
    return cleaned.strip("_") or "evento"

class EventManager(object):
    def __init__(self, events_dir, cooldown_seconds=60, retention_days=30):
        self.events_dir = events_dir
        self.cooldown_seconds = int(cooldown_seconds)
        self.retention_days = int(retention_days)
        self.last_event_by_name = {}
        if not os.path.isdir(events_dir):
            os.makedirs(events_dir)

    def may_create(self, name):
        return time.time() - self.last_event_by_name.get(name, 0) >= self.cooldown_seconds

    def save(self, name, confidence, frame):
        if not self.may_create(name):
            return None
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = "{}_{}_{:03d}.jpg".format(
            safe_name(name), stamp, int(round(confidence * 100))
        )
        path = os.path.join(self.events_dir, filename)
        if not cv2.imwrite(path, frame):
            LOG.error("No se pudo guardar evento: %s", path)
            return None
        self.last_event_by_name[name] = time.time()
        LOG.info("Evento guardado: %s", path)
        return path

    def cleanup(self):
        if self.retention_days <= 0:
            return
        limit = datetime.now() - timedelta(days=self.retention_days)
        for filename in os.listdir(self.events_dir):
            path = os.path.join(self.events_dir, filename)
            if os.path.isfile(path):
                modified = datetime.fromtimestamp(os.path.getmtime(path))
                if modified < limit:
                    try:
                        os.remove(path)
                    except OSError as exc:
                        LOG.warning("No se pudo eliminar %s: %s", path, exc)
