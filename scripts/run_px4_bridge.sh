#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${PX4_CONNECTION:=udpin:0.0.0.0:14540}"
export PX4_CONNECTION
python -m backend.px4_service
