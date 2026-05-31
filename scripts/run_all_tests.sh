#!/usr/bin/env bash
# Batería completa de tests del repo (unitarios + HTTP booking si Docker disponible).
# Uso: bash scripts/run_all_tests.sh
# Windows: powershell -File scripts/run_all_tests.ps1

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# shellcheck source=lib/docker-php-test.fn.sh
source "${ROOT}/scripts/lib/docker-php-test.fn.sh"
# shellcheck source=lib/ensure-web-stack.fn.sh
source "${ROOT}/scripts/lib/ensure-web-stack.fn.sh"

BASH_TESTS=(
  tests/test_aws_deploy_env.sh
  tests/test_bootstrap_lib_loader.sh
  tests/test_docker_bootstrap_plugins.sh
  tests/test_compose_traffic_preflight.sh
  tests/test_ec2_cloud_init_lib_load.sh
)

for t in "${BASH_TESTS[@]}"; do
  echo "== ${t} =="
  bash "$t"
done

echo "== run_monitoring_checks.sh =="
bash tests/run_monitoring_checks.sh

echo "== test_compose_traffic_parity.py =="
python3 tests/test_compose_traffic_parity.py

echo "== test_traffic_simulator_lib.php =="
run_php_cli_test "$ROOT" tests/test_traffic_simulator_lib.php

if [[ -f scripts/verify_aws_stack.sh ]]; then
  echo "== verify_aws_stack.sh =="
  bash scripts/verify_aws_stack.sh
fi

if [[ -f .env ]] && [[ -f scripts/deploy_aws_docker.sh ]]; then
  echo "== deploy_aws_docker.sh (DEPLOY_PREFLIGHT_ONLY) =="
  DEPLOY_PREFLIGHT_ONLY=1 SKIP_SECRET_STRICT_CHECK=1 bash scripts/deploy_aws_docker.sh
fi

BOOKING_HTTP_TESTS=(
  tests/test_booking_access.php
  tests/test_booking_roundtrip.php
  tests/test_booking_validation.php
  tests/test_booking_conflict.php
  tests/test_perfil_requires_login.php
)

if ensure_web_stack_for_http_tests "$ROOT"; then
  for t in "${BOOKING_HTTP_TESTS[@]}"; do
    echo "== ${t} (HTTP) =="
    run_booking_http_test "$ROOT" "$t"
  done
else
  echo "ERROR: tests HTTP de booking omitidos porque web/mysql no arrancaron" >&2
  exit 1
fi

echo "run_all_tests.sh: OK"
