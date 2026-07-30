#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import time

import cv2

from config import settings
from face_detector import FaceDetector
from person_management.repository import (
    ensure_person_dir,
    next_sample_number,
    validate_person_name,
)


class FaceCapture(object):
    """
    Captura muestras faciales utilizando la cámara de la Jetson Nano.
    """

    def __init__(self, camera):
        self.camera = camera

        self.detector = FaceDetector(
            settings.haar_model,
            settings.detection_scale_factor,
            settings.detection_min_neighbors,
            settings.detection_min_size
        )

    def capture(self, name, samples=30, interval=0.25, display=True):
        name = validate_person_name(name)

        if samples <= 0:
            raise ValueError("El número de muestras debe ser mayor que cero.")

        if interval < 0:
            raise ValueError("El intervalo no puede ser negativo.")

        person_dir = ensure_person_dir(settings.faces_dir, name)
        sample_number = next_sample_number(person_dir)

        saved = 0
        last_capture = 0.0

        print("")
        print("Persona: {}".format(name))
        print("Muestras solicitadas: {}".format(samples))
        print("Destino: {}".format(person_dir))
        print("")
        print("Presione q para cancelar.")
        print("")

        while saved < samples:
            frame = self.camera.read()

            if frame is None:
                print("No se pudo obtener una imagen de la cámara.")
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = sorted(
                self.detector.detect(gray),
                key=lambda item: int(item[2]) * int(item[3]),
                reverse=True
            )

            if faces:
                x, y, w, h = faces[0]

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0),
                    2
                )

                now = time.time()

                if now - last_capture >= interval:
                    crop = gray[y:y + h, x:x + w]

                    if crop is not None and crop.size > 0:
                        filename = "{:04d}.jpg".format(sample_number)
                        path = os.path.join(person_dir, filename)

                        if cv2.imwrite(path, crop):
                            saved += 1
                            sample_number += 1
                            last_capture = now

                            print(
                                "[GUARDADA] {}/{} - {}".format(
                                    saved,
                                    samples,
                                    path
                                )
                            )

            cv2.putText(
                frame,
                "Persona: {}".format(name),
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                "Muestras: {}/{}".format(saved, samples),
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            if display:
                cv2.imshow("Captura de rostros", frame)

                key = cv2.waitKey(1) & 0xFF

                if key == ord("q"):
                    print("Captura cancelada por el usuario.")
                    break

        if display:
            cv2.destroyAllWindows()

        return {
            "person": name,
            "saved": saved,
            "requested": samples,
            "directory": person_dir
        }
