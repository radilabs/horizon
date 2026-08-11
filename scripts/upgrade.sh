#!/usr/bin/env bash
# Upgrade an existing Horizon user installation from this source tree.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "${ROOT}/scripts/install.sh"
