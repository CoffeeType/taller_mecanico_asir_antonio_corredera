#!/usr/bin/env bash
# Helpers for Docker Buildx / dnf checks on EC2 bootstrap (Amazon Linux 2023).
# Sourced by scripts/ec2-user-data-bootstrap.sh (via same-dir path or curl) and tests/test_docker_bootstrap_plugins.sh.

# Extract first semantic tag vX.Y.Z from `docker buildx version` output (or similar).
docker_buildx_version_from_output() {
  # grep exits 1 when there is no match; avoid breaking callers with pipefail.
  { printf '%s' "${1:-}" | grep -oE 'v[0-9]+\.[0-9]+\.[0-9]+' || true; } | head -1
}

# Return 0 if buildx version in $1 (full output) or from live `docker buildx version` is >= v0.17.0.
docker_buildx_meets_minimum() {
  local min="v0.17.0" text cur
  if [[ $# -ge 1 ]]; then
    text="$1"
  else
    text="$(docker buildx version 2>/dev/null || true)"
  fi
  cur="$(docker_buildx_version_from_output "$text")"
  [[ -n "$cur" ]] || return 1
  [[ "$(printf '%s\n' "$min" "$cur" | sort -V | head -n1)" == "$min" ]]
}

# Return 0 if dnf can install the package from configured repos (does not install).
dnf_package_available() {
  local pkg="$1"
  dnf list --available "$pkg" &>/dev/null
}
