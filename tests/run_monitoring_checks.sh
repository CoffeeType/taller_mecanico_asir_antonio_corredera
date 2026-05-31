#!/usr/bin/env bash
# Run unit checks for Grafana URLs / NOC / AWS deploy env (plan: enlaces Grafana dinámicos).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# shellcheck source=../scripts/lib/docker-php-test.fn.sh
source "${ROOT}/scripts/lib/docker-php-test.fn.sh"

echo "== test_aws_deploy_env.sh =="
bash tests/test_aws_deploy_env.sh

echo "== test_patch_grafana_public_urls.py =="
python3 tests/test_patch_grafana_public_urls.py

echo "== test_grafana_noc_dashboard.py =="
python3 tests/test_grafana_noc_dashboard.py

echo "== test_traffic_simulator_monitoring_api.php =="
run_php_cli_test "$ROOT" tests/test_traffic_simulator_monitoring_api.php

echo "All monitoring checks passed."
