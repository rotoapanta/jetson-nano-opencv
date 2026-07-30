#!/usr/bin/env python3
import cv2

class FaceDetector(object):
    def __init__(self, model_path, scale_factor=1.15,
                 min_neighbors=5, min_size=80):
        self.cascade = cv2.CascadeClassifier(model_path)
        if self.cascade.empty():
            raise RuntimeError("No se pudo cargar Haar Cascade: {}".format(model_path))
        self.scale_factor = float(scale_factor)
        self.min_neighbors = int(min_neighbors)
        self.min_size = int(min_size)

    def detect(self, gray):
        return list(self.cascade.detectMultiScale(
            gray,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=(self.min_size, self.min_size)
        ))
