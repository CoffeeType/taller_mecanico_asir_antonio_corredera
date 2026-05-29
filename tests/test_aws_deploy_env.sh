#!/usr/bin/env bash
# Unit tests for scripts/lib/aws-deploy-env.sh (exit 0 if all pass).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/lib/aws-deploy-env.sh
source "${ROOT}/scripts/lib/aws-deploy-env.sh"

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

FIXTURE="${ROOT}/tests/fixtures/aws_deploy_test.env"
TMP_ENV="$(mktemp)"
trap 'rm -f "$TMP_ENV"' EXIT
cp "$FIXTURE" "$TMP_ENV"

val="$(read_env_value "$TMP_ENV" MYSQL_PASSWORD)"
assert_eq "read password with special chars" "pass\$word#x" "$val"

COMPOSE_PROFILES="monitoring,traffic"
profiles_contain monitoring && rc=0 || rc=1
assert_ok "profiles_contain monitoring" "$rc"

COMPOSE_PROFILES=" monitoring , traffic "
profiles_contain traffic && rc=0 || rc=1
assert_ok "profiles_contain with spaces" "$rc"

COMPOSE_PROFILES="web"
profiles_contain monitoring && rc=0 || rc=1
assert_fail "profiles_contain absent" "$rc"

AWS_DEPLOY_SECRET_GEN="generated_secret_48_chars_xxxxxxxxxxxxxxxx"
seed_env_secret_if_placeholder "$TMP_ENV" SIMULATOR_CONTROL_TOKEN 48
tok="$(read_env_value "$TMP_ENV" SIMULATOR_CONTROL_TOKEN)"
assert_eq "seed replaces CAMBIAR placeholder" "$AWS_DEPLOY_SECRET_GEN" "$tok"

set_env_value "$TMP_ENV" MYSQL_PASSWORD "app_password"
AWS_DEPLOY_SECRET_GEN="rotated_secret_xxxxxxxxxxxxxxxxxxxxxxxx"
seed_env_secret_if_placeholder "$TMP_ENV" MYSQL_PASSWORD 36
mp="$(read_env_value "$TMP_ENV" MYSQL_PASSWORD)"
assert_eq "seed replaces app_password" "$AWS_DEPLOY_SECRET_GEN" "$mp"

AWS_METADATA_MOCK_DIR="$(mktemp -d)"
trap 'rm -f "$TMP_ENV"; rm -rf "$AWS_METADATA_MOCK_DIR"' EXIT
printf 'mock-token' >"${AWS_METADATA_MOCK_DIR}/token"
printf 'ec2-mock.example.com' >"${AWS_METADATA_MOCK_DIR}/public-hostname"
host="$(public_browser_host "$TMP_ENV")"
assert_eq "public_browser_host uses metadata mock" "ec2-mock.example.com" "$host"

rm -rf "$AWS_METADATA_MOCK_DIR"
AWS_METADATA_MOCK_DIR=""

STACK_VERIFY_TIMEOUT_SEC=""
TRAFFIC_SMOKE_TIMEOUT_SEC=""
COMPOSE_UP_WAIT_TIMEOUT=""
WEB_SMOKE_WAIT_SEC=""
apply_deploy_timeouts_for_memory_budget 5120
assert_eq "timeouts tuned for t3.small budget STACK" "900" "${STACK_VERIFY_TIMEOUT_SEC}"
assert_eq "timeouts tuned for t3.small budget TRAFFIC_SMOKE" "180" "${TRAFFIC_SMOKE_TIMEOUT_SEC}"

if [[ "$FAILS" -gt 0 ]]; then
  echo "${FAILS} test(s) failed"
  exit 1
fi

echo "test_aws_deploy_env.sh: OK (${FAILS} failures)"
