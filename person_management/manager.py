#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import os
import subprocess
import sys

from config import settings

from person_management.importer import (
    FaceImporter,
    print_summary,
)

from person_management.repository import (
    count_person_samples,
    delete_person,
    list_people,
    validate_person_name,
)

from person_management.trainer import (
    DatasetValidator,
    print_validation_report,
)


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)


def build_parser():
    """
    Construye el administrador de comandos.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Administrador de personas "
            "- Jetson Nano OpenCV V2"
        )
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Operación que se desea realizar"
    )

    # --------------------------------------------------
    # list
    # --------------------------------------------------
    subparsers.add_parser(
        "list",
        help="Lista las personas registradas"
    )

    # --------------------------------------------------
    # capture
    # --------------------------------------------------
    capture_parser = subparsers.add_parser(
        "capture",
        help="Registra una persona utilizando la cámara"
    )

    capture_parser.add_argument(
        "--name",
        required=True,
        help="Nombre de la persona"
    )

    capture_parser.add_argument(
        "--samples",
        type=int,
        default=30,
        help="Número de muestras que se capturarán"
    )

    capture_parser.add_argument(
        "--interval",
        type=float,
        default=0.25,
        help="Intervalo entre capturas, en segundos"
    )

    # --------------------------------------------------
    # import
    # --------------------------------------------------
    import_parser = subparsers.add_parser(
        "import",
        help="Importa fotografías existentes"
    )

    import_parser.add_argument(
        "--name",
        required=True,
        help="Nombre de la persona"
    )

    import_parser.add_argument(
        "--input",
        required=True,
        help="Carpeta que contiene las fotografías"
    )

    import_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Número máximo de muestras válidas a importar"
    )

    # --------------------------------------------------
    # delete
    # --------------------------------------------------
    delete_parser = subparsers.add_parser(
        "delete",
        help="Elimina una persona registrada"
    )

    delete_parser.add_argument(
        "--name",
        required=True,
        help="Nombre de la persona"
    )

    delete_parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirma la eliminación sin preguntar"
    )

    # --------------------------------------------------
    # validate
    # --------------------------------------------------
    subparsers.add_parser(
        "validate",
        help=(
            "Valida las imágenes y realiza una prueba "
            "de entrenamiento LBPH en memoria"
        )
    )

    return parser


def command_list():
    """
    Lista las personas registradas en data/faces.
    """
    people = list_people(settings.faces_dir)

    print("")
    print("=" * 60)
    print("PERSONAS REGISTRADAS")
    print("=" * 60)

    if not people:
        print("No existen personas registradas.")
        print("=" * 60)
        print("")
        return 0

    total_samples = 0

    for index, person in enumerate(people, start=1):
        total_samples += person["samples"]

        print(
            "{:>2}. {:<35} {:>4} muestras".format(
                index,
                person["name"],
                person["samples"]
            )
        )

    print("-" * 60)
    print("Personas registradas: {}".format(len(people)))
    print("Muestras totales:     {}".format(total_samples))
    print("=" * 60)
    print("")

    return 0


def command_capture(args):
    """
    Ejecuta collect_faces.py para capturar muestras
    mediante la cámara CSI.
    """
    name = validate_person_name(args.name)

    if args.samples <= 0:
        raise ValueError(
            "--samples debe ser mayor que cero."
        )

    if args.interval < 0:
        raise ValueError(
            "--interval no puede ser negativo."
        )

    collect_script = os.path.join(
        PROJECT_ROOT,
        "collect_faces.py"
    )

    if not os.path.isfile(collect_script):
        raise RuntimeError(
            "No se encontró collect_faces.py en: {}".format(
                collect_script
            )
        )

    print("")
    print("=" * 60)
    print("CAPTURA DE ROSTROS")
    print("=" * 60)
    print("Persona:   {}".format(name))
    print("Muestras:  {}".format(args.samples))
    print("Intervalo: {} segundos".format(args.interval))
    print("")
    print(
        "IMPORTANTE: el servicio jetson-vision debe estar detenido."
    )
    print("")
    print("Comando para detenerlo:")
    print("  sudo systemctl stop jetson-vision")
    print("")

    response = input(
        "¿El servicio está detenido y desea continuar? [s/N]: "
    ).strip().lower()

    valid_responses = (
        "s",
        "si",
        "sí",
        "y",
        "yes"
    )

    if response not in valid_responses:
        print("")
        print("Captura cancelada.")
        print("")
        return 1

    command = [
        sys.executable,
        collect_script,
        "--name",
        name,
        "--samples",
        str(args.samples),
        "--interval",
        str(args.interval)
    ]

    print("")
    print("Iniciando captura...")
    print("")

    result = subprocess.call(
        command,
        cwd=PROJECT_ROOT
    )

    if result != 0:
        print("")
        print("La captura terminó con errores.")
        print("")
        return result

    samples = count_person_samples(
        settings.faces_dir,
        name
    )

    print("")
    print("=" * 60)
    print("CAPTURA FINALIZADA")
    print("=" * 60)
    print("Persona: {}".format(name))
    print("Muestras disponibles: {}".format(samples))
    print("")
    print("Para iniciar nuevamente el sistema:")
    print("  sudo systemctl start jetson-vision")
    print("=" * 60)
    print("")

    return 0


def command_import(args):
    """
    Importa imágenes desde una carpeta.
    """
    name = validate_person_name(args.name)

    if args.limit is not None and args.limit <= 0:
        raise ValueError(
            "--limit debe ser mayor que cero."
        )

    importer = FaceImporter()

    summary = importer.import_directory(
        name=name,
        input_dir=args.input,
        limit=args.limit
    )

    print_summary(summary)

    if summary["saved"] == 0:
        return 1

    print("")
    print("Para cargar las nuevas muestras ejecute:")
    print("  sudo systemctl restart jetson-vision")
    print("")

    return 0


def command_delete(args):
    """
    Elimina una persona y todas sus muestras.
    """
    name = validate_person_name(args.name)

    person_path = os.path.join(
        settings.faces_dir,
        name
    )

    if not os.path.isdir(person_path):
        raise ValueError(
            "La persona '{}' no está registrada.".format(
                name
            )
        )

    samples = count_person_samples(
        settings.faces_dir,
        name
    )

    print("")
    print("=" * 60)
    print("ELIMINAR PERSONA")
    print("=" * 60)
    print("Persona:  {}".format(name))
    print("Muestras: {}".format(samples))
    print("")
    print(
        "ADVERTENCIA: se eliminará completamente "
        "la carpeta de esta persona."
    )
    print("")

    confirmed = args.yes

    if not confirmed:
        response = input(
            "Escriba ELIMINAR para confirmar: "
        ).strip()

        confirmed = response == "ELIMINAR"

    if not confirmed:
        print("")
        print("Eliminación cancelada.")
        print("")
        return 1

    deleted_path = delete_person(
        settings.faces_dir,
        name
    )

    print("")
    print("=" * 60)
    print("PERSONA ELIMINADA")
    print("=" * 60)
    print("Persona: {}".format(name))
    print("Carpeta eliminada: {}".format(deleted_path))
    print("")
    print("Para actualizar el reconocimiento ejecute:")
    print("  sudo systemctl restart jetson-vision")
    print("=" * 60)
    print("")

    return 0


def command_validate():
    """
    Valida las imágenes y realiza un entrenamiento
    LBPH de prueba en memoria.
    """
    validator = DatasetValidator()

    result = validator.validate()

    print_validation_report(result)

    if result["valid"]:
        return 0

    return 1


def main():
    """
    Punto de entrada principal.
    """
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == "list":
            return command_list()

        if args.command == "capture":
            return command_capture(args)

        if args.command == "import":
            return command_import(args)

        if args.command == "delete":
            return command_delete(args)

        if args.command == "validate":
            return command_validate()

        parser.print_help()
        return 1

    except KeyboardInterrupt:
        print("")
        print("Operación cancelada por el usuario.")
        print("")
        return 130

    except Exception as exc:
        print("")
        print("=" * 60)
        print("ERROR")
        print("=" * 60)
        print(str(exc))
        print("=" * 60)
        print("")
        return 1


if __name__ == "__main__":
    sys.exit(main())
