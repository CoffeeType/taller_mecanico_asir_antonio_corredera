# Run a PHP test script via host php or ephemeral php:8.2-cli container.
# Source from test runners; do not execute directly.

docker_php_volume_mount() {
  local root="${1:?}"
  if [[ -n "${MSYSTEM:-}" || "${OSTYPE:-}" == msys* || "${OSTYPE:-}" == cygwin* ]]; then
    MSYS_NO_PATHCONV=1
    printf '%s' "$(cd "$root" && pwd -W | tr '\\' '/')"
  else
    printf '%s' "$root"
  fi
}

run_php_cli_test() {
  local root="${1:?}"
  local rel="${2:?}"
  if command -v php >/dev/null 2>&1; then
    (cd "$root" && php "$rel")
    return
  fi
  if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
    echo "SKIP: php y Docker no disponibles ($rel)" >&2
    return 1
  fi
  local vol
  vol="$(docker_php_volume_mount "$root")"
  MSYS_NO_PATHCONV=1 docker run --rm \
    -v "${vol}:/var/www/html" \
    -w /var/www/html \
    php:8.2-cli php "$rel"
}
