#!/usr/bin/env python3
from __future__ import print_function

import os
import re
import shutil


SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")


def validate_person_name(name):
    """
    Valida y normaliza el nombre de una persona.

    Se permiten:
    - letras
    - números
    - espacios
    - guion
    - guion bajo
    - caracteres acentuados
    """
    if name is None:
        raise ValueError("El nombre no puede estar vacío.")

    name = name.strip()

    if not name:
        raise ValueError("El nombre no puede estar vacío.")

    if "/" in name or "\\" in name:
        raise ValueError("El nombre no puede contener '/' ni '\\'.")

    if name in (".", ".."):
        raise ValueError("Nombre no válido.")

    if not re.match(r"^[\wÀ-ÿ .-]+$", name, re.UNICODE):
        raise ValueError(
            "El nombre contiene caracteres no permitidos."
        )

    return name


def get_person_dir(faces_dir, name):
    """
    Devuelve la carpeta correspondiente a una persona.
    """
    safe_name = validate_person_name(name)
    return os.path.join(faces_dir, safe_name)


def ensure_person_dir(faces_dir, name):
    """
    Crea la carpeta de la persona si todavía no existe.
    """
    person_dir = get_person_dir(faces_dir, name)

    if not os.path.isdir(person_dir):
        os.makedirs(person_dir)

    return person_dir


def image_files(directory):
    """
    Devuelve una lista ordenada de imágenes válidas.
    """
    if not os.path.isdir(directory):
        return []

    files = []

    for filename in os.listdir(directory):
        path = os.path.join(directory, filename)

        if not os.path.isfile(path):
            continue

        if filename.lower().endswith(SUPPORTED_EXTENSIONS):
            files.append(path)

    return sorted(files)


def count_person_samples(faces_dir, name):
    """
    Cuenta las muestras de una persona.
    """
    person_dir = get_person_dir(faces_dir, name)
    return len(image_files(person_dir))


def list_people(faces_dir):
    """
    Lista las personas registradas y el número de muestras.
    """
    people = []

    if not os.path.isdir(faces_dir):
        return people

    for name in sorted(os.listdir(faces_dir)):
        path = os.path.join(faces_dir, name)

        if not os.path.isdir(path):
            continue

        count = len(image_files(path))

        people.append({
            "name": name,
            "samples": count,
            "path": path
        })

    return people


def next_sample_number(person_dir):
    """
    Obtiene el siguiente número disponible para guardar una muestra.

    Ejemplo:
        0001.jpg
        0002.jpg
        0003.jpg
    """
    maximum = 0

    for path in image_files(person_dir):
        filename = os.path.basename(path)
        stem = os.path.splitext(filename)[0]

        try:
            number = int(stem)
        except ValueError:
            continue

        maximum = max(maximum, number)

    return maximum + 1


def delete_person(faces_dir, name):
    """
    Elimina completamente la carpeta de una persona.
    """
    person_dir = get_person_dir(faces_dir, name)

    if not os.path.isdir(person_dir):
        raise ValueError(
            "La persona '{}' no está registrada.".format(name)
        )

    shutil.rmtree(person_dir)

    return person_dir
