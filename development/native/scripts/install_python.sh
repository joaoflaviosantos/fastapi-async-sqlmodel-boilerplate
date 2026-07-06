#!/usr/bin/env bash
set -euo pipefail

PYTHON_VERSION="3.11.13"
POETRY_VERSION="2.1.4"
PREFIX="/usr/local"
BUILD_DIR="/usr/src/python-build"
NPROC="$(nproc)"

# locations for per-python poetry installs (separate to avoid clobbering)
POETRY_HOME_SYSTEM="$HOME/.local"
POETRY_HOME_PY311="$HOME/.local_py311"

if [ "$(id -u)" -eq 0 ]; then
  SUDO=""
else
  SUDO="sudo"
fi

echo "==> Updating apt and installing build dependencies..."
$SUDO apt-get update -y
$SUDO apt-get install -y --no-install-recommends \
  build-essential \
  ca-certificates \
  curl \
  wget \
  libssl-dev \
  zlib1g-dev \
  libbz2-dev \
  libreadline-dev \
  libsqlite3-dev \
  libffi-dev \
  libncursesw5-dev \
  libgdbm-dev \
  liblzma-dev \
  tk-dev \
  uuid-dev \
  xz-utils \
  make \
  gcc \
  libncurses5-dev \
  python3-distutils || true

echo
echo "==> Creating build directory: $BUILD_DIR"
$SUDO rm -rf "$BUILD_DIR"
$SUDO mkdir -p "$BUILD_DIR"
$SUDO chown "$(id -u):$(id -g)" "$BUILD_DIR"
cd "$BUILD_DIR"

PY_TARBALL="Python-${PYTHON_VERSION}.tar.xz"
PY_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/${PY_TARBALL}"

echo "==> Downloading Python ${PYTHON_VERSION} from: $PY_URL"
if [ -f "$PY_TARBALL" ]; then
  echo "   -> File already exists, skipping download"
else
  curl -fSL "$PY_URL" -o "$PY_TARBALL"
fi

echo "==> Extracting..."
tar -xf "$PY_TARBALL"

cd "Python-${PYTHON_VERSION}"

echo "==> Configuring build (prefix=${PREFIX})"
# --enable-optimizations uses PGO/LTO and takes longer, but produces faster binaries.
# Remove it if you'd prefer faster build times.
./configure --prefix="$PREFIX" --enable-optimizations --with-ensurepip=install

echo "==> Compiling (jobs=$NPROC). This may take several minutes..."
make -j"$NPROC"

echo "==> Installing with 'altinstall' (does not overwrite system 'python3')"
$SUDO make altinstall

echo
echo "==> Verifying Python installation:"
PY311_BIN="${PREFIX}/bin/python3.11"
if command -v "$PY311_BIN" >/dev/null 2>&1; then
  "$PY311_BIN" --version
else
  echo "ERROR: python3.11 not found in ${PREFIX}/bin. Check logs."
  exit 1
fi

echo
echo "==> Ensuring pip is available for python3.11"
if ! "$PY311_BIN" -m pip --version >/dev/null 2>&1; then
  echo "pip not found for python3.11 -> bootstrapping with ensurepip"
  "$PY311_BIN" -m ensurepip --upgrade
fi
echo "python3.11 pip: $($PY311_BIN -m pip --version | awk '{print $1,$2}')"

# -------------------------
# Install Poetry for system Python (python3)
# -------------------------
echo
echo "==> Installing Poetry ${POETRY_VERSION} for system python (python3) into $POETRY_HOME_SYSTEM"
# ensure curl exists
if ! command -v curl >/dev/null 2>&1; then
  echo "curl not found — installing curl..."
  $SUDO apt-get update -y
  $SUDO apt-get install -y --no-install-recommends curl ca-certificates
fi

# ensure pip for system python
if ! python3 -m pip --version >/dev/null 2>&1; then
  echo "pip for system python3 not found — installing python3-pip..."
  $SUDO apt-get update -y
  $SUDO apt-get install -y python3-pip
fi

# run installer with explicit XDG_DATA_HOME to isolate installs if needed (default is $HOME/.local)
env XDG_DATA_HOME="$POETRY_HOME_SYSTEM" curl -sSL https://install.python-poetry.org | python3 - --version "$POETRY_VERSION"

# -------------------------
# Install Poetry for python3.11
# -------------------------
echo
echo "==> Installing Poetry ${POETRY_VERSION} for Python 3.11 (${PY311_BIN}) into $POETRY_HOME_PY311"
env XDG_DATA_HOME="$POETRY_HOME_PY311" curl -sSL https://install.python-poetry.org | "$PY311_BIN" - --version "$POETRY_VERSION"

# -------------------------
# Ensure PATH is updated for both poetry installs
# -------------------------
echo
echo "==> Ensuring PATH entries are present in ~/.bashrc and ~/.profile (idempotent)"

BASHRC="$HOME/.bashrc"
PROFILE="$HOME/.profile"

add_path_if_missing() {
  local path_line="$1"
  local file="$2"
  if [ ! -f "$file" ]; then
    touch "$file"
  fi
  if ! grep -qxF "$path_line" "$file" 2>/dev/null; then
    echo "$path_line" >> "$file"
    echo "Added $path_line to $file"
  else
    echo "Line already present in $file: $path_line"
  fi
}

# lines to add
LINE1='export PATH="$HOME/.local/bin:$PATH"'
LINE2='export PATH="$HOME/.local_py311/bin:$PATH"'

add_path_if_missing "$LINE1" "$BASHRC"
add_path_if_missing "$LINE2" "$BASHRC"
add_path_if_missing "$LINE1" "$PROFILE"
add_path_if_missing "$LINE2" "$PROFILE"

# apply to current session so we can verify right away
export PATH="$HOME/.local/bin:$HOME/.local_py311/bin:$PATH"
hash -r

echo
echo "==> Verifying installations (both should report Poetry ${POETRY_VERSION})"

if command -v poetry >/dev/null 2>&1; then
  echo "Default 'poetry' (first found in PATH):"
  poetry --version || true
else
  echo "poetry not found in PATH for current session."
fi

# check explicit locations
POETRY_SYS_BIN="$POETRY_HOME_SYSTEM/bin/poetry"
POETRY_PY311_BIN="$POETRY_HOME_PY311/bin/poetry"

if [ -x "$POETRY_SYS_BIN" ]; then
  echo "System-Python poetry at: $POETRY_SYS_BIN -> $( "$POETRY_SYS_BIN" --version 2>/dev/null || true )"
else
  echo "System-Python poetry binary not found at $POETRY_SYS_BIN"
fi

if [ -x "$POETRY_PY311_BIN" ]; then
  echo "Python3.11 poetry at: $POETRY_PY311_BIN -> $( "$POETRY_PY311_BIN" --version 2>/dev/null || true )"
else
  echo "Python3.11 poetry binary not found at $POETRY_PY311_BIN"
fi

# -------------------------
# Create system-wide symlinks for convenience
# -------------------------
echo
echo "==> Creating system-wide symlinks in /usr/local/bin (requires sudo) for convenience:"
echo "  /usr/local/bin/poetry -> $POETRY_SYS_BIN"
echo "  /usr/local/bin/poetry3.11 -> $POETRY_PY311_BIN"

if [ -x "$POETRY_SYS_BIN" ]; then
  $SUDO ln -sf "$POETRY_SYS_BIN" /usr/local/bin/poetry
  $SUDO chmod +x /usr/local/bin/poetry || true
  echo "Created /usr/local/bin/poetry"
fi

if [ -x "$POETRY_PY311_BIN" ]; then
  $SUDO ln -sf "$POETRY_PY311_BIN" /usr/local/bin/poetry3.11
  $SUDO chmod +x /usr/local/bin/poetry3.11 || true
  echo "Created /usr/local/bin/poetry3.11"
fi

echo
echo "==> Cleanup build directory (optional)"
cd /
$SUDO rm -rf "$BUILD_DIR"

echo
echo "==> Completed. Quick usage notes:"
echo "- 'poetry' will point to the system-python installation (also accessible via $POETRY_SYS_BIN)."
echo "- 'poetry3.11' will point to the poetry installed under Python 3.11 (also accessible via $POETRY_PY311_BIN)."
echo "- Both installs live in the user home directories:"
echo "    system : $POETRY_HOME_SYSTEM"
echo "    python3.11 : $POETRY_HOME_PY311"
echo "- To ensure shell sessions pick up the PATH changes, open a new terminal or run: source ~/.bashrc (or source ~/.profile)."
echo
echo "Python3.11: $($PY311_BIN --version)"
echo "System python: $(python3 --version 2>/dev/null || echo 'not found')"
echo "Poetry (poetry): $(command -v poetry >/dev/null 2>&1 && poetry --version || echo 'poetry not found')"
echo "Poetry (poetry3.11): $(command -v poetry3.11 >/dev/null 2>&1 && poetry3.11 --version || echo 'poetry3.11 not found')"

exit 0
