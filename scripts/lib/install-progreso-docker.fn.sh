#!/bin/bash
# Instala el comando progreso_docker y elimina hooks antiguos de login SSH.

install_progreso_docker() {
  local src="${1:-}"
  local dest="/usr/local/bin/progreso_docker"
  local boot_user="${BOOT_USER:-ec2-user}"
  local user_home bp marker="# taller-ec2-bootstrap-login-tail"
  local target_dir="${TARGET_DIR:-/opt/taller_mecanico_asir}"

  rm -f /etc/profile.d/99-taller-ec2-bootstrap-tail.sh

  user_home="$(getent passwd "${boot_user}" | cut -d: -f6)"
  if [[ -n "${user_home}" && -f "${user_home}/.bash_profile" ]]; then
    if grep -qF "${marker}" "${user_home}/.bash_profile" 2>/dev/null; then
      sed -i '\|# taller-ec2-bootstrap-login-tail|,$d' "${user_home}/.bash_profile"
      chown "${boot_user}:${boot_user}" "${user_home}/.bash_profile"
    fi
  fi

  if [[ -z "${src}" || ! -f "${src}" ]]; then
    if [[ -f "${target_dir}/scripts/progreso_docker.sh" ]]; then
      src="${target_dir}/scripts/progreso_docker.sh"
    else
      local here
      here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
      if [[ -f "${here}/../progreso_docker.sh" ]]; then
        src="${here}/../progreso_docker.sh"
      fi
    fi
  fi

  if [[ ! -f "${src}" ]]; then
    cat >"${dest}" <<'PROGRESO_DOCKER'
#!/bin/bash
set -euo pipefail
LOG="${TALLER_BOOTSTRAP_LOG:-/var/log/taller-ec2-bootstrap.log}"
echo "=== progreso_docker — bootstrap / deploy (Ctrl+C para salir) ==="
echo "Log: ${LOG}"
echo ""
if command -v docker >/dev/null 2>&1; then
  echo "--- Contenedores (docker ps -a) ---"
  docker ps -a 2>/dev/null || sudo docker ps -a 2>/dev/null || true
  echo ""
fi
if [[ ! -f "${LOG}" ]]; then
  echo "Aún no existe ${LOG}."
  [[ -f /var/log/cloud-init-output.log ]] && tail -n 40 -f /var/log/cloud-init-output.log
  exit 1
fi
if [[ ! -r "${LOG}" ]]; then sudo tail -n 60 -f "${LOG}"; else tail -n 60 -f "${LOG}"; fi
PROGRESO_DOCKER
    chmod 0755 "${dest}"
  else
    install -m 0755 "${src}" "${dest}"
  fi
  chmod 644 /var/log/taller-ec2-bootstrap.log 2>/dev/null || true
}
