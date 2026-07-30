<p align="right"><a href="README.md">English</a></p>

# <p align="center">Jetson Nano OpenCV – Sistema de reconocimiento facial</p>

<p align="center">
    <a href="https://developer.nvidia.com/embedded/jetson-nano-developer-kit"><img src="https://img.shields.io/badge/NVIDIA-Jetson%20Nano-76B900?logo=nvidia" alt="NVIDIA Jetson Nano"></a>
    <a href="https://developer.nvidia.com/embedded/jetpack"><img src="https://img.shields.io/badge/JetPack-4.6.6-76B900" alt="JetPack"></a>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.6-3776AB?logo=python&logoColor=white" alt="Python"></a>
    <a href="https://opencv.org/"><img src="https://img.shields.io/badge/OpenCV-3.2.0-5C3EE8?logo=opencv&logoColor=white" alt="OpenCV"></a>
    <a href="https://github.com/rotoapanta/jetson-nano-opencv/issues"><img src="https://img.shields.io/github/issues/rotoapanta/jetson-nano-opencv" alt="Incidencias de GitHub"></a>
    <a href="https://github.com/rotoapanta/jetson-nano-opencv"><img src="https://img.shields.io/github/repo-size/rotoapanta/jetson-nano-opencv" alt="Tamaño del repositorio"></a>
    <a href="https://github.com/rotoapanta/jetson-nano-opencv/commits"><img src="https://img.shields.io/github/last-commit/rotoapanta/jetson-nano-opencv" alt="Último commit"></a>
    <a href="https://www.linux.org/"><img src="https://img.shields.io/badge/Plataforma-Linux-orange" alt="Linux"></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/Licencia-MIT-blue.svg" alt="Licencia MIT"></a>
    <a href="https://www.linkedin.com/in/roberto-carlos-toapanta-g/"><img src="https://img.shields.io/badge/Autor-Roberto%20Toapanta-brightgreen" alt="Autor"></a>
    <a href="#-registro-de-cambios"><img src="https://img.shields.io/badge/Versión-1.0.0-brightgreen" alt="Versión"></a>
    <a href="https://github.com/rotoapanta/jetson-nano-opencv/fork"><img src="https://img.shields.io/github/forks/rotoapanta/jetson-nano-opencv?style=social" alt="Forks de GitHub"></a>
</p>

Sistema de visión artificial para NVIDIA Jetson Nano que captura video mediante una cámara CSI, detecta rostros, realiza reconocimiento facial local con OpenCV LBPH, almacena eventos de reconocimiento y permite el monitoreo y la administración remota mediante Telegram.

El proyecto está diseñado para funcionar continuamente como un servicio Linux `systemd` y mantener fuera del control de versiones la información sensible, los rostros capturados, las imágenes de eventos, los registros y el entorno virtual de Python.

---

## ✨ Características

- **Compatibilidad con cámara CSI:** Captura de video optimizada para la interfaz de cámara de la Jetson Nano.
- **Detección facial:** Localización de rostros en tiempo real dentro del flujo de video.
- **Reconocimiento facial local:** Reconocimiento OpenCV LBPH a partir de imágenes almacenadas en `data/faces/`.
- **Entrenamiento en memoria:** El reconocedor reconstruye el modelo desde el conjunto de rostros cada vez que inicia la aplicación.
- **Gestión de personas:** Captura, importación, registro y administración de personas reconocidas.
- **Registro de eventos:** Guarda localmente los eventos de reconocimiento en `data/events/`.
- **Integración con Telegram:** Comandos remotos, notificaciones, control de acceso y monitoreo del sistema.
- **Transmisión de video:** Servidor de streaming integrado para visualización remota.
- **Funcionamiento continuo:** Ejecución automática mediante `systemd`, con reinicio después de fallos o reinicios del equipo.
- **Comprobaciones de estado:** Incluye scripts para probar la cámara y verificar el servicio.
- **Configuración mediante variables de entorno:** Los valores sensibles se guardan en `.env`, mientras `.env.example` documenta las variables necesarias.
- **Repositorio orientado a la privacidad:** Rostros, eventos, registros, secretos y entorno virtual se excluyen mediante `.gitignore`.

---

## 🛠️ Requisitos del sistema

| Componente | Versión / Requisito |
|------------|---------------------|
| Hardware | NVIDIA Jetson Nano Production Module P3448-0002 |
| Tarjeta portadora | Tarjeta compatible con Jetson Nano |
| Sistema operativo | Ubuntu 18.04 |
| JetPack | 4.6.6 |
| Python | 3.6 |
| OpenCV | 3.2.0 |
| Cámara | Cámara CSI compatible |
| Red | Acceso a Internet requerido para Telegram |
| Gestor de servicios | `systemd` |

---

## 🗂️ Estructura del proyecto

```text
jetson-nano-opencv/
├── data/
│   ├── events/
│   │   └── .gitkeep
│   └── faces/
│       └── .gitkeep
├── models/
│   └── .gitkeep
├── person_management/
│   ├── __init__.py
│   ├── capture.py
│   ├── importer.py
│   ├── manager.py
│   ├── repository.py
│   └── trainer.py
├── scripts/
│   ├── healthcheck.sh
│   └── test_camera.py
├── systemd/
│   └── jetson-vision.service
├── telegram_management/
│   ├── __init__.py
│   ├── access.py
│   ├── commands.py
│   ├── helpers.py
│   ├── manager.py
│   ├── monitor.py
│   ├── notifier.py
│   └── reboot.py
├── .env.example
├── .gitignore
├── README.md
├── README.es.md
├── camera.py
├── collect_faces.py
├── config.py
├── event_manager.py
├── face_detector.py
├── install.sh
├── logger.py
├── main.py
├── recognizer.py
├── requirements.txt
├── stream_server.py
├── telegram_notifier.py
└── uninstall.sh
```

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone git@github.com:rotoapanta/jetson-nano-opencv.git
cd jetson-nano-opencv
```

### 2. Ejecutar el instalador

```bash
chmod +x install.sh
./install.sh
```

### 3. Configurar las variables de entorno

```bash
cp .env.example .env
nano .env
```

Ingresa la configuración local y las credenciales de Telegram. Nunca agregues el archivo `.env` al repositorio.

---

## ⚙️ Configuración

El proyecto obtiene su configuración de ejecución desde `.env`.

Los parámetros habituales incluyen:

- Parámetros de la cámara.
- Umbrales de reconocimiento.
- Token del bot de Telegram.
- Usuarios o chats autorizados en Telegram.
- Rutas de almacenamiento de eventos.
- Opciones del servidor de streaming.
- Parámetros de registro.

Usa `.env.example` como plantilla de referencia y conserva todos los secretos únicamente en `.env`.

---

## 👤 Registro de rostros

```bash
source jetson-nano-opencv-env/bin/activate
python3 collect_faces.py
```

Las imágenes capturadas se almacenan en `data/faces/`. El modelo de reconocimiento se entrena en memoria cuando inicia la aplicación; la implementación actual no requiere un modelo `.yml` persistente.

---

## ▶️ Ejecución de la aplicación

### Ejecución manual

```bash
source jetson-nano-opencv-env/bin/activate
python3 main.py
```

### Ejecución como servicio del sistema

```bash
sudo systemctl daemon-reload
sudo systemctl enable jetson-vision
sudo systemctl start jetson-vision
```

Comprobar el servicio:

```bash
systemctl status jetson-vision
```

Seguir los registros:

```bash
journalctl -u jetson-vision -f
```

---

## ✅ Verificación del sistema

### Probar la cámara

```bash
source jetson-nano-opencv-env/bin/activate
python3 scripts/test_camera.py
```

### Ejecutar la comprobación de estado

```bash
chmod +x scripts/healthcheck.sh
./scripts/healthcheck.sh
```

### Verificar el entorno activo de Python

```bash
echo "$VIRTUAL_ENV"
which python3
python3 --version
python3 -c "import cv2; print(cv2.__version__)"
```

Entorno esperado:

```text
Python 3.6
OpenCV 3.2.0
```

---

## 🤖 Integración con Telegram

El subsistema de Telegram está organizado dentro de `telegram_management/` e incluye control de acceso, procesamiento de comandos, notificaciones, monitoreo, reinicio remoto y utilidades compartidas.

Las credenciales de Telegram y los identificadores autorizados deben configurarse en `.env`.

---

## 🔒 Privacidad y seguridad

El repositorio excluye:

```text
.env
jetson-nano-opencv-env/
logs/
data/faces/*
data/events/*
```

Dentro de los directorios de rostros y eventos únicamente se versionan los archivos `.gitkeep`.

No publiques tokens de bots de Telegram, claves SSH privadas, fotografías personales de rostros, imágenes de eventos de reconocimiento, credenciales de producción ni información privada de red.

---

## 🧰 Administración del servicio

```bash
sudo systemctl start jetson-vision
sudo systemctl stop jetson-vision
sudo systemctl restart jetson-vision
sudo systemctl enable jetson-vision
sudo systemctl disable jetson-vision
```

---

## 🗑️ Desinstalación

```bash
chmod +x uninstall.sh
./uninstall.sh
```

Revisa el script antes de ejecutarlo en una instalación de producción.

---

## 💬 Comentarios

Para comentarios o sugerencias: robertocarlos.toapanta@gmail.com

## 🛟 Soporte

Para soporte, escribe a robertocarlos.toapanta@gmail.com

## 📄 Licencia

[MIT](https://opensource.org/licenses/MIT)

## 👥 Autores

- [@rotoapanta](https://github.com/rotoapanta)

---

## 📜 Registro de cambios

Este proyecto sigue [Keep a Changelog](https://keepachangelog.com/es-ES/) y [Versionado Semántico](https://semver.org/lang/es/).

### [Sin publicar]

- Mejoras en la documentación del proyecto.
- Futuras mejoras de cámara, reconocimiento y Telegram.

### 1.0.0 – 2026-07-30

- Primera versión estable.
- Adquisición de video mediante cámara CSI.
- Detección facial y reconocimiento LBPH con OpenCV.
- Entrenamiento del modelo en memoria desde `data/faces/`.
- Herramientas para captura, importación y administración de personas.
- Almacenamiento de eventos de reconocimiento.
- Comandos, notificaciones y control de acceso mediante Telegram.
- Servidor de streaming integrado.
- Ejecución automática mediante `systemd`.
- Scripts de instalación, desinstalación, prueba de cámara y comprobación de estado.
- Exclusión de archivos sensibles, fotografías de rostros, imágenes de eventos, registros y entorno virtual.

---

## 🔗 Enlaces

[![linkedin](https://img.shields.io/badge/linkedin-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/roberto-carlos-toapanta-g/)

[![twitter](https://img.shields.io/badge/twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/rotoapanta)
