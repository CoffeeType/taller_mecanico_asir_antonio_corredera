#!/usr/bin/env python3
"""
Paridad del simulador de tráfico entre docker-compose.yml (local) y docker-compose.aws.yml.
Ejecutar desde la raíz del repo: python tests/test_compose_traffic_parity.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ENV = ROOT / "tests" / "fixtures" / "compose_traffic_parity.env"

TRAFFIC_SERVICES = ("traffic-simulator", "traffic-simulator-ui")

# Claves de entorno que deben coincidir entre local y AWS (mismo contrato operativo).
TRAFFIC_ENV_KEYS = (
    "SIM_BASE_URL",
    "SIM_LOG_DIR",
    "SIMULATOR_CONTROL_TOKEN",
    "SIMULATOR_CONTROL_PORT",
    "SIM_JMETER_BIN",
    "SIM_JMETER_WORK_DIR",
    "SIM_JMETER_HEAP",
    "SIM_JMETER_HTML_REPORT",
    "SIM_EXTERNAL_TARGETS_ENABLED",
    "SIM_REQUIRE_EXTERNAL_CONFIRMATION",
    "SIM_ALLOW_PRIVATE_TARGETS",
    "SIM_SSL_VERIFY",
    "SIMULATOR_CONTAINER_URL",
    "SIM_UI_DEFAULT_BASE_URL",
    "TZ",
)

UI_PORT_ENV_KEYS = ("TRAFFIC_SIMULATOR_UI_HOST_PORT", "MONITORING_UI_HOST_BIND")


def compose_config(compose_file: str) -> dict:
    cmd = [
        "docker",
        "compose",
        "-f",
        compose_file,
        "--env-file",
        str(FIXTURE_ENV),
        "--profile",
        "traffic",
        "config",
        "--format",
        "json",
    ]
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"docker compose config failed for {compose_file}:\n{proc.stderr or proc.stdout}"
        )
    return json.loads(proc.stdout)


def env_map(service: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in service.get("environment") or []:
        if isinstance(item, str) and "=" in item:
            k, v = item.split("=", 1)
            out[k] = v
        elif isinstance(item, dict):
            out.update(item)
    return out


def first_published_port(service: dict) -> tuple[str | None, str | None]:
    """Returns (bind_host, published_port) for the first ingress mapping."""
    for port in service.get("ports") or []:
        if isinstance(port, dict):
            return (
                str(port.get("host_ip") or "0.0.0.0"),
                str(port.get("published")) if port.get("published") is not None else None,
            )
        if isinstance(port, str):
            parts = port.split(":")
            if len(parts) >= 3:
                return parts[0], parts[1]
            if len(parts) == 2:
                return "0.0.0.0", parts[0]
    return None, None


def healthcheck_test(service: dict) -> list:
    hc = service.get("healthcheck") or {}
    return hc.get("test") or []


def build_block(service: dict) -> dict | None:
    build = service.get("build")
    if isinstance(build, dict):
        return build
    return None


def normalized_build_context(build: dict) -> str:
    ctx = build.get("context") or ""
    return str(Path(ctx).resolve())


def assert_traffic_build_context(services: dict, label: str) -> None:
    compose_dir = (ROOT / "compose").resolve()
    for name in TRAFFIC_SERVICES:
        build = build_block(services.get(name) or {})
        if not build:
            fail(f"{label} compose missing build block for {name}")
        ctx = normalized_build_context(build)
        if ctx == str(compose_dir):
            fail(
                f"{name} build context is compose/ ({ctx}); "
                "use context: .. in compose/traffic-services.yml"
            )
        if ctx != str(ROOT.resolve()):
            fail(f"{name} build context {ctx!r} != project root {ROOT.resolve()!r}")
        dockerfile = build.get("dockerfile") or ""
        if dockerfile:
            df_path = Path(ctx) / dockerfile
            if not df_path.is_file():
                fail(f"{name} dockerfile missing: {df_path}")


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def main() -> int:
    if not FIXTURE_ENV.is_file():
        fail(f"missing fixture {FIXTURE_ENV}")

    local = compose_config("docker-compose.yml")
    aws = compose_config("docker-compose.aws.yml")

    local_svcs = local.get("services") or {}
    aws_svcs = aws.get("services") or {}

    for name in TRAFFIC_SERVICES:
        if name not in local_svcs:
            fail(f"local compose missing service {name}")
        if name not in aws_svcs:
            fail(f"aws compose missing service {name}")

    assert_traffic_build_context(local_svcs, "local")
    assert_traffic_build_context(aws_svcs, "aws")

    for key in TRAFFIC_ENV_KEYS:
        for name in TRAFFIC_SERVICES:
            le = env_map(local_svcs[name])
            ae = env_map(aws_svcs[name])
            if key in le or key in ae:
                if le.get(key) != ae.get(key):
                    fail(
                        f"{name} env {key}: local={le.get(key)!r} aws={ae.get(key)!r}"
                    )

    ui_local = local_svcs["traffic-simulator-ui"]
    ui_aws = aws_svcs["traffic-simulator-ui"]

    bind_local, pub_local = first_published_port(ui_local)
    bind_aws, pub_aws = first_published_port(ui_aws)

    if pub_local != "8890":
        fail(f"local UI host port expected 8890, got {pub_local!r}")
    if pub_aws != "8890":
        fail(f"aws UI host port expected 8890, got {pub_aws!r}")

    if bind_local != "127.0.0.1":
        fail(f"local UI bind expected 127.0.0.1, got {bind_local!r}")
    if bind_aws != "127.0.0.1":
        fail(f"aws UI bind expected 127.0.0.1, got {bind_aws!r}")

    if healthcheck_test(local_svcs["traffic-simulator"]) != healthcheck_test(
        aws_svcs["traffic-simulator"]
    ):
        fail("traffic-simulator healthcheck differs between local and aws")

    if healthcheck_test(ui_local) != healthcheck_test(ui_aws):
        fail("traffic-simulator-ui healthcheck differs between local and aws")

    for label, compose_path in (
        ("local", ROOT / "docker-compose.yml"),
        ("aws", ROOT / "docker-compose.aws.yml"),
    ):
        text = compose_path.read_text(encoding="utf-8")
        if "TRAFFIC_SIMULATOR_UI_PORT" in text:
            fail(f"{label} compose still references deprecated TRAFFIC_SIMULATOR_UI_PORT")

    print("test_compose_traffic_parity.py: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
