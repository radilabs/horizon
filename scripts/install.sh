#!/usr/bin/env bash
# Install Horizon collector + Plasma plasmoid to stable user locations.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LIB_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/horizon/collector"
BIN_DIR="${HOME}/.local/bin"
PLASMOID_SRC="${ROOT}/plasmoid"

die() { echo "error: $*" >&2; exit 1; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing dependency: $1"
}

need_cmd python3
need_cmd kpackagetool6

if ! python3 -c 'import dbus' >/dev/null 2>&1; then
  die "Python D-Bus bindings required (e.g. python3-dbus) for StepFun KWallet storage"
fi

mkdir -p "${LIB_DIR}/providers" "${BIN_DIR}"

install -m 0755 "${ROOT}/collector/ai-usage" "${LIB_DIR}/ai-usage"
install -m 0644 "${ROOT}/collector/cache.py" "${LIB_DIR}/cache.py"
install -m 0644 "${ROOT}/collector/secret_store.py" "${LIB_DIR}/secret_store.py"
install -m 0644 "${ROOT}/collector/stepfun_auth_helper.py" "${LIB_DIR}/stepfun_auth_helper.py"
install -m 0644 "${ROOT}/collector/providers/__init__.py" "${LIB_DIR}/providers/__init__.py"
install -m 0644 "${ROOT}/collector/providers/codex.py" "${LIB_DIR}/providers/codex.py"
install -m 0644 "${ROOT}/collector/providers/cursor.py" "${LIB_DIR}/providers/cursor.py"
install -m 0644 "${ROOT}/collector/providers/stepfun.py" "${LIB_DIR}/providers/stepfun.py"

# Stable launcher (not a symlink into the git checkout)
cat > "${BIN_DIR}/ai-usage" <<EOF
#!/usr/bin/env bash
exec python3 "${LIB_DIR}/ai-usage" "\$@"
EOF
chmod 0755 "${BIN_DIR}/ai-usage"

if kpackagetool6 --type Plasma/Applet --list 2>/dev/null | grep -q 'com.radilabs.horizon'; then
  kpackagetool6 --type Plasma/Applet --upgrade "${PLASMOID_SRC}"
else
  kpackagetool6 --type Plasma/Applet --install "${PLASMOID_SRC}"
fi

echo "Horizon installed."
echo "  collector: ${LIB_DIR}"
echo "  launcher:  ${BIN_DIR}/ai-usage"
echo "  plasmoid:  com.radilabs.horizon"
echo
echo "Add the Horizon widget from the Plasma widget picker."
echo "StepFun token (optional): ai-usage auth stepfun set"
echo "Or configure providers / token from the widget settings."
