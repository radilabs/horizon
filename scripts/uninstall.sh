#!/usr/bin/env bash
# Remove Horizon user installation files. Does not delete KWallet secrets or usage cache
# unless --purge is passed.
set -euo pipefail

LIB_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/horizon"
BIN="${HOME}/.local/bin/ai-usage"
CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/horizon"
PURGE=0

for arg in "$@"; do
  case "$arg" in
    --purge) PURGE=1 ;;
    -h|--help)
      echo "Usage: uninstall.sh [--purge]"
      echo "  --purge  also remove usage cache; still keeps KWallet Oasis token"
      exit 0
      ;;
  esac
done

if command -v kpackagetool6 >/dev/null 2>&1; then
  if kpackagetool6 --type Plasma/Applet --list 2>/dev/null | grep -q 'com.radilabs.horizon'; then
    kpackagetool6 --type Plasma/Applet --remove com.radilabs.horizon || true
  fi
fi

rm -f "${BIN}"
rm -rf "${LIB_DIR}/collector"
rmdir "${LIB_DIR}" 2>/dev/null || true

if [[ "${PURGE}" -eq 1 ]]; then
  rm -rf "${CACHE_DIR}"
  echo "Removed usage cache at ${CACHE_DIR}"
fi

echo "Horizon uninstalled."
echo "KWallet StepFun token (if any) was left in place."
echo "Clear it with: ai-usage auth stepfun clear   # if ai-usage still available"
echo "Or: keep using KWallet Manager to remove Horizon/stepfun/oasis-token"
