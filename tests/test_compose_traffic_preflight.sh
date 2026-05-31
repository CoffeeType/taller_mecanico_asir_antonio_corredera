#!/usr/bin/env bash
# Smoke test for compose/traffic-services.yml include path resolution.
# Ejecutar desde la raiz: bash tests/test_compose_traffic_preflight.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/lib/compose-traffic-preflight.fn.sh
source "${ROOT}/scripts/lib/compose-traffic-preflight.fn.sh"

ENV_FILE="${ROOT}/tests/fixtures/compose_traffic_parity.env"
COMPOSE_FILE="${ROOT}/docker-compose.aws.yml"

check_traffic_compose_paths "$ROOT"
assert_traffic_build_context "$ROOT" "$COMPOSE_FILE" --env-file "$ENV_FILE" --profile traffic

echo "test_compose_traffic_preflight.sh: OK"
