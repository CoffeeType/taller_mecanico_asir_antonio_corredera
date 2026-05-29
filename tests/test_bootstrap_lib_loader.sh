#!/usr/bin/env bash
# Unit tests for scripts/lib/bootstrap-lib-loader.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_URL="https://github.com/CoffeeType/taller_mecanico_asir.git"
GIT_REF="main"

# shellcheck source=scripts/lib/bootstrap-lib-loader.sh
source "${ROOT}/scripts/lib/bootstrap-lib-loader.sh"

FAILS=0

assert_eq() {
  local name="$1" expected="$2" actual="$3"
  if [[ "$expected" != "$actual" ]]; then
    echo "FAIL: ${name} (expected '${expected}', got '${actual}')"
    FAILS=$((FAILS + 1))
  fi
}

assert_ok() {
  local name="$1" rc="$2"
  if [[ "$rc" != 0 ]]; then
    echo "FAIL: ${name} (exit ${rc})"
    FAILS=$((FAILS + 1))
  fi
}

# --- bootstrap_lib_github_raw_url ---
u="$(bootstrap_lib_github_raw_url "scripts/lib/install-progreso-docker.fn.sh")"
assert_eq "github raw url" \
  "https://raw.githubusercontent.com/CoffeeType/taller_mecanico_asir/main/scripts/lib/install-progreso-docker.fn.sh" \
  "$u"

REPO_URL="https://github.com/org/repo.git"
GIT_REF="feature/x"
u="$(bootstrap_lib_github_raw_url "scripts/lib/docker-bootstrap-plugins.sh")"
assert_eq "custom ref url" \
  "https://raw.githubusercontent.com/org/repo/feature/x/scripts/lib/docker-bootstrap-plugins.sh" \
  "$u"

if REPO_URL="https://gitlab.com/foo/bar.git" bootstrap_lib_github_raw_url "scripts/lib/x.sh" 2>/dev/null; then
  echo "FAIL: non-github URL should not produce url"
  FAILS=$((FAILS + 1))
fi

REPO_URL="https://github.com/CoffeeType/taller_mecanico_asir.git"
GIT_REF="main"

# --- load_bootstrap_lib via mock curl (simulates cloud-init without lib dir) ---
STUB="$(mktemp)"
cat >"$STUB" <<'STUB'
install_progreso_docker_mocked() { :; }
STUB

curl() {
  if [[ "$1" == "-fSsL" ]]; then
    local dest=""
    local next=0
    for arg in "$@"; do
      if [[ "$next" == 1 ]]; then
        dest="$arg"
        break
      fi
      [[ "$arg" == "-o" ]] && next=1
    done
    if [[ -n "$dest" ]]; then
      cp "$STUB" "$dest"
      return 0
    fi
  fi
  return 1
}

BOOTSTRAP_SCRIPT_DIR="/nonexistent/cloud-init/scripts"
unset -f install_progreso_docker_mocked 2>/dev/null || true
load_bootstrap_lib "scripts/lib/_test_cloud_init_stub.fn.sh" && rc=0 || rc=1
assert_ok "load_bootstrap_lib via curl stub" "$rc"
type install_progreso_docker_mocked >/dev/null 2>&1 && rc=0 || rc=1
assert_ok "stub function defined after curl load" "$rc"

unset -f curl 2>/dev/null || true
unset BOOTSTRAP_SCRIPT_DIR
rm -f "$STUB"

# --- local load from repo ---
load_bootstrap_lib "scripts/lib/docker-bootstrap-plugins.sh" && rc=0 || rc=1
assert_ok "load docker-bootstrap-plugins from disk" "$rc"
type docker_buildx_meets_minimum >/dev/null 2>&1 && rc=0 || rc=1
assert_ok "docker_buildx_meets_minimum available after load" "$rc"

if [[ "$FAILS" -gt 0 ]]; then
  echo "${FAILS} test(s) failed"
  exit 1
fi

echo "test_bootstrap_lib_loader.sh: OK (${FAILS} failures)"
