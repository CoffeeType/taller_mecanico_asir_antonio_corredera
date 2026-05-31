# Ensure docker-compose web+mysql are up for HTTP integration tests (source only).

ensure_web_stack_for_http_tests() {
  local root="${1:?}"
  local port="${WEB_PORT:-8081}"
  local url="http://127.0.0.1:${port}/health.php"
  local deadline i=0 max_wait="${WEB_STACK_WAIT_SEC:-180}"

  if curl -sf --max-time 5 "$url" 2>/dev/null | grep -qE 'ok|OK'; then
    echo "OK: web stack already healthy (${url})"
    return 0
  fi

  if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
    echo "ERROR: web stack no responde y Docker no esta disponible (${url})" >&2
    return 1
  fi

  echo "Levantando web+mysql (docker compose) para tests HTTP..."
  (cd "$root" && docker compose up -d web mysql)

  while [[ "$i" -lt "$max_wait" ]]; do
    if curl -sf --max-time 5 "$url" 2>/dev/null | grep -qE 'ok|OK'; then
      echo "OK: web stack healthy tras ~${i}s"
      return 0
    fi
    sleep 3
    i=$((i + 3))
  done

  echo "ERROR: web no healthy en ${url} tras ${max_wait}s" >&2
  return 1
}

run_booking_http_test() {
  local root="${1:?}"
  local rel="${2:?}"
  local port="${WEB_PORT:-8081}"
  local host_base="http://127.0.0.1:${port}"
  local docker_base="http://host.docker.internal:${port}"

  if command -v php >/dev/null 2>&1; then
    BOOKING_TEST_BASE="$host_base" php "${root}/${rel}"
    return
  fi

  local vol
  vol="$(docker_php_volume_mount "$root")"
  MSYS_NO_PATHCONV=1 docker run --rm \
    -e "BOOKING_TEST_BASE=${docker_base}" \
    --add-host=host.docker.internal:host-gateway \
    -v "${vol}:/var/www/html" \
    -w /var/www/html \
    php:8.2-cli php "$rel"
}
