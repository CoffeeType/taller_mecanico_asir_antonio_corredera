#!/bin/bash
# Ver en vivo el progreso del bootstrap/despliegue Docker en EC2.
# Instalado como /usr/local/bin/progreso_docker

set -euo pipefail

LOG="${TALLER_BOOTSTRAP_LOG:-/var/log/taller-ec2-bootstrap.log}"
TARGET="${TALLER_DEPLOY_DIR:-/opt/taller_mecanico_asir}"

echo "=== progreso_docker — bootstrap / deploy (Ctrl+C para salir) ==="
echo "Log: ${LOG}"
echo ""

if command -v docker >/dev/null 2>&1; then
  echo "--- Contenedores (docker ps -a) ---"
  docker ps -a 2>/dev/null || sudo docker ps -a 2>/dev/null || true
  echo ""
fi

if [[ ! -f "${LOG}" ]]; then
  echo "Aún no existe ${LOG} (¿arranque reciente o bootstrap no iniciado?)."
  if [[ -f /var/log/cloud-init-output.log ]]; then
    echo "Mostrando cloud-init-output.log:"
    tail -n 40 -f /var/log/cloud-init-output.log
  fi
  exit 1
fi

if [[ ! -r "${LOG}" ]]; then
  sudo tail -n 60 -f "${LOG}"
else
  tail -n 60 -f "${LOG}"
fi
