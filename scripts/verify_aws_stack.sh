#!/usr/bin/env bash
# Validacion estatica del stack AWS (sin levantar contenedores).
# Uso: desde raiz del repo: ./scripts/verify_aws_stack.sh
# Opcional: ENV_FILE=/ruta/.env ./scripts/verify_aws_stack.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

ENV_FILE="${ENV_FILE:-}"
if [[ -z "$ENV_FILE" ]]; then
  if [[ -f "$ROOT/.env" ]]; then
    ENV_FILE="$ROOT/.env"
  else
    ENV_FILE="$ROOT/.env.aws.example"
  fi
fi

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.aws.yml}"
echo "Using env file: $ENV_FILE"
echo "Compose file: $COMPOSE_FILE"

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config >/dev/null
echo "OK: docker compose config"

echo "--- services (resolved) ---"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" config --services | sort

profiles="$(grep -E '^COMPOSE_PROFILES=' "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- || true)"
if [[ ",${profiles},," == *",traffic,"* ]]; then
  # shellcheck source=lib/compose-traffic-preflight.fn.sh
  source "${SCRIPT_DIR}/lib/compose-traffic-preflight.fn.sh"
  assert_traffic_build_context "$ROOT" "$COMPOSE_FILE" --env-file "$ENV_FILE"
  echo "OK: traffic build context (compose include paths)"
fi

echo "verify_aws_stack.sh: OK"
