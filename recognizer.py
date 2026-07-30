#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import logging
import os

import cv2
import numpy as np

LOG = logging.getLogger("jetson-vision.recognizer")


def normalize_face(gray_face, width, height):
    """
    Normaliza el rostro antes del entrenamiento y reconocimiento.
    """
    face = cv2.resize(gray_face, (int(width), int(height)))
    face = cv2.equalizeHist(face)
    return face


class TemplateFaceRecognizer(object):
    """
    Reconocedor facial basado en LBPH.

    Se mantiene el nombre TemplateFaceRecognizer para no modificar main.py.
    """

    def __init__(
        self,
        faces_dir,
        face_width=160,
        face_height=160,
        threshold=0.60,
        best_k=5
    ):

        self.faces_dir = faces_dir
        self.face_width = int(face_width)
        self.face_height = int(face_height)

        self.label_to_name = {}
        self.trained = False

        # Compatible con OpenCV 3.2
        self.recognizer = cv2.face.createLBPHFaceRecognizer(
            radius=1,
            neighbors=8,
            grid_x=8,
            grid_y=8
        )

        self.reload()

    def reload(self):

        images = []
        labels = []

        label = 0
        self.label_to_name = {}

        if not os.path.isdir(self.faces_dir):
            os.makedirs(self.faces_dir)

        for person in sorted(os.listdir(self.faces_dir)):

            person_dir = os.path.join(self.faces_dir, person)

            if not os.path.isdir(person_dir):
                continue

            count = 0

            for filename in sorted(os.listdir(person_dir)):

                if not filename.lower().endswith(
                    (".jpg", ".jpeg", ".png")
                ):
                    continue

                path = os.path.join(person_dir, filename)

                image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

                if image is None:
                    continue

                image = normalize_face(
                    image,
                    self.face_width,
                    self.face_height
                )

                images.append(image)
                labels.append(label)
                count += 1

            if count > 0:
                self.label_to_name[label] = person
                LOG.info("%s: %d muestras", person, count)
                label += 1

        if len(images) == 0:
            LOG.warning("No existen muestras para entrenar.")
            self.trained = False
            return

        self.recognizer.train(
            images,
            np.array(labels)
        )

        self.trained = True

        LOG.info(
            "Personas cargadas: %d",
            len(self.label_to_name)
        )

    def predict(self, gray_face):

        if not self.trained:
            return "Desconocido", 0.0

        face = normalize_face(
            gray_face,
            self.face_width,
            self.face_height
        )

        label, distance = self.recognizer.predict(face)

        #
        # LBPH:
        #
        # distancia pequeña = mejor coincidencia
        #

        if distance < 40:
            confidence = 0.99

        elif distance < 50:
            confidence = 0.95

        elif distance < 60:
            confidence = 0.90

        elif distance < 70:
            confidence = 0.80

        elif distance < 80:
            confidence = 0.70

        else:
            confidence = 0.0

        if distance >= 80:
            return "Desconocido", confidence

        return self.label_to_name[label], confidence
