# Shared .env helpers for AWS deploy scripts (source, do not execute).
# Set AWS_DEPLOY_ENV_FILE for deploy_aws_docker.sh (read_env_var / 2-arg set_env_value).

aws_env_read() {
  local file="$1" key="$2"
  local line val
  [[ -f "$file" ]] || return 1
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line//$'\r'/}"
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line// }" ]] && continue
    if [[ "$line" == "$key="* ]]; then
      val="${line#*=}"
      if [[ "$val" =~ ^\"(.*)\"$ ]]; then val="${BASH_REMATCH[1]}"; fi
      if [[ "$val" =~ ^\'(.*)\'$ ]]; then val="${BASH_REMATCH[1]}"; fi
      printf '%s' "$val"
      return 0
    fi
  done <"$file"
  return 1
}

read_env_value() {
  local file="$1" key="$2"
  aws_env_read "$file" "$key"
}

read_env_var() {
  local key="$1" default="${2:-}"
  [[ -n "${AWS_DEPLOY_ENV_FILE:-}" ]] || {
    printf '%s' "$default"
    return 0
  }
  local val
  if val="$(aws_env_read "$AWS_DEPLOY_ENV_FILE" "$key")"; then
    printf '%s' "$val"
  else
    printf '%s' "$default"
  fi
}

_aws_env_set_hook() {
  :
}

set_env_value() {
  local file key value
  if [[ $# -eq 3 ]]; then
    file="$1"
    key="$2"
    value="$3"
  elif [[ $# -eq 2 && -n "${AWS_DEPLOY_ENV_FILE:-}" ]]; then
    file="$AWS_DEPLOY_ENV_FILE"
    key="$1"
    value="$2"
  else
    echo "set_env_value: expected (file key value) or (key value) with AWS_DEPLOY_ENV_FILE" >&2
    return 1
  fi
  [[ -f "$file" ]] || touch "$file"
  if grep -qE "^${key}=" "$file"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$file"
  else
    printf '\n%s=%s\n' "$key" "$value" >>"$file"
  fi
  _aws_env_set_hook "$file"
}

profiles_contain() {
  local needle="$1"
  local raw="${COMPOSE_PROFILES:-}"
  local IFS=',' p
  raw="${raw//[[:space:]]/}"
  [[ -n "$raw" ]] || return 1
  IFS=',' read -ra _prof_parts <<<"$raw"
  for p in "${_prof_parts[@]}"; do
    [[ -z "$p" ]] && continue
    [[ "$p" == "$needle" ]] && return 0
  done
  return 1
}

metadata_token() {
  if [[ -n "${AWS_METADATA_MOCK_DIR:-}" ]]; then
    cat "${AWS_METADATA_MOCK_DIR}/token" 2>/dev/null || true
    return 0
  fi
  curl -sf --max-time 2 -X PUT \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 60" \
    "http://169.254.169.254/latest/api/token" 2>/dev/null || true
}

metadata_get() {
  local path="$1"
  if [[ -n "${AWS_METADATA_MOCK_DIR:-}" ]]; then
    local safe="${path//\//_}"
    cat "${AWS_METADATA_MOCK_DIR}/${safe}" 2>/dev/null || true
    return 0
  fi
  local token
  token="$(metadata_token)"
  if [[ -n "$token" ]]; then
    curl -sf --max-time 2 -H "X-aws-ec2-metadata-token: ${token}" \
      "http://169.254.169.254/latest/meta-data/${path}" 2>/dev/null || true
  else
    curl -sf --max-time 2 "http://169.254.169.254/latest/meta-data/${path}" 2>/dev/null || true
  fi
}

public_browser_host() {
  local file="${1:-${AWS_DEPLOY_ENV_FILE:-}}"
  local host=""
  if [[ -n "$file" && -f "$file" ]]; then
    host="$(read_env_value "$file" PUBLIC_ACCESS_HOST 2>/dev/null || true)"
  fi
  [[ -n "$host" ]] || host="$(metadata_get public-hostname)"
  [[ -n "$host" ]] || host="$(metadata_get public-ipv4)"
  [[ -n "$host" ]] || host="PUBLIC_IP_O_DNS"
  printf '%s' "$host"
}

env_value_is_placeholder_secret() {
  local current="$1"
  [[ -z "$current" || "$current" == *CAMBIAR* || "$current" == *changeme* \
    || "$current" == "rootpassword" || "$current" == "app_password" || "$current" == "admin123" ]]
}

random_secret() {
  local len="${1:-32}"
  if [[ -n "${AWS_DEPLOY_SECRET_GEN:-}" ]]; then
    printf '%s' "$AWS_DEPLOY_SECRET_GEN"
    return 0
  fi
  local secret
  set +o pipefail
  secret="$(LC_ALL=C tr -dc 'A-Za-z0-9_@%+=:,.~-' </dev/urandom | head -c "$len")"
  set -o pipefail
  printf '%s' "$secret"
}

seed_env_secret_if_placeholder() {
  local file="$1" key="$2" len="${3:-36}" current
  current="$(read_env_value "$file" "$key" 2>/dev/null || true)"
  if env_value_is_placeholder_secret "$current"; then
    set_env_value "$file" "$key" "$(random_secret "$len")"
  fi
}

seed_env_secrets() {
  local file="$1"
  seed_env_secret_if_placeholder "$file" MYSQL_PASSWORD 36
  seed_env_secret_if_placeholder "$file" MYSQL_ROOT_PASSWORD 36
  seed_env_secret_if_placeholder "$file" GRAFANA_ADMIN_PASSWORD 36
  seed_env_secret_if_placeholder "$file" SIMULATOR_CONTROL_TOKEN 48
}

raise_env_min_if_lower() {
  local file="$1" key="$2" minimum="$3" current
  current="$(read_env_value "$file" "$key" 2>/dev/null || true)"
  if [[ ! "$current" =~ ^[0-9]+$ ]]; then
    set_env_value "$file" "$key" "$minimum"
  elif ((current < minimum)); then
    set_env_value "$file" "$key" "$minimum"
  fi
}

apply_deploy_timeouts_for_memory_budget() {
  local budget="$1"
  if [[ "$budget" -ge 4200 && "$budget" -lt 7000 ]]; then
    : "${STACK_VERIFY_TIMEOUT_SEC:=900}"
    : "${TRAFFIC_SMOKE_TIMEOUT_SEC:=180}"
    : "${COMPOSE_UP_WAIT_TIMEOUT:=900}"
    : "${WEB_SMOKE_WAIT_SEC:=360}"
  fi
}
