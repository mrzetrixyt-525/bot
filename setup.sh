#!/usr/bin/env bash
# =============================================================================
# RGNODES™ VPS Bot — Deep Auto Setup / Repair v9
# Debian/Ubuntu • LXD • SSH • libvirt/KVM (best-effort) • Python venv • PM2
# Safe: never overwrites existing .env or vps.db; idempotent and rollback-aware.
# =============================================================================
set -Eeuo pipefail
IFS=$'\n\t'
umask 022

APP_DIR="${RGNODES_APP_DIR:-/root/rgnodes-vps-bot}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
SERVICE_NAME="bot.service"
PM2_APP="RGNODES-VPS-BOT"
LOG_FILE="/var/log/rgnodes-setup.log"
LOCK_FILE="/run/lock/rgnodes-setup.lock"
BACKUP_ROOT="/var/backups/rgnodes-bot"

log(){ printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
warn(){ log "⚠️ $*"; }
die(){ log "❌ $*"; exit 1; }

mkdir -p /run/lock "$BACKUP_ROOT" /var/log
exec 9>"$LOCK_FILE"
if command -v flock >/dev/null 2>&1; then
  flock -n 9 || die "Another RGNODES™ setup/repair process is already running."
fi
exec > >(tee -a "$LOG_FILE") 2>&1
trap 'rc=$?; (( rc != 0 )) && warn "Setup stopped at line $LINENO (exit $rc). See $LOG_FILE"' EXIT

[[ $EUID -eq 0 ]] || die 'Run as root: sudo bash setup_rgnodes.sh'
command -v apt >/dev/null 2>&1 || die 'apt is required.'

export DEBIAN_FRONTEND=noninteractive
export APT_LISTCHANGES_FRONTEND=none
export NEEDRESTART_MODE=a

. /etc/os-release
log "Detected: ${PRETTY_NAME:-unknown}"
case "${ID:-}" in
  debian|ubuntu) ;;
  *) warn "This setup is optimized for Debian/Ubuntu; continuing with safety checks." ;;
esac

# ---------- helpers ----------
retry(){
  local attempts="$1"; shift
  local i
  for ((i=1;i<=attempts;i++)); do
    if "$@"; then return 0; fi
    (( i < attempts )) && sleep $((i*2))
  done
  return 1
}

pkg_install(){
  apt install -y --no-install-recommends "$@"
}

backup_runtime(){
  local stamp dir
  stamp="$(date '+%Y%m%d_%H%M%S')"
  dir="$BACKUP_ROOT/$stamp"
  mkdir -p "$dir"
  [[ -f "$APP_DIR/bot.py" ]] && cp -a "$APP_DIR/bot.py" "$dir/" || true
  [[ -f "$APP_DIR/requirements.txt" ]] && cp -a "$APP_DIR/requirements.txt" "$dir/" || true
  [[ -f "$APP_DIR/ecosystem.config.js" ]] && cp -a "$APP_DIR/ecosystem.config.js" "$dir/" || true
  [[ -f "$APP_DIR/node-agent.py" ]] && cp -a "$APP_DIR/node-agent.py" "$dir/" || true
  [[ -f "$APP_DIR/.env" ]] && cp -a "$APP_DIR/.env" "$dir/.env" || true
  for db in "$APP_DIR"/*.db "$APP_DIR"/*.db-wal "$APP_DIR"/*.db-shm; do
    [[ -f "$db" ]] && cp -a "$db" "$dir/" || true
  done
  if [[ -d "$APP_DIR/db_backups" ]]; then cp -a "$APP_DIR/db_backups" "$dir/"; fi
  echo "$dir" > "$BACKUP_ROOT/latest"
  chmod 700 "$dir"
  log "Backup: $dir"
}

# ---------- base host packages ----------
log "📦 Updating package indexes..."
retry 5 apt update || die 'apt update failed after retries.'

log "📦 Installing host dependencies..."
pkg_install \
  python3 python3-pip python3-venv python3-dev \
  build-essential libffi-dev pkg-config \
  curl ca-certificates git unzip \
  sudo openssh-server openssh-client \
  util-linux procps iproute2 iputils-ping net-tools \
  lsb-release \
  snapd

# ---------- SSH ----------
log "🔐 Repairing OpenSSH baseline..."
mkdir -p /etc/ssh /run/sshd
[[ -e /etc/ssh/sshd_config ]] || touch /etc/ssh/sshd_config
chmod 0755 /etc/ssh
chmod 0600 /etc/ssh/sshd_config 2>/dev/null || true

SSHD_UNIT=""
if systemctl list-unit-files ssh.service >/dev/null 2>&1; then SSHD_UNIT=ssh; fi
if [[ -z "$SSHD_UNIT" ]] && systemctl list-unit-files sshd.service >/dev/null 2>&1; then SSHD_UNIT=sshd; fi

if command -v sshd >/dev/null 2>&1; then
  sshd -t || die 'Existing sshd configuration is invalid; fix it before restarting SSH.'
fi
if [[ -n "$SSHD_UNIT" ]]; then
  systemctl enable --now "$SSHD_UNIT" || warn "Could not start $SSHD_UNIT automatically."
fi

log "🔎 SSH config:"
ls -la /etc/ssh/sshd_config || true

# ---------- libvirt / KVM ----------
log "🧩 Checking hardware virtualization (diagnostic only)..."
if command -v lscpu >/dev/null 2>&1; then
  lscpu | grep -iE '^Virtualization|^Virtualization type' || warn 'Hardware virtualization flags are not visible. LXC can still work; nested KVM may not.'
fi

log "📦 Installing libvirt/KVM packages when available..."
# These are host-side helpers. Failure here must not block LXD/LXC deployments.
if ! pkg_install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virt-manager virtinst; then
  warn 'Some KVM/libvirt packages are unavailable on this host/repository; continuing with LXD.'
fi

for unit in libvirtd virtqemud; do
  if systemctl list-unit-files "$unit.service" >/dev/null 2>&1; then
    systemctl enable --now "$unit" || warn "$unit could not be started."
  fi
done
systemctl status libvirtd --no-pager >/dev/null 2>&1 || true

# root is the runtime user for this bot; group changes are harmless and retained.
usermod -aG libvirt root >/dev/null 2>&1 || true
usermod -aG kvm root >/dev/null 2>&1 || true

# ---------- LXD ----------
log "🦎 Detecting LXD..."
if ! command -v lxc >/dev/null 2>&1; then
  log "LXD CLI missing; installing official snap package."
  systemctl enable --now snapd.socket >/dev/null 2>&1 || true
  if ! snap list lxd >/dev/null 2>&1; then
    snap install lxd
  fi
fi

# Prefer snap binaries when present, but don't create dangerous aliases over an existing native installation.
command -v lxd >/dev/null 2>&1 || [[ -x /snap/bin/lxd ]] || die 'lxd command is unavailable.'
command -v lxc >/dev/null 2>&1 || [[ -x /snap/bin/lxc ]] || die 'lxc command is unavailable.'
export PATH="/snap/bin:$PATH"
hash -r

mkdir -p /etc/lxd

lxd_initialized=0
if lxc info >/dev/null 2>&1; then
  lxd_initialized=1
fi

if (( lxd_initialized == 0 )); then
  log "🛠️ Initializing LXD without interactive prompts..."
  if [[ ! -e /dev/loop-control ]]; then
    warn '/dev/loop-control is unavailable; forcing non-loop dir storage.'
  fi

  # A deterministic preseed avoids `lxd init --auto` choosing loop/LVM on nested hosts.
  # It is also safe to use when dir storage is required explicitly.
  cat > /tmp/rgnodes-lxd-preseed.yaml <<'YAML'
config: {}
networks:
- name: lxdbr0
  type: bridge
  description: RGNODES NAT bridge
  config:
    ipv4.address: auto
    ipv4.nat: "true"
    ipv6.address: auto
    ipv6.nat: "true"
storage_pools:
- name: default
  driver: dir
  description: RGNODES non-loop storage
  config: {}
profiles:
- name: default
  description: RGNODES default profile
  config: {}
  devices:
    eth0:
      type: nic
      name: eth0
      network: lxdbr0
    root:
      type: disk
      path: /
      pool: default
YAML
  if ! lxd init --preseed < /tmp/rgnodes-lxd-preseed.yaml; then
    rm -f /tmp/rgnodes-lxd-preseed.yaml
    die 'LXD initialization failed.'
  fi
  rm -f /tmp/rgnodes-lxd-preseed.yaml
else
  log "✅ LXD already initialized; preserving existing configuration."
fi

# ---------- Repair/validate LXD objects ----------
log "🔎 Validating LXD storage/network/profile..."
if ! lxc storage show default >/dev/null 2>&1; then
  warn 'Storage pool "default" is missing.'
  # Only create it when there are no existing pools. Never overwrite a live pool.
  pool_count="$(lxc storage list --format csv 2>/dev/null | sed '/^$/d' | wc -l || echo 0)"
  if [[ "$pool_count" -eq 0 ]]; then
    lxc storage create default dir || die 'Could not create default dir storage pool.'
  else
    warn 'Existing storage pools detected; refusing destructive pool replacement. Set DEFAULT_STORAGE_POOL in .env to the correct pool.'
  fi
fi

if ! lxc network show lxdbr0 >/dev/null 2>&1; then
  log 'Creating missing lxdbr0 NAT network.'
  lxc network create lxdbr0 ipv4.address=auto ipv4.nat=true ipv6.address=auto ipv6.nat=true || warn 'Could not create lxdbr0.'
fi
# Upgrade an existing managed lxdbr0 from IPv6-disabled to managed dual-stack only when it is explicitly disabled.
if lxc network show lxdbr0 >/dev/null 2>&1; then
  ipv6_state="$(lxc network get lxdbr0 ipv6.address 2>/dev/null || true)"
  if [[ "$ipv6_state" == "none" || -z "$ipv6_state" ]]; then
    lxc network set lxdbr0 ipv6.address auto >/dev/null 2>&1 || warn 'Could not enable managed IPv6 on lxdbr0.'
    lxc network set lxdbr0 ipv6.nat true >/dev/null 2>&1 || true
  fi
fi

if ! lxc profile show default >/dev/null 2>&1; then
  lxc profile create default || true
fi
# Add missing devices without replacing existing custom devices.
lxc profile device show default 2>/dev/null | grep -q '^root:' || lxc profile device add default root disk path=/ pool=default || true
lxc profile device show default 2>/dev/null | grep -q '^eth0:' || lxc profile device add default eth0 nic name=eth0 network=lxdbr0 || true

lxc storage show default >/dev/null 2>&1 || warn 'default storage is still unavailable.'
lxc network show lxdbr0 >/dev/null 2>&1 || warn 'lxdbr0 is still unavailable.'
lxc profile show default >/dev/null 2>&1 || die 'default LXD profile is unavailable.'
lxc info >/dev/null 2>&1 || die 'LXD daemon is not responding.'

# ZFS/udev are optional for dir storage. Do not fail the installer if absent.
modprobe zfs >/dev/null 2>&1 || udevadm trigger >/dev/null 2>&1 || true
source /etc/profile >/dev/null 2>&1 || true
hash -r

# ---------- bot source ----------
log "📁 Locating bot files..."
BOT_SOURCE=""
REQ_SOURCE=""
for candidate in "$SCRIPT_DIR/bot.py" "$SCRIPT_DIR/../bot.py" "/root/bot.py"; do
  if [[ -f "$candidate" ]]; then BOT_SOURCE="$candidate"; break; fi
done
[[ -n "$BOT_SOURCE" ]] || die 'bot.py not found.'

for candidate in "$SCRIPT_DIR/requirements.txt" "$APP_DIR/requirements.txt" "/root/requirements.txt"; do
  if [[ -f "$candidate" ]]; then REQ_SOURCE="$candidate"; break; fi
done
[[ -n "$REQ_SOURCE" ]] || die 'requirements.txt not found.'

mkdir -p "$APP_DIR" "$APP_DIR/db_backups" "$APP_DIR/vps_backups" /var/log
# Stop only our bot before taking the application/database snapshot.
systemctl stop "$SERVICE_NAME" >/dev/null 2>&1 || true
pm2 delete "$PM2_APP" >/dev/null 2>&1 || true
backup_runtime

# Preserve .env and DB at all costs.
if [[ ! -f "$APP_DIR/.env" ]]; then
  if [[ -f "$SCRIPT_DIR/.env.example" ]]; then
    install -m 0600 "$SCRIPT_DIR/.env.example" "$APP_DIR/.env"
    warn "Created $APP_DIR/.env from .env.example. Set DISCORD_TOKEN before start."
  else
    : > "$APP_DIR/.env"
    chmod 0600 "$APP_DIR/.env"
    warn "Created empty $APP_DIR/.env. Set DISCORD_TOKEN before start."
  fi
else
  chmod 0600 "$APP_DIR/.env"
fi

install -m 0755 "$BOT_SOURCE" "$APP_DIR/bot.py"
install -m 0644 "$REQ_SOURCE" "$APP_DIR/requirements.txt"
# Add new optional environment defaults only when missing; never overwrite an existing value.
ensure_env_default(){
  local key="$1" value="$2"
  touch "$APP_DIR/.env"
  chmod 0600 "$APP_DIR/.env"
  if ! grep -qE "^[[:space:]]*${key}=" "$APP_DIR/.env"; then
    printf '%s=%s\n' "$key" "$value" >> "$APP_DIR/.env"
  fi
}
ensure_env_default AUTO_DETECT_PUBLIC_IP true
ensure_env_default DOCKER_INSTALL_ON_DEPLOY true
ensure_env_default DOCKER_STRICT_DEPLOY false
ensure_env_default PINGGY_ENABLED true
ensure_env_default PINGGY_AUTO_START true
ensure_env_default PINGGY_HOST free.pinggy.io
ensure_env_default PINGGY_SSH_PORT 443
ensure_env_default EMOJI_LOADING Loading
ensure_env_default EMOJI_MAINTENANCE WiFi_Maintenance
ensure_env_default EMOJI_PINGGY WiFi_Online
ensure_env_default EMOJI_PINGGY_OFFLINE WiFi_Offline

if [[ -f "$SCRIPT_DIR/node-agent.py" ]]; then
  install -m 0755 "$SCRIPT_DIR/node-agent.py" "$APP_DIR/node-agent.py"
fi

# ---------- Python environment ----------
log "🐍 Creating/repairing isolated Python environment..."
VENV_CREATED=0
if [[ ! -x "$APP_DIR/.venv/bin/python" ]]; then
  "$PYTHON_BIN" -m venv "$APP_DIR/.venv"
  VENV_CREATED=1
fi
TOOL_HASH="$(printf '%s\n' "python-packaging-tools-v1" | sha256sum | awk '{print $1}')"
OLD_TOOL_HASH="$(cat "$APP_DIR/.packaging-tools.sha256" 2>/dev/null || true)"
if [[ "$VENV_CREATED" -eq 1 || "$TOOL_HASH" != "$OLD_TOOL_HASH" ]]; then
  log "🔧 Updating isolated pip tooling (first run/version marker changed)..."
  "$APP_DIR/.venv/bin/python" -m pip install --upgrade pip setuptools wheel >/dev/null
  printf '%s\n' "$TOOL_HASH" > "$APP_DIR/.packaging-tools.sha256"
else
  log "✅ Python packaging tools already initialized; skipping upgrade."
fi
REQ_HASH="$(sha256sum "$APP_DIR/requirements.txt" | awk '{print $1}')"
INSTALLED_REQ_HASH="$(cat "$APP_DIR/.requirements.sha256" 2>/dev/null || true)"
if [[ "$REQ_HASH" != "$INSTALLED_REQ_HASH" ]] || ! "$APP_DIR/.venv/bin/python" -m pip check >/dev/null 2>&1; then
  log "📦 Python requirements changed or incomplete; synchronizing dependencies..."
  "$APP_DIR/.venv/bin/python" -m pip install -r "$APP_DIR/requirements.txt"
  printf '%s\n' "$REQ_HASH" > "$APP_DIR/.requirements.sha256"
else
  log "✅ Python requirements already synchronized; skipping reinstall."
fi

# Explicitly ensure DAVE/PyNaCl requested by the user are installed if requirements omitted them.
if ! "$APP_DIR/.venv/bin/python" -c 'import davey, nacl' >/dev/null 2>&1; then
  log "📦 Optional requested Python security dependencies are missing; installing them."
  "$APP_DIR/.venv/bin/python" -m pip install 'davey>=0.1.6,<0.2' 'PyNaCl>=1.6.2,<2'
fi

log "🧪 Validating Python syntax/imports..."
"$APP_DIR/.venv/bin/python" -m py_compile "$APP_DIR/bot.py"
"$APP_DIR/.venv/bin/python" - <<'PY'
import importlib
for name in ('discord', 'dotenv', 'requests', 'psutil', 'nacl', 'davey'):
    importlib.import_module(name)
print('dependency-import-smoke-test: OK')
PY

# ---------- permissions / stale locks ----------
log "🔒 Repairing ownership/permissions and stale runtime files..."
chown -R root:root "$APP_DIR"
chmod 0755 "$APP_DIR"
chmod 0600 "$APP_DIR/.env" 2>/dev/null || true
find "$APP_DIR" -maxdepth 1 -type f -name '*.db' -exec chmod 0600 {} + 2>/dev/null || true
find "$APP_DIR/db_backups" "$APP_DIR/vps_backups" -type f -exec chmod 0600 {} + 2>/dev/null || true
chmod 0755 "$APP_DIR/node-agent.py" 2>/dev/null || true
mkdir -p /run/rgnodes
chmod 0755 /run/rgnodes
rm -f /run/rgnodes/*.pid /run/rgnodes/*.lock 2>/dev/null || true

# ---------- Node.js / PM2 runtime ----------
log "🟢 Checking Node.js runtime..."
NODE_MAJOR=0
if command -v node >/dev/null 2>&1; then
  NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)"
fi
if ! [[ "$NODE_MAJOR" =~ ^[0-9]+$ ]] || (( NODE_MAJOR < 20 )); then
  log "📦 Current Node.js is below 20; installing Node.js 24 LTS."
  ARCH="$(dpkg --print-architecture 2>/dev/null || true)"
  case "$ARCH" in
    amd64) NODE_ARCH=x64 ;;
    arm64) NODE_ARCH=arm64 ;;
    ppc64el) NODE_ARCH=ppc64le ;;
    s390x) NODE_ARCH=s390x ;;
    *) die "Unsupported architecture $ARCH for automatic Node.js installation. Install Node.js >=20 manually." ;;
  esac
  NODE_VERSION=24.21.0
  NODE_TARBALL="node-v${NODE_VERSION}-linux-${NODE_ARCH}.tar.xz"
  NODE_URL="https://nodejs.org/dist/v${NODE_VERSION}/${NODE_TARBALL}"
  curl -fL --retry 5 --retry-delay 2 -o "/tmp/$NODE_TARBALL" "$NODE_URL"
  rm -rf "/opt/node-v${NODE_VERSION}-linux-${NODE_ARCH}"
  tar -xJf "/tmp/$NODE_TARBALL" -C /opt
  ln -sfn "/opt/node-v${NODE_VERSION}-linux-${NODE_ARCH}" /opt/node
  ln -sfn /opt/node/bin/node /usr/local/bin/node
  ln -sfn /opt/node/bin/npm /usr/local/bin/npm
  ln -sfn /opt/node/bin/npx /usr/local/bin/npx
  NODE_MAJOR="$(/usr/local/bin/node -p 'process.versions.node.split(".")[0]')"
  (( NODE_MAJOR >= 20 )) || die "Node.js installation did not produce a supported runtime."
fi
node --version
npm --version

# ---------- PM2 ----------
log "⚙️ Checking PM2..."
if command -v pm2 >/dev/null 2>&1 && command -v pm2-runtime >/dev/null 2>&1; then
  log "✅ PM2 already installed; skipping global reinstall."
else
  log "📦 PM2 missing/incomplete; installing..."
  npm install -g pm2
fi
PM2_RUNTIME="$(command -v pm2-runtime || true)"
[[ -n "$PM2_RUNTIME" ]] || [[ -x /usr/local/lib/node_modules/pm2/bin/pm2-runtime.js ]] || die 'pm2-runtime not found.'

# Encode paths as JSON strings using Python to avoid shell/JS quoting corruption.
APP_DIR_JSON="$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$APP_DIR")"
PYTHON_JSON="$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$APP_DIR/.venv/bin/python")"

cat > "$APP_DIR/ecosystem.config.js" <<EOFJS
module.exports = {
  apps: [{
    name: 'RGNODES-VPS-BOT',
    cwd: $APP_DIR_JSON,
    script: 'bot.py',
    interpreter: $PYTHON_JSON,
    interpreter_args: '-u',
    exec_mode: 'fork',
    instances: 1,
    autorestart: true,
    restart_delay: 5000,
    exp_backoff_restart_delay: 100,
    max_memory_restart: '768M',
    kill_timeout: 15000,
    listen_timeout: 15000,
    merge_logs: true,
    time: false,
    env: {
      PYTHONUNBUFFERED: '1'
    }
  }]
};
EOFJS
node --check "$APP_DIR/ecosystem.config.js"

# ---------- systemd wrapper ----------
log "🛡️ Installing single-process systemd → PM2 runtime supervision..."
cat > "/etc/systemd/system/$SERVICE_NAME" <<EOFUNIT
[Unit]
Description=RGNODES VPS Bot - PM2 Runtime
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
Environment=HOME=/root
Environment=PM2_HOME=/root/.pm2
Environment=PYTHONUNBUFFERED=1
ExecStart=$PM2_RUNTIME $APP_DIR/ecosystem.config.js
Restart=always
RestartSec=5
KillMode=mixed
TimeoutStopSec=30
LimitNOFILE=65535
TasksMax=infinity

[Install]
WantedBy=multi-user.target
EOFUNIT

# ---------- optional system health ----------
cat > /usr/local/sbin/rgnodes-healthcheck <<'EOF'
#!/usr/bin/env bash
set -u
if ! command -v lxc >/dev/null 2>&1; then exit 0; fi
lxc info >/dev/null 2>&1 || exit 0
ENV_FILE="/root/rgnodes-vps-bot/.env"
if [[ -f "$ENV_FILE" ]] && grep -qE '^DISCORD_TOKEN[[:space:]]*=[[:space:]]*$' "$ENV_FILE"; then exit 0; fi
systemctl is-enabled --quiet bot.service || exit 0
systemctl restart bot.service >/dev/null 2>&1 || true
EOF
chmod 0755 /usr/local/sbin/rgnodes-healthcheck
cat > /etc/systemd/system/rgnodes-healthcheck.service <<'EOF'
[Unit]
Description=RGNODES VPS Bot health check

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/rgnodes-healthcheck
EOF
cat > /etc/systemd/system/rgnodes-healthcheck.timer <<'EOF'
[Unit]
Description=RGNODES VPS Bot health check timer

[Timer]
OnBootSec=3min
OnUnitActiveSec=3min
AccuracySec=15s
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl enable --now rgnodes-healthcheck.timer >/dev/null 2>&1 || true

# Don't start a crash-loop when the operator has not entered the Discord token yet.
if grep -qE '^DISCORD_TOKEN[[:space:]]*=[[:space:]]*$' "$APP_DIR/.env"; then
  systemctl stop "$SERVICE_NAME" >/dev/null 2>&1 || true
  warn "DISCORD_TOKEN is empty; bot.service is installed/enabled but intentionally not started."
else
  systemctl restart "$SERVICE_NAME"
  sleep 4
fi

log "🧪 Final host validation..."
lxc info >/dev/null 2>&1 || die 'LXD validation failed.'
lxc storage show default >/dev/null 2>&1 || warn 'default storage pool not available.'
node --version || true
npm --version || true
"$APP_DIR/.venv/bin/python" --version
python3 -m py_compile "$APP_DIR/bot.py"
systemctl --no-pager --full status "$SERVICE_NAME" || true

if grep -qE '^DISCORD_TOKEN[[:space:]]*=[[:space:]]*$' "$APP_DIR/.env"; then
  warn "DISCORD_TOKEN is empty: edit $APP_DIR/.env before expecting Discord connection."
fi
if grep -q '^YOUR_SERVER_IP=127.0.0.1$' "$APP_DIR/.env" 2>/dev/null; then
  warn 'YOUR_SERVER_IP is 127.0.0.1; bot will prefer detected public IPv4 when AUTO_DETECT_PUBLIC_IP=true, but configure PUBLIC_IPV4 for reliable inbound access.'
fi

log "✅ RGNODES™ deep setup/repair completed."
log "Service: systemctl status $SERVICE_NAME"
log "Logs:    journalctl -u $SERVICE_NAME -f"
log "PM2:     pm2 list"
log "App:     $APP_DIR"
