#!/usr/bin/env bash
# Load bootstrap helper libs from repo checkout or GitHub raw (EC2 user-data has no scripts/lib/).
# Sourced by ec2-user-data-bootstrap.sh and tests/test_bootstrap_lib_loader.sh.
# Optional: BOOTSTRAP_SCRIPT_DIR = directory of ec2-user-data-bootstrap.sh (cloud-init part-001 dir).
# Expects REPO_URL and GIT_REF when using remote fallback.

bootstrap_lib_github_raw_url() {
  local rel_path="${1:?relative path required}"
  local base="${REPO_URL%.git}"
  case "$base" in
    https://github.com/*)
      printf 'https://raw.githubusercontent.com/%s/%s/%s' "${base#https://github.com/}" "${GIT_REF:-main}" "$rel_path"
      ;;
    http://github.com/*)
      printf 'https://raw.githubusercontent.com/%s/%s/%s' "${base#http://github.com/}" "${GIT_REF:-main}" "$rel_path"
      ;;
    *)
      return 1
      ;;
  esac
}

_bootstrap_lib_local_path() {
  local rel_path="$1"
  local lib_name="${rel_path#scripts/lib/}"
  local loader_dir root

  if [[ "$rel_path" != scripts/lib/* ]]; then
    return 1
  fi

  if [[ -n "${BOOTSTRAP_SCRIPT_DIR:-}" && -f "${BOOTSTRAP_SCRIPT_DIR}/lib/${lib_name}" ]]; then
    printf '%s' "${BOOTSTRAP_SCRIPT_DIR}/lib/${lib_name}"
    return 0
  fi

  loader_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [[ -f "${loader_dir}/${lib_name}" ]]; then
    printf '%s' "${loader_dir}/${lib_name}"
    return 0
  fi

  root="$(cd "${loader_dir}/../.." && pwd)"
  if [[ -f "${root}/${rel_path}" ]]; then
    printf '%s' "${root}/${rel_path}"
    return 0
  fi
  return 1
}

load_bootstrap_lib() {
  local rel_path="$1"
  local lib tmp u prev
  lib="$(_bootstrap_lib_local_path "$rel_path" 2>/dev/null || true)"
  if [[ -n "$lib" && -f "$lib" ]]; then
    # shellcheck source=/dev/null
    source "$lib"
    return 0
  fi
  prev=""
  for u in "$(bootstrap_lib_github_raw_url "$rel_path" 2>/dev/null || true)" \
    "https://raw.githubusercontent.com/CoffeeType/taller_mecanico_asir/${GIT_REF:-main}/${rel_path}"; do
    [[ -n "$u" ]] || continue
    [[ "$u" == "$prev" ]] && continue
    prev="$u"
    tmp="$(mktemp)"
    if curl -fSsL "$u" -o "$tmp" 2>/dev/null; then
      # shellcheck source=/dev/null
      source "$tmp"
      rm -f "$tmp"
      return 0
    fi
    rm -f "$tmp"
  done
  echo "ERROR: no se pudo cargar ${rel_path} (ruta local ni curl GitHub)." >&2
  return 1
}
