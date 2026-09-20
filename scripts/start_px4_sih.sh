#!/usr/bin/env bash
set -euo pipefail
PX4_DIR="${PX4_DIR:-$HOME/PX4-Autopilot}"
if [ ! -d "$PX4_DIR" ]; then
  echo "PX4-Autopilot not found: $PX4_DIR"
  echo "Set PX4_DIR to your PX4-Autopilot checkout, then rerun."
  exit 1
fi
cd "$PX4_DIR"
exec make px4_sitl_sih sihsim_quadx
