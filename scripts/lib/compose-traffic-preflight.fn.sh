# Traffic simulator compose preflight (source, do not execute).
# Validates paths and build context resolution for compose/traffic-services.yml includes.

TRAFFIC_COMPOSE_PREFLIGHT_PATHS=(
  compose/traffic-services.yml
  docker/traffic-simulator/Dockerfile
  docker/traffic-simulator/entrypoint.sh
  docker/traffic-simulator/control_router.php
  docker/traffic-simulator-ui/Dockerfile
  docker/traffic-simulator-ui/public
)

check_traffic_compose_paths() {
  local root="${1:?}"
  local rel missing=0
  for rel in "${TRAFFIC_COMPOSE_PREFLIGHT_PATHS[@]}"; do
    if [[ ! -e "${root}/${rel}" ]]; then
      echo "ERROR: falta ruta requerida para perfil traffic: ${rel}" >&2
      missing=1
    fi
  done
  [[ "$missing" == "0" ]]
}

assert_traffic_build_context_from_config() {
  local project_dir="${1:?}"
  local config_json="${2:?}"

  if ! command -v python3 >/dev/null 2>&1; then
    echo "WARN: python3 no disponible; omito validacion build context traffic." >&2
    return 0
  fi

  COMPOSE_CONFIG_JSON="$config_json" python3 - "$project_dir" <<'PY'
import json
import os
import sys

root = os.path.normpath(sys.argv[1])
compose_dir = os.path.join(root, "compose")
try:
    cfg = json.loads(os.environ["COMPOSE_CONFIG_JSON"])
except json.JSONDecodeError as exc:
    print(f"ERROR: compose config JSON invalido: {exc}", file=sys.stderr)
    sys.exit(1)

services = cfg.get("services") or {}
for svc in ("traffic-simulator", "traffic-simulator-ui"):
    build = services.get(svc, {}).get("build")
    if not isinstance(build, dict):
        print(
            f"ERROR: servicio {svc} sin bloque build (perfil traffic activo?)",
            file=sys.stderr,
        )
        sys.exit(1)
    ctx = os.path.normpath(build.get("context") or "")
    if ctx in (compose_dir, os.path.join(root, "compose")):
        print(
            f"ERROR: {svc} build context apunta a compose/ ({ctx}); "
            "use context: .. en compose/traffic-services.yml",
            file=sys.stderr,
        )
        sys.exit(1)
    if ctx != root:
        print(
            f"ERROR: {svc} build context {ctx!r} != raiz del proyecto {root!r}",
            file=sys.stderr,
        )
        sys.exit(1)
    dockerfile = build.get("dockerfile") or ""
    if dockerfile and not os.path.isfile(os.path.join(ctx, dockerfile)):
        print(
            f"ERROR: {svc} dockerfile no encontrado: {os.path.join(ctx, dockerfile)}",
            file=sys.stderr,
        )
        sys.exit(1)
PY
}

assert_traffic_build_context() {
  local project_dir="${1:?}"
  local compose_file="${2:?}"
  shift 2
  local config_json

  check_traffic_compose_paths "$project_dir" || return 1

  if ! config_json="$(docker compose "$@" -f "$compose_file" config --format json 2>/dev/null)"; then
    echo "ERROR: docker compose config --format json fallo (${compose_file})" >&2
    return 1
  fi

  assert_traffic_build_context_from_config "$project_dir" "$config_json"
}
