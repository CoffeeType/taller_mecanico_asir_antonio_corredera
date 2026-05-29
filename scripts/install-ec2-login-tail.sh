#!/bin/bash
# Alias: instala progreso_docker (sustituye install-ec2-login-tail.sh).
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/install-progreso-docker.sh" "$@"
