#!/usr/bin/env bash
# Integration: EC2 user-data has no scripts/lib/ beside part-001; libs load via curl or fail clearly.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_URL="${REPO_URL:-https://github.com/CoffeeType/taller_mecanico_asir.git}"
GIT_REF="${GIT_REF:-main}"
FAILS=0

assert_ok() {
  local name="$1" rc="$2"
  if [[ "$rc" != 0 ]]; then
    echo "FAIL: ${name} (exit ${rc})"
    FAILS=$((FAILS + 1))
  fi
}

# --- Remote availability (optional; warns if push pending) ---
_bl_url="https://raw.githubusercontent.com/CoffeeType/taller_mecanico_asir/${GIT_REF}/scripts/lib/bootstrap-lib-loader.sh"
_ip_url="https://raw.githubusercontent.com/CoffeeType/taller_mecanico_asir/${GIT_REF}/scripts/lib/install-progreso-docker.fn.sh"
if curl -fSsI "$_bl_url" >/dev/null 2>&1; then
  echo "INFO: bootstrap-lib-loader.sh disponible en GitHub (${GIT_REF})"
else
  echo "WARN: ${_bl_url} no existe en remoto; user-data EC2 fallará en curl hasta hacer push." >&2
fi
if curl -fSsI "$_ip_url" >/dev/null 2>&1; then
  echo "INFO: install-progreso-docker.fn.sh disponible en GitHub (${GIT_REF})"
else
  echo "WARN: ${_ip_url} no existe en remoto; push pendiente." >&2
fi

# --- Simulated cloud-init dir (no lib/) ---
# shellcheck source=scripts/lib/bootstrap-lib-loader.sh
source "${ROOT}/scripts/lib/bootstrap-lib-loader.sh"
BOOTSTRAP_SCRIPT_DIR="/var/lib/cloud/instance/scripts"
STUB="$(mktemp)"
cat >"$STUB" <<'EOF'
install_progreso_docker() { :; }
EOF
curl() {
  if [[ "$1" == "-fSsL" || "$1" == "-fSsI" ]]; then
    local dest="" next=0
    for arg in "$@"; do
      [[ "$next" == 1 ]] && { dest="$arg"; break; }
      [[ "$arg" == "-o" ]] && next=1
    done
    [[ -n "$dest" && -f "$dest" ]] && return 0
    if [[ "$1" == "-fSsI" ]]; then return 1; fi
    if [[ -n "$dest" ]]; then cp "$STUB" "$dest"; return 0; fi
  fi
  return 1
}
unset -f install_progreso_docker 2>/dev/null || true
load_bootstrap_lib "scripts/lib/install-progreso-docker.fn.sh" && rc=0 || rc=1
assert_ok "cloud-init sim: load install-progreso via curl" "$rc"
unset -f curl 2>/dev/null || true
unset BOOTSTRAP_SCRIPT_DIR
rm -f "$STUB"

# --- docker-bootstrap-plugins on GitHub (existing on main) ---
if curl -fSsI "https://raw.githubusercontent.com/CoffeeType/taller_mecanico_asir/${GIT_REF}/scripts/lib/docker-bootstrap-plugins.sh" >/dev/null 2>&1; then
  echo "INFO: docker-bootstrap-plugins.sh OK en remoto"
else
  echo "FAIL: docker-bootstrap-plugins.sh missing on remote"
  FAILS=$((FAILS + 1))
fi

if [[ "$FAILS" -gt 0 ]]; then
  echo "${FAILS} test(s) failed"
  exit 1
fi
echo "test_ec2_cloud_init_lib_load.sh: OK (${FAILS} failures)"
