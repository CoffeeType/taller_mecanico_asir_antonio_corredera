#!/usr/bin/env bash
# Unit tests for scripts/lib/docker-bootstrap-plugins.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/lib/docker-bootstrap-plugins.sh
source "${ROOT}/scripts/lib/docker-bootstrap-plugins.sh"

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

assert_fail() {
  local name="$1" rc="$2"
  if [[ "$rc" == 0 ]]; then
    echo "FAIL: ${name} (expected failure)"
    FAILS=$((FAILS + 1))
  fi
}

# --- docker_buildx_version_from_output ---
v="$(docker_buildx_version_from_output 'github.com/docker/buildx v0.19.3 deadbeef')"
assert_eq "parse from buildx line" "v0.19.3" "$v"

v="$(docker_buildx_version_from_output 'Version:  v0.12.1')"
assert_eq "parse spaced" "v0.12.1" "$v"

v="$(docker_buildx_version_from_output 'v0.0.0+unknown extra')"
assert_eq "parse v0.0.0+unknown prefix" "v0.0.0" "$v"

v="$(docker_buildx_version_from_output '')"
assert_eq "empty output" "" "$v"

# --- docker_buildx_meets_minimum (explicit output text) ---
docker_buildx_meets_minimum 'github.com/docker/buildx v0.19.3 xxx' && rc=0 || rc=1
assert_ok "meets min v0.19.3" "$rc"

docker_buildx_meets_minimum 'github.com/docker/buildx v0.12.1 xxx' && rc=0 || rc=1
assert_fail "below min v0.12.1" "$rc"

docker_buildx_meets_minimum 'Plugins: buildx v0.0.0+unknown' && rc=0 || rc=1
assert_fail "v0.0.0 not meeting 0.17" "$rc"

docker_buildx_meets_minimum '' && rc=0 || rc=1
assert_fail "empty text" "$rc"

# --- dnf_package_available (mock dnf) ---
dnf() {
  if [[ "$1" == "list" && "$2" == "--available" ]]; then
    case "$3" in
      docker-buildx-plugin) return 0 ;;
      missing-pkg) return 1 ;;
      *) return 1 ;;
    esac
  fi
  return 99
}

dnf_package_available docker-buildx-plugin && rc=0 || rc=1
assert_ok "dnf_package_available when mock says yes" "$rc"

dnf_package_available missing-pkg && rc=0 || rc=1
assert_fail "dnf_package_available when mock says no" "$rc"

unset -f dnf

if [[ "$FAILS" -gt 0 ]]; then
  echo "${FAILS} test(s) failed"
  exit 1
fi

echo "test_docker_bootstrap_plugins.sh: OK (${FAILS} failures)"
