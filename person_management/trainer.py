#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import os

import cv2
import numpy as np

from config import settings
from recognizer import normalize_face


class DatasetValidator(object):
    """
    Valida que el conjunto de rostros pueda utilizarse
    para entrenar LBPH correctamente.
    """

    def __init__(self, face_width=160, face_height=160):
        self.face_width = int(face_width)
        self.face_height = int(face_height)

    def validate(self):
        images = []
        labels = []
        people = []
        invalid_files = []

        label = 0

        if not os.path.isdir(settings.faces_dir):
            return {
                "valid": False,
                "people": 0,
                "samples": 0,
                "invalid_files": [],
                "message": "No existe la carpeta de rostros."
            }

        for person in sorted(os.listdir(settings.faces_dir)):
            person_dir = os.path.join(settings.faces_dir, person)

            if not os.path.isdir(person_dir):
                continue

            person_count = 0

            for filename in sorted(os.listdir(person_dir)):
                if not filename.lower().endswith(
                    (".jpg", ".jpeg", ".png")
                ):
                    continue

                path = os.path.join(person_dir, filename)

                image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

                if image is None:
                    invalid_files.append(path)
                    continue

                try:
                    image = normalize_face(
                        image,
                        self.face_width,
                        self.face_height
                    )
                except Exception:
                    invalid_files.append(path)
                    continue

                images.append(image)
                labels.append(label)
                person_count += 1

            if person_count > 0:
                people.append({
                    "name": person,
                    "samples": person_count
                })
                label += 1

        if not images:
            return {
                "valid": False,
                "people": 0,
                "samples": 0,
                "invalid_files": invalid_files,
                "message": "No existen muestras válidas."
            }

        recognizer = cv2.face.createLBPHFaceRecognizer(
            radius=1,
            neighbors=8,
            grid_x=8,
            grid_y=8
        )

        try:
            recognizer.train(
                images,
                np.array(labels)
            )
        except Exception as exc:
            return {
                "valid": False,
                "people": len(people),
                "samples": len(images),
                "invalid_files": invalid_files,
                "message": "Error durante la validación: {}".format(exc)
            }

        return {
            "valid": True,
            "people": len(people),
            "samples": len(images),
            "people_detail": people,
            "invalid_files": invalid_files,
            "message": "El conjunto de rostros es válido."
        }


def print_validation_report(result):
    print("")
    print("=" * 55)
    print("VALIDACIÓN DEL CONJUNTO DE ROSTROS")
    print("=" * 55)

    print("Estado: {}".format(
        "VÁLIDO" if result["valid"] else "NO VÁLIDO"
    ))

    print("Personas: {}".format(result["people"]))
    print("Muestras válidas: {}".format(result["samples"]))

    if result.get("people_detail"):
        print("")
        print("Detalle:")

        for person in result["people_detail"]:
            print(
                "- {}: {} muestras".format(
                    person["name"],
                    person["samples"]
                )
            )

    invalid_files = result.get("invalid_files", [])

    if invalid_files:
        print("")
        print("Archivos inválidos:")

        for path in invalid_files:
            print("- {}".format(path))

    print("")
    print(result["message"])
    print("=" * 55)
    print("")
