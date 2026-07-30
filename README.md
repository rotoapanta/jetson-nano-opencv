<p align="right"><a href="README.es.md">Español</a></p>

# <p align="center">Jetson Nano OpenCV – Face Recognition System</p>

<p align="center">
    <a href="https://developer.nvidia.com/embedded/jetson-nano-developer-kit"><img src="https://img.shields.io/badge/NVIDIA-Jetson%20Nano-76B900?logo=nvidia" alt="NVIDIA Jetson Nano"></a>
    <a href="https://developer.nvidia.com/embedded/jetpack"><img src="https://img.shields.io/badge/JetPack-4.6.6-76B900" alt="JetPack"></a>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.6-3776AB?logo=python&logoColor=white" alt="Python"></a>
    <a href="https://opencv.org/"><img src="https://img.shields.io/badge/OpenCV-3.2.0-5C3EE8?logo=opencv&logoColor=white" alt="OpenCV"></a>
    <a href="https://github.com/rotoapanta/jetson-nano-opencv/issues"><img src="https://img.shields.io/github/issues/rotoapanta/jetson-nano-opencv" alt="GitHub issues"></a>
    <a href="https://github.com/rotoapanta/jetson-nano-opencv"><img src="https://img.shields.io/github/repo-size/rotoapanta/jetson-nano-opencv" alt="GitHub repo size"></a>
    <a href="https://github.com/rotoapanta/jetson-nano-opencv/commits"><img src="https://img.shields.io/github/last-commit/rotoapanta/jetson-nano-opencv" alt="GitHub last commit"></a>
    <a href="https://www.linux.org/"><img src="https://img.shields.io/badge/Platform-Linux-orange" alt="Linux"></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
    <a href="https://www.linkedin.com/in/roberto-carlos-toapanta-g/"><img src="https://img.shields.io/badge/Author-Roberto%20Toapanta-brightgreen" alt="Author"></a>
    <a href="#-changelog"><img src="https://img.shields.io/badge/Version-1.0.0-brightgreen" alt="Version"></a>
    <a href="https://github.com/rotoapanta/jetson-nano-opencv/fork"><img src="https://img.shields.io/github/forks/rotoapanta/jetson-nano-opencv?style=social" alt="GitHub forks"></a>
</p>

A computer vision system for NVIDIA Jetson Nano that captures video from a CSI camera, detects faces, performs local face recognition with OpenCV LBPH, stores recognition events and provides remote monitoring and management through Telegram.

The project is designed to run continuously as a Linux `systemd` service and keeps sensitive information, captured faces, event images, logs and the Python virtual environment outside version control.

---

## ✨ Features

- **CSI camera support:** Video capture optimized for the Jetson Nano camera interface.
- **Face detection:** Real-time face localization from the camera stream.
- **Local face recognition:** OpenCV LBPH recognition using images stored in `data/faces/`.
- **In-memory training:** The recognizer rebuilds its model from the face dataset when the application starts.
- **Person management:** Capture, import, register and manage recognized people.
- **Event recording:** Saves recognition events locally in `data/events/`.
- **Telegram integration:** Remote commands, notifications, access control and system monitoring.
- **Video streaming:** Integrated stream server for remote visualization.
- **Continuous operation:** Runs automatically through `systemd` and restarts after failures or reboots.
- **Health checks:** Includes scripts for camera testing and service verification.
- **Environment-based configuration:** Sensitive values are stored in `.env`, while `.env.example` documents the required variables.
- **Privacy-aware repository:** Faces, events, logs, secrets and the virtual environment are excluded through `.gitignore`.

---

## 🛠️ System Requirements

| Component | Version / Requirement |
|-----------|------------------------|
| Hardware | NVIDIA Jetson Nano Production Module P3448-0002 |
| Carrier board | Compatible Jetson Nano carrier board |
| Operating system | Ubuntu 18.04 |
| JetPack | 4.6.6 |
| Python | 3.6 |
| OpenCV | 3.2.0 |
| Camera | Compatible CSI camera |
| Network | Internet access required for Telegram |
| Service manager | `systemd` |

---

## 🗂️ Project Structure

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

## 🚀 Installation

### 1. Clone the repository

```bash
git clone git@github.com:rotoapanta/jetson-nano-opencv.git
cd jetson-nano-opencv
```

### 2. Run the installer

```bash
chmod +x install.sh
./install.sh
```

### 3. Configure environment variables

```bash
cp .env.example .env
nano .env
```

Enter the required local settings and Telegram credentials. Never commit the `.env` file.

---

## ⚙️ Configuration

The project reads its runtime configuration from `.env`.

Typical settings include:

- Camera parameters.
- Recognition thresholds.
- Telegram bot token.
- Authorized Telegram users or chats.
- Event storage paths.
- Stream server options.
- Logging parameters.

Use `.env.example` as the reference template and keep all secrets only in `.env`.

---

## 👤 Registering Faces

```bash
source jetson-nano-opencv-env/bin/activate
python3 collect_faces.py
```

The captured images are stored under `data/faces/`. The recognition model is trained in memory when the application starts; the current implementation does not require a persistent `.yml` model.

---

## ▶️ Running the Application

### Manual execution

```bash
source jetson-nano-opencv-env/bin/activate
python3 main.py
```

### Run as a system service

```bash
sudo systemctl daemon-reload
sudo systemctl enable jetson-vision
sudo systemctl start jetson-vision
```

Check the service:

```bash
systemctl status jetson-vision
```

Follow the logs:

```bash
journalctl -u jetson-vision -f
```

---

## ✅ System Verification

### Test the camera

```bash
source jetson-nano-opencv-env/bin/activate
python3 scripts/test_camera.py
```

### Run the health check

```bash
chmod +x scripts/healthcheck.sh
./scripts/healthcheck.sh
```

### Verify the active Python environment

```bash
echo "$VIRTUAL_ENV"
which python3
python3 --version
python3 -c "import cv2; print(cv2.__version__)"
```

Expected environment:

```text
Python 3.6
OpenCV 3.2.0
```

---

## 🤖 Telegram Integration

The Telegram subsystem is organized under `telegram_management/` and includes access control, command processing, notifications, monitoring, remote reboot actions and shared helper utilities.

Telegram credentials and authorized identifiers must be configured in `.env`.

---

## 🔒 Privacy and Security

The repository excludes:

```text
.env
jetson-nano-opencv-env/
logs/
data/faces/*
data/events/*
```

Only the `.gitkeep` files are tracked inside the face and event directories.

Do not publish Telegram bot tokens, private SSH keys, personal face images, recognition event images, production credentials or private network information.

---

## 🧰 Service Management

```bash
sudo systemctl start jetson-vision
sudo systemctl stop jetson-vision
sudo systemctl restart jetson-vision
sudo systemctl enable jetson-vision
sudo systemctl disable jetson-vision
```

---

## 🗑️ Uninstallation

```bash
chmod +x uninstall.sh
./uninstall.sh
```

Review the script before running it in a production installation.

---

## 💬 Feedback

For comments or suggestions: robertocarlos.toapanta@gmail.com

## 🛟 Support

For support, email robertocarlos.toapanta@gmail.com

## 📄 License

[MIT](https://opensource.org/licenses/MIT)

## 👥 Authors

- [@rotoapanta](https://github.com/rotoapanta)

---

## 📜 Changelog

This project follows [Keep a Changelog](https://keepachangelog.com/) and [Semantic Versioning](https://semver.org/).

### [Unreleased]

- Project documentation improvements.
- Future camera, recognition and Telegram enhancements.

### 1.0.0 – 2026-07-30

- Initial stable release.
- CSI camera acquisition.
- OpenCV face detection and LBPH recognition.
- In-memory model training from `data/faces/`.
- Person capture, import and management tools.
- Recognition event storage.
- Telegram commands, notifications and access control.
- Integrated stream server.
- Automatic execution through `systemd`.
- Installation, uninstallation, camera test and health-check scripts.
- Sensitive files, face images, event images, logs and virtual environment excluded from Git.

---

## 🔗 Links

[![linkedin](https://img.shields.io/badge/linkedin-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/roberto-carlos-toapanta-g/)

[![twitter](https://img.shields.io/badge/twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white)](https://twitter.com/rotoapanta)
