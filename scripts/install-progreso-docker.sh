#!/bin/bash
# Instala el comando progreso_docker en /usr/local/bin (EC2).
# Uso: sudo bash scripts/install-progreso-docker.sh
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "ERROR: ejecuta con sudo o como root." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/install-progreso-docker.fn.sh
source "${SCRIPT_DIR}/lib/install-progreso-docker.fn.sh"

export BOOT_USER="${BOOT_USER:-ec2-user}"
export TARGET_DIR="${TARGET_DIR:-/opt/taller_mecanico_asir}"

install_progreso_docker "${SCRIPT_DIR}/progreso_docker.sh"

echo "OK: comando instalado → progreso_docker"
echo "Uso: progreso_docker"
