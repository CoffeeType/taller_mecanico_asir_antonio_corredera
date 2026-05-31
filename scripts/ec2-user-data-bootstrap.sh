#!/bin/bash

if ! exec > >(tee /var/log/taller-ec2-bootstrap.log) 2>&1; then
  exec >>/var/log/taller-ec2-bootstrap.log 2>&1
fi
chmod 644 /var/log/taller-ec2-bootstrap.log 2>/dev/null || true
set -euxo pipefail

retry() {
  local max="${1:-5}"
  shift
  local delay="${1:-15}"
  shift
  local i=1
  while [[ "$i" -le "$max" ]]; do
    if "$@"; then
      return 0
    fi
    echo "WARN: attempt ${i}/${max} failed: $* ; sleeping ${delay}s" >&2
    sleep "$delay"
    i=$((i + 1))
  done
  return 1
}

bootstrap_msg() {
  echo ""
  echo "================================================================"
  echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] taller-bootstrap: $*"
  echo "================================================================"
}

ensure_swap() {
  local size_gb="${SWAP_SIZE_GB:-4}"
  local swap_file="${SWAP_FILE:-/swapfile}"
  local desired_bytes current_bytes active

  if [[ "${ENABLE_SWAP:-1}" != "1" ]]; then
    echo "Swap disabled (ENABLE_SWAP=${ENABLE_SWAP})."
    return 0
  fi

  desired_bytes="$((size_gb * 1024 * 1024 * 1024))"
  current_bytes="$(stat -c%s "$swap_file" 2>/dev/null || printf '0')"
  active=0
  if swapon --show=NAME | grep -qx "$swap_file"; then
    active=1
  fi

  if [[ ! -f "$swap_file" || "$current_bytes" -lt "$desired_bytes" ]]; then
    if [[ "$active" == "1" ]]; then
      echo "Resizing active swap ${swap_file} from $((current_bytes / 1024 / 1024))MB to ${size_gb}G."
      swapoff "$swap_file"
      active=0
    else
      echo "Creating ${size_gb}G swap at ${swap_file} to avoid OOM during Docker bootstrap."
    fi
    fallocate -l "${size_gb}G" "$swap_file" || dd if=/dev/zero of="$swap_file" bs=1M count="$((size_gb * 1024))"
    chmod 600 "$swap_file"
    mkswap "$swap_file"
  else
    echo "Swap file ${swap_file} already sized at $((current_bytes / 1024 / 1024))MB."
  fi

  if ! swapon --show=NAME | grep -qx "$swap_file"; then
    swapon "$swap_file"
  fi

  if ! grep -qF "${swap_file} none swap" /etc/fstab; then
    echo "${swap_file} none swap sw 0 0" >> /etc/fstab
  fi

  cat >/etc/sysctl.d/99-taller-swap.conf <<'EOF'
vm.swappiness = 10
vm.vfs_cache_pressure = 50
EOF
  sysctl --system >/dev/null || true
  free -h || true
}

normalize_env_defaults() {
  local file="$1"
  local host prometheus_port grafana_port alertmanager_port traffic_ui_port ses_region smtp_smarthost
  raise_env_min_if_lower "$file" MIN_MONITORING_MEM_MB 3200
  raise_env_min_if_lower "$file" MIN_TRAFFIC_STACK_MEM_MB 4200
  set_env_value "$file" MONITORING_UI_HOST_BIND "0.0.0.0"
  set_env_value "$file" EXPORTER_HOST_BIND "127.0.0.1"
  if ! grep -qE '^CADVISOR_IMAGE_TAG=' "$file"; then
    set_env_value "$file" CADVISOR_IMAGE_TAG "0.56.2"
  fi
  if ! grep -qE '^JMETER_VERSION=' "$file"; then
    set_env_value "$file" JMETER_VERSION "5.6.3"
  fi
  if ! grep -qE '^SIM_JMETER_HEAP=' "$file"; then
    set_env_value "$file" SIM_JMETER_HEAP "-Xms128m -Xmx256m -XX:MaxMetaspaceSize=128m"
  fi
  if ! grep -qE '^SIM_JMETER_WORK_DIR=' "$file"; then
    set_env_value "$file" SIM_JMETER_WORK_DIR "/var/www/html/logs/jmeter"
  fi
  if ! grep -qE '^SIM_JMETER_HTML_REPORT=' "$file"; then
    set_env_value "$file" SIM_JMETER_HTML_REPORT "true"
  fi
  host="$(public_browser_host "$file")"
  prometheus_port="$(read_env_value "$file" PROMETHEUS_HOST_PORT || printf '9090')"
  grafana_port="$(read_env_value "$file" GRAFANA_HOST_PORT || printf '3000')"
  alertmanager_port="$(read_env_value "$file" ALERTMANAGER_HOST_PORT || printf '9093')"
  traffic_ui_port="$(read_env_value "$file" TRAFFIC_SIMULATOR_UI_HOST_PORT || printf '8890')"
  web_host_port="$(read_env_value "$file" WEB_HOST_PORT || printf '80')"
  set_env_value "$file" PROMETHEUS_EXTERNAL_URL "http://${host}:${prometheus_port}"
  set_env_value "$file" GRAFANA_EXTERNAL_URL "http://${host}:${grafana_port}"
  set_env_value "$file" ALERTMANAGER_EXTERNAL_URL "http://${host}:${alertmanager_port}"
  set_env_value "$file" TRAFFIC_SIMULATOR_UI_EXTERNAL_URL "http://${host}:${traffic_ui_port}"
  if [[ "$web_host_port" == "80" ]]; then
    set_env_value "$file" SIM_UI_PUBLIC_APP_URL "http://${host}"
  else
    set_env_value "$file" SIM_UI_PUBLIC_APP_URL "http://${host}:${web_host_port}"
  fi
  ses_region="$(read_env_value "$file" SES_SMTP_REGION || true)"
  smtp_smarthost="$(read_env_value "$file" SMTP_SMARTHOST || true)"
  if [[ -z "$smtp_smarthost" && -n "$ses_region" ]]; then
    set_env_value "$file" SMTP_SMARTHOST "email-smtp.${ses_region}.amazonaws.com:587"
  fi
}

authorize_public_ui_ingress() {
  local file="$1"
  local cidr region az mac sg port out profiles ports=()
  command -v aws >/dev/null 2>&1 || { echo "WARN: aws CLI no disponible; no se abre Security Group automaticamente." >&2; return 0; }
  cidr="$(read_env_value "$file" MONITORING_SG_CIDR 2>/dev/null || printf '0.0.0.0/0')"
  profiles="$(read_env_value "$file" COMPOSE_PROFILES 2>/dev/null || true)"
  if [[ "$profiles" == *monitoring* ]]; then
    ports+=("$(read_env_value "$file" GRAFANA_HOST_PORT 2>/dev/null || printf '3000')")
    ports+=("$(read_env_value "$file" PROMETHEUS_HOST_PORT 2>/dev/null || printf '9090')")
    ports+=("$(read_env_value "$file" ALERTMANAGER_HOST_PORT 2>/dev/null || printf '9093')")
  fi
  if [[ "$profiles" == *traffic* ]]; then
    ports+=("$(read_env_value "$file" TRAFFIC_SIMULATOR_UI_HOST_PORT 2>/dev/null || printf '8890')")
  fi
  [[ "${#ports[@]}" -gt 0 ]] || return 0
  az="$(metadata_get placement/availability-zone)"
  [[ -n "$az" ]] || { echo "WARN: no se pudo detectar region EC2; omito Security Group automatico." >&2; return 0; }
  region="${az::-1}"
  mac="$(metadata_get network/interfaces/macs/ | head -1 | tr -d '/')"
  [[ -n "$mac" ]] || { echo "WARN: no se pudo detectar interfaz EC2; omito Security Group automatico." >&2; return 0; }
  for sg in $(metadata_get "network/interfaces/macs/${mac}/security-group-ids"); do
    for port in "${ports[@]}"; do
      [[ -z "$port" ]] && continue
      if out="$(aws ec2 authorize-security-group-ingress --region "$region" --group-id "$sg" --protocol tcp --port "$port" --cidr "$cidr" 2>&1)"; then
        echo "OK: Security Group ${sg} permite tcp/${port} desde ${cidr}"
      elif [[ "$out" == *InvalidPermission.Duplicate* ]]; then
        echo "OK: Security Group ${sg} ya permitia tcp/${port} desde ${cidr}"
      else
        echo "WARN: no pude abrir tcp/${port} en ${sg}: ${out}" >&2
      fi
    done
  done
}

REPO_URL="${REPO_URL:-https://github.com/CoffeeType/taller_mecanico_asir.git}"
GIT_REF="${GIT_REF:-main}"
BOOT_USER="ec2-user"
TARGET_DIR="/opt/taller_mecanico_asir"

BOOTSTRAP_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bootstrap_early_clone_repo() {
  install -d -o "${BOOT_USER}" -g "${BOOT_USER}" "${TARGET_DIR}"
  if [[ -d "${TARGET_DIR}/.git" ]]; then
    echo "OK: repositorio ya presente en ${TARGET_DIR}"
    return 0
  fi
  retry 5 20 runuser -u "${BOOT_USER}" -- git clone --depth 1 --branch "${GIT_REF}" "${REPO_URL}" "${TARGET_DIR}"
}

_source_bootstrap_libs() {
  local loader="" _bl_tmp _bl_base _bl_raw
  for loader in \
    "${BOOTSTRAP_SCRIPT_DIR}/lib/bootstrap-lib-loader.sh" \
    "${TARGET_DIR}/scripts/lib/bootstrap-lib-loader.sh"; do
    if [[ -f "$loader" ]]; then
      source "$loader"
      echo "OK: bootstrap-lib-loader desde ${loader}"
      return 0
    fi
  done
  _bl_tmp="$(mktemp)"
  _bl_base="${REPO_URL%.git}"
  _bl_raw="https://raw.githubusercontent.com/${_bl_base#https://github.com/}/${GIT_REF}/scripts/lib/bootstrap-lib-loader.sh"
  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    if curl -fSsL -H "Authorization: Bearer ${GITHUB_TOKEN}" "$_bl_raw" -o "$_bl_tmp" 2>/dev/null; then
      source "$_bl_tmp"
      rm -f "$_bl_tmp"
      echo "OK: bootstrap-lib-loader via raw.githubusercontent.com (GITHUB_TOKEN)"
      return 0
    fi
  elif curl -fSsL "$_bl_raw" -o "$_bl_tmp" 2>/dev/null; then
    source "$_bl_tmp"
    rm -f "$_bl_tmp"
    echo "OK: bootstrap-lib-loader via raw.githubusercontent.com"
    return 0
  fi
  rm -f "$_bl_tmp"
  echo "ERROR: no se pudo cargar scripts/lib/bootstrap-lib-loader.sh." >&2
  echo "ERROR: Repos privados: exporta GITHUB_TOKEN o REPO_URL=https://<token>@github.com/org/repo.git (git clone en paso 3b)." >&2
  echo "ERROR: Repos publicos: haz push de scripts/lib/ a la rama ${GIT_REF} en GitHub." >&2
  return 1
}

_load_docker_bootstrap_plugins_lib() {
  load_bootstrap_lib "scripts/lib/docker-bootstrap-plugins.sh" || exit 1
}

install_resource_guard() {
  install -m 0755 "${TARGET_DIR}/scripts/taller-docker-safe-mode.sh" /usr/local/sbin/taller-docker-safe-mode

  cat >/etc/systemd/system/taller-docker-safe-mode.service <<EOF
[Unit]
Description=Optional: stop heavy Docker services on low-memory EC2 (only if ALLOW_DEGRADED_STACK=1 in .env)
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
Environment=TALLER_ENV_FILE=${TARGET_DIR}/.env
ExecStart=/usr/local/sbin/taller-docker-safe-mode

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable taller-docker-safe-mode.service
}

DOCKER_COMPOSE_VERSION="${DOCKER_COMPOSE_VERSION:-latest}"
DOCKER_BUILDX_VERSION="${DOCKER_BUILDX_VERSION:-v0.19.3}"

bootstrap_msg "Paso 1/9 - swap y comprobacion de memoria (evita OOM durante pull/build)"
ensure_swap

bootstrap_msg "Paso 2/9 - dnf update (paquetes del sistema; puede tardar varios minutos)"
retry 5 20 dnf update -y

bootstrap_msg "Paso 3/9 - paquetes base (git, httpd, ec2-instance-connect, awscli opcional)"
retry 5 10 dnf install -y ec2-instance-connect git httpd
retry 3 10 dnf install -y awscli || true
systemctl disable --now httpd || true

_source_bootstrap_libs || exit 1
bootstrap_early_clone_repo || true
load_bootstrap_lib "scripts/lib/install-progreso-docker.fn.sh" || exit 1

bootstrap_msg "Paso 4/9 - motor Docker (dnf install docker si falta) y arranque del servicio"
if ! command -v docker >/dev/null 2>&1; then
  retry 5 10 dnf install -y docker
fi

systemctl enable --now docker

sudo usermod -aG docker ec2-user || true
install_progreso_docker

bootstrap_msg "Paso 5/9 - Docker Compose V2 (plugin RPM o binario desde GitHub)"
mkdir -p /usr/libexec/docker/cli-plugins
if ! docker compose version >/dev/null 2>&1; then
  retry 3 10 dnf install -y docker-compose-plugin || true
fi
if ! docker compose version >/dev/null 2>&1; then
  ARCH="$(uname -m)"
  if [[ "${DOCKER_COMPOSE_VERSION}" == "latest" ]]; then
    COMPOSE_URL="https://github.com/docker/compose/releases/latest/download/docker-compose-linux-${ARCH}"
  else
    COMPOSE_URL="https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-linux-${ARCH}"
  fi
  retry 5 15 curl -fSL \
    "${COMPOSE_URL}" \
    -o /usr/libexec/docker/cli-plugins/docker-compose
  chmod +x /usr/libexec/docker/cli-plugins/docker-compose
fi

bootstrap_msg "Paso 6/9 - Docker Buildx (>= 0.17 para compose build)"
_load_docker_bootstrap_plugins_lib
mkdir -p /usr/libexec/docker/cli-plugins
if ! docker_buildx_meets_minimum; then
  if dnf_package_available docker-buildx-plugin; then
    dnf install -y docker-buildx-plugin
  fi
fi
if ! docker_buildx_meets_minimum; then
  retry 3 10 dnf upgrade -y docker || true
fi
if ! docker_buildx_meets_minimum; then
  case "$(uname -m)" in
    x86_64) BX_ARCH=amd64 ;;
    aarch64) BX_ARCH=arm64 ;;
    *) BX_ARCH=$(uname -m) ;;
  esac
  retry 5 15 curl -fSL \
    "https://github.com/docker/buildx/releases/download/${DOCKER_BUILDX_VERSION}/buildx-${DOCKER_BUILDX_VERSION}.linux-${BX_ARCH}" \
    -o /usr/libexec/docker/cli-plugins/docker-buildx
  chmod +x /usr/libexec/docker/cli-plugins/docker-buildx
fi

bootstrap_msg "Paso 7/9 - verificacion de versiones (docker, compose, buildx)"
docker version
docker compose version
docker buildx version

bootstrap_msg "Paso 8/9 - clonar repositorio (si no existe), .env y reglas de seguridad (SG)"
install -d -o "${BOOT_USER}" -g "${BOOT_USER}" "${TARGET_DIR}"
if [[ ! -d "${TARGET_DIR}/.git" ]]; then
  retry 5 20 runuser -u "${BOOT_USER}" -- git clone --depth 1 --branch "${GIT_REF}" "${REPO_URL}" "${TARGET_DIR}"
fi

source "${TARGET_DIR}/scripts/lib/aws-deploy-env.sh"

if [[ ! -f "${TARGET_DIR}/.env" ]]; then
  runuser -u "${BOOT_USER}" -- cp "${TARGET_DIR}/.env.aws.example" "${TARGET_DIR}/.env"
fi
seed_env_secrets "${TARGET_DIR}/.env"
normalize_env_defaults "${TARGET_DIR}/.env"
_profiles="$(read_env_value "${TARGET_DIR}/.env" COMPOSE_PROFILES 2>/dev/null || true)"
if [[ "${_profiles}" == *monitoring* ]]; then
  patch_grafana_dashboard_public_urls_file \
    "${TARGET_DIR}/.env" \
    "${TARGET_DIR}/monitoring/grafana/dashboards/taller-mecanico-dashboard.json" \
    "${TARGET_DIR}"
fi
chown "${BOOT_USER}:${BOOT_USER}" "${TARGET_DIR}/.env"
chmod 600 "${TARGET_DIR}/.env"
authorize_public_ui_ingress "${TARGET_DIR}/.env"

install_resource_guard

if [[ -f "${TARGET_DIR}/scripts/progreso_docker.sh" ]]; then
  install_progreso_docker "${TARGET_DIR}/scripts/progreso_docker.sh"
else
  install_progreso_docker
fi

bootstrap_msg "Paso 9/9 - despliegue Compose (build/pull/up, smoke tests); ver tambien salida de deploy_aws_docker.sh"
cd "${TARGET_DIR}"
chmod +x scripts/deploy_aws_docker.sh scripts/taller-docker-safe-mode.sh scripts/print-jmeter-usage.sh \
  scripts/install-progreso-docker.sh scripts/progreso_docker.sh

export SKIP_BACKUP=1
export STACK_VERIFY_TIMEOUT_SEC="${STACK_VERIFY_TIMEOUT_SEC:-900}"
export TRAFFIC_SMOKE_TIMEOUT_SEC="${TRAFFIC_SMOKE_TIMEOUT_SEC:-180}"
export COMPOSE_UP_WAIT_TIMEOUT="${COMPOSE_UP_WAIT_TIMEOUT:-900}"
export SKIP_TRAFFIC_SMOKE="${SKIP_TRAFFIC_SMOKE:-1}"

deploy_hook_fail() {
  echo "ERROR: deploy_aws_docker.sh failed; extra diagnostics:" >&2
  if ! docker compose --env-file .env -f docker-compose.aws.yml config >/dev/null 2>&1; then
    echo "--- compose config (errors) ---" >&2
    docker compose --env-file .env -f docker-compose.aws.yml config 2>&1 | tail -40 >&2 || true
  fi
  local profiles
  profiles="$(grep -E '^COMPOSE_PROFILES=' .env 2>/dev/null | head -1 | cut -d= -f2- || true)"
  if [[ ",${profiles},," == *",traffic,"* && -f scripts/lib/compose-traffic-preflight.fn.sh ]]; then
    source scripts/lib/compose-traffic-preflight.fn.sh
    assert_traffic_build_context "${TARGET_DIR}" docker-compose.aws.yml --env-file .env \
      || true
  fi
  docker compose --env-file .env -f docker-compose.aws.yml ps -a || true
  local s
  while read -r s; do
    [[ -z "${s}" ]] && continue
    echo "--- logs ${s} ---" >&2
    docker compose --env-file .env -f docker-compose.aws.yml logs --tail 160 "${s}" 2>/dev/null || true
  done < <(docker compose --env-file .env -f docker-compose.aws.yml config --services 2>/dev/null || true)
}

if ! ./scripts/deploy_aws_docker.sh; then
  deploy_hook_fail
  exit 1
fi

bootstrap_msg "Contenedores en el host tras el despliegue (docker ps -a)"
docker ps -a || true

if [[ -x "${TARGET_DIR}/scripts/print-jmeter-usage.sh" ]]; then
  bootstrap_msg "Guia operativa JMeter (docs/TRAFFIC_SIMULATOR.md)"
  _tu="$(read_env_value "${TARGET_DIR}/.env" TRAFFIC_SIMULATOR_UI_EXTERNAL_URL || true)"
  if [[ -z "${_tu}" ]]; then
    _tu="http://$(public_browser_host "${TARGET_DIR}/.env"):$(read_env_value "${TARGET_DIR}/.env" TRAFFIC_SIMULATOR_UI_HOST_PORT || printf '8890')"
  fi
  _gr=""
  _profiles="$(read_env_value "${TARGET_DIR}/.env" COMPOSE_PROFILES || true)"
  if [[ "${_profiles}" == *monitoring* ]]; then
    _gr="http://$(public_browser_host "${TARGET_DIR}/.env"):$(read_env_value "${TARGET_DIR}/.env" GRAFANA_HOST_PORT || printf '3000')"
  fi
  bash "${TARGET_DIR}/scripts/print-jmeter-usage.sh" "${_tu}" "${_gr}" || true
fi

echo "Bootstrap done. Log: /var/log/taller-ec2-bootstrap.log"
echo "Ver progreso en vivo: progreso_docker"
echo "Note for SSH: user ${BOOT_USER} was added to group docker. Run 'exit' and open a NEW SSH session (or run: newgrp docker) before using docker without sudo."
