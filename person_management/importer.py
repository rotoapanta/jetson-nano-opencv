#!/usr/bin/env python3
from __future__ import print_function

import os

import cv2

from config import settings
from face_detector import FaceDetector
from person_management.repository import (
    SUPPORTED_EXTENSIONS,
    ensure_person_dir,
    image_files,
    next_sample_number,
    validate_person_name,
)


class FaceImporter(object):
    """
    Importa muestras faciales desde una carpeta de fotografías.
    """

    def __init__(self):
        self.detector = FaceDetector(
            settings.haar_model,
            settings.detection_scale_factor,
            settings.detection_min_neighbors,
            settings.detection_min_size
        )

    def import_directory(self, name, input_dir, limit=None):
        """
        Importa fotografías desde input_dir.

        Parámetros:
            name:
                Nombre de la persona.

            input_dir:
                Carpeta que contiene las fotografías.

            limit:
                Número máximo de muestras válidas a importar.
                Si es None, procesa todas las imágenes.
        """
        name = validate_person_name(name)
        input_dir = os.path.abspath(os.path.expanduser(input_dir))

        if not os.path.isdir(input_dir):
            raise ValueError(
                "La carpeta de entrada no existe: {}".format(input_dir)
            )

        source_files = image_files(input_dir)

        if not source_files:
            raise ValueError(
                "No se encontraron imágenes compatibles en: {}".format(
                    input_dir
                )
            )

        output_dir = ensure_person_dir(settings.faces_dir, name)
        sample_number = next_sample_number(output_dir)

        summary = {
            "person": name,
            "input_dir": input_dir,
            "output_dir": output_dir,
            "found": len(source_files),
            "processed": 0,
            "saved": 0,
            "without_face": 0,
            "invalid": 0,
            "errors": []
        }

        print("")
        print("Persona: {}".format(name))
        print("Carpeta de entrada: {}".format(input_dir))
        print("Imágenes encontradas: {}".format(len(source_files)))
        print("Destino: {}".format(output_dir))
        print("")

        for source_path in source_files:
            if limit is not None and summary["saved"] >= limit:
                break

            summary["processed"] += 1

            image = cv2.imread(source_path)

            if image is None:
                summary["invalid"] += 1
                summary["errors"].append(
                    "No se pudo leer: {}".format(source_path)
                )
                print("[DESCARTADA] No se pudo leer: {}".format(source_path))
                continue

            try:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                faces = sorted(
                    self.detector.detect(gray),
                    key=lambda item: int(item[2]) * int(item[3]),
                    reverse=True
                )

                if not faces:
                    summary["without_face"] += 1
                    print(
                        "[SIN ROSTRO] {}".format(
                            os.path.basename(source_path)
                        )
                    )
                    continue

                x, y, w, h = faces[0]

                crop = gray[y:y + h, x:x + w]

                if crop is None or crop.size == 0:
                    summary["invalid"] += 1
                    print(
                        "[DESCARTADA] Recorte vacío: {}".format(
                            os.path.basename(source_path)
                        )
                    )
                    continue

                filename = "{:04d}.jpg".format(sample_number)
                destination = os.path.join(output_dir, filename)

                if not cv2.imwrite(destination, crop):
                    summary["invalid"] += 1
                    summary["errors"].append(
                        "No se pudo guardar: {}".format(destination)
                    )
                    print("[ERROR] No se pudo guardar: {}".format(destination))
                    continue

                summary["saved"] += 1
                sample_number += 1

                print(
                    "[GUARDADA] {}/{} - {}".format(
                        summary["saved"],
                        limit if limit is not None else len(source_files),
                        destination
                    )
                )

            except Exception as exc:
                summary["invalid"] += 1
                summary["errors"].append(
                    "{}: {}".format(source_path, exc)
                )
                print(
                    "[ERROR] {}: {}".format(
                        os.path.basename(source_path),
                        exc
                    )
                )

        return summary


def print_summary(summary):
    """
    Muestra el resumen de la importación.
    """
    print("")
    print("=" * 55)
    print("RESUMEN DE IMPORTACIÓN")
    print("=" * 55)
    print("Persona:              {}".format(summary["person"]))
    print("Imágenes encontradas: {}".format(summary["found"]))
    print("Imágenes procesadas:  {}".format(summary["processed"]))
    print("Muestras guardadas:   {}".format(summary["saved"]))
    print("Sin rostro detectado: {}".format(summary["without_face"]))
    print("Imágenes inválidas:   {}".format(summary["invalid"]))
    print("Carpeta de destino:   {}".format(summary["output_dir"]))
    print("=" * 55)
    print("")

    if summary["saved"] == 0:
        print("No se agregó ninguna muestra válida.")
    else:
        print(
            "Las muestras fueron agregadas correctamente para '{}'."
            .format(summary["person"])
        )
        print(
            "Reinicie jetson-vision para cargar la nueva información."
        )
