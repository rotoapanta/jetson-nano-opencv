#!/usr/bin/env bash
set -Eeuo pipefail

SERVICE_NAME="jetson-vision.service"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}"

info() {
    printf '[INFO] %s\n' "$1"
}

ok() {
    printf '[OK] %s\n' "$1"
}

warn() {
    printf '[WARN] %s\n' "$1"
}

error_exit() {
    printf '[ERROR] %s\n' "$1" >&2
    exit 1
}

trap 'error_exit "La desinstalación falló en la línea ${LINENO}."' ERR

if [[ "${EUID}" -eq 0 ]]; then
    SUDO=""
else
    command -v sudo >/dev/null 2>&1 \
        || error_exit "sudo no está instalado o no está disponible."
    SUDO="sudo"
fi

command -v systemctl >/dev/null 2>&1 \
    || error_exit "systemctl no está disponible en este sistema."

info "Iniciando desinstalación del servicio ${SERVICE_NAME}..."

if systemctl list-unit-files --type=service \
    | grep -q "^${SERVICE_NAME}[[:space:]]"; then

    if systemctl is-active --quiet "${SERVICE_NAME}"; then
        info "Deteniendo ${SERVICE_NAME}..."
        ${SUDO} systemctl stop "${SERVICE_NAME}"
        ok "Servicio detenido."
    else
        warn "El servicio no está activo."
    fi

    if systemctl is-enabled --quiet "${SERVICE_NAME}" 2>/dev/null; then
        info "Deshabilitando inicio automático..."
        ${SUDO} systemctl disable "${SERVICE_NAME}"
        ok "Inicio automático deshabilitado."
    else
        warn "El servicio ya estaba deshabilitado."
    fi
else
    warn "El servicio ${SERVICE_NAME} no está registrado."
fi

if [[ -e "${SERVICE_FILE}" || -L "${SERVICE_FILE}" ]]; then
    info "Eliminando ${SERVICE_FILE}..."
    ${SUDO} rm -f "${SERVICE_FILE}"
    ok "Archivo del servicio eliminado."
else
    warn "El archivo ${SERVICE_FILE} no existe."
fi

info "Recargando systemd..."
${SUDO} systemctl daemon-reload
${SUDO} systemctl reset-failed "${SERVICE_NAME}" 2>/dev/null || true

if systemctl list-unit-files --type=service \
    | grep -q "^${SERVICE_NAME}[[:space:]]"; then
    error_exit "El servicio todavía aparece registrado en systemd."
fi

printf '\n'
ok "Desinstalación completada."
printf 'El servicio fue eliminado.\n'
printf 'El proyecto, el entorno virtual, la configuración y los datos se conservaron.\n'
