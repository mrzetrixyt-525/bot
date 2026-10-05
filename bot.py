import discord
from discord.ext import commands
import asyncio
import subprocess
import json
from datetime import datetime, timedelta
import shlex
import logging
import shutil
import os
from typing import Optional, List, Dict, Any
import threading
import time
import sqlite3
import random
import requests
import string
import secrets
import base64
import socket
import re
import sys
import io
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Load environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
BOT_NAME = os.getenv('BOT_NAME', 'RGNODES™')
PREFIX = os.getenv('PREFIX', '-')
YOUR_SERVER_IP = os.getenv('YOUR_SERVER_IP', '').strip()
MAIN_ADMIN_ID = int(os.getenv('MAIN_ADMIN_ID', '1493564911039811725'))
VPS_USER_ROLE_ID = int(os.getenv('VPS_USER_ROLE_ID', '1503617617066197033'))
DEFAULT_STORAGE_POOL = os.getenv('DEFAULT_STORAGE_POOL', 'default')
DEFAULT_MOTD_TEXT = os.getenv('HOST_MOTD', 'Welcome to RGNODES™ Powerfull\nAuthorized access only. VPS resources are monitored for stability and safety.')[:1200]
HOST_MOTD = DEFAULT_MOTD_TEXT
VPS_BANDWIDTH_GB = 50  # Fixed plan bandwidth quota for every VPS.
LOG_HEALTH_INTERVAL = max(300, int(os.getenv('LOG_HEALTH_INTERVAL', '900')))
HOST_STATS_CACHE_TTL = max(3.0, float(os.getenv('HOST_STATS_CACHE_TTL', '8')))
GUEST_ACCESS_RETRY_INTERVAL = max(120, int(os.getenv('GUEST_ACCESS_RETRY_INTERVAL', '300')))
MAX_BACKGROUND_REPAIR_CONCURRENCY = max(1, min(4, int(os.getenv('MAX_BACKGROUND_REPAIR_CONCURRENCY', '2'))))
BANDWIDTH_SAMPLE_INTERVAL = max(300, int(os.getenv('BANDWIDTH_SAMPLE_INTERVAL', '600')))
BANDWIDTH_QUOTA_BYTES = VPS_BANDWIDTH_GB * 1024**3
# Background persistence / audit tuning: frequent full-database writes can create
# unnecessary disk I/O on a small Ryzen host. Critical operations still save immediately.
AUTOSAVE_INTERVAL = max(30, int(os.getenv('AUTOSAVE_INTERVAL', '60')))
AUDIT_NOISY_COMMANDS = {
    'ping', 'help', 'quickhelp', 'commands', 'stats', 'info', 'uptime',
}
LOG_CHANNEL_SNAPSHOT_LINES = max(8, min(30, int(os.getenv('LOG_CHANNEL_SNAPSHOT_LINES', '16'))))
BOT_VERSION = os.getenv('BOT_VERSION', '8.90 DeepFix Pro Max')
BOT_DEVELOPER = os.getenv('BOT_DEVELOPER', 'MrZetrix')
BOT_THUMBNAIL_URL = os.getenv('BOT_THUMBNAIL_URL', 'https://cdn.discordapp.com/icons/1503614184477167616/f1534b0b4cb22ff19872549b8a52d59f.webp?size=2048')
BOT_ICON_URL = os.getenv('BOT_ICON_URL', 'https://cdn.discordapp.com/icons/1503614184477167616/f1534b0b4cb22ff19872549b8a52d59f.webp?size=2048')
VPS_HOSTNAME = os.getenv('VPS_HOSTNAME', 'rgnodes-vps')
DEFAULT_VPS_RAM_GB = int(os.getenv('DEFAULT_VPS_RAM_GB', '8'))
DEFAULT_VPS_CPU = int(os.getenv('DEFAULT_VPS_CPU', '2'))
DEFAULT_VPS_STORAGE_GB = int(os.getenv('DEFAULT_VPS_STORAGE_GB', '25'))
DEFAULT_PORT_QUOTA = int(os.getenv('DEFAULT_PORT_QUOTA', '10'))
PORT_HOST_MIN = int(os.getenv('PORT_HOST_MIN', '20000'))
PORT_HOST_MAX = int(os.getenv('PORT_HOST_MAX', '50000'))
VPS_BACKUP_DIR_NAME = os.getenv('VPS_BACKUP_DIR', 'vps_backups')
VPS_RENEWAL_DAYS = int(os.getenv('VPS_RENEWAL_DAYS', '60'))
RENEWAL_WINDOW_DAYS = int(os.getenv('RENEWAL_WINDOW_DAYS', '2'))
ANTI_MINING_ENABLED = str(os.getenv('ANTI_MINING_ENABLED', 'true')).strip().lower() in {'1', 'true', 'yes', 'on'}

AUTO_DETECT_PUBLIC_IP = str(os.getenv('AUTO_DETECT_PUBLIC_IP', 'true')).strip().lower() in {'1','true','yes','on'}
PUBLIC_IPV4 = os.getenv('PUBLIC_IPV4', '').strip()
PUBLIC_IPV6 = os.getenv('PUBLIC_IPV6', '').strip()
# Docker is optional during provisioning; enabling it on the host can add avoidable memory/IO pressure.
DOCKER_STRICT_DEPLOY = str(os.getenv('DOCKER_STRICT_DEPLOY', 'false')).strip().lower() in {'1','true','yes','on'}
VPS_SWAP_ENABLED = str(os.getenv('VPS_SWAP_ENABLED', 'false')).strip().lower() in {'1','true','yes','on'}

HOST_PROVIDER_NAME = os.getenv('HOST_PROVIDER_NAME', 'RGNODES™ Powerfull').strip() or 'RGNODES™ Powerfull'
HOST_RAM_RESERVE_GB = max(0.5, float(os.getenv('HOST_RAM_RESERVE_GB', '1.5')))
HOST_DISK_RESERVE_GB = max(2.0, float(os.getenv('HOST_DISK_RESERVE_GB', '10')))
HOST_CPU_MAX_DEPLOY_PCT = max(50.0, min(95.0, float(os.getenv('HOST_CPU_MAX_DEPLOY_PCT', '85'))))
MIN_HOST_RAM_FREE_PCT_DEPLOY = max(5.0, min(50.0, float(os.getenv('MIN_HOST_RAM_FREE_PCT_DEPLOY', '18'))))
MAX_DEPLOY_RAM_SHARE = max(0.10, min(0.90, float(os.getenv('MAX_DEPLOY_RAM_SHARE', '0.80'))))
DEPLOY_EXECUTION_TIMEOUT = max(300, int(os.getenv('DEPLOY_EXECUTION_TIMEOUT', '1800')))
GUEST_BOOTSTRAP_TIMEOUT = max(120, int(os.getenv('GUEST_BOOTSTRAP_TIMEOUT', '600')))
# Docker can be enabled explicitly in .env, but the default is off to protect the main node.
DOCKER_INSTALL_ON_DEPLOY = str(os.getenv('DOCKER_INSTALL_ON_DEPLOY', 'false')).strip().lower() in {'1','true','yes','on'}
PINGGY_ENABLED = str(os.getenv('PINGGY_ENABLED', 'true')).strip().lower() in {'1','true','yes','on'}
PINGGY_AUTO_START = str(os.getenv('PINGGY_AUTO_START', 'true')).strip().lower() in {'1','true','yes','on'}
PINGGY_HOST = os.getenv('PINGGY_HOST', 'free.pinggy.io').strip() or 'free.pinggy.io'
PINGGY_SSH_PORT = int(os.getenv('PINGGY_SSH_PORT', '443'))
SSHX_ENABLED = str(os.getenv('SSHX_ENABLED', 'true')).strip().lower() in {'1','true','yes','on'}
AUTO_CREATE_SERVER_EMOJIS = str(os.getenv('AUTO_CREATE_SERVER_EMOJIS', 'true')).strip().lower() in {'1','true','yes','on'}
EMOJI_PROVISION_LOCK = asyncio.Lock()
DEPLOYMENT_GLOBAL_LOCK = asyncio.Lock()
TUNNEL_SETUP_LOCKS: Dict[tuple[str, int], asyncio.Lock] = {}
HOST_STATS_CACHE: Dict[int, tuple[float, Dict[str, Any]]] = {}
HOST_STATS_CACHE_LOCK = asyncio.Lock()
TUNNEL_REPAIR_INTERVAL = max(180, int(os.getenv('TUNNEL_REPAIR_INTERVAL', '900')))
ACCESS_REPAIR_INTERVAL = max(180, int(os.getenv('ACCESS_REPAIR_INTERVAL', '600')))
TUNNEL_START_TIMEOUT = max(25, int(os.getenv('TUNNEL_START_TIMEOUT', '65')))
SSHX_START_RETRIES = max(1, min(3, int(os.getenv('SSHX_START_RETRIES', '2'))))
SSHX_HEALTHCHECK_INTERVAL = max(30, int(os.getenv('SSHX_HEALTHCHECK_INTERVAL', '90')))
SSHX_SESSION_WAIT_SECONDS = max(15, min(90, int(os.getenv('SSHX_SESSION_WAIT_SECONDS', '45'))))
SSHX_ACTION_TIMEOUT = max(90, int(os.getenv('SSHX_ACTION_TIMEOUT', '140')))
DEPLOY_NODE_SERIALIZE = str(os.getenv('DEPLOY_NODE_SERIALIZE', 'true')).strip().lower() in {'1','true','yes','on'}
HOST_PROCESSOR_NAME = os.getenv('HOST_PROCESSOR_NAME', 'AMD Ryzen').strip() or 'AMD Ryzen'

# Custom Discord emoji names/codes. Upload your preferred animated emojis to your
# server and set these to the exact custom emoji name (or full <:name:id>/<a:name:id>).
# Emoji.gg currently documents real IDs such as `online` and `StatusOnline`; all other
# names below are safe local names you can create yourself. Unicode remains the fallback.
CUSTOM_EMOJI_NAMES = {
    'online': os.getenv('EMOJI_ONLINE', 'StatusOnline'),
    'status': os.getenv('EMOJI_STATUS', 'StatusOnline'),
    'vps': os.getenv('EMOJI_VPS', 'rgnodes_vps'),
    'deploy': os.getenv('EMOJI_DEPLOY', 'rgnodes_deploy'),
    'rocket': os.getenv('EMOJI_ROCKET', 'rgnodes_rocket'),
    'server': os.getenv('EMOJI_SERVER', 'rgnodes_server'),
    'cpu': os.getenv('EMOJI_CPU', 'rgnodes_cpu'),
    'ram': os.getenv('EMOJI_RAM', 'rgnodes_ram'),
    'disk': os.getenv('EMOJI_DISK', 'rgnodes_disk'),
    'network': os.getenv('EMOJI_NETWORK', 'rgnodes_network'),
    'docker': os.getenv('EMOJI_DOCKER', 'rgnodes_docker'),
    'ssh': os.getenv('EMOJI_SSH', 'rgnodes_ssh'),
    'sshx': os.getenv('EMOJI_SSHX', 'rgnodes_sshx'),
    'ports': os.getenv('EMOJI_PORTS', 'rgnodes_ports'),
    'password': os.getenv('EMOJI_PASSWORD', 'rgnodes_password'),
    'reinstall': os.getenv('EMOJI_REINSTALL', 'rgnodes_reinstall'),
    'renew': os.getenv('EMOJI_RENEW', 'rgnodes_renew'),
    'start': os.getenv('EMOJI_START', 'rgnodes_start'),
    'stop': os.getenv('EMOJI_STOP', 'rgnodes_stop'),
    'stats': os.getenv('EMOJI_STATS', 'rgnodes_stats'),
    'refresh': os.getenv('EMOJI_REFRESH', 'rgnodes_refresh'),
    'delete': os.getenv('EMOJI_DELETE', 'rgnodes_delete'),
    'success': os.getenv('EMOJI_SUCCESS', 'rgnodes_success'),
    'warning': os.getenv('EMOJI_WARNING', 'rgnodes_warning'),
    'error': os.getenv('EMOJI_ERROR', 'StatusOffline'),
    'offline': os.getenv('EMOJI_OFFLINE', 'StatusOffline'),
    'loading': os.getenv('EMOJI_LOADING', 'Loading'),
    'maintenance': os.getenv('EMOJI_MAINTENANCE', 'WiFi_Maintenance'),
    'pinggy': os.getenv('EMOJI_PINGGY', 'WiFi_Online'),
    'pinggy_offline': os.getenv('EMOJI_PINGGY_OFFLINE', 'WiFi_Offline'),
}

# VPS Expiration Settings
DEFAULT_VPS_EXPIRATION_DAYS = int(os.getenv('DEFAULT_VPS_EXPIRATION_DAYS', '60'))
EXPIRATION_WARNING_DAYS = int(os.getenv('EXPIRATION_WARNING_DAYS', '2'))

# SSH Configuration
SSH_FIX_SCRIPT = None  # Deprecated; configure_ssh uses an sshd_config.d drop-in.


# OS Options for VPS Creation and Reinstall
OS_OPTIONS = [
    {"label": "Ubuntu 20.04 LTS", "value": "ubuntu:20.04"},
    {"label": "Ubuntu 22.04 LTS", "value": "ubuntu:22.04"},
    {"label": "Ubuntu 24.04 LTS", "value": "ubuntu:24.04"},
    {"label": "Debian 11", "value": "images:debian/11"},
    {"label": "Debian 12 (Bookworm)", "value": "images:debian/12"},
    {"label": "Debian 13 (Trixie)", "value": "images:debian/13"},
]

LXD_IMAGE_CANDIDATES = {
    "ubuntu:20.04": ["ubuntu:20.04", "ubuntu:focal", "images:ubuntu/20.04", "images:ubuntu/focal"],
    "ubuntu:22.04": ["ubuntu:22.04", "ubuntu:jammy", "images:ubuntu/22.04", "images:ubuntu/jammy"],
    "ubuntu:24.04": ["ubuntu:24.04", "ubuntu:noble", "images:ubuntu/24.04", "images:ubuntu/noble"],
    "images:debian/11": ["images:debian/11", "images:debian/11/default", "images:debian/bullseye", "images:debian/bullseye/default", "images:debian/11/cloud", "debian:11", "debian:bullseye"],
    "images:debian/12": ["images:debian/12", "images:debian/12/default", "images:debian/bookworm", "images:debian/bookworm/default", "images:debian/12/cloud", "debian:12", "debian:bookworm"],
    "images:debian/13": ["images:debian/13", "images:debian/13/default", "images:debian/trixie", "images:debian/trixie/default", "images:debian/13/cloud", "debian:13", "debian:trixie"],
}

# Configure logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(f'{BOT_NAME.lower()}_vps_bot')

# Prevent accidental duplicate Discord gateway sessions.
PROCESS_LOCK_HANDLE = None
try:
    import fcntl
    _lock_path = Path(__file__).resolve().parent / 'bot-process.lock'
    PROCESS_LOCK_HANDLE = open(_lock_path, 'a+', encoding='utf-8')
    fcntl.flock(PROCESS_LOCK_HANDLE.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    print('Another RGNODES™ bot process is already running; exiting.', file=sys.stderr)
    raise SystemExit(1)
except Exception as _lock_error:
    print(f'Warning: bot process lock unavailable: {_lock_error}', file=sys.stderr)

# ═══════════════════════════════════════════════════════════════════════════
# ROBUST SQLITE DATABASE SYSTEM - PERSISTENT + CRASH SAFE + SILENT SAVES
# ═══════════════════════════════════════════════════════════════════════════

import atexit
from pathlib import Path

# Always keep the database beside this Python file.
# This prevents a restart from another working directory creating a new vps.db.
BASE_DIR = Path(__file__).resolve().parent
DB_FILE = str(BASE_DIR / "vps.db")
DB_BACKUP_DIR = BASE_DIR / "db_backups"
DB_LOCK = threading.RLock()

DB_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
VPS_BACKUP_DIR = BASE_DIR / VPS_BACKUP_DIR_NAME
VPS_BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def get_db():
    """Open a reliable SQLite connection for persistent bot data."""
    conn = sqlite3.connect(
        DB_FILE,
        timeout=30.0,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row

    # WAL is configured once during init_db(). These settings are safe
    # for concurrent reads and writes and avoid unnecessary lock errors.
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA synchronous=FULL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA wal_autocheckpoint=1000")
    return conn


def backup_database():
    """Create a consistent SQLite backup without noisy console output."""
    try:
        if not os.path.exists(DB_FILE):
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = DB_BACKUP_DIR / f"vps_backup_{timestamp}.db"

        with DB_LOCK:
            source = get_db()
            try:
                destination = sqlite3.connect(str(backup_path))
                try:
                    source.backup(destination)
                finally:
                    destination.close()
            finally:
                source.close()

        backups = sorted(DB_BACKUP_DIR.glob("vps_backup_*.db"))
        for old_backup in backups[:-10]:
            try:
                old_backup.unlink()
            except OSError:
                pass
    except Exception as e:
        logger.error(f"Database backup failed: {e}")


def init_db():
    """Create/migrate every persistent table and verify database integrity."""
    with DB_LOCK:
        conn = get_db()
        try:
            if os.path.exists(DB_FILE):
                backup_database()
            # Configure WAL once instead of running journal_mode=WAL on every
            # connection. Repeated journal changes can cause lock errors.
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=FULL")
            conn.execute("PRAGMA foreign_keys=ON")

            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    user_id TEXT PRIMARY KEY,
                    added_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute(
                "INSERT OR IGNORE INTO admins (user_id) VALUES (?)",
                (str(MAIN_ADMIN_ID),),
            )

            cur.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    location TEXT,
                    total_vps INTEGER,
                    tags TEXT DEFAULT '[]',
                    api_key TEXT,
                    url TEXT,
                    is_local INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Make sure a local node always exists.
            cur.execute("SELECT id FROM nodes WHERE is_local = 1 ORDER BY id LIMIT 1")
            if cur.fetchone() is None:
                cur.execute("""
                    INSERT INTO nodes
                    (name, location, total_vps, tags, api_key, url, is_local)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("Local Node", "Local", 100, "[]", None, None, 1))

            cur.execute("""
                CREATE TABLE IF NOT EXISTS vps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    node_id INTEGER NOT NULL DEFAULT 1,
                    container_name TEXT UNIQUE NOT NULL,
                    ram TEXT NOT NULL,
                    cpu TEXT NOT NULL,
                    storage TEXT NOT NULL,
                    config TEXT NOT NULL,
                    os_version TEXT DEFAULT 'ubuntu:22.04',
                    status TEXT DEFAULT 'stopped',
                    suspended INTEGER DEFAULT 0,
                    whitelisted INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    shared_with TEXT DEFAULT '[]',
                    suspension_history TEXT DEFAULT '[]',
                    expiration_date TEXT DEFAULT NULL,
                    root_password TEXT DEFAULT NULL,
                    last_modified TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (node_id) REFERENCES nodes(id)
                )
            """)

            # Safe migrations for databases created by older bot versions.
            # SQLite does not permit non-constant defaults on ALTER TABLE ADD COLUMN,
            # so timestamp columns are added without a default and then backfilled.
            def ensure_column(table: str, column: str, ddl: str):
                cur.execute(f"PRAGMA table_info({table})")
                existing = {row[1] for row in cur.fetchall()}
                if column not in existing:
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")

            ensure_column("nodes", "last_updated", "last_updated TEXT")
            ensure_column("vps", "os_version", "os_version TEXT DEFAULT 'ubuntu:22.04'")
            ensure_column("vps", "node_id", "node_id INTEGER DEFAULT 1")
            ensure_column("vps", "expiration_date", "expiration_date TEXT DEFAULT NULL")
            ensure_column("vps", "root_password", "root_password TEXT DEFAULT NULL")
            ensure_column("vps", "last_modified", "last_modified TEXT")
            ensure_column("vps", "sshx_url", "sshx_url TEXT DEFAULT NULL")
            ensure_column("vps", "sshx_started_at", "sshx_started_at TEXT DEFAULT NULL")
            ensure_column("vps", "pinggy_host", "pinggy_host TEXT DEFAULT NULL")
            ensure_column("vps", "pinggy_port", "pinggy_port INTEGER")
            ensure_column("vps", "pinggy_url", "pinggy_url TEXT DEFAULT NULL")
            ensure_column("vps", "pinggy_pid", "pinggy_pid INTEGER")
            ensure_column("vps", "pinggy_started_at", "pinggy_started_at TEXT DEFAULT NULL")
            ensure_column("vps", "bandwidth_gb", "bandwidth_gb INTEGER DEFAULT 50")
            ensure_column("vps", "bandwidth_used_bytes", "bandwidth_used_bytes INTEGER DEFAULT 0")
            ensure_column("vps", "bandwidth_cycle_start", "bandwidth_cycle_start TEXT DEFAULT NULL")
            ensure_column("vps", "bandwidth_last_rx_bytes", "bandwidth_last_rx_bytes INTEGER DEFAULT 0")
            ensure_column("vps", "bandwidth_last_tx_bytes", "bandwidth_last_tx_bytes INTEGER DEFAULT 0")
            ensure_column("vps", "bandwidth_last_sample_at", "bandwidth_last_sample_at TEXT DEFAULT NULL")
            ensure_column("vps", "ssh_ready", "ssh_ready INTEGER DEFAULT 0")
            # Stable, concurrency-safe user-facing VMID. Kept separate from SQLite row id.
            ensure_column("vps", "vmid", "vmid INTEGER")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vps_vmid_sequence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reserved_at TEXT NOT NULL
                )
            """)
            cur.execute("UPDATE vps SET vmid = id WHERE vmid IS NULL")
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_vps_vmid ON vps(vmid)")
            max_vmid = int(cur.execute("SELECT COALESCE(MAX(vmid), 0) FROM vps").fetchone()[0] or 0)
            seq_row = cur.execute("SELECT seq FROM sqlite_sequence WHERE name = 'vps_vmid_sequence'").fetchone()
            current_seq = int(seq_row[0]) if seq_row and seq_row[0] is not None else 0
            if max_vmid > current_seq:
                if seq_row is None:
                    cur.execute("INSERT INTO vps_vmid_sequence (reserved_at) VALUES (CURRENT_TIMESTAMP)")
                cur.execute("UPDATE sqlite_sequence SET seq = ? WHERE name = 'vps_vmid_sequence'", (max_vmid,))
            cur.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    last_modified TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            for key, value in (
                ("cpu_threshold", "90"),
                ("ram_threshold", "90"),
                ("maintenance", "off"),
                ("logs_channel_id", "0"),
                ("motd_text", DEFAULT_MOTD_TEXT),
                ("bandwidth_gb", str(VPS_BANDWIDTH_GB)),
            ):
                cur.execute(
                    "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                    (key, value),
                )

            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    action TEXT NOT NULL,
                    detail TEXT DEFAULT '',
                    user_id TEXT,
                    node_id INTEGER,
                    vps_container TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_vps ON audit_logs(vps_container, created_at)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_node ON audit_logs(node_id, created_at)")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS port_allocations (
                    user_id TEXT PRIMARY KEY,
                    allocated_ports INTEGER DEFAULT 0,
                    last_modified TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS port_forwards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    vps_container TEXT NOT NULL,
                    vps_port INTEGER NOT NULL,
                    host_port INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    last_modified TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Legacy installations may have older port tables. The tables must
            # exist before ALTER TABLE migrations are applied. SQLite also does
            # not allow non-constant defaults on ALTER TABLE ADD COLUMN.
            ensure_column("port_allocations", "last_modified", "last_modified TEXT")
            ensure_column("port_forwards", "last_modified", "last_modified TEXT")

            # Backfill timestamp columns for migrated rows.
            cur.execute("UPDATE nodes SET last_updated = COALESCE(last_updated, CURRENT_TIMESTAMP)")
            cur.execute("UPDATE vps SET last_modified = COALESCE(last_modified, CURRENT_TIMESTAMP)")
            cur.execute("UPDATE vps SET bandwidth_gb = ?", (VPS_BANDWIDTH_GB,))
            cur.execute("UPDATE vps SET ssh_ready = CASE WHEN COALESCE(TRIM(root_password), '') <> '' THEN 1 ELSE COALESCE(ssh_ready, 0) END")
            cur.execute("UPDATE vps SET bandwidth_used_bytes = COALESCE(bandwidth_used_bytes, 0)")
            cur.execute("UPDATE vps SET bandwidth_cycle_start = COALESCE(bandwidth_cycle_start, CURRENT_TIMESTAMP)")
            cur.execute("UPDATE vps SET bandwidth_last_rx_bytes = COALESCE(bandwidth_last_rx_bytes, 0)")
            cur.execute("UPDATE vps SET bandwidth_last_tx_bytes = COALESCE(bandwidth_last_tx_bytes, 0)")
            cur.execute("UPDATE vps SET bandwidth_last_sample_at = bandwidth_last_sample_at")
            cur.execute("UPDATE port_allocations SET last_modified = COALESCE(last_modified, CURRENT_TIMESTAMP)")
            cur.execute("UPDATE port_forwards SET last_modified = COALESCE(last_modified, CURRENT_TIMESTAMP)")

            # Repair orphaned VPS node references left by older/deleted nodes.
            local_row = cur.execute("SELECT id FROM nodes WHERE is_local = 1 ORDER BY id LIMIT 1").fetchone()
            if local_row:
                local_node_id = int(local_row[0])
                cur.execute("UPDATE vps SET node_id = ? WHERE node_id IS NULL OR node_id NOT IN (SELECT id FROM nodes)", (local_node_id,))

            # Repair old node tag values that may have been double-encoded.
            cur.execute("SELECT id, tags FROM nodes")
            for row in cur.fetchall():
                raw = row["tags"]
                try:
                    parsed = json.loads(raw or "[]")
                    if isinstance(parsed, str):
                        parsed = json.loads(parsed)
                    if not isinstance(parsed, list):
                        parsed = []
                except (TypeError, ValueError, json.JSONDecodeError):
                    parsed = []
                cur.execute(
                    "UPDATE nodes SET tags = ? WHERE id = ?",
                    (json.dumps(parsed), row["id"]),
                )

            conn.commit()

            # SQLite integrity check. This does not modify user data.
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise sqlite3.DatabaseError(
                    f"SQLite integrity check failed: {integrity}"
                )
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def get_setting(key: str, default: Any = None):
    with DB_LOCK:
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
            return row[0] if row else default
        finally:
            conn.close()


def set_setting(key: str, value: str):
    with DB_LOCK:
        conn = get_db()
        try:
            conn.execute("""
                INSERT INTO settings (key, value, last_modified)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    last_modified = CURRENT_TIMESTAMP
            """, (key, value))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def get_nodes() -> List[Dict]:
    with DB_LOCK:
        conn = get_db()
        try:
            rows = conn.execute("SELECT * FROM nodes ORDER BY id").fetchall()
            nodes = []
            for row in rows:
                node = dict(row)
                try:
                    tags = json.loads(node.get("tags") or "[]")
                    if isinstance(tags, str):
                        tags = json.loads(tags)
                    node["tags"] = tags if isinstance(tags, list) else []
                except (TypeError, ValueError, json.JSONDecodeError):
                    node["tags"] = []
                node["is_local"] = int(node.get("is_local", 1)) == 1
                nodes.append(node)
            return nodes
        finally:
            conn.close()


def get_node(node_id: int) -> Optional[Dict]:
    with DB_LOCK:
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT * FROM nodes WHERE id = ?", (node_id,)
            ).fetchone()
            if not row:
                return None
            node = dict(row)
            try:
                tags = json.loads(node.get("tags") or "[]")
                if isinstance(tags, str):
                    tags = json.loads(tags)
                node["tags"] = tags if isinstance(tags, list) else []
            except (TypeError, ValueError, json.JSONDecodeError):
                node["tags"] = []
            node["is_local"] = int(node.get("is_local", 1)) == 1
            return node
        finally:
            conn.close()


def _decode_vps_row(row) -> Dict[str, Any]:
    vps = dict(row)
    try:
        vps["shared_with"] = json.loads(vps.get("shared_with") or "[]")
        if not isinstance(vps["shared_with"], list):
            vps["shared_with"] = []
    except (TypeError, ValueError, json.JSONDecodeError):
        vps["shared_with"] = []

    try:
        vps["suspension_history"] = json.loads(
            vps.get("suspension_history") or "[]"
        )
        if not isinstance(vps["suspension_history"], list):
            vps["suspension_history"] = []
    except (TypeError, ValueError, json.JSONDecodeError):
        vps["suspension_history"] = []

    vps["suspended"] = bool(vps.get("suspended", 0))
    vps["whitelisted"] = bool(vps.get("whitelisted", 0))
    vps["os_version"] = vps.get("os_version") or "ubuntu:22.04"
    vps["sshx_url"] = vps.get("sshx_url") or None
    vps["sshx_started_at"] = vps.get("sshx_started_at") or None
    vps["pinggy_host"] = vps.get("pinggy_host") or None
    try:
        vps["pinggy_port"] = int(vps.get("pinggy_port") or 0) or None
    except (TypeError, ValueError):
        vps["pinggy_port"] = None
    vps["pinggy_url"] = vps.get("pinggy_url") or None
    try:
        vps["pinggy_pid"] = int(vps.get("pinggy_pid") or 0) or None
    except (TypeError, ValueError):
        vps["pinggy_pid"] = None
    vps["pinggy_started_at"] = vps.get("pinggy_started_at") or None
    # RGNODES fixed plan: every managed VPS has exactly 50 GB/month.
    vps["bandwidth_gb"] = VPS_BANDWIDTH_GB
    try:
        vps["bandwidth_used_bytes"] = max(0, int(vps.get("bandwidth_used_bytes") or 0))
    except (TypeError, ValueError):
        vps["bandwidth_used_bytes"] = 0
    vps["bandwidth_cycle_start"] = vps.get("bandwidth_cycle_start") or datetime.now().isoformat()
    for _bw_key in ("bandwidth_last_rx_bytes", "bandwidth_last_tx_bytes"):
        try:
            vps[_bw_key] = max(0, int(vps.get(_bw_key) or 0))
        except (TypeError, ValueError):
            vps[_bw_key] = 0
    vps["bandwidth_last_sample_at"] = vps.get("bandwidth_last_sample_at") or None
    vps["ssh_ready"] = bool(vps.get("ssh_ready", 0))
    try:
        vps["vmid"] = int(vps.get("vmid") or vps.get("id") or 0)
    except (TypeError, ValueError):
        vps["vmid"] = 0
    raw_expiration = vps.get("expiration_date")
    if raw_expiration:
        try:
            datetime.fromisoformat(str(raw_expiration))
        except (TypeError, ValueError):
            logger.warning(f"Invalid expiration_date for {vps.get('container_name')}; clearing corrupt value")
            vps["expiration_date"] = None
    return vps


def get_vps_by_id(vps_id: int) -> Optional[Dict]:
    with DB_LOCK:
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT * FROM vps WHERE id = ?", (vps_id,)
            ).fetchone()
            return _decode_vps_row(row) if row else None
        finally:
            conn.close()


def get_current_vps_count(node_id: int) -> int:
    with DB_LOCK:
        conn = get_db()
        try:
            return conn.execute(
                "SELECT COUNT(*) FROM vps WHERE node_id = ?", (node_id,)
            ).fetchone()[0]
        finally:
            conn.close()


def get_vps_data() -> Dict[str, List[Dict[str, Any]]]:
    with DB_LOCK:
        conn = get_db()
        try:
            rows = conn.execute("SELECT * FROM vps ORDER BY id").fetchall()
            data: Dict[str, List[Dict[str, Any]]] = {}
            for row in rows:
                vps = _decode_vps_row(row)
                user_id = str(vps["user_id"])
                data.setdefault(user_id, []).append(vps)
            return data
        finally:
            conn.close()


def reserve_vps_vmid() -> int:
    """Reserve a globally unique persistent VMID."""
    with DB_LOCK:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO vps_vmid_sequence (reserved_at) VALUES (CURRENT_TIMESTAMP)")
            vmid = int(cur.lastrowid)
            conn.commit()
            return vmid
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def get_admins() -> List[str]:
    with DB_LOCK:
        conn = get_db()
        try:
            rows = conn.execute(
                "SELECT user_id FROM admins ORDER BY user_id"
            ).fetchall()
            return [str(row["user_id"]) for row in rows]
        finally:
            conn.close()


def save_vps_data():
    """
    Persist the complete in-memory VPS state.

    Important:
    - UPSERT is based on container_name (UNIQUE), not the in-memory id.
    - This fixes the old 'UPDATE affected 0 rows' problem where data could
      disappear after restart.
    - One transaction writes the whole VPS state atomically.
    - No normal save-success messages are printed to the console.
    """
    with DB_LOCK:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("BEGIN IMMEDIATE")

            for user_id, vps_list in list(vps_data.items()):
                for vps in list(vps_list):
                    container_name = str(vps.get("container_name") or "").strip()
                    if not container_name:
                        raise ValueError("Cannot persist VPS without container_name")

                    shared_json = json.dumps(
                        vps.get("shared_with", []),
                        ensure_ascii=False,
                    )
                    history_json = json.dumps(
                        vps.get("suspension_history", []),
                        ensure_ascii=False,
                    )
                    vmid = int(vps.get("vmid") or 0)
                    if vmid <= 0:
                        cur.execute("INSERT INTO vps_vmid_sequence (reserved_at) VALUES (CURRENT_TIMESTAMP)")
                        vmid = int(cur.lastrowid)
                        vps["vmid"] = vmid

                    cur.execute("""
                        INSERT INTO vps (
                            user_id, node_id, container_name, ram, cpu, storage,
                            config, os_version, status, suspended, whitelisted,
                            created_at, shared_with, suspension_history,
                            expiration_date, root_password, last_modified, vmid, sshx_url, sshx_started_at,
                            pinggy_host, pinggy_port, pinggy_url, pinggy_pid, pinggy_started_at,
                            bandwidth_gb, bandwidth_used_bytes, bandwidth_cycle_start,
                            bandwidth_last_rx_bytes, bandwidth_last_tx_bytes, bandwidth_last_sample_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(container_name) DO UPDATE SET
                            user_id = excluded.user_id,
                            node_id = excluded.node_id,
                            ram = excluded.ram,
                            cpu = excluded.cpu,
                            storage = excluded.storage,
                            config = excluded.config,
                            os_version = excluded.os_version,
                            status = excluded.status,
                            suspended = excluded.suspended,
                            whitelisted = excluded.whitelisted,
                            created_at = excluded.created_at,
                            shared_with = excluded.shared_with,
                            suspension_history = excluded.suspension_history,
                            expiration_date = excluded.expiration_date,
                            root_password = excluded.root_password,
                            vmid = excluded.vmid,
                            sshx_url = excluded.sshx_url,
                            sshx_started_at = excluded.sshx_started_at,
                            pinggy_host = excluded.pinggy_host,
                            pinggy_port = excluded.pinggy_port,
                            pinggy_url = excluded.pinggy_url,
                            pinggy_pid = excluded.pinggy_pid,
                            pinggy_started_at = excluded.pinggy_started_at,
                            bandwidth_gb = excluded.bandwidth_gb,
                            bandwidth_used_bytes = excluded.bandwidth_used_bytes,
                            bandwidth_cycle_start = excluded.bandwidth_cycle_start,
                            bandwidth_last_rx_bytes = excluded.bandwidth_last_rx_bytes,
                            bandwidth_last_tx_bytes = excluded.bandwidth_last_tx_bytes,
                            bandwidth_last_sample_at = excluded.bandwidth_last_sample_at,
                            last_modified = CURRENT_TIMESTAMP
                    """, (
                        str(user_id),
                        int(vps.get("node_id", 1)),
                        container_name,
                        str(vps.get("ram", "0GB")),
                        str(vps.get("cpu", "0")),
                        str(vps.get("storage", "0GB")),
                        str(vps.get("config", "Custom")),
                        str(vps.get("os_version", "ubuntu:22.04")),
                        str(vps.get("status", "stopped")),
                        1 if vps.get("suspended", False) else 0,
                        1 if vps.get("whitelisted", False) else 0,
                        str(vps.get("created_at") or datetime.now().isoformat()),
                        shared_json,
                        history_json,
                        vps.get("expiration_date"),
                        vps.get("root_password"),
                        vmid,
                        vps.get("sshx_url"),
                        vps.get("sshx_started_at"),
                        vps.get("pinggy_host"),
                        vps.get("pinggy_port"),
                        vps.get("pinggy_url"),
                        vps.get("pinggy_pid"),
                        vps.get("pinggy_started_at"),
                        VPS_BANDWIDTH_GB,
                        int(vps.get("bandwidth_used_bytes") or 0),
                        vps.get("bandwidth_cycle_start") or datetime.now().isoformat(),
                        int(vps.get("bandwidth_last_rx_bytes") or 0),
                        int(vps.get("bandwidth_last_tx_bytes") or 0),
                        vps.get("bandwidth_last_sample_at"),
                    ))

                    row = cur.execute(
                        "SELECT id FROM vps WHERE container_name = ?",
                        (container_name,),
                    ).fetchone()
                    if row:
                        vps["id"] = row[0]

            conn.commit()
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.error(f"Database error while saving VPS data: {e}", exc_info=True)
            raise
        finally:
            conn.close()


def save_vps_data_immediate() -> bool:
    """Persist VPS data immediately and report whether persistence succeeded."""
    try:
        save_vps_data()
        return True
    except Exception as e:
        logger.error(f"Critical VPS database save failed: {e}")
        backup_database()
        return False


def save_admin_data():
    """Persist administrator data atomically."""
    with DB_LOCK:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("BEGIN IMMEDIATE")

            # Keep the main admin in the database as well.
            admin_ids = {str(x) for x in admin_data.get("admins", [])}
            admin_ids.add(str(MAIN_ADMIN_ID))

            cur.execute("DELETE FROM admins")
            cur.executemany(
                "INSERT INTO admins (user_id) VALUES (?)",
                [(admin_id,) for admin_id in sorted(admin_ids)],
            )
            conn.commit()

            # Keep in-memory state consistent with the database.
            admin_data["admins"] = sorted(admin_ids)
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            logger.error(f"Database error while saving admin data: {e}", exc_info=True)
            raise
        finally:
            conn.close()


def save_admin_data_immediate():
    try:
        save_admin_data()
    except Exception as e:
        logger.error(f"Critical admin database save failed: {e}")
        backup_database()


def get_user_allocation(user_id: str) -> int:
    with DB_LOCK:
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT allocated_ports FROM port_allocations WHERE user_id = ?",
                (str(user_id),),
            ).fetchone()
            return int(row[0]) if row else 0
        finally:
            conn.close()


def ensure_user_port_allocation(user_id: str) -> int:
    """Create the default quota only when no quota row exists; preserve explicit zero quotas."""
    user_id = str(user_id)
    with DB_LOCK:
        conn = get_db()
        try:
            row = conn.execute("SELECT allocated_ports FROM port_allocations WHERE user_id = ?", (user_id,)).fetchone()
            if row is not None:
                return int(row[0] or 0)
            quota = max(0, int(DEFAULT_PORT_QUOTA))
            conn.execute(
                "INSERT INTO port_allocations (user_id, allocated_ports, last_modified) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (user_id, quota),
            )
            conn.commit()
            return quota
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def get_user_used_ports(user_id: str) -> int:
    with DB_LOCK:
        conn = get_db()
        try:
            return conn.execute(
                "SELECT COUNT(*) FROM port_forwards WHERE user_id = ?",
                (str(user_id),),
            ).fetchone()[0]
        finally:
            conn.close()


def allocate_ports(user_id: str, amount: int):
    with DB_LOCK:
        conn = get_db()
        try:
            conn.execute("""
                INSERT INTO port_allocations (user_id, allocated_ports, last_modified)
                VALUES (?, MAX(0, ?), CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    allocated_ports = MAX(0, port_allocations.allocated_ports + excluded.allocated_ports),
                    last_modified = CURRENT_TIMESTAMP
            """, (str(user_id), int(amount)))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def deallocate_ports(user_id: str, amount: int):
    with DB_LOCK:
        conn = get_db()
        try:
            conn.execute("""
                INSERT INTO port_allocations (user_id, allocated_ports, last_modified)
                VALUES (?, 0, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    allocated_ports = MAX(0, port_allocations.allocated_ports - ?),
                    last_modified = CURRENT_TIMESTAMP
            """, (str(user_id), int(amount)))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def _host_port_in_use(host_port: int) -> bool:
    """Return True when a TCP or UDP listener already occupies the port."""
    for sock_type, proto_name in ((socket.SOCK_STREAM, "tcp"), (socket.SOCK_DGRAM, "udp")):
        s = socket.socket(socket.AF_INET, sock_type)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("0.0.0.0", host_port))
        except OSError:
            return True
        finally:
            s.close()
    return False


def get_available_host_port(node_id: int) -> Optional[int]:
    """Allocate a host port that is absent from DB and currently free on the node."""
    with DB_LOCK:
        conn = get_db()
        try:
            rows = conn.execute("""
                SELECT host_port FROM port_forwards
                WHERE vps_container IN (SELECT container_name FROM vps WHERE node_id = ?)
            """, (node_id,)).fetchall()
            used_ports = {int(row[0]) for row in rows}
        finally:
            conn.close()

    low = max(1024, PORT_HOST_MIN)
    high = min(65535, max(low, PORT_HOST_MAX))
    candidates = list(range(low, high + 1))
    random.shuffle(candidates)
    node = get_node(node_id) or {}
    local_probe = bool(node.get('is_local'))
    for port in candidates[: min(len(candidates), 2000)]:
        if port in used_ports:
            continue
        if local_probe and _host_port_in_use(port):
            continue
        return port
    return None


async def _port_device_add(container: str, host_port: int, vps_port: int, node_id: int) -> None:
    """Create host proxy devices without the IPv4/IPv6 wildcard collision."""
    endpoints = await detect_public_endpoints(node_id)
    public_v6 = str(endpoints.get('ipv6') or '').strip()
    required = [
        (f"rgnodes-pf-tcp-{host_port}", f"config device add {container} rgnodes-pf-tcp-{host_port} proxy listen=tcp:0.0.0.0:{host_port} connect=tcp:127.0.0.1:{vps_port} bind=host"),
        (f"rgnodes-pf-udp-{host_port}", f"config device add {container} rgnodes-pf-udp-{host_port} proxy listen=udp:0.0.0.0:{host_port} connect=udp:127.0.0.1:{vps_port} bind=host"),
    ]
    optional = []
    if public_v6:
        optional = [
            (f"rgnodes-pf6-tcp-{host_port}", f"config device add {container} rgnodes-pf6-tcp-{host_port} proxy listen=tcp:[{public_v6}]:{host_port} connect=tcp:127.0.0.1:{vps_port} bind=host"),
            (f"rgnodes-pf6-udp-{host_port}", f"config device add {container} rgnodes-pf6-udp-{host_port} proxy listen=udp:[{public_v6}]:{host_port} connect=udp:127.0.0.1:{vps_port} bind=host"),
        ]
    created = []
    try:
        for name, command in required:
            await execute_lxc(container, command, node_id=node_id)
            created.append(name)
        for name, command in optional:
            try:
                await execute_lxc(container, command, node_id=node_id)
                created.append(name)
            except Exception as exc:
                logger.info(f"IPv6 forwarding unavailable for {container} on {name}: {exc}")
    except Exception:
        for name in reversed(created):
            try:
                await execute_lxc(container, f"config device remove {container} {name}", node_id=node_id)
            except Exception:
                pass
        raise

async def create_port_forward(user_id: str, container: str, vps_port: int, node_id: int) -> Optional[int]:
    """Create a persistent TCP+UDP host-bound proxy and record it atomically."""
    user_id = str(user_id)
    container = str(container).strip()
    vps_port = int(vps_port)
    if not container or not (1 <= vps_port <= 65535):
        return None

    async with PORT_OPERATION_LOCK:
        with DB_LOCK:
            conn = get_db()
            try:
                duplicate = conn.execute(
                    "SELECT host_port FROM port_forwards WHERE vps_container = ? AND vps_port = ?",
                    (container, vps_port),
                ).fetchone()
                if duplicate:
                    return int(duplicate[0])
            finally:
                conn.close()

        allocated = ensure_user_port_allocation(user_id)
        used = get_user_used_ports(user_id)
        if allocated <= 0 or used >= allocated:
            logger.warning(f"Port quota exhausted for user {user_id}: {used}/{allocated}")
            return None

        host_port = get_available_host_port(node_id)
        if not host_port:
            logger.error(f"No available host port for {container}:{vps_port}")
            return None

        devices_added = False
        try:
            await _port_device_add(container, host_port, vps_port, node_id)
            devices_added = True
            for dev in (f"rgnodes-pf-tcp-{host_port}", f"rgnodes-pf-udp-{host_port}"):
                check = await execute_lxc(container, f"config device get {container} {dev} listen", node_id=node_id, timeout=30)
                if not str(check or '').strip():
                    raise RuntimeError(f"Port proxy device {dev} was not confirmed on node {node_id}.")
            with DB_LOCK:
                conn = get_db()
                try:
                    conn.execute(
                        "INSERT INTO port_forwards (user_id, vps_container, vps_port, host_port, created_at, last_modified) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                        (user_id, container, vps_port, host_port, datetime.now().isoformat()),
                    )
                    conn.commit()
                finally:
                    conn.close()
            return host_port
        except Exception as e:
            if devices_added:
                for device_name in (
                    f"rgnodes-pf-tcp-{host_port}",
                    f"rgnodes-pf-udp-{host_port}",
                    f"rgnodes-pf6-tcp-{host_port}",
                    f"rgnodes-pf6-udp-{host_port}",
                ):
                    try:
                        await execute_lxc(container, f"config device remove {container} {device_name}", node_id=node_id)
                    except Exception:
                        pass
            logger.error(f"Failed to create port forward {container}:{vps_port}: {e}", exc_info=True)
            return None


async def remove_port_forward(forward_id: int, requester_id: Optional[str] = None, is_admin: bool = False) -> tuple[bool, Optional[str]]:
    async with PORT_OPERATION_LOCK:
        with DB_LOCK:
            conn = get_db()
            try:
                row = conn.execute(
                    "SELECT user_id, vps_container, host_port FROM port_forwards WHERE id = ?",
                    (int(forward_id),),
                ).fetchone()
            finally:
                conn.close()
        if not row:
            return False, None

        owner_id, container, host_port = str(row[0]), row[1], int(row[2])
        if not is_admin and str(requester_id) != owner_id:
            return False, owner_id

        node_id = find_node_id_for_container(container)
        try:
            removal_failures = []
            for device_name in (
                f"rgnodes-pf-tcp-{host_port}",
                f"rgnodes-pf-udp-{host_port}",
                f"rgnodes-pf6-tcp-{host_port}",
                f"rgnodes-pf6-udp-{host_port}",
            ):
                try:
                    await execute_lxc(container, f"config device remove {container} {device_name}", node_id=node_id)
                except Exception as e:
                    msg = str(e).lower()
                    if not any(x in msg for x in ("not found", "doesn't exist", "not exist")):
                        removal_failures.append(f"{device_name}: {e}")
            if removal_failures:
                logger.error(f"Port forward {forward_id} was not fully removed: {'; '.join(removal_failures)}")
                return False, owner_id
            with DB_LOCK:
                conn = get_db()
                try:
                    conn.execute("DELETE FROM port_forwards WHERE id = ?", (int(forward_id),))
                    conn.commit()
                finally:
                    conn.close()
            return True, owner_id
        except Exception as e:
            logger.error(f"Failed to remove port forward {forward_id}: {e}", exc_info=True)
            return False, owner_id

def get_user_forwards(user_id: str) -> List[Dict]:
    with DB_LOCK:
        conn = get_db()
        try:
            rows = conn.execute("SELECT * FROM port_forwards WHERE user_id = ? ORDER BY created_at DESC", (str(user_id),)).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()


async def recreate_port_forwards(container_name: str, node_id_override: Optional[int] = None) -> int:
    """Rebuild all persistent proxy devices after a restart/reinstall."""
    async with PORT_OPERATION_LOCK:
        node_id = int(node_id_override) if node_id_override is not None else find_node_id_for_container(container_name)
        with DB_LOCK:
            conn = get_db()
            try:
                rows = conn.execute(
                    "SELECT vps_port, host_port FROM port_forwards WHERE vps_container = ?",
                    (container_name,),
                ).fetchall()
            finally:
                conn.close()

        count = 0
        for row in rows:
            vps_port, old_host_port = int(row[0]), int(row[1])
            host_port = old_host_port
            try:
                for device_name in (
                    f"rgnodes-pf-tcp-{old_host_port}",
                    f"rgnodes-pf-udp-{old_host_port}",
                    f"rgnodes-pf6-tcp-{old_host_port}",
                    f"rgnodes-pf6-udp-{old_host_port}",
                ):
                    try:
                        await execute_lxc(container_name, f"config device remove {container_name} {device_name}", node_id=node_id)
                    except Exception:
                        pass
                if _host_port_in_use(old_host_port):
                    replacement = get_available_host_port(node_id)
                    if not replacement:
                        raise RuntimeError(f"No replacement host port is available for forward {old_host_port}->{vps_port}")
                    host_port = replacement
                    with DB_LOCK:
                        conn = get_db()
                        try:
                            conn.execute("UPDATE port_forwards SET host_port = ?, last_modified = CURRENT_TIMESTAMP WHERE vps_container = ? AND vps_port = ?", (host_port, container_name, vps_port))
                            conn.commit()
                        finally:
                            conn.close()
                    logger.warning(f"Moved occupied forward {old_host_port}->{vps_port} on {container_name} to host port {host_port}")
                await _port_device_add(container_name, host_port, vps_port, node_id)
                count += 1
            except Exception as e:
                logger.error(f"Failed to recreate forward {host_port}->{vps_port} for {container_name}: {e}")
        return count

def find_node_id_for_container(container_name: str) -> int:
    with DB_LOCK:
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT node_id FROM vps WHERE container_name = ?",
                (container_name,),
            ).fetchone()
            return int(row[0]) if row else 1
        finally:
            conn.close()


# Initialize database. Any initialization error must stop startup rather
# than allowing the bot to run with a blank/new in-memory state.
try:
    init_db()
except Exception as db_init_error:
    logger.error(f"Fatal database initialization error: {db_init_error}", exc_info=True)
    raise

# Load persistent state after the schema is ready.
vps_data = get_vps_data()
admin_data = {"admins": get_admins()}

# Make sure the main admin can never disappear from the persistent admin list.
if str(MAIN_ADMIN_ID) not in admin_data["admins"]:
    admin_data["admins"].append(str(MAIN_ADMIN_ID))
    save_admin_data()

# Silent background persistence. Immediate saves are still used by critical
# operations, while this catches any future mutation that forgot to save.
async def auto_save_task():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            await asyncio.sleep(AUTOSAVE_INTERVAL)
            # Critical mutations call *_immediate() directly; this is a low-frequency
            # safety flush for non-critical state changes.
            save_vps_data()
            save_admin_data()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Background database save failed: {e}")


def cleanup_on_shutdown():
    """Final persistent save without normal database-success console messages."""
    try:
        save_vps_data()
        save_admin_data()
    except Exception as e:
        logger.error(f"Final database save failed: {e}")
        backup_database()


atexit.register(cleanup_on_shutdown)

# Global settings from DB
CPU_THRESHOLD = int(get_setting('cpu_threshold', 90))
RAM_THRESHOLD = int(get_setting('ram_threshold', 90))

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# Runtime guards. systemd -> PM2 keeps one bot process, while these prevent duplicate
# user actions and duplicate expiration warnings inside that process.
ACTIVE_DEPLOYMENTS = set()
EXPIRATION_WARNING_SENT = set()
EXPIRATION_EXPIRED_NOTICE_SENT = set()
PORT_OPERATION_LOCK = asyncio.Lock()
TUNNEL_OPERATION_LOCKS: Dict[str, asyncio.Lock] = {}
DEPLOY_NODE_LOCKS: Dict[int, asyncio.Lock] = {}
AUDIT_CHANNEL_SEND_LOCK = asyncio.Lock()

async def _publish_log_bundle(channel, embed, content: str, filename: str) -> None:
    """Publish an operational log embed plus a bounded text attachment.

    Discord embeds are intentionally small; the attachment preserves a useful
    complete snapshot without flooding the channel with many messages.
    """
    if channel is None or not hasattr(channel, "send"):
        return
    content = str(content or "No log output.")
    # Keep attachment comfortably below Discord's message/attachment limits and
    # avoid dumping unbounded guest logs to the host or Discord.
    content = content[-90000:]
    payload = io.BytesIO(content.encode("utf-8", errors="replace"))
    file = discord.File(payload, filename=str(filename)[:80])
    await channel.send(embed=embed, file=file, allowed_mentions=discord.AllowedMentions.none())

def _audit_channel_id() -> int:
    try:
        return int(get_setting("logs_channel_id", "0") or 0)
    except (TypeError, ValueError):
        return 0

def set_audit_channel_id(channel_id: Optional[int]) -> None:
    set_setting("logs_channel_id", str(int(channel_id or 0)))

def get_motd_text() -> str:
    return str(get_setting("motd_text", DEFAULT_MOTD_TEXT) or "").strip()[:1200]

async def record_audit_event(kind: str, action: str, detail: str = "", user_id: Optional[int | str] = None,
                             node_id: Optional[int] = None, vps_container: Optional[str] = None,
                             announce: bool = True) -> None:
    safe_detail = str(detail or "").strip()[:1800]
    safe_kind = str(kind or "system").strip()[:32]
    safe_action = str(action or "event").strip()[:120]
    try:
        with DB_LOCK:
            conn = get_db()
            try:
                conn.execute(
                    "INSERT INTO audit_logs (kind, action, detail, user_id, node_id, vps_container, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (safe_kind, safe_action, safe_detail, str(user_id) if user_id is not None else None,
                     int(node_id) if node_id is not None else None,
                     str(vps_container)[:120] if vps_container else None,
                     datetime.now().isoformat()),
                )
                conn.execute("DELETE FROM audit_logs WHERE id NOT IN (SELECT id FROM audit_logs ORDER BY id DESC LIMIT 2000)")
                conn.commit()
            finally:
                conn.close()
    except Exception as exc:
        logger.warning("Audit log persistence failed: %s", exc)
        return
    if not announce:
        return
    channel_id = _audit_channel_id()
    if not channel_id:
        return
    try:
        channel = bot.get_channel(channel_id)
        if channel is None:
            channel = await bot.fetch_channel(channel_id)
        if not hasattr(channel, "send"):
            return
        icon = {"vps": "🖥️", "node": "🧩", "command": "⌘", "system": "⚙️", "security": "🛡️", "error": "🚨"}.get(safe_kind, "📝")
        embed = create_info_embed(f"{icon} {safe_action}", safe_detail or "No additional details.")
        if node_id is not None:
            add_field(embed, "Node", f"`{node_id}`", True)
        if vps_container:
            add_field(embed, "VPS", f"`{vps_container}`", True)
        if user_id is not None:
            add_field(embed, "User", f"`{user_id}`", True)
        embed.set_footer(text=f"{HOST_PROVIDER_NAME} • RGNODES™ audit log")
        async with AUDIT_CHANNEL_SEND_LOCK:
            await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
    except Exception as exc:
        logger.debug("Could not publish audit log to channel %s: %s", channel_id, exc)

def get_recent_audit_logs(limit: int = 20, *, vps_container: Optional[str] = None, node_id: Optional[int] = None) -> list[dict]:
    limit = max(1, min(100, int(limit)))
    clauses = []
    params: list = []
    if vps_container:
        clauses.append("vps_container = ?"); params.append(str(vps_container))
    if node_id is not None:
        clauses.append("node_id = ?"); params.append(int(node_id))
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(limit)
    with DB_LOCK:
        conn = get_db()
        try:
            rows = conn.execute(f"SELECT kind, action, detail, user_id, node_id, vps_container, created_at FROM audit_logs{where} ORDER BY id DESC LIMIT ?", params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

MAINTENANCE_SAFE_COMMANDS = {
    "ping", "uptime", "about", "help", "quickhelp", "manage", "status", "vps-log", "vps-logs", "bandwidth",
}

class RGNODESMaintenanceError(commands.CheckFailure):
    """Raised when a normal user's command is blocked by maintenance mode."""

class RGNODESView(discord.ui.View):
    """Base view with a safe Discord UI error response."""
    async def on_error(self, interaction: discord.Interaction, error: Exception, item):
        error_id = secrets.token_hex(4).upper()
        logger.error(
            "Discord UI callback failed [%s] item=%s: %s",
            error_id, getattr(item, "custom_id", None) or getattr(item, "label", type(item).__name__), error, exc_info=True
        )
        message = "The requested action could not be completed right now. No destructive operation was continued. Please try again."
        if is_admin_user(getattr(interaction, "user", None)):
            message += f"\n\n**Error ID:** `{error_id}`\n**Technical:** `{str(error)[:700]}`"
        else:
            message += f"\n\n**Error ID:** `{error_id}`"
        try:
            embed=create_error_embed("⚠️ Action Failed", message)
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception:
            logger.exception("Unable to deliver UI error response [%s]", error_id)

expiration_task_handle = None
protection_task_handle = None
tunnel_repair_task_handle = None
access_repair_task_handle = None

# Resource monitoring settings (logging only)
resource_monitor_active = True
status_task_handle = None


def get_presence_counts():
    created = sum(len(items) for items in vps_data.values())
    running = sum(1 for items in vps_data.values() for v in items if v.get("status") == "running" and not v.get("suspended", False))
    expired = sum(1 for items in vps_data.values() for v in items if v.get("expiration_date") and _safe_fromiso(v["expiration_date"]) <= datetime.now())
    total_slots = sum(max(0, int(n.get("total_vps") or 0)) for n in get_nodes())
    if total_slots <= 0:
        total_slots = max(created, 1)
    return created, total_slots, running, expired


def _safe_fromiso(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return datetime.max


def _parse_gb(value: Any, default: int) -> int:
    try:
        return max(1, int(float(str(value).strip().lower().replace('gb', '').strip())))
    except (TypeError, ValueError):
        return int(default)


def _parse_cpu(value: Any, default: int) -> int:
    try:
        return max(1, int(float(str(value).strip())))
    except (TypeError, ValueError):
        return int(default)


async def status_presence_task():
    while not bot.is_closed():
        try:
            created, total_slots, running, expired = get_presence_counts()
            if maintenance_enabled():
                activity = f"🔧 MAINTENANCE | {created}/{total_slots} VPS | 🟢 {running} Running"
            else:
                activity = f"🖥️ {created}/{total_slots} | 🟢 {running} Running | ⏰ {expired} Expired"
            await bot.change_presence(activity=discord.Game(name=activity))
        except Exception as e:
            logger.debug(f"Presence update failed: {e}")
        await asyncio.sleep(30)

# ═══════════════════════════════════════════════════════════════════════════
# MODERN UI/UX SYSTEM - Beautiful Discord Embeds
# ═══════════════════════════════════════════════════════════════════════════

# Professional Color Palette
COLOR_PRIMARY = 0x2c3e50      # Dark slate blue
COLOR_SUCCESS = 0x27ae60      # Modern green  
COLOR_ERROR = 0xe74c3c        # Bright red
COLOR_WARNING = 0xf39c12      # Amber
COLOR_INFO = 0x3498db         # Ocean blue
COLOR_NETWORK = 0x16a085      # Teal
COLOR_EXPIRED = 0xc0392b      # Dark red
COLOR_ACTIVE = 0x16a085       # Teal green
COLOR_SUSPENDED = 0x95a5a6    # Gray
COLOR_NODE = 0x8e44ad         # Purple

# Helper function to truncate text
def truncate_text(text, max_length=1024):
    if not text:
        return text
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

# Password generation and management functions
def generate_strong_password(length=16):
    """Generate a cryptographically strong password"""
    # Use mix of uppercase, lowercase, digits, and special characters
    charset = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(charset) for _ in range(length))
    return password

def sanitize_username_for_container(username: str) -> str:
    """
    Sanitize username for LXC container naming.
    LXC only allows alphanumeric and hyphen characters.
    Replace underscores, spaces, and other invalid chars with hyphens.
    """
    # Replace underscores and spaces with hyphens
    sanitized = username.replace('_', '-').replace(' ', '-')
    # Remove any character that's not alphanumeric or hyphen
    sanitized = ''.join(c for c in sanitized if c.isalnum() or c == '-')
    # Ensure it doesn't start or end with hyphen (LXC requirement)
    sanitized = sanitized.strip('-').lower()
    # Discord usernames can theoretically contain only characters that are
    # removed above. Never allow an empty/leading-dash LXC instance name.
    sanitized = sanitized[:30] or 'user'
    return sanitized

def get_vps_password(container_name):
    """Get password from VPS data"""
    for user_id, vps_list in vps_data.items():
        for vps in vps_list:
            if vps['container_name'] == container_name:
                return vps.get('root_password', None)
    return None

def set_vps_password(container_name, password):
    """Set password for VPS"""
    for user_id, vps_list in vps_data.items():
        for vps in vps_list:
            if vps['container_name'] == container_name:
                vps['root_password'] = password
                save_vps_data_immediate()
                return True
    return False

async def _exec_guest_bash(container_name: str, node_id: int, script: str, timeout: int = 300):
    """Execute a bash script safely without shell-quote corruption."""
    encoded = base64.b64encode(script.encode("utf-8")).decode("ascii")
    cmd = f"exec {container_name} -- bash -lc 'echo {encoded} | base64 -d | bash'"
    return await execute_lxc(container_name, cmd, timeout=timeout, node_id=node_id)




async def apply_guest_motd(container_name: str, node_id: int, motd_text: Optional[str] = None) -> bool:
    """Apply a distro-safe MOTD exactly once, with PAM or SSH-shell fallback."""
    text = str(motd_text if motd_text is not None else get_motd_text() or "").replace("\x00", "").strip()[:1200]
    b64 = base64.b64encode(text.encode("utf-8")).decode("ascii") if text else ""
    profile_path = "/etc/profile.d/00-rgnodes-motd.sh"
    if text:
        script = f"""set -Eeuo pipefail
mkdir -p /etc/profile.d
printf '%s' '{b64}' | base64 -d > /etc/motd
chmod 0644 /etc/motd
# Older RGNODES versions commented pam_motd lines to avoid duplicates; restore those exact lines.
for cfg in /etc/pam.d/sshd /etc/pam.d/common-session /etc/pam.d/common-session-noninteractive; do
  [ -f "$cfg" ] || continue
  sed -i 's/^# RGNODES disabled duplicate MOTD: //' "$cfg" 2>/dev/null || true
done
if grep -RqsE '^[[:space:]]*[^#].*pam_motd\\.so' /etc/pam.d 2>/dev/null; then
  # PAM is already responsible for displaying /etc/motd; do not double-print it from the shell.
  rm -f {profile_path}
  printf 'MOTD_READY_PAM\n'
else
  # Minimal fallback for images without pam_motd (notably some Alpine/OpenRC builds).
  cat > {profile_path} <<'EOF'
# RGNODES MOTD fallback: only print for interactive SSH sessions when PAM does not provide pam_motd.
if [ -n "$SSH_CONNECTION" ] && [ -t 1 ] && [ -r /etc/motd ]; then
    cat /etc/motd
fi
EOF
  chmod 0644 {profile_path}
  printf 'MOTD_READY_PROFILE\n'
fi
"""
    else:
        script = f"""set -Eeuo pipefail
: > /etc/motd
chmod 0644 /etc/motd
rm -f {profile_path}
for cfg in /etc/pam.d/sshd /etc/pam.d/common-session /etc/pam.d/common-session-noninteractive; do
  [ -f "$cfg" ] || continue
  sed -i 's/^# RGNODES disabled duplicate MOTD: //' "$cfg" 2>/dev/null || true
done
printf 'MOTD_CLEARED\n'
"""
    try:
        out = await _exec_guest_bash(container_name, node_id, script, timeout=45)
        out_text = str(out or "")
        if text:
            return "MOTD_READY_PAM" in out_text or "MOTD_READY_PROFILE" in out_text
        return "MOTD_CLEARED" in out_text
    except Exception as exc:
        logger.warning("MOTD apply failed for %s: %s", container_name, exc)
        return False

async def apply_motd_to_all_running_vps() -> tuple[int, int]:
    ok = failed = 0
    sem = asyncio.Semaphore(2)
    async def one(vps):
        nonlocal ok, failed
        if str(vps.get("status", "")).lower() != "running" or vps.get("suspended"):
            return
        async with sem:
            try:
                if await apply_guest_motd(str(vps.get("container_name")), int(vps.get("node_id", 1))):
                    ok += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
    items = [v for owner_items in list(vps_data.values()) for v in list(owner_items)]
    for start in range(0, len(items), 20):
        await asyncio.gather(*(one(v) for v in items[start:start + 20]), return_exceptions=True)
    return ok, failed


async def configure_ssh(container_name, node_id, password):
    """Configure root/password SSH deterministically and verify the effective daemon config."""
    script = rf'''set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive
mkdir -p /etc/ssh/sshd_config.d /run/sshd /var/log
[ -f /etc/ssh/sshd_config ] || touch /etc/ssh/sshd_config
[ -f /etc/ssh/sshd_config.rgnodes-original ] || cp -a /etc/ssh/sshd_config /etc/ssh/sshd_config.rgnodes-original 2>/dev/null || true
# Some cloud images ship PasswordAuthentication no / AuthenticationMethods publickey.
# OpenSSH uses the first obtained value, so this file must be lexically first.
cat > /etc/ssh/sshd_config.d/00-rgnodes-access.conf <<'EOF'
Port 22
AddressFamily any
ListenAddress 0.0.0.0
ListenAddress ::
PasswordAuthentication yes
KbdInteractiveAuthentication yes
ChallengeResponseAuthentication yes
PubkeyAuthentication yes
PermitRootLogin yes
UsePAM yes
MaxAuthTries 6
MaxSessions 50
TCPKeepAlive yes
ClientAliveInterval 60
ClientAliveCountMax 6
PermitEmptyPasswords no
PrintMotd yes
PrintLastLog yes
EOF
# If the distribution keeps a global AuthenticationMethods/PasswordAuthentication before Include,
# comment just those auth overrides; retain unrelated vendor configuration.
for cfg in /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*.conf; do
  [ -f "$cfg" ] || continue
  [ "$cfg" = /etc/ssh/sshd_config.d/00-rgnodes-access.conf ] && continue
  sed -i -E 's/^[[:space:]]*(PasswordAuthentication|KbdInteractiveAuthentication|ChallengeResponseAuthentication|PubkeyAuthentication|PermitRootLogin|AuthenticationMethods)[[:space:]].*$/# RGNODES neutralized: &/' "$cfg" 2>/dev/null || true
done
printf '%s:%s\n' root {shlex.quote(password)} | chpasswd
passwd -u root >/dev/null 2>&1 || true
usermod -U root >/dev/null 2>&1 || true
chage -M -1 root >/dev/null 2>&1 || true
SSHD=$(command -v sshd || true)
if [ -z "$SSHD" ]; then
  install_pkg() {{
    case "$1" in
      apt)
        apt-get install -y --no-install-recommends openssh-server openssh-client >/dev/null 2>&1 && return 0
        apt-get update -qq >/dev/null 2>&1 || true
        apt-get install -y --no-install-recommends openssh-server openssh-client >/dev/null 2>&1 || return 1
        ;;
      dnf) dnf install -y openssh-server openssh-clients >/dev/null 2>&1 || return 1 ;;
      yum) yum install -y openssh-server openssh-clients >/dev/null 2>&1 || return 1 ;;
      apk) apk add --no-cache openssh >/dev/null 2>&1 || return 1 ;;
      zypper) zypper --non-interactive install -y openssh >/dev/null 2>&1 || return 1 ;;
      *) return 1 ;;
    esac
  }}
  if command -v apt-get >/dev/null 2>&1; then install_pkg apt || true
  elif command -v dnf >/dev/null 2>&1; then install_pkg dnf || true
  elif command -v yum >/dev/null 2>&1; then install_pkg yum || true
  elif command -v apk >/dev/null 2>&1; then install_pkg apk || true
  elif command -v zypper >/dev/null 2>&1; then install_pkg zypper || true
  fi
  SSHD=$(command -v sshd || true)
fi
[ -n "$SSHD" ] || {{ echo 'SSH_SERVER_NOT_READY'; exit 12; }}
chmod 600 /etc/ssh/sshd_config /etc/ssh/sshd_config.d/00-rgnodes-access.conf 2>/dev/null || true
# Restore any MOTD lines disabled by older RGNODES releases. We now rely on distro PAM
# when available and only install a shell fallback when PAM has no pam_motd module.
for cfg in /etc/pam.d/sshd /etc/pam.d/common-session /etc/pam.d/common-session-noninteractive; do
  [ -f "$cfg" ] || continue
  sed -i 's/^# RGNODES disabled duplicate MOTD: //' "$cfg" 2>/dev/null || true
done
$SSHD -t
EFFECTIVE=$($SSHD -T -C user=root,addr=127.0.0.1,localport=22,host=$(hostname -f 2>/dev/null || hostname) 2>/dev/null || true)
printf '%s\n' "$EFFECTIVE" | grep -Eq '^passwordauthentication yes$' || {{ echo 'PASSWORD_AUTH_NOT_EFFECTIVE'; exit 13; }}
printf '%s\n' "$EFFECTIVE" | grep -Eq '^kbdinteractiveauthentication yes$' || {{ echo 'KBD_AUTH_NOT_EFFECTIVE'; exit 14; }}
printf '%s\n' "$EFFECTIVE" | grep -Eq '^permitrootlogin yes$' || {{ echo 'ROOT_LOGIN_NOT_EFFECTIVE'; exit 15; }}
printf '%s\n' "$EFFECTIVE" | grep -Eq '^printmotd yes$' || {{ echo 'PRINT_MOTD_NOT_EFFECTIVE'; exit 16; }}
if command -v systemctl >/dev/null 2>&1 && [ "$(cat /proc/1/comm 2>/dev/null)" = "systemd" ]; then
  systemctl daemon-reload >/dev/null 2>&1 || true
  systemctl enable ssh >/dev/null 2>&1 || systemctl enable sshd >/dev/null 2>&1 || true
  systemctl restart ssh >/dev/null 2>&1 || systemctl restart sshd >/dev/null 2>&1 || true
elif command -v rc-service >/dev/null 2>&1; then
  rc-service sshd restart >/dev/null 2>&1 || rc-service ssh restart >/dev/null 2>&1 || rc-service sshd start >/dev/null 2>&1 || true
elif command -v service >/dev/null 2>&1; then
  service ssh restart >/dev/null 2>&1 || service sshd restart >/dev/null 2>&1 || service ssh start >/dev/null 2>&1 || true
fi
if ! ss -lntH 2>/dev/null | awk '$4 ~ /:(22)$/ {{ok=1}} END {{exit ok?0:1}}'; then
  mkdir -p /run/sshd
  nohup $SSHD -D >/var/log/rgnodes-sshd.log 2>&1 &
  sleep 2
fi
ss -lntH 2>/dev/null | awk '$4 ~ /:(22)$/ {{ok=1}} END {{exit ok?0:1}}'
printf 'SSH_READY\n'
'''
    try:
        output=await _exec_guest_bash(container_name,node_id,script,timeout=105)
        if 'SSH_READY' not in str(output): raise RuntimeError('SSH readiness check did not pass inside the VPS.')
        set_vps_password(container_name,password)
        return True,password
    except Exception as e:
        logger.error(f"Failed to configure SSH for {container_name}: {e}",exc_info=True)
        return False,str(e)



async def set_guest_hostname(container_name: str, node_id: int, hostname: str = VPS_HOSTNAME):
    safe = re.sub(r'[^A-Za-z0-9.-]', '-', hostname).strip('.-') or 'rgnodes-vps'
    script = f"""set -e
printf '%s\\n' {shlex.quote(safe)} > /etc/hostname
(hostnamectl set-hostname {shlex.quote(safe)} 2>/dev/null || hostname {shlex.quote(safe)} || true)
sed -i -E '/^[[:space:]]*127\\.0\\.1\\.1[[:space:]]+/d' /etc/hosts 2>/dev/null || true
printf '127.0.1.1 %s\\n' {shlex.quote(safe)} >> /etc/hosts
"""
    return await _exec_guest_bash(container_name, node_id, script, timeout=60)



async def bootstrap_vps_guest(container_name: str, node_id: int):
    """Install the lightweight RGNODES baseline; heavy virtualization is never installed automatically."""
    script = r'''set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a
if command -v apt-get >/dev/null 2>&1; then
  for attempt in 1 2 3 4; do apt-get update -qq && break; sleep $((attempt*2)); done
  apt-get install -y --no-install-recommends bash coreutils grep sed gawk sudo openssh-server openssh-client curl ca-certificates iproute2 iputils-ping procps net-tools python3
elif command -v dnf >/dev/null 2>&1; then
  dnf install -y bash coreutils grep sed gawk sudo openssh-server openssh-clients curl ca-certificates iproute iputils procps-ng net-tools python3
elif command -v yum >/dev/null 2>&1; then
  yum install -y bash coreutils grep sed gawk sudo openssh-server openssh-clients curl ca-certificates iproute iputils procps net-tools python3
elif command -v apk >/dev/null 2>&1; then
  apk add --no-cache bash coreutils grep sed gawk sudo openssh curl ca-certificates iproute2 iputils procps net-tools python3
else
  echo 'SUPPORTED_PACKAGE_MANAGER_NOT_FOUND' >&2
  exit 20
fi
mkdir -p /etc/ssh/sshd_config.d /run/sshd /var/lib/rgnodes
command -v sshd >/dev/null 2>&1 || { echo 'SSH_SERVER_MISSING' >&2; exit 21; }
printf 'BASELINE_READY\n'
'''
    await _exec_guest_bash(container_name,node_id,script,timeout=GUEST_BOOTSTRAP_TIMEOUT)


async def install_anti_mining_guard(container_name: str, node_id: int):
    """Install conservative best-effort anti-cryptomining protection in every VPS."""
    if not ANTI_MINING_ENABLED:
        return
    script = r'''set +u
cat > /usr/local/sbin/rgnodes-mining-guard <<'GUARD'
#!/usr/bin/env bash
set +e
MINER_NAMES='^(xmrig|xmrig-proxy|xmr-stak|cpuminer|cpuminer-multi|minerd|ccminer|cgminer|bfgminer|nbminer|lolminer|t-rex|ethminer|nanominer|rigel|gminer|teamredminer|phoenixminer)$'
for proc in /proc/[0-9]*; do
  pid=${proc##*/}
  [ "$pid" = "$$" ] && continue
  [ -r "$proc/cmdline" ] || continue
  [ -r "$proc/comm" ] || continue
  comm=$(tr -d '\0\n' < "$proc/comm" 2>/dev/null)
  cmd=$(tr '\0' ' ' < "$proc/cmdline" 2>/dev/null)
  lower_comm=$(printf '%s' "$comm" | tr '[:upper:]' '[:lower:]')
  lower_cmd=$(printf '%s' "$cmd" | tr '[:upper:]' '[:lower:]')
  suspicious=0
  printf '%s\n' "$lower_comm" | grep -Eq "$MINER_NAMES" && suspicious=1
  printf '%s\n' "$lower_cmd" | grep -Eq '(^|[[:space:]])(stratum\+tcp|stratum\+ssl|ethashstratum|nicehash)([^[:alnum:]_-]|$)' && suspicious=1
  [ "$suspicious" -eq 1 ] || continue
  case "$lower_cmd" in
    *rgnodes-mining-guard*|*/sshd*|*/systemd*|*/init*|*cloud-init*|*apt*|*dpkg*) continue ;;
  esac
  kill -TERM "$pid" 2>/dev/null || true
  sleep 0.25
  kill -KILL "$pid" 2>/dev/null || true
  logger -t rgnodes-mining-guard "Blocked suspected cryptominer pid=$pid comm=$comm" 2>/dev/null || true
done
GUARD
chmod 0755 /usr/local/sbin/rgnodes-mining-guard
if command -v systemctl >/dev/null 2>&1; then
  cat > /etc/systemd/system/rgnodes-mining-guard.service <<'EOF2'
[Unit]
Description=RGNODES Anti-Mining Protection
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/rgnodes-mining-guard
EOF2
  cat > /etc/systemd/system/rgnodes-mining-guard.timer <<'EOF2'
[Unit]
Description=RGNODES Anti-Mining Protection Timer

[Timer]
OnBootSec=30s
OnUnitActiveSec=30s
AccuracySec=5s
Persistent=true
Unit=rgnodes-mining-guard.service

[Install]
WantedBy=timers.target
EOF2
  systemctl daemon-reload >/dev/null 2>&1 || true
  systemctl enable --now rgnodes-mining-guard.timer >/dev/null 2>&1 || true
else
  mkdir -p /etc/cron.d
  printf '*/1 * * * * root /usr/local/sbin/rgnodes-mining-guard >/dev/null 2>&1\n' > /etc/cron.d/rgnodes-mining-guard
  chmod 0644 /etc/cron.d/rgnodes-mining-guard
fi
/usr/local/sbin/rgnodes-mining-guard >/dev/null 2>&1 || true
'''
    try:
        await _exec_guest_bash(container_name, node_id, script, timeout=45)
    except Exception as e:
        logger.warning(f"Anti-mining guard installation skipped for {container_name}: {e}")

async def _run_tunnel_control(container_name: str, node_id: int, action: str, tunnel_name: str, timeout: int = 60):
    '''Start/restart exactly one tunnel supervisor.

    LXC images often ship a `systemctl` binary without systemd as PID 1, so the
    real init process is detected before systemd is used. Non-systemd guests get
    a direct supervisor plus a cron @reboot fallback.
    '''
    if action not in {"start", "restart"}:
        raise ValueError("Unsupported tunnel control action")
    if tunnel_name not in {"sshx", "pinggy"}:
        raise ValueError("Unsupported tunnel name")
    sup = f"/usr/local/sbin/rgnodes-{tunnel_name}-supervisor"
    service = f"rgnodes-{tunnel_name}.service"
    log = f"/var/lib/rgnodes/{tunnel_name}-supervisor.log"
    supervisor_pid_file = f"/var/lib/rgnodes/{tunnel_name}.supervisor.pid"
    cron_file = f"/etc/cron.d/rgnodes-{tunnel_name}"
    command = r'''set +e
systemd_ok=false
[ -d /run/systemd/system ] && [ "$(cat /proc/1/comm 2>/dev/null)" = "systemd" ] && systemd_ok=true
SUP="__SUP__"
SERVICE="__SERVICE__"
LOG="__LOG__"
SUPPID="__SUPPID__"
CRON_FILE="__CRON_FILE__"
is_alive() {
  pid=$(cat "$SUPPID" 2>/dev/null | head -n1)
  [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1
}
start_bg() {
  is_alive && return 0
  mkdir -p "$(dirname "$LOG")"
  nohup "$SUP" >>"$LOG" 2>&1 </dev/null &
  sleep 1
}
stop_bg() {
  pid=$(cat "$SUPPID" 2>/dev/null | head -n1)
  if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then
    kill -TERM "$pid" >/dev/null 2>&1 || true
    for _ in 1 2 3 4 5; do
      sleep 1
      kill -0 "$pid" >/dev/null 2>&1 || break
    done
    kill -KILL "$pid" >/dev/null 2>&1 || true
  fi
  rm -f "$SUPPID"
}
if [ "$systemd_ok" = true ]; then
  systemctl daemon-reload >/dev/null 2>&1 || true
  if [ "__ACTION__" = "restart" ]; then
    systemctl restart "$SERVICE" >/dev/null 2>&1 || true
  else
    systemctl start "$SERVICE" >/dev/null 2>&1 || true
  fi
  systemctl enable "$SERVICE" >/dev/null 2>&1 || true
else
  stop_bg
  start_bg
fi
if [ "$systemd_ok" = true ] && ! systemctl is-active --quiet "$SERVICE" >/dev/null 2>&1; then
  start_bg
fi
if [ "$systemd_ok" != true ]; then
  start_bg
  mkdir -p /etc/cron.d
  printf 'SHELL=/bin/sh\nPATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n@reboot root %s >>%s 2>&1\n' "$SUP" "$LOG" > "$CRON_FILE"
  chmod 0644 "$CRON_FILE" 2>/dev/null || true
  if command -v service >/dev/null 2>&1; then
    service cron start >/dev/null 2>&1 || service crond start >/dev/null 2>&1 || true
  elif command -v cron >/dev/null 2>&1; then
    pgrep -x cron >/dev/null 2>&1 || nohup cron >/dev/null 2>&1 &
  elif command -v crond >/dev/null 2>&1; then
    pgrep -x crond >/dev/null 2>&1 || nohup crond >/dev/null 2>&1 &
  fi
fi
if is_alive; then
  printf 'TUNNEL_CONTROL_DONE\n'
else
  printf 'TUNNEL_CONTROL_FAILED\n'
fi
'''.replace('__ACTION__', action).replace('__SUP__', sup).replace('__SERVICE__', service).replace('__LOG__', log).replace('__CRON_FILE__', cron_file).replace('__SUPPID__', supervisor_pid_file)
    return await _exec_guest_bash(container_name, node_id, command, timeout=timeout)


def _get_tunnel_lock(container_name: str, tunnel_name: str) -> asyncio.Lock:
    key = f"{container_name}:{tunnel_name}"
    lock = TUNNEL_OPERATION_LOCKS.get(key)
    if lock is None:
        lock = asyncio.Lock()
        TUNNEL_OPERATION_LOCKS[key] = lock
    return lock


def _get_deploy_node_lock(node_id: int) -> asyncio.Lock:
    key = int(node_id)
    lock = DEPLOY_NODE_LOCKS.get(key)
    if lock is None:
        lock = asyncio.Lock()
        DEPLOY_NODE_LOCKS[key] = lock
    return lock


async def start_sshx_session(container_name: str, node_id: int) -> Optional[str]:
    """Create a fresh SSHX session with durable-supervisor and direct-run fallback."""
    if not SSHX_ENABLED:
        return None
    lock = _get_tunnel_lock(container_name, "sshx")
    async with lock:
        async def persist(url: str) -> str:
            for items in vps_data.values():
                for vps in items:
                    if str(vps.get('container_name')) == str(container_name):
                        vps['sshx_url'] = url
                        vps['sshx_started_at'] = datetime.now().isoformat()
                        save_vps_data_immediate()
                        return url
            return url

        try:
            await asyncio.wait_for(install_tunnel_supervisors(container_name, node_id), timeout=95)
            cleanup = r"""set +e
mkdir -p /var/lib/rgnodes
rm -f /var/lib/rgnodes/sshx.url /var/lib/rgnodes/sshx.pid /var/lib/rgnodes/sshx-direct.pid
pid=$(cat /var/lib/rgnodes/sshx.supervisor.pid 2>/dev/null | head -n1)
if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then
  kill -TERM "$pid" >/dev/null 2>&1 || true
  sleep 1
fi
rm -f /var/lib/rgnodes/sshx.supervisor.pid
"""
            await _exec_guest_bash(container_name, node_id, cleanup, timeout=20)
            for attempt in range(1, SSHX_START_RETRIES + 1):
                control = await _run_tunnel_control(container_name, node_id, "start", "sshx", timeout=55)
                poll_script = rf"""set +e
for _ in $(seq 1 {SSHX_SESSION_WAIT_SECONDS}); do
  url=$(cat /var/lib/rgnodes/sshx.url 2>/dev/null | head -n1)
  if ! printf '%s' "$url" | grep -Eq '^https?://sshx\.io/[A-Za-z0-9._/-]+'; then
    url=$(grep -hEo 'https?://sshx\.io/[^[:space:]`<>]+' /var/lib/rgnodes/sshx.log /var/lib/rgnodes/sshx-tty.log 2>/dev/null | tail -n1)
  fi
  if printf '%s' "$url" | grep -Eq '^https?://sshx\.io/[A-Za-z0-9._/-]+'; then
    printf '%s\n' "$url"; exit 0
  fi
  sleep 1
done
printf 'SSHX_TIMEOUT\n'
tail -n 35 /var/lib/rgnodes/sshx.log 2>/dev/null || true
tail -n 25 /var/lib/rgnodes/sshx-tty.log 2>/dev/null || true
"""
                output = await _exec_guest_bash(container_name, node_id, poll_script, timeout=min(100, SSHX_SESSION_WAIT_SECONDS + 20))
                m = re.search(r'https?://sshx\.io/[A-Za-z0-9._/-]+', str(output or ''))
                if m:
                    return await persist(m.group(0).rstrip('`.,);'))
                logger.warning("SSHX supervisor attempt %s/%s failed for %s: %s", attempt, SSHX_START_RETRIES, container_name, str(output or '')[-1200:])
                if attempt < SSHX_START_RETRIES:
                    await asyncio.sleep(2)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("SSHX supervisor path unavailable for %s: %s", container_name, exc)

        # Direct fallback: documented SSHX temporary-run mode, with no systemd/cron dependency.
        direct = r"""set +e
D=/var/lib/rgnodes
mkdir -p "$D"
rm -f "$D/sshx-direct.url" "$D/sshx-direct.pid"
cat > "$D/sshx-direct-run.sh" <<'EOF_DIRECT'
#!/bin/sh
set +e
export TERM="${TERM:-xterm-256color}"
exec 2>&1
if command -v curl >/dev/null 2>&1; then
  exec curl -sSf --retry 3 --connect-timeout 12 --max-time 90 https://sshx.io/get | sh -s run
elif command -v wget >/dev/null 2>&1; then
  exec wget -qO- --tries=3 --timeout=12 https://sshx.io/get | sh -s run
else
  exit 127
fi
EOF_DIRECT
chmod 0755 "$D/sshx-direct-run.sh"
if command -v script >/dev/null 2>&1; then
  nohup script -q -f -c "$D/sshx-direct-run.sh" "$D/sshx-direct-tty.log" >"$D/sshx-direct.log" 2>&1 </dev/null &
else
  nohup "$D/sshx-direct-run.sh" >"$D/sshx-direct.log" 2>&1 </dev/null &
fi
printf '%s\n' "$!" > "$D/sshx-direct.pid"
printf 'DIRECT_STARTED\n'
"""
        try:
            await _exec_guest_bash(container_name, node_id, direct, timeout=20)
            poll = r"""set +e
D=/var/lib/rgnodes
for _ in $(seq 1 70); do
  url=$(grep -hEo 'https?://sshx\.io/[^[:space:]`<>]+' "$D/sshx-direct.log" "$D/sshx-direct-tty.log" 2>/dev/null | tail -n1)
  if printf '%s' "$url" | grep -Eq '^https?://sshx\.io/[A-Za-z0-9._/-]+'; then
    printf '%s\n' "$url" > "$D/sshx-direct.url"
    printf '%s\n' "$url"
    exit 0
  fi
  sleep 1
done
printf 'SSHX_DIRECT_TIMEOUT\n'
tail -n 50 "$D/sshx-direct.log" 2>/dev/null || true
tail -n 30 "$D/sshx-direct-tty.log" 2>/dev/null || true
"""
            output = await _exec_guest_bash(container_name, node_id, poll, timeout=95)
            m = re.search(r'https?://sshx\.io/[A-Za-z0-9._/-]+', str(output or ''))
            if m:
                return await persist(m.group(0).rstrip('`.,);'))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("SSHX direct fallback failed for %s: %s", container_name, exc)
        return None

async def get_sshx_diagnostics(container_name: str, node_id: int) -> str:
    """Collect a bounded admin-only SSHX diagnostic snapshot."""
    script = r'''set +e
printf '%s\n' '--- SSHX supervisor ---'
pid=$(cat /var/lib/rgnodes/sshx.supervisor.pid 2>/dev/null | head -n1)
printf 'supervisor_pid=%s\n' "$pid"
if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then printf '%s\n' 'supervisor_alive=true'; else printf '%s\n' 'supervisor_alive=false'; fi
printf '%s\n' '--- child ---'
cpid=$(cat /var/lib/rgnodes/sshx.pid 2>/dev/null | head -n1)
printf 'child_pid=%s\n' "$cpid"
if [ -n "$cpid" ] && kill -0 "$cpid" >/dev/null 2>&1; then printf '%s\n' 'child_alive=true'; else printf '%s\n' 'child_alive=false'; fi
printf '%s\n' '--- tools ---'
command -v sshx 2>/dev/null || true
command -v curl 2>/dev/null || true
command -v wget 2>/dev/null || true
command -v script 2>/dev/null || true
printf '%s\n' '--- mode/url ---'
cat /var/lib/rgnodes/sshx.mode 2>/dev/null || true
cat /var/lib/rgnodes/sshx.url 2>/dev/null || true
printf '%s\n' '--- architecture ---'
uname -m 2>/dev/null || true
printf '%s\n' '--- network ---'
getent hosts sshx.io 2>/dev/null || true
if command -v curl >/dev/null 2>&1; then curl -IsS --max-time 8 https://sshx.io/get 2>&1 | head -n 6 || true; fi
printf '%s\n' '--- recent log ---'
tail -n 80 /var/lib/rgnodes/sshx.log 2>/dev/null || true
printf '%s\n' '--- PTY log ---'
tail -n 60 /var/lib/rgnodes/sshx-tty.log 2>/dev/null || true
printf '%s\n' '--- install log ---'
tail -n 40 /tmp/rgnodes-sshx-install.log 2>/dev/null || true
'''
    try:
        out = await _exec_guest_bash(container_name, node_id, script, timeout=15)
        return str(out or '')[-6000:]
    except Exception as exc:
        return f"diagnostics unavailable: {exc}"



async def get_sshx_session_info(container_name: str, node_id: int) -> tuple[Optional[str], bool]:
    """Return current SSHX URL and whether the supervisor/session is alive."""
    script=r'''set +e
url=$(cat /var/lib/rgnodes/sshx.url 2>/dev/null | head -n1)
pid=$(cat /var/lib/rgnodes/sshx.pid 2>/dev/null | head -n1)
[ -n "$pid" ] || pid=$(cat /var/lib/rgnodes/sshx-direct.pid 2>/dev/null | head -n1)
sup=$(cat /var/lib/rgnodes/sshx.supervisor.pid 2>/dev/null | head -n1)
child_alive=false; sup_alive=false
[ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1 && child_alive=true
[ -n "$sup" ] && kill -0 "$sup" >/dev/null 2>&1 && sup_alive=true
if ! printf '%s' "$url" | grep -Eq '^https://sshx\.io/[A-Za-z0-9._/-]+'; then
  url=$(grep -hEo 'https?://sshx\.io/[A-Za-z0-9._/-]+' /var/lib/rgnodes/sshx.log /var/lib/rgnodes/sshx-tty.log 2>/dev/null | tail -n1)
fi
if ! $sup_alive && [ -x /usr/local/bin/sshx ]; then
  command -v sshx >/dev/null 2>&1 && sup_alive=false
fi
# A supervisor process alone is not a connected tunnel. Require the tunnel child + URL.
printf '%s\n' "$child_alive"; printf '%s\n' "$sup_alive"; printf '%s\n' "$url"
'''
    try:
        output=await _exec_guest_bash(container_name,node_id,script,timeout=20)
        lines=[x.strip() for x in str(output or '').splitlines()]
        child=len(lines)>0 and lines[0].lower()=='true'; sup=len(lines)>1 and lines[1].lower()=='true'
        url=next((x for x in lines[2:] if re.match(r'^https?://sshx\.io/', x, re.I)),None)
        if url and url.lower().startswith('http://'):
            url='https://' + url[7:]
        return url,bool(url and child)
    except Exception: return None,False



PINGGY_ENDPOINT_RE = re.compile(
    r"(?:(?:tcp|http|https)://)?([A-Za-z0-9][A-Za-z0-9.-]*pinggy(?:-free)?\.(?:link|online)):(\d{2,5})",
    re.IGNORECASE,
)
ANSI_RE = re.compile(r"\x1B(?:[@-_][0-?]*[ -/]*[@-~])")


def parse_pinggy_endpoint(output: str) -> tuple[Optional[str], Optional[int], Optional[str]]:
    """Parse current Pinggy TCP endpoint formats robustly."""
    cleaned = ANSI_RE.sub('', str(output or ''))
    for text in [cleaned] + re.findall(r"tcp://[^\s`'<>]+", cleaned, flags=re.IGNORECASE):
        m = PINGGY_ENDPOINT_RE.search(text)
        if m:
            host = m.group(1).rstrip('.,);]')
            try:
                port = int(m.group(2))
            except ValueError:
                continue
            if 1 <= port <= 65535:
                return host, port, f"tcp://{host}:{port}"
    host_m = re.search(r"([A-Za-z0-9][A-Za-z0-9.-]*(?:pinggy(?:-free)?|pinggy-free)\.(?:link|online))", cleaned, re.I)
    port_m = re.search(r"\b([1-9]\d{2,4})\b", cleaned)
    if host_m and port_m:
        host = host_m.group(1)
        port = int(port_m.group(1))
        if 1 <= port <= 65535:
            return host, port, f"tcp://{host}:{port}"
    return None, None, None


async def _install_tunnel_supervisors_unlocked(container_name: str, node_id: int) -> None:
    """Install durable low-memory SSHX/Pinggy tunnel supervisors (serialized wrapper below)."""
    safe_host = re.sub(r"[^A-Za-z0-9.-]", "", PINGGY_HOST).strip('.') or "free.pinggy.io"
    safe_port = max(1, min(65535, int(PINGGY_SSH_PORT)))
    script = r"""set +e
export DEBIAN_FRONTEND=noninteractive
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
D=/var/lib/rgnodes
mkdir -p /usr/local/sbin "$D"

install_pkg() {
  pkgs="$*"
  [ -n "$pkgs" ] || return 0
  if command -v apt-get >/dev/null 2>&1; then
    # Avoid repeated apt index downloads on every tunnel health check.
    apt-get install -y --no-install-recommends $pkgs >/dev/null 2>&1 || {
      apt-get update -qq >/dev/null 2>&1 || true
      apt-get install -y --no-install-recommends $pkgs >/dev/null 2>&1 || true
    }
  elif command -v apk >/dev/null 2>&1; then
    apk add --no-cache $pkgs >/dev/null 2>&1 || true
  elif command -v dnf >/dev/null 2>&1; then
    dnf install -y $pkgs >/dev/null 2>&1 || true
  elif command -v yum >/dev/null 2>&1; then
    yum install -y $pkgs >/dev/null 2>&1 || true
  elif command -v zypper >/dev/null 2>&1; then
    zypper --non-interactive install -y $pkgs >/dev/null 2>&1 || true
  fi
}
command -v ssh >/dev/null 2>&1 || install_pkg openssh-client
command -v ssh >/dev/null 2>&1 || install_pkg openssh-clients
command -v curl >/dev/null 2>&1 || install_pkg curl
command -v curl >/dev/null 2>&1 || command -v wget >/dev/null 2>&1 || install_pkg wget
command -v script >/dev/null 2>&1 || install_pkg util-linux
command -v flock >/dev/null 2>&1 || true

cat > /usr/local/sbin/rgnodes-sshx-supervisor <<'EOF_SSHX'
#!/usr/bin/env bash
set +e
export TERM="${TERM:-xterm-256color}"
export LANG="${LANG:-C.UTF-8}"
export LC_ALL="${LC_ALL:-C.UTF-8}"
D=/var/lib/rgnodes
LOG="$D/sshx.log"
TTYLOG="$D/sshx-tty.log"
URL="$D/sshx.url"
PID="$D/sshx.pid"
SUPPID="$D/sshx.supervisor.pid"
LOCK="$D/sshx.lock"
mkdir -p "$D"
umask 022
printf '%s\n' "$$" > "$SUPPID"
exec 9>"$LOCK"
if command -v flock >/dev/null 2>&1; then flock -n 9 || exit 0; fi

extract_url() {
  for f in "$LOG" "$TTYLOG"; do
    [ -s "$f" ] || continue
    cleaned=$(sed -E $'s/\\x1B\\[[0-9;]*[[:alpha:]]//g' "$f" 2>/dev/null || true)
    found=$(printf '%s\n' "$cleaned" | grep -Eo '(https?://)?sshx\.io/[^[:space:]`<>]+' | tail -n1 | sed -E 's/[.,;:)\\]]+$//' || true)
    if [ -n "$found" ]; then
      case "$found" in
        https://*|http://*) printf '%s\n' "$found" ;;
        *) printf 'https://%s\n' "$found" ;;
      esac
      return 0
    fi
  done
  return 1
}

run_with_pty() {
  cmd="$1"
  if command -v script >/dev/null 2>&1; then
    script -q -f -c "$cmd" "$TTYLOG"
    return $?
  fi
  if command -v setsid >/dev/null 2>&1; then
    setsid /bin/bash -lc "$cmd"
    return $?
  fi
  /bin/bash -lc "$cmd"
}

find_sshx_bin() {
  for b in /usr/local/bin/sshx /usr/bin/sshx /root/.local/bin/sshx "$HOME/.local/bin/sshx" "$HOME/.cargo/bin/sshx"; do
    [ -x "$b" ] && { printf '%s\n' "$b"; return 0; }
  done
  command -v sshx 2>/dev/null || true
}

install_sshx_once() {
  bin=$(find_sshx_bin)
  [ -n "$bin" ] && { printf '%s\n' "$bin"; return 0; }
  if command -v curl >/dev/null 2>&1; then
    curl -sSf --retry 4 --connect-timeout 12 --max-time 90 https://sshx.io/get | sh >/var/lib/rgnodes/sshx-install.log 2>&1 || true
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- --tries=4 --timeout=12 https://sshx.io/get | sh >/var/lib/rgnodes/sshx-install.log 2>&1 || true
  fi
  find_sshx_bin
}

run_sshx() {
  # Primary path: SSHX's documented no-install/CI mode. This avoids dependency on
  # where a binary was installed and is designed to print a live session URL.
  if command -v curl >/dev/null 2>&1; then
    run_with_pty 'curl -sSf --retry 4 --connect-timeout 12 --max-time 90 https://sshx.io/get | sh -s run'
    rc=$?
    [ $rc -eq 0 ] && return 0
  elif command -v wget >/dev/null 2>&1; then
    run_with_pty 'wget -qO- --tries=4 --timeout=12 https://sshx.io/get | sh -s run'
    rc=$?
    [ $rc -eq 0 ] && return 0
  fi
  # Fallback: cached/system binary with a real pseudo-terminal.
  bin=$(install_sshx_once)
  if [ -n "$bin" ]; then
    run_with_pty "$bin"
    return $?
  fi
  return 127
}

trap 'rm -f "$PID" "$SUPPID"' EXIT INT TERM
while true; do
  # Keep the tunnel's own logs tiny; never let reconnect loops fill guest disk.
  for f in "$LOG" "$TTYLOG" "/var/lib/rgnodes/sshx-supervisor.log"; do
    [ -f "$f" ] && [ "$(wc -c < "$f" 2>/dev/null || echo 0)" -gt 2097152 ] && tail -c 524288 "$f" > "$f.tmp" 2>/dev/null && mv "$f.tmp" "$f" 2>/dev/null || true
  done
  : > "$URL"
  : > "$LOG"
  : > "$TTYLOG"
  run_sshx >>"$LOG" 2>&1 &
  child=$!
  printf '%s\n' "$child" > "$PID"
  connected=0
  for _ in $(seq 1 90); do
    sleep 1
    found=$(extract_url)
    if printf '%s' "$found" | grep -Eq '^https://sshx\.io/[^[:space:]`<>]+'; then
      printf '%s\n' "$found" | head -n1 > "$URL"
      connected=1
      break
    fi
    kill -0 "$child" >/dev/null 2>&1 || break
  done
  if [ "$connected" -ne 1 ]; then
    printf '%s SSHX session did not publish a URL; retrying\n' "$(date -u +%FT%TZ)" >> "$LOG"
  fi
  wait "$child" >/dev/null 2>&1 || true
  rm -f "$PID"
  sleep 3
done
EOF_SSHX
chmod 0755 /usr/local/sbin/rgnodes-sshx-supervisor

cat > /usr/local/sbin/rgnodes-pinggy-supervisor <<'EOF_PINGGY'
#!/usr/bin/env bash
set +e
D=/var/lib/rgnodes
LOG="$D/pinggy.log"
INFO="$D/pinggy.info"
PID="$D/pinggy.pid"
SUPPID="$D/pinggy.supervisor.pid"
KEY="$D/pinggy_ed25519"
HOST="__PINGGY_HOST__"
PORT="__PINGGY_PORT__"
LOCK="$D/pinggy.lock"
mkdir -p "$D"
printf '%s\n' "$$" > "$SUPPID"
exec 8>"$LOCK"
if command -v flock >/dev/null 2>&1; then flock -n 8 || exit 0; fi
if command -v ssh-keygen >/dev/null 2>&1 && [ ! -s "$KEY" ]; then
  ssh-keygen -q -t ed25519 -N '' -f "$KEY" -C rgnodes-pinggy >/dev/null 2>&1 || true
  chmod 0600 "$KEY" >/dev/null 2>&1 || true
fi
extract_endpoint() {
  sed -E $'s/\\x1B\\[[0-9;]*[[:alpha:]]//g' "$LOG" 2>/dev/null | \
    grep -Eo '(tcp://)?[A-Za-z0-9][A-Za-z0-9.-]*(pinggy(-free)?|pinggy-free)\\.(link|online):[0-9]{2,5}' | head -n1 || true
}
trap 'rm -f "$PID" "$SUPPID"' EXIT INT TERM
while true; do
  if [ -f "$LOG" ] && [ "$(wc -c < "$LOG" 2>/dev/null || echo 0)" -gt 2097152 ]; then
    tail -c 524288 "$LOG" > "$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG" 2>/dev/null || true
  fi
  : > "$INFO"
  : > "$LOG"
  if [ -s "$KEY" ]; then
    (printf '\n' | ssh -T \
      -o PreferredAuthentications=keyboard-interactive,password \
      -o PasswordAuthentication=yes \
      -o KbdInteractiveAuthentication=yes \
      -o StrictHostKeyChecking=no \
      -o UserKnownHostsFile=/dev/null \
      -o UpdateHostkeys=no \
      -o ServerAliveInterval=20 \
      -o ServerAliveCountMax=3 \
      -o TCPKeepAlive=yes \
      -o ExitOnForwardFailure=yes \
      -o ConnectTimeout=15 \
      -o ConnectionAttempts=3 \
      -o IdentitiesOnly=yes \
      -o IdentityFile="$KEY" \
      -p "$PORT" -R 0:127.0.0.1:22 "tcp@$HOST" >"$LOG" 2>&1) &
  else
    (printf '\n' | ssh -T \
      -o StrictHostKeyChecking=no \
      -o UserKnownHostsFile=/dev/null \
      -o UpdateHostkeys=no \
      -o ServerAliveInterval=20 \
      -o ServerAliveCountMax=3 \
      -o TCPKeepAlive=yes \
      -o ExitOnForwardFailure=yes \
      -o ConnectTimeout=15 \
      -o ConnectionAttempts=3 \
      -p "$PORT" -R 0:127.0.0.1:22 "tcp@$HOST" >"$LOG" 2>&1) &
  fi
  child=$!
  printf '%s\n' "$child" > "$PID"
  for _ in $(seq 1 70); do
    sleep 1
    endpoint=$(extract_endpoint)
    if [ -n "$endpoint" ]; then
      case "$endpoint" in tcp://*) ;; *) endpoint="tcp://$endpoint" ;; esac
      printf '%s\n' "$endpoint" > "$INFO"
      break
    fi
    kill -0 "$child" >/dev/null 2>&1 || break
  done
  wait "$child" >/dev/null 2>&1 || true
  rm -f "$PID"
  sleep 4
done
EOF_PINGGY
chmod 0755 /usr/local/sbin/rgnodes-pinggy-supervisor

if [ -d /run/systemd/system ] && [ "$(cat /proc/1/comm 2>/dev/null)" = "systemd" ]; then
  cat > /etc/systemd/system/rgnodes-sshx.service <<'EOF_UNIT'
[Unit]
Description=RGNODES SSHX Tunnel Supervisor
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
ExecStart=/usr/local/sbin/rgnodes-sshx-supervisor
Restart=always
RestartSec=3
KillMode=control-group
[Install]
WantedBy=multi-user.target
EOF_UNIT
  cat > /etc/systemd/system/rgnodes-pinggy.service <<'EOF_UNIT'
[Unit]
Description=RGNODES Pinggy SSH Tunnel Supervisor
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
ExecStart=/usr/local/sbin/rgnodes-pinggy-supervisor
Restart=always
RestartSec=3
KillMode=control-group
[Install]
WantedBy=multi-user.target
EOF_UNIT
  systemctl daemon-reload >/dev/null 2>&1 || true
  systemctl enable rgnodes-sshx.service rgnodes-pinggy.service >/dev/null 2>&1 || true
else
  mkdir -p /etc/cron.d
  printf '%s\n' '@reboot root /usr/local/sbin/rgnodes-sshx-supervisor >>/var/lib/rgnodes/sshx-supervisor.log 2>&1' > /etc/cron.d/rgnodes-sshx
  printf '%s\n' '@reboot root /usr/local/sbin/rgnodes-pinggy-supervisor >>/var/lib/rgnodes/pinggy-supervisor.log 2>&1' > /etc/cron.d/rgnodes-pinggy
  chmod 0644 /etc/cron.d/rgnodes-sshx /etc/cron.d/rgnodes-pinggy 2>/dev/null || true
fi
printf 'TUNNEL_SUPERVISORS_READY\n'
""".replace('__PINGGY_HOST__', safe_host).replace('__PINGGY_PORT__', str(safe_port))
    await _exec_guest_bash(container_name, node_id, script, timeout=180)


async def install_tunnel_supervisors(container_name: str, node_id: int) -> None:
    """Serialize tunnel bootstrap per VPS to avoid package-manager/systemd races."""
    key = (str(container_name), int(node_id))
    lock = TUNNEL_SETUP_LOCKS.get(key)
    if lock is None:
        lock = asyncio.Lock()
        TUNNEL_SETUP_LOCKS[key] = lock
    async with lock:
        await _install_tunnel_supervisors_unlocked(container_name, node_id)


async def start_pinggy_session(container_name: str, node_id: int) -> Optional[dict]:
    """Restart Pinggy's durable supervisor and return the fresh public TCP endpoint."""
    if not PINGGY_ENABLED:
        return None
    lock = _get_tunnel_lock(container_name, "pinggy")
    async with lock:
        try:
            await install_tunnel_supervisors(container_name, node_id)
            await _exec_guest_bash(container_name, node_id, "rm -f /var/lib/rgnodes/pinggy.info /var/lib/rgnodes/pinggy.pid", timeout=10)
            await _run_tunnel_control(container_name, node_id, "restart", "pinggy", timeout=50)
            poll_script = r'''set +e
for _ in $(seq 1 60); do
  info=$(cat /var/lib/rgnodes/pinggy.info 2>/dev/null || true)
  if printf '%s' "$info" | grep -Eq '(tcp://)?[A-Za-z0-9][A-Za-z0-9.-]*(pinggy(-free)?|pinggy-free)\\.(link|online):[0-9]{2,5}'; then
    printf '%s\n' "$info"
    exit 0
  fi
  sleep 1
done
printf 'PINGGY_TIMEOUT\n'
tail -n 30 /var/lib/rgnodes/pinggy.log 2>/dev/null || true
exit 0
'''
            output = await _exec_guest_bash(container_name, node_id, poll_script, timeout=min(max(TUNNEL_START_TIMEOUT, 90), 120))
            host, port, url = parse_pinggy_endpoint(str(output or ''))
            if not (host and port):
                logger.warning(f'Pinggy endpoint was not produced for {container_name}: {str(output)[-1800:]}')
                return None
            result = {'host': host, 'port': port, 'url': url}
            for items in vps_data.values():
                for vps in items:
                    if str(vps.get('container_name')) == str(container_name):
                        vps['pinggy_host'] = host
                        vps['pinggy_port'] = port
                        vps['pinggy_url'] = url
                        vps['pinggy_started_at'] = datetime.now().isoformat()
                        try:
                            pid_out = await _exec_guest_bash(container_name, node_id, 'cat /var/lib/rgnodes/pinggy.pid 2>/dev/null || true', timeout=10)
                            vps['pinggy_pid'] = int(str(pid_out).strip()) if str(pid_out).strip().isdigit() else None
                        except Exception:
                            vps['pinggy_pid'] = None
                        save_vps_data_immediate()
                        break
            return result
        except Exception as e:
            logger.warning(f'Pinggy session failed for {container_name}: {e}', exc_info=True)
            return None


async def get_pinggy_session_info(container_name: str, node_id: int) -> tuple[Optional[str], Optional[int], bool]:
    script = r'''set +e
systemd_ok=false
[ -d /run/systemd/system ] && [ "$(cat /proc/1/comm 2>/dev/null)" = "systemd" ] && systemd_ok=true
active=false
if [ "$systemd_ok" = true ] && systemctl is-active --quiet rgnodes-pinggy.service; then active=true; fi
sup_pid=$(cat /var/lib/rgnodes/pinggy.supervisor.pid 2>/dev/null | head -n1)
if [ -n "$sup_pid" ] && kill -0 "$sup_pid" >/dev/null 2>&1; then active=true; fi
pid=$(cat /var/lib/rgnodes/pinggy.pid 2>/dev/null | head -n1)
if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then active=true; fi
printf '%s\n' "$active"
cat /var/lib/rgnodes/pinggy.info 2>/dev/null || true
'''
    try:
        output = await _exec_guest_bash(container_name, node_id, script, timeout=20)
        lines = [x.strip() for x in str(output or '').splitlines() if x.strip()]
        active = bool(lines and lines[0].lower() == 'true')
        host, port, _ = parse_pinggy_endpoint('\n'.join(lines[1:]))
        return host, port, active and bool(host and port)
    except Exception:
        return None, None, False



def _png_rgba(width: int, height: int, pixels: bytearray) -> bytes:
    """Encode RGBA pixels to a tiny dependency-free PNG."""
    import struct, zlib
    raw = bytearray()
    stride = width * 4
    for y in range(height):
        raw.append(0)
        raw.extend(pixels[y * stride:(y + 1) * stride])
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    header = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header) + chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b'')


def _draw_disc(pix: bytearray, size: int, cx: int, cy: int, r: int, rgba):
    rr = r * r
    for y in range(max(0, cy-r), min(size, cy+r+1)):
        for x in range(max(0, cx-r), min(size, cx+r+1)):
            if (x-cx)*(x-cx) + (y-cy)*(y-cy) <= rr:
                i = (y*size+x)*4
                pix[i:i+4] = bytes(rgba)


def _draw_rect(pix: bytearray, size: int, x0: int, y0: int, x1: int, y1: int, rgba):
    for y in range(max(0,y0), min(size,y1+1)):
        for x in range(max(0,x0), min(size,x1+1)):
            i=(y*size+x)*4
            pix[i:i+4]=bytes(rgba)


def _draw_line(pix: bytearray, size: int, x0: int, y0: int, x1: int, y1: int, width: int, rgba):
    steps=max(abs(x1-x0),abs(y1-y0),1)
    for n in range(steps+1):
        x=round(x0+(x1-x0)*n/steps); y=round(y0+(y1-y0)*n/steps)
        _draw_disc(pix,size,x,y,max(1,width//2),rgba)


def _builtin_emoji_gif(key: str, size: int = 96) -> bytes | None:
    """Create a tiny animated emoji when Pillow is available; return None otherwise."""
    try:
        from PIL import Image, ImageDraw
        import io
        size=max(64,min(96,int(size)))
        frames=[]
        for phase in (0,1,0,2):
            img=Image.new('RGBA',(size,size),(0,0,0,0))
            draw=ImageDraw.Draw(img)
            scale=1.0 + phase*0.035
            r=int(size*0.40*scale); cx=cy=size//2
            bg={
                'online':(46,204,113,255),'status':(46,204,113,255),'success':(46,204,113,255),'start':(46,204,113,255),'pinggy':(46,204,113,255),
                'offline':(231,76,60,255),'error':(231,76,60,255),'delete':(192,57,43,255),'stop':(231,76,60,255),'pinggy_offline':(231,76,60,255),
                'warning':(241,196,15,255),'maintenance':(231,76,60,255),'loading':(52,152,219,255),'sshx':(52,152,219,255),
                'vps':(155,89,182,255),'server':(52,73,94,255),'ssh':(127,140,141,255),'ports':(230,126,34,255),'password':(243,156,18,255),
            }.get(key,(52,152,219,255))
            draw.ellipse((cx-r,cy-r,cx+r,cy+r),fill=bg)
            rr=max(2,int(size*0.045))
            draw.ellipse((cx-int(size*.10),cy-int(size*.10),cx+int(size*.10),cy+int(size*.10)),fill=(255,255,255,255))
            draw.line((cx-int(size*.06),cy,cx+int(size*.10),cy),fill=bg,width=rr)
            frames.append(img)
        out=io.BytesIO(); frames[0].save(out,format='GIF',save_all=True,append_images=frames[1:],duration=180,loop=0,disposal=2,optimize=True)
        return out.getvalue()
    except Exception:
        return None


def _builtin_emoji_png(key: str, size: int = 96) -> bytes:
    """Generate a compact, consistent server emoji without Pillow or image files."""
    size=max(64,min(128,int(size)))
    pix=bytearray(b'\x00'*(size*size*4)); cx=cy=size//2
    bg_map={
        'online':(46,204,113,255),'status':(46,204,113,255),'success':(46,204,113,255),'start':(46,204,113,255),'pinggy':(46,204,113,255),
        'offline':(231,76,60,255),'error':(231,76,60,255),'delete':(192,57,43,255),'stop':(231,76,60,255),'pinggy_offline':(231,76,60,255),
        'warning':(241,196,15,255),'maintenance':(231,76,60,255),'loading':(52,152,219,255),'sshx':(52,152,219,255),
        'vps':(155,89,182,255),'deploy':(52,152,219,255),'rocket':(52,152,219,255),'server':(52,73,94,255),
        'cpu':(26,188,156,255),'ram':(52,152,219,255),'disk':(149,165,166,255),'network':(22,160,133,255),
        'docker':(41,128,185,255),'ssh':(127,140,141,255),'ports':(230,126,34,255),'password':(243,156,18,255),
        'reinstall':(142,68,173,255),'renew':(39,174,96,255),'stats':(52,152,219,255),'refresh':(52,152,219,255),
    }
    bg=bg_map.get(key,(96,125,139,255)); white=(255,255,255,255)
    _draw_disc(pix,size,cx,cy,int(size*0.45),bg)
    if key in {'online','status','success','start','pinggy'}:
        _draw_disc(pix,size,cx,cy,int(size*0.18),white); _draw_disc(pix,size,cx,cy,int(size*0.08),bg)
    elif key in {'offline','error','delete','stop','pinggy_offline'}:
        w=max(4,int(size*.09)); _draw_line(pix,size,int(size*.32),int(size*.32),int(size*.68),int(size*.68),w,white); _draw_line(pix,size,int(size*.68),int(size*.32),int(size*.32),int(size*.68),w,white)
    elif key in {'warning','maintenance'}:
        _draw_rect(pix,size,int(size*.47),int(size*.30),int(size*.53),int(size*.58),white); _draw_disc(pix,size,cx,int(size*.68),max(2,int(size*.045)),white)
    elif key in {'vps','server','docker'}:
        _draw_rect(pix,size,int(size*.28),int(size*.31),int(size*.72),int(size*.69),white); _draw_rect(pix,size,int(size*.34),int(size*.39),int(size*.66),int(size*.45),bg); _draw_rect(pix,size,int(size*.34),int(size*.51),int(size*.66),int(size*.57),bg); _draw_disc(pix,size,int(size*.38),int(size*.62),3,white)
    elif key=='cpu':
        _draw_rect(pix,size,int(size*.34),int(size*.34),int(size*.66),int(size*.66),white); _draw_rect(pix,size,int(size*.29),int(size*.43),int(size*.33),int(size*.49),white); _draw_rect(pix,size,int(size*.67),int(size*.43),int(size*.71),int(size*.49),white)
    elif key=='ram':
        for y in (int(size*.36),int(size*.49),int(size*.62)): _draw_rect(pix,size,int(size*.29),y,int(size*.71),y+int(size*.07),white)
    elif key=='disk':
        _draw_disc(pix,size,cx,int(size*.48),int(size*.18),white); _draw_rect(pix,size,int(size*.30),int(size*.53),int(size*.70),int(size*.62),white); _draw_disc(pix,size,cx,int(size*.48),int(size*.07),bg)
    elif key in {'network','ports'}:
        a=(int(size*.35),int(size*.60)); b=(int(size*.63),int(size*.36)); c=(int(size*.66),int(size*.65)); _draw_line(pix,size,*a,*b,int(size*.05),white); _draw_line(pix,size,*b,*c,int(size*.05),white); _draw_disc(pix,size,*a,int(size*.10),white); _draw_disc(pix,size,*b,int(size*.10),white); _draw_disc(pix,size,*c,int(size*.10),white)
    elif key in {'ssh','sshx'}:
        _draw_disc(pix,size,cx,cy,int(size*.22),white); _draw_line(pix,size,int(size*.38),int(size*.50),int(size*.58),int(size*.50),int(size*.05),bg); _draw_line(pix,size,int(size*.50),int(size*.38),int(size*.50),int(size*.62),int(size*.05),bg)
    elif key=='password':
        _draw_disc(pix,size,int(size*.42),int(size*.47),int(size*.13),white); _draw_rect(pix,size,int(size*.48),int(size*.44),int(size*.70),int(size*.54),white)
    elif key=='refresh':
        _draw_line(pix,size,int(size*.35),int(size*.60),int(size*.35),int(size*.42),int(size*.07),white); _draw_line(pix,size,int(size*.35),int(size*.42),int(size*.50),int(size*.32),int(size*.07),white); _draw_line(pix,size,int(size*.65),int(size*.40),int(size*.65),int(size*.58),int(size*.07),white); _draw_line(pix,size,int(size*.65),int(size*.58),int(size*.50),int(size*.68),int(size*.07),white)
    elif key in {'rocket','deploy'}:
        _draw_line(pix,size,int(size*.36),int(size*.66),int(size*.60),int(size*.34),int(size*.10),white); _draw_disc(pix,size,int(size*.56),int(size*.44),int(size*.06),bg)
    elif key=='stats':
        _draw_rect(pix,size,int(size*.32),int(size*.54),int(size*.41),int(size*.68),white); _draw_rect(pix,size,int(size*.45),int(size*.43),int(size*.54),int(size*.68),white); _draw_rect(pix,size,int(size*.58),int(size*.32),int(size*.71),int(size*.68),white)
    elif key=='loading':
        _draw_disc(pix,size,cx,cy,int(size*.23),white); _draw_line(pix,size,cx,cy,int(size*.60),int(size*.42),int(size*.05),bg)
    elif key in {'renew','reinstall'}:
        _draw_line(pix,size,int(size*.33),int(size*.55),int(size*.48),int(size*.68),int(size*.08),white); _draw_line(pix,size,int(size*.48),int(size*.68),int(size*.70),int(size*.36),int(size*.08),white)
    else:
        _draw_disc(pix,size,cx,cy,int(size*.12),white)
    return _png_rgba(size,size,pix)


async def auto_provision_server_emojis(guild: discord.Guild) -> None:
    """Idempotently create the local RGNODES emoji pack when Discord permits it."""
    if not AUTO_CREATE_SERVER_EMOJIS:
        return
    async with EMOJI_PROVISION_LOCK:
        try:
            me = guild.me
            if not me or not me.guild_permissions.manage_emojis_and_stickers:
                logger.info(f"Emoji auto-provision skipped for {guild.name}: Manage Expressions is unavailable.")
                return
            try:
                fetched = await guild.fetch_emojis()
                existing = {str(e.name): e for e in fetched}
                current_count = len(fetched)
            except Exception:
                existing = {str(e.name): e for e in guild.emojis}
                current_count = len(guild.emojis)
            emoji_limit = max(0, int(getattr(guild, 'emoji_limit', 50)))
            available = max(0, emoji_limit - current_count)
            if available <= 0:
                logger.info(f"Emoji auto-provision skipped for {guild.name}: no emoji slots available.")
                return
            created = 0
            for key, configured in CUSTOM_EMOJI_NAMES.items():
                raw = str(configured or '').strip()
                if not raw or re.fullmatch(r'<a?:[A-Za-z0-9_]{2,32}:\d+>', raw):
                    continue
                safe_name = re.sub(r'[^A-Za-z0-9_]', '_', raw)[:32]
                if len(safe_name) < 2 or safe_name in existing or available <= 0:
                    continue
                try:
                    animated_image = _builtin_emoji_gif(key)
                    try:
                        emoji = await guild.create_custom_emoji(
                            name=safe_name,
                            image=animated_image or _builtin_emoji_png(key),
                            reason=f"{BOT_NAME} automatic emoji pack",
                        )
                    except discord.HTTPException:
                        if animated_image is None:
                            raise
                        emoji = await guild.create_custom_emoji(
                            name=safe_name,
                            image=_builtin_emoji_png(key),
                            reason=f"{BOT_NAME} automatic emoji pack (static fallback)",
                        )
                    existing[safe_name] = emoji
                    available -= 1
                    created += 1
                    await asyncio.sleep(1.2)
                except discord.Forbidden as exc:
                    logger.warning(f"Emoji auto-provision forbidden in {guild.name}: {exc}")
                    break
                except discord.HTTPException as exc:
                    retry_after = float(getattr(exc, "retry_after", 3.0) or 3.0)
                    retry_after = min(20.0, max(2.0, retry_after))
                    logger.warning(f"Emoji creation failed for {safe_name!r} in {guild.name}: {exc}; retrying in {retry_after:.1f}s")
                    await asyncio.sleep(retry_after)
                except Exception as exc:
                    logger.warning(f"Emoji creation failed for {safe_name!r}: {exc}")
            logger.info(f"Emoji auto-provision completed for {guild.name}: created={created}, remaining_slots={available}")
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception(f"Emoji auto-provision crashed for {getattr(guild, 'name', guild.id)}: {exc}")


def resolve_custom_emoji(key: str, fallback: str = '') -> str:
    """Return a server custom emoji when available, otherwise a Unicode fallback."""
    raw = str(CUSTOM_EMOJI_NAMES.get(key, '') or '').strip()
    if re.fullmatch(r'<a?:[A-Za-z0-9_]{2,32}:\d+>', raw):
        return raw
    try:
        cached = discord.utils.get(bot.emojis, name=raw) if raw else None
        if cached:
            return str(cached)
    except Exception:
        pass
    return fallback

# Create professional embeds with modern styling
def create_embed(title, description="", color=None):
    """Create a deliberately colorless RGNODES embed; legacy color args are ignored."""
    embed = discord.Embed(
        title=str(title),
        description=truncate_text(description, 4096),
        timestamp=datetime.now(),
    )
    if BOT_THUMBNAIL_URL:
        embed.set_thumbnail(url=BOT_THUMBNAIL_URL)
    footer_icon = BOT_ICON_URL or None
    if footer_icon:
        embed.set_footer(text=f"⚡ {BOT_NAME} • {BOT_DEVELOPER} • v{BOT_VERSION}", icon_url=footer_icon)
    else:
        embed.set_footer(text=f"⚡ {BOT_NAME} • {BOT_DEVELOPER} • v{BOT_VERSION}")
    return embed

def add_field(embed, name, value, inline=False):
    """Add a field with professional formatting"""
    embed.add_field(
        name=f"➤ {name}",
        value=truncate_text(value, 1024),
        inline=inline
    )
    return embed

def create_success_embed(title, description=""):
    """Create a success embed (green)"""
    return create_embed(title, description, COLOR_SUCCESS)

def create_error_embed(title, description=""):
    """Create an error embed (red)"""
    return create_embed(title, description, COLOR_ERROR)

def create_info_embed(title, description=""):
    """Create an info embed (blue)"""
    return create_embed(title, description, COLOR_INFO)

def create_warning_embed(title, description=""):
    """Create a warning embed (orange)"""
    return create_embed(title, description, COLOR_WARNING)

# Visual helper functions
def create_progress_bar(value, max_value=100, length=15):
    """Create a visual progress bar with emoji blocks"""
    if max_value == 0:
        percentage = 0
    else:
        percentage = int((value / max_value) * 100)
    filled = int((percentage / 100) * length)
    bar = "🟩" * filled + "⬜" * (length - filled)
    return f"{bar} `{percentage}%`"

def format_expiration(vps):
    """Format expiration date without crashing on corrupt legacy data."""
    raw = vps.get('expiration_date')
    if not raw:
        return "🔵 No expiration"
    try:
        exp_dt = datetime.fromisoformat(str(raw))
    except (TypeError, ValueError):
        return "⚠️ Invalid expiration"
    days = (exp_dt - datetime.now()).days
    
    if days < 0:
        return f"🔴 **EXPIRED** (`{abs(days)}d ago`)"
    elif days <= EXPIRATION_WARNING_DAYS:
        return f"🟡 **EXPIRING** (`{days}d left`)"
    else:
        return f"🟢 **ACTIVE** (`{days}d left`)"

def create_vps_card(vps, index):
    """Create a formatted VPS information card"""
    node = get_node(vps.get('node_id', 1))
    status_emoji = "🟢" if (vps.get('status') == 'running' and not vps.get('suspended')) else "🟡" if vps.get('suspended') else "🔴"
    node_emoji = "📍" if (node and node.get('is_local')) else "🌐"
    
    card = (
        f"**#{index}** `{vps['container_name']}`\n"
        f"{status_emoji} {vps.get('status', 'unknown').upper()}"
    )
    if vps.get('suspended'):
        card += " (SUSPENDED)"
    
    card += (
        f"\n⚙️ **Config:** {vps.get('config', 'Custom')}\n"
        f"💾 **RAM:** {vps['ram']} | **CPU:** {vps['cpu']} | **Disk:** {vps['storage']} | **Bandwidth:** {int(vps.get('bandwidth_gb') or VPS_BANDWIDTH_GB)}GB\n"
        f"{node_emoji} **Node:** {node['name'] if node else 'Unknown'}\n"
        f"⏰ **Expiration:** {format_expiration(vps)}"
    )
    return card

# Admin checks
def is_admin():
    async def predicate(ctx):
        if is_admin_user(ctx.author):
            return True
        raise commands.CheckFailure("You need RGNODES admin access or Discord Administrator permission to use this command.")
    return commands.check(predicate)

def is_main_admin():
    async def predicate(ctx):
        if str(ctx.author.id) == str(MAIN_ADMIN_ID):
            return True
        raise commands.CheckFailure("Only the main admin can use this command.")
    return commands.check(predicate)

# LXC command execution with multi-node support
async def execute_lxc(container_name: str, command: str, timeout: int = 300, node_id: Optional[int] = None):
    """Execute an LXC/LXD command without blocking the Discord event loop."""
    if node_id is None:
        node_id = find_node_id_for_container(container_name)
    node = get_node(node_id)
    if not node:
        raise RuntimeError(f"Node {node_id} not found")

    full_command = f"lxc {command}".strip()
    if not full_command:
        raise ValueError("LXC command cannot be empty")

    if node.get('is_local'):
        try:
            cmd = shlex.split(full_command)
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                raise asyncio.TimeoutError(f"Command timed out after {timeout} seconds")
            out = stdout.decode(errors='replace').strip() if stdout else ''
            err = stderr.decode(errors='replace').strip() if stderr else ''
            if proc.returncode != 0:
                detail = err or out or 'Command failed without output'
                raise RuntimeError(f"Local LXC command failed: {detail}\nCommand: {full_command}")
            return out if out else True
        except asyncio.TimeoutError:
            logger.error(f"LXC command timed out: {full_command}")
            raise
        except FileNotFoundError as e:
            raise RuntimeError("LXC client is not installed or is not in PATH.") from e
        except Exception as e:
            logger.error(f"LXC error: {full_command} - {e}")
            raise

    url = str(node.get('url') or '').rstrip('/') + '/api/execute'
    api_key = node.get('api_key')
    if not node.get('url') or not api_key:
        raise RuntimeError(f"Remote node {node.get('name', node_id)!r} is missing URL/API key")
    data = {"command": full_command}
    headers = {"X-API-Key": str(api_key)}
    try:
        response = await asyncio.to_thread(
            requests.post,
            url,
            json=data,
            headers=headers,
            timeout=timeout,
        )
    except requests.exceptions.Timeout as e:
        raise RuntimeError(f"Remote execution timed out on {node['name']} after {timeout}s") from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Remote node {node['name']} is unreachable: {e}") from e

    if response.status_code != 200:
        detail = response.text.strip()[:1200]
        try:
            payload = response.json()
            detail = str(payload.get('detail') or payload.get('error') or payload.get('stderr') or payload)[:1200]
        except Exception:
            pass
        raise RuntimeError(f"Remote execution failed on {node['name']} (HTTP {response.status_code}): {detail}")

    try:
        res = response.json()
    except ValueError as e:
        raise RuntimeError(f"Remote node {node['name']} returned invalid JSON") from e

    returncode = res.get('returncode', res.get('return_code', 0))
    try:
        returncode = int(returncode)
    except (TypeError, ValueError):
        returncode = 1
    if returncode != 0:
        stderr = str(res.get('stderr') or res.get('error') or 'Command failed')
        raise RuntimeError(f"Remote LXC command failed on {node['name']}: {stderr[:1600]}\nCommand: {full_command}")
    return res.get('stdout', True)

# Apply LXC config

async def apply_vps_performance_profile(container_name: str, node_id: int, ram_mb: int, cpu: int) -> None:
    """Apply strict memory/CPU limits while letting the real AMD Ryzen host scheduler do the work."""
    ram_mb=max(256,int(ram_mb)); cpu=max(1,int(cpu))
    critical=[
        f"config set {container_name} limits.memory {ram_mb}MB",
        f"config set {container_name} limits.cpu {cpu}",
        f"config set {container_name} boot.autostart true",
        f"config set {container_name} limits.memory.enforce hard",
        f"config set {container_name} limits.memory.swap {'true' if VPS_SWAP_ENABLED else 'false'}",
    ]
    for cmd in critical:
        await execute_lxc(container_name,cmd,node_id=node_id,timeout=60)
    optional=[
        f"config set {container_name} limits.cpu.priority 5",
        f"config set {container_name} limits.cpu.allowance 100%",
        f"config set {container_name} limits.network.priority 5",
        f"config set {container_name} limits.disk.priority 5",
        f"config set {container_name} limits.memory.swap.priority 5",
        f"config set {container_name} limits.processes 2048",
        f"config set {container_name} boot.autostart.priority 100",
    ]
    for cmd in optional:
        try:
            await execute_lxc(container_name,cmd,node_id=node_id,timeout=30)
        except Exception as exc:
            logger.debug(f"Optional performance setting skipped on {container_name}: {cmd}: {exc}")

async def apply_lxc_config(container_name: str, node_id: int):
    """Apply nested/privileged LXC settings with critical vs best-effort handling."""
    critical = [
        f"config set {container_name} security.nesting true",
        f"config set {container_name} security.privileged true",
    ]
    for cmd in critical:
        await execute_lxc(container_name, cmd, node_id=node_id)

    optional = [
        f"config set {container_name} security.syscalls.intercept.mknod true",
        f"config set {container_name} security.syscalls.intercept.setxattr true",
        f"config set {container_name} linux.kernel_modules overlay,loop,nf_nat,ip_tables,ip6_tables,netlink_diag,br_netfilter",
    ]
    for cmd in optional:
        try:
            await execute_lxc(container_name, cmd, node_id=node_id)
        except Exception as e:
            logger.warning(f"Optional LXC setting skipped for {container_name}: {e}")

    try:
        await execute_lxc(
            container_name,
            f"config device add {container_name} fuse unix-char path=/dev/fuse",
            node_id=node_id,
        )
    except Exception as e:
        logger.warning(f"FUSE device could not be added to {container_name}: {e}")

    # KVM is exposed only when the host/device is available. This is deliberately
    # best-effort because many VPS hosts do not expose nested KVM.
    try:
        await execute_lxc(
            container_name,
            f"config device add {container_name} kvm unix-char path=/dev/kvm",
            node_id=node_id,
        )
    except Exception as e:
        logger.info(f"KVM device not available for {container_name}: {e}")

    try:
        await execute_lxc(
            container_name,
            f"config device add {container_name} tun unix-char path=/dev/net/tun",
            node_id=node_id,
        )
    except Exception as e:
        logger.info(f"TUN device not available for {container_name}: {e}")

    # Keep raw.lxc minimal. Older versions used cgroup/mount directives that can
    # conflict with modern cgroup v2/LXD setups and prevent the container from booting.
    raw_lxc_config = (
        "lxc.apparmor.profile = unconfined\n"
        "lxc.apparmor.allow_nesting = 1\n"
        "lxc.cap.drop =\n"
    )
    try:
        await execute_lxc(
            container_name,
            f"config set {container_name} raw.lxc {shlex.quote(raw_lxc_config)}",
            node_id=node_id,
        )
    except Exception as e:
        # Not all LXD builds expose every raw.lxc AppArmor key. The container
        # can still operate with the high-level security settings above.
        logger.warning(f"Optional raw.lxc settings skipped for {container_name}: {e}")

# Apply internal permissions
async def apply_internal_permissions(container_name: str, node_id: int):
    try:
        await asyncio.sleep(5)
        commands = [
            "mkdir -p /etc/sysctl.d/",
            "echo 'net.ipv4.ip_unprivileged_port_start=0' > /etc/sysctl.d/99-custom.conf",
            "echo 'net.ipv4.ping_group_range=0 2147483647' >> /etc/sysctl.d/99-custom.conf",
            "echo 'fs.inotify.max_user_watches=524288' >> /etc/sysctl.d/99-custom.conf",
            "echo 'kernel.unprivileged_userns_clone=1' >> /etc/sysctl.d/99-custom.conf",
            "sysctl -p /etc/sysctl.d/99-custom.conf || true"
        ]
        for cmd in commands:
            try:
                await execute_lxc(container_name, f"exec {container_name} -- bash -c \"{cmd}\"", node_id=node_id)
            except Exception as cmd_error:
                logger.warning(f"Command failed in {container_name}: {cmd} - {cmd_error}")
        logger.info(f"Internal permissions applied to {container_name}")
    except Exception as e:
        logger.error(f"Failed to apply internal permissions to {container_name}: {e}")

# Get or create VPS role
async def get_or_create_vps_role(guild):
    global VPS_USER_ROLE_ID

    me = guild.me
    if not me or not me.guild_permissions.manage_roles:
        return None

    role_name = f"{BOT_NAME} VPS User"

    # Try cached role
    if VPS_USER_ROLE_ID:
        role = guild.get_role(VPS_USER_ROLE_ID)
        if role and role < me.top_role:
            return role
        VPS_USER_ROLE_ID = None

    # Find by name
    role = discord.utils.get(guild.roles, name=role_name)
    if role:
        if role >= me.top_role:
            try:
                await role.delete(reason="Role above bot, recreating")
            except discord.Forbidden:
                return None
            role = None
        else:
            VPS_USER_ROLE_ID = role.id
            return role

    # Create safely below bot
    try:
        role = await guild.create_role(
            name=role_name,
            color=discord.Color.dark_purple(),
            permissions=discord.Permissions.none(),
            reason=f"{BOT_NAME} VPS User role"
        )
        await role.edit(position=me.top_role.position - 1)
        VPS_USER_ROLE_ID = role.id
        logger.info(f"Created VPS role: {role.id}")
        return role
    except Exception as e:
        logger.error(f"Failed to create VPS role: {e}")
        return None

# Host resource functions
def get_host_cpu_usage():
    """Get host CPU usage - cross-platform compatible"""
    try:
        import platform
        system = platform.system()
        
        if system == "Windows":
            # Windows: Use wmic or psutil as fallback
            try:
                import psutil
                return psutil.cpu_percent(interval=1)
            except ImportError:
                # Fallback for Windows without psutil
                try:
                    result = subprocess.run(['wmic', 'os', 'get', 'TotalVisibleMemorySize'], 
                                          capture_output=True, text=True, timeout=5)
                    return 0.0  # Default value on Windows
                except:
                    return 0.0
        else:
            # Linux/Unix: Use mpstat or top
            if shutil.which("mpstat"):
                result = subprocess.run(['mpstat', '1', '1'], capture_output=True, text=True, timeout=10)
                output = result.stdout
                for line in output.split('\n'):
                    if 'all' in line and '%' in line:
                        parts = line.split()
                        idle = float(parts[-1])
                        return 100.0 - idle
            else:
                result = subprocess.run(['top', '-bn1'], capture_output=True, text=True, timeout=10)
                output = result.stdout
                for line in output.split('\n'):
                    if '%Cpu(s):' in line:
                        # Parse CPU line - format: %Cpu(s): us,sy,ni,id,wa,hi,si,st
                        cpu_data = line.split('%Cpu(s):')[1].strip()
                        parts = []
                        for item in cpu_data.split(','):
                            val = item.split()[0].strip()
                            try:
                                parts.append(float(val))
                            except ValueError:
                                parts.append(0.0)
                        
                        if len(parts) >= 8:
                            us = parts[0]
                            sy = parts[1]
                            ni = parts[2]
                            id_ = parts[3]
                            wa = parts[4]
                            hi = parts[5]
                            si = parts[6]
                            st = parts[7]
                            usage = us + sy + ni + wa + hi + si + st
                            return usage
            return 0.0
    except Exception as e:
        logger.debug(f"Error getting CPU usage: {e}")
        return 0.0

def get_host_ram_usage():
    """Get host RAM usage - cross-platform compatible"""
    try:
        import platform
        system = platform.system()
        
        if system == "Windows":
            # Windows: Use psutil or wmic
            try:
                import psutil
                mem = psutil.virtual_memory()
                return mem.percent
            except ImportError:
                # Fallback for Windows without psutil
                try:
                    result = subprocess.run(['wmic', 'OS', 'get', 'TotalVisibleMemorySize,FreePhysicalMemory'], 
                                          capture_output=True, text=True, timeout=5)
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        values = lines[1].split()
                        if len(values) >= 2:
                            total = int(values[0])
                            free = int(values[1])
                            used = total - free
                            return (used / total * 100) if total > 0 else 0.0
                except:
                    pass
                return 0.0
        else:
            # Linux/Unix: Use free command
            result = subprocess.run(['free', '-m'], capture_output=True, text=True, timeout=10)
            lines = result.stdout.splitlines()
            if len(lines) > 1:
                mem = lines[1].split()
                total = int(mem[1])
                used = int(mem[2])
                return (used / total * 100) if total > 0 else 0.0
            return 0.0
    except Exception as e:
        logger.debug(f"Error getting RAM usage: {e}")
        return 0.0


async def get_host_stats(node_id: int) -> Dict:
    """Low-overhead host capacity snapshot with a short cache per node."""
    node_id = int(node_id)
    now_mono = time.monotonic()
    cached = HOST_STATS_CACHE.get(node_id)
    if cached and (now_mono - cached[0]) < HOST_STATS_CACHE_TTL:
        return dict(cached[1])

    node = get_node(node_id)
    empty = {"cpu":0.0,"ram":0.0,"disk":"Unknown","ram_bytes_total":0,"ram_bytes_used":0,
             "ram_bytes_available":0,"disk_total":0,"disk_free":0,"cpu_count":0}
    if not node:
        return empty
    stats = empty
    try:
        if node.get('is_local'):
            try:
                import psutil
                vm = psutil.virtual_memory()
                du = psutil.disk_usage('/')
                # interval=None is non-blocking and keeps this path cheap.
                cpu = float(psutil.cpu_percent(interval=None))
                stats = {"cpu":cpu,"ram":float(vm.percent),
                         "disk":{"used":int(du.used),"total":int(du.total),"free":int(du.free),"percent":float(du.percent)},
                         "ram_bytes_total":int(vm.total),"ram_bytes_used":int(vm.used),"ram_bytes_available":int(vm.available),
                         "disk_total":int(du.total),"disk_free":int(du.free),"cpu_count":int(psutil.cpu_count() or 0)}
            except Exception:
                stats = empty
        else:
            response = await asyncio.to_thread(
                requests.get,
                str(node.get('url') or '').rstrip('/') + '/api/get_host_stats',
                headers={"X-API-Key": str(node.get('api_key') or '')},
                timeout=8,
            )
            response.raise_for_status()
            payload = response.json()
            disk = payload.get('disk') or {}
            total = int(payload.get('ram_bytes_total',0) or 0)
            used = int(payload.get('ram_bytes_used',0) or 0)
            stats = {"cpu":float(payload.get('cpu',0.0) or 0.0),"ram":float(payload.get('ram',0.0) or 0.0),
                     "disk":disk,"ram_bytes_total":total,"ram_bytes_used":used,
                     "ram_bytes_available":max(0,total-used),
                     "disk_total":int(disk.get('total',0) or 0) if isinstance(disk,dict) else 0,
                     "disk_free":int(disk.get('free',0) or 0) if isinstance(disk,dict) else 0,
                     "cpu_count":int(payload.get('cpu_count',0) or 0)}
    except Exception as exc:
        logger.debug("Host stats unavailable on %s: %s: %s", node.get('name'), type(exc).__name__, exc)
        stats = empty

    HOST_STATS_CACHE[node_id] = (time.monotonic(), dict(stats))
    return stats

async def check_vps_expiration():
    """Suspend expired VPS and send warning DMs on the bot's own event loop."""
    now = datetime.now()
    warning_window = max(0, EXPIRATION_WARNING_DAYS) * 24 * 3600
    for user_id, vps_list in list(vps_data.items()):
        for vps in list(vps_list):
            raw = vps.get('expiration_date')
            if not raw:
                continue
            try:
                expiration_dt = datetime.fromisoformat(str(raw))
            except (TypeError, ValueError):
                logger.warning(f"Invalid expiration date for {vps.get('container_name')}: {raw!r}")
                continue

            container_name = vps.get('container_name')
            node_id = int(vps.get('node_id', 1))
            seconds_left = (expiration_dt - now).total_seconds()
            key = (str(container_name), str(raw))

            if seconds_left <= 0:
                if not vps.get('suspended', False):
                    try:
                        try:
                            await execute_lxc(container_name, f"stop {container_name} --force", timeout=120, node_id=node_id)
                        except Exception as stop_error:
                            text_error = str(stop_error).lower()
                            if 'not running' not in text_error and 'already stopped' not in text_error:
                                raise
                        vps['status'] = 'stopped'
                        vps['suspended'] = True
                        history = vps.setdefault('suspension_history', [])
                        history.append({
                            'time': datetime.now().isoformat(),
                            'reason': f'Auto-suspended due to VPS expiration on {expiration_dt.strftime("%Y-%m-%d")}',
                            'by': 'Expiration Monitor',
                        })
                        save_vps_data_immediate()
                    except Exception as e:
                        logger.error(f"Failed to auto-suspend VPS {container_name}: {e}")
                        continue

                if key not in EXPIRATION_EXPIRED_NOTICE_SENT:
                    try:
                        owner = await bot.fetch_user(int(user_id))
                        dm = create_error_embed(
                            "VPS Expired and Suspended",
                            f"Your VPS `{container_name}` has expired and has been suspended.\n\n"
                            f"Expiration: `{expiration_dt.strftime('%Y-%m-%d %H:%M:%S')}`\n"
                            f"Use `{PREFIX}renew` to request a {VPS_RENEWAL_DAYS}-day renewal.",
                        )
                        await owner.send(embed=dm)
                    except Exception as e:
                        logger.debug(f"Failed to notify expired VPS owner {user_id}: {e}")
                    finally:
                        EXPIRATION_EXPIRED_NOTICE_SENT.add(key)
                EXPIRATION_WARNING_SENT.discard(key)

            elif seconds_left <= warning_window and key not in EXPIRATION_WARNING_SENT:
                try:
                    owner = await bot.fetch_user(int(user_id))
                    hours = max(1, int(seconds_left // 3600))
                    dm = create_warning_embed(
                        "VPS Expiring Soon",
                        f"Your VPS `{container_name}` expires in approximately **{hours} hour(s)**.\n\n"
                        f"Expiration: `{expiration_dt.strftime('%Y-%m-%d %H:%M:%S')}`\n"
                        f"Use `{PREFIX}renew` during the final {RENEWAL_WINDOW_DAYS} days to add {VPS_RENEWAL_DAYS} days.",
                    )
                    await owner.send(embed=dm)
                    EXPIRATION_WARNING_SENT.add(key)
                except Exception as e:
                    logger.debug(f"Failed to send expiration warning to {user_id}: {e}")

def resource_monitor():
    """Low-frequency host resource logger; expiration checks run on bot's event loop."""
    global resource_monitor_active
    while resource_monitor_active:
        try:
            for node in get_nodes():
                if not node.get('is_local'):
                    continue
                try:
                    stats = asyncio.run(get_host_stats(node['id']))
                    cpu = float(stats.get('cpu', 0.0) or 0.0)
                    ram = float(stats.get('ram', 0.0) or 0.0)
                    logger.info(f"Node {node['name']}: CPU {cpu:.1f}%, RAM {ram:.1f}%")
                    if cpu > CPU_THRESHOLD or ram > RAM_THRESHOLD:
                        logger.warning(
                            f"Node {node['name']} exceeded thresholds "
                            f"(CPU: {CPU_THRESHOLD}%, RAM: {RAM_THRESHOLD}%). Manual intervention required."
                        )
                except Exception as e:
                    logger.debug(f"Resource check failed for node {node.get('name')}: {e}")
            time.sleep(180)
        except Exception as e:
            logger.error(f"Error in resource monitor: {e}")
            time.sleep(180)

# Start resource monitoring thread
monitor_thread = threading.Thread(target=resource_monitor, daemon=True)
monitor_thread.start()

# Container stats with multi-node
async def get_container_stats(container_name: str, node_id: Optional[int] = None) -> Dict:
    if node_id is None:
        node_id = find_node_id_for_container(container_name)
    node = get_node(node_id)
    if not node:
        return {"status": "unknown", "cpu": 0.0, "ram": {"used": 0, "total": 0, "pct": 0.0}, "disk": "Unknown", "uptime": "Unknown"}
    if node['is_local']:
        status = await get_container_status_local(container_name)
        cpu = await get_container_cpu_pct_local(container_name)
        ram = await get_container_ram_local(container_name)
        disk = await get_container_disk_local(container_name)
        uptime = await get_container_uptime_local(container_name)
        return {"status": status, "cpu": cpu, "ram": ram, "disk": disk, "uptime": uptime}
    else:
        # Remote node - handle unreachable nodes gracefully without spamming logs
        url = str(node.get('url') or '').rstrip('/') + '/api/get_container_stats'
        data = {"container": container_name}
        headers = {"X-API-Key": str(node.get('api_key') or '')}
        try:
            response = await asyncio.to_thread(requests.post, url, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            # Remote node unreachable - return graceful defaults
            logger.debug(f"Remote node {node['name']} unreachable for container {container_name}")
            return {"status": "unknown", "cpu": 0.0, "ram": {"used": 0, "total": 0, "pct": 0.0}, "disk": "Unknown", "uptime": "Unknown"}
        except Exception as e:
            logger.debug(f"Failed to get container stats from remote node {node['name']}: {e}")
            return {"status": "unknown", "cpu": 0.0, "ram": {"used": 0, "total": 0, "pct": 0.0}, "disk": "Unknown", "uptime": "Unknown"}

async def _run_local_lxc(*args: str, timeout: int = 20) -> tuple[str, str, int]:
    """Run one local LXC command with a hard timeout and decoded output."""
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise
    return (
        stdout.decode(errors='replace') if stdout else '',
        stderr.decode(errors='replace') if stderr else '',
        int(proc.returncode or 0),
    )


async def get_container_status_local(container_name: str):
    try:
        stdout, _, _ = await _run_local_lxc('lxc', 'info', container_name, timeout=12)
        for line in stdout.splitlines():
            if line.startswith('Status: '):
                return line.split(': ', 1)[1].strip().lower()
        return 'unknown'
    except Exception:
        return 'unknown'


async def get_container_cpu_pct_local(container_name: str):
    """Read guest CPU usage from /proc/stat using a short delta; no fragile top parsing."""
    script = r'''set +e
read -r total_a idle_a < <(awk '/^cpu / {total=$2+$3+$4+$5+$6+$7+$8+$9+$10; idle=$5+$6; print total, idle; exit}' /proc/stat)
sleep 0.20
read -r total_b idle_b < <(awk '/^cpu / {total=$2+$3+$4+$5+$6+$7+$8+$9+$10; idle=$5+$6; print total, idle; exit}' /proc/stat)
if [[ "$total_a" =~ ^[0-9]+$ && "$total_b" =~ ^[0-9]+$ && "$idle_a" =~ ^[0-9]+$ && "$idle_b" =~ ^[0-9]+$ ]]; then
  dt=$((total_b-total_a)); di=$((idle_b-idle_a))
  if (( dt > 0 )); then awk -v dt="$dt" -v di="$di" 'BEGIN{printf "%.2f", ((dt-di)*100/dt)}'; exit 0; fi
fi
printf '0.00\n'
'''
    try:
        stdout, _, _ = await _run_local_lxc('lxc', 'exec', container_name, '--', 'bash', '-lc', script, timeout=15)
        value = float(str(stdout).strip().splitlines()[-1])
        return max(0.0, min(100.0, value))
    except Exception as e:
        logger.debug(f'CPU stats failed for {container_name}: {e}')
        return 0.0

async def get_container_ram_local(container_name: str):
    try:
        stdout, _, _ = await _run_local_lxc('lxc', 'exec', container_name, '--', 'free', '-m', timeout=15)
        for line in stdout.splitlines():
            parts = line.split()
            if parts and parts[0].lower() == 'mem:' and len(parts) >= 3:
                total = int(parts[1])
                used = int(parts[2])
                pct = (used / total * 100) if total > 0 else 0.0
                return {'used': used, 'total': total, 'pct': pct}
        return {'used': 0, 'total': 0, 'pct': 0.0}
    except asyncio.TimeoutError:
        logger.debug(f'RAM stats timed out for {container_name}')
        return {'used': 0, 'total': 0, 'pct': 0.0}
    except Exception as e:
        logger.debug(f'RAM stats failed for {container_name}: {e}')
        return {'used': 0, 'total': 0, 'pct': 0.0}


async def get_container_disk_local(container_name: str):
    """Return guest disk usage using the configured VPS plan as the advertised quota."""
    try:
        stdout, _, _ = await _run_local_lxc('lxc', 'exec', container_name, '--', 'df', '-Pk', '/', timeout=15)
        used_kb = 0
        percent = '0%'
        for line in stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 5 and parts[4].endswith('%'):
                try:
                    used_kb = int(parts[2])
                except ValueError:
                    used_kb = 0
                percent = parts[4]
                break

        plan_gb = DEFAULT_VPS_STORAGE_GB
        _, _, vps = find_vps_record(container_name)
        if vps:
            try:
                plan_gb = int(str(vps.get('storage', plan_gb)).lower().replace('gb', '').strip())
            except (TypeError, ValueError):
                pass
        plan_gb = max(1, int(plan_gb))
        plan_kb = plan_gb * 1024 * 1024
        used_gb = used_kb / 1024 / 1024
        return f'{used_gb:.1f} GB used ({percent})'
    except Exception as e:
        logger.debug(f'Disk stats failed for {container_name}: {e}')
        return 'Unknown'

async def get_container_uptime_local(container_name: str):
    try:
        stdout, _, _ = await _run_local_lxc('lxc', 'exec', container_name, '--', 'uptime', timeout=12)
        return stdout.strip() or 'Unknown'
    except Exception:
        return 'Unknown'

async def get_container_status(container_name: str, node_id: Optional[int] = None):
    stats = await get_container_stats(container_name, node_id)
    return stats['status']

async def get_container_cpu(container_name: str, node_id: Optional[int] = None):
    stats = await get_container_stats(container_name, node_id)
    return f"{stats['cpu']:.1f}%"

async def get_container_cpu_pct(container_name: str, node_id: Optional[int] = None):
    stats = await get_container_stats(container_name, node_id)
    return stats['cpu']

async def get_container_memory(container_name: str, node_id: Optional[int] = None):
    stats = await get_container_stats(container_name, node_id)
    ram = stats['ram']
    return f"{ram['used']}/{ram['total']} MB ({ram['pct']:.1f}%)"

async def get_container_ram_pct(container_name: str, node_id: Optional[int] = None):
    stats = await get_container_stats(container_name, node_id)
    return stats['ram']['pct']

async def get_container_addresses(container_name: str, node_id: Optional[int] = None) -> Dict[str, List[str]]:
    """Return actual guest IPv4 and globally-scoped IPv6 addresses."""
    if node_id is None:
        node_id = find_node_id_for_container(container_name)
    result: Dict[str, List[str]] = {"ipv4": [], "ipv6": []}
    try:
        v4 = await execute_lxc(container_name, f"exec {container_name} -- ip -4 -o addr show scope global", timeout=20, node_id=node_id)
        for line in str(v4 or '').splitlines():
            parts = line.split()
            if len(parts) >= 4 and parts[2] == 'inet':
                addr = parts[3].split('/',1)[0]
                if addr and addr not in result['ipv4'] and not addr.startswith('127.'):
                    result['ipv4'].append(addr)
    except Exception as e:
        logger.debug(f'IPv4 discovery failed for {container_name}: {e}')
    try:
        v6 = await execute_lxc(container_name, f"exec {container_name} -- ip -6 -o addr show scope global", timeout=20, node_id=node_id)
        for line in str(v6 or '').splitlines():
            parts = line.split()
            if len(parts) >= 4 and parts[2] == 'inet6':
                addr = parts[3].split('/',1)[0]
                if addr and addr not in result['ipv6'] and addr != '::1' and not addr.lower().startswith('fe80:'):
                    result['ipv6'].append(addr)
    except Exception as e:
        logger.debug(f'IPv6 discovery failed for {container_name}: {e}')
    return result

async def get_container_networks(container_name: str, node_id: Optional[int] = None) -> Dict[str, str]:
    """Backward-compatible IPv4 interface map."""
    if node_id is None:
        node_id = find_node_id_for_container(container_name)
    try:
        output = await execute_lxc(container_name, f"exec {container_name} -- ip -4 -o addr show scope global", timeout=20, node_id=node_id)
        networks: Dict[str, str] = {}
        for line in str(output or '').splitlines():
            parts = line.split()
            if len(parts) >= 4 and parts[2] == 'inet':
                interface = parts[1].rstrip(':')
                addr = parts[3].split('/',1)[0]
                if interface != 'lo' and addr and not addr.startswith('127.'):
                    networks[interface] = addr
        return networks
    except Exception as e:
        logger.debug(f'Failed to get IPv4 networks for {container_name}: {e}')
        return {}

async def detect_public_endpoints(node_id: int) -> Dict[str, str]:
    """Return externally useful host endpoints for SSH/forwarding.

    Configured values win. Otherwise the local node uses optional public-IP
    autodetection, while remote nodes ask the node agent. No private/loopback
    address is advertised as a public endpoint.
    """
    def valid_v4(value: str) -> bool:
        try:
            import ipaddress
            ip = ipaddress.ip_address(value.strip())
            return ip.version == 4 and not ip.is_loopback and not ip.is_private and not ip.is_link_local
        except Exception:
            return False
    def valid_v6(value: str) -> bool:
        try:
            import ipaddress
            ip = ipaddress.ip_address(value.strip())
            return ip.version == 6 and ip.is_global
        except Exception:
            return False

    node = get_node(node_id) or {}
    if node.get('is_local'):
        v4 = PUBLIC_IPV4 if valid_v4(PUBLIC_IPV4) else ''
        v6 = PUBLIC_IPV6 if valid_v6(PUBLIC_IPV6) else ''
        if AUTO_DETECT_PUBLIC_IP and not v4:
            try:
                r = await asyncio.to_thread(requests.get, 'https://api4.ipify.org', timeout=3)
                candidate = r.text.strip()
                if valid_v4(candidate):
                    v4 = candidate
            except Exception:
                pass
        if AUTO_DETECT_PUBLIC_IP and not v6:
            try:
                route = await asyncio.to_thread(
                    subprocess.run,
                    ['ip', '-6', 'route', 'get', '2606:4700:4700::1111'],
                    capture_output=True, text=True, timeout=4, check=False,
                )
                parts = (route.stdout or '').split()
                if 'src' in parts:
                    candidate = parts[parts.index('src') + 1]
                    if valid_v6(candidate):
                        v6 = candidate
            except Exception:
                pass
        if AUTO_DETECT_PUBLIC_IP and not v6:
            try:
                r = await asyncio.to_thread(
                    requests.get,
                    'https://api6.ipify.org',
                    timeout=3,
                    headers={'User-Agent': 'RGNODES-VPS-Manager/8'},
                )
                candidate = r.text.strip()
                if valid_v6(candidate):
                    v6 = candidate
            except Exception:
                pass
        if not v4 and YOUR_SERVER_IP:
            try:
                import ipaddress
                candidate = ipaddress.ip_address(YOUR_SERVER_IP)
                if candidate.version == 4 and candidate.is_global:
                    v4 = YOUR_SERVER_IP
            except Exception:
                pass
        return {'ipv4': v4, 'ipv6': v6}

    url = str(node.get('url') or '').rstrip('/') + '/api/get_access_info' 
    headers = {'X-API-Key': str(node.get('api_key') or '')}
    try:
        response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        return {'ipv4': str(data.get('public_ipv4') or ''), 'ipv6': str(data.get('public_ipv6') or '')}
    except Exception as e:
        logger.debug(f'Public endpoint discovery failed on {node.get("name")}: {e}')
        return {'ipv4': '', 'ipv6': ''}

def format_public_ssh_access(endpoints: Dict[str, str], ssh_port: Optional[int]) -> Dict[str, str]:
    result = {"ipv4": str(endpoints.get("ipv4") or ""), "ipv6": str(endpoints.get("ipv6") or ""), "ssh_ipv4": "", "ssh_ipv6": ""}
    try:
        port = int(ssh_port or 0)
    except (TypeError, ValueError):
        port = 0
    if port and result["ipv4"]:
        result["ssh_ipv4"] = "ssh root@{} -p {}".format(result["ipv4"], port)
    if port and result["ipv6"]:
        result["ssh_ipv6"] = "ssh -6 root@[{}] -p {}".format(result["ipv6"], port)
    return result


async def get_container_network_counters(container_name: str, node_id: Optional[int] = None) -> tuple[int, int]:
    """Return aggregate RX/TX byte counters for non-loopback guest interfaces."""
    if node_id is None:
        node_id = find_node_id_for_container(container_name)
    script = r'''set +e
rx=0; tx=0
while IFS= read -r line; do
  iface=${line%%:*}
  rest=${line#*:}
  iface=$(echo "$iface" | xargs)
  [ -n "$iface" ] || continue
  [ "$iface" = "lo" ] && continue
  read -r -a f <<< "$rest"
  [ "${#f[@]}" -ge 9 ] || continue
  [[ "${f[0]}" =~ ^[0-9]+$ ]] || continue
  [[ "${f[8]}" =~ ^[0-9]+$ ]] || continue
  rx=$((rx + f[0])); tx=$((tx + f[8]))
done < /proc/net/dev
printf '%s %s\n' "$rx" "$tx"
'''
    output = await _exec_guest_bash(container_name, node_id, script, timeout=20)
    parts = str(output or '').strip().split()
    if len(parts) < 2:
        raise RuntimeError("Guest network counters unavailable")
    return max(0, int(parts[0])), max(0, int(parts[1]))


def _human_bytes(n: int) -> str:
    n = float(max(0, int(n))); units = ['B','KB','MB','GB','TB','PB']; i = 0
    while n >= 1024 and i < len(units)-1:
        n /= 1024; i += 1
    return f'{n:.1f} {units[i]}' if i else f'{int(n)} B'


async def get_container_network_usage(container_name: str, node_id: Optional[int] = None) -> tuple[str, str]:
    """Return aggregate RX/TX byte counters as readable strings."""
    try:
        rx, tx = await get_container_network_counters(container_name, node_id)
        return _human_bytes(rx), _human_bytes(tx)
    except Exception:
        return 'N/A', 'N/A'


async def get_container_docker_status(container_name: str, node_id: Optional[int] = None) -> str:
    """Report the actual Docker state instead of claiming Docker is ready from LXC nesting alone."""
    try:
        out = await _exec_guest_bash(
            container_name,
            node_id,
            """set +e
if ! command -v docker >/dev/null 2>&1; then
  printf 'UNINSTALLED\n'
  exit 0
fi
if docker info >/dev/null 2>&1; then
  printf 'READY\n'
elif systemctl is-active --quiet docker 2>/dev/null; then
  printf 'DAEMON_WAIT\n'
else
  printf 'STOPPED\n'
fi
""",
            timeout=25,
        )
        state = str(out or '').strip().splitlines()[-1:]
        state = state[0] if state else 'UNKNOWN'
        return {
            'READY': '🐳 Ready',
            'DAEMON_WAIT': '🐳 Starting',
            'STOPPED': '🐳 Stopped',
            'UNINSTALLED': '⚪ Not Installed',
        }.get(state, '⚪ Unknown')
    except Exception:
        return '⚪ Unavailable'


async def ensure_docker_ready(container_name: str, node_id: int, strict: bool = False) -> bool:
    """Install Docker with distro packages first, then Docker's official repository fallback, and verify daemon readiness."""
    script = r'''set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

verify() {
  command -v docker >/dev/null 2>&1 || return 1
  docker info >/dev/null 2>&1 || return 1
  docker version --format '{{.Server.Version}}' >/dev/null 2>&1 || return 1
  return 0
}

if verify; then
  printf 'READY\n'; exit 0
fi

apt update -qq
apt install -y ca-certificates curl gnupg >/dev/null

# First try the distribution package because it is simplest inside LXC.
if apt-cache show docker.io >/dev/null 2>&1; then
  apt install -y docker.io >/dev/null 2>&1 || true
fi

# Official Docker repository fallback for Debian/Ubuntu where docker.io is unavailable/broken.
if ! command -v docker >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  . /etc/os-release
  case "$ID" in
    ubuntu|debian)
      curl -fsSL "https://download.docker.com/linux/$ID/gpg" | gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg
      chmod a+r /etc/apt/keyrings/docker.gpg
      arch="$(dpkg --print-architecture)"
      if [ "$ID" = "ubuntu" ]; then
        codename="${VERSION_CODENAME:-$(. /etc/os-release; printf '%s' "${UBUNTU_CODENAME:-}")}"
      else
        codename="${VERSION_CODENAME:-$(. /etc/os-release; printf '%s' "${VERSION_CODENAME:-}")}"
      fi
      [ -n "$codename" ] || codename="stable"
      printf 'deb [arch=%s signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/%s %s stable\n' "$arch" "$ID" "$codename" > /etc/apt/sources.list.d/docker.list
      apt update -qq
      apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin >/dev/null 2>&1 || true
      ;;
  esac
fi

# Fallback to any docker package discovered after repo setup.
if ! command -v docker >/dev/null 2>&1 && apt-cache show docker.io >/dev/null 2>&1; then
  apt install -y docker.io >/dev/null 2>&1 || true
fi

if ! command -v docker >/dev/null 2>&1; then
  printf 'UNINSTALLED\n'
  exit 21
fi

# LXC commonly runs without a usable systemd PID 1. Prefer the distro service when available.
if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files docker.service >/dev/null 2>&1; then
  systemctl enable docker >/dev/null 2>&1 || true
  systemctl start docker >/dev/null 2>&1 || true
fi
if command -v service >/dev/null 2>&1; then
  service docker start >/dev/null 2>&1 || true
fi

# If dockerd is installed but not running, launch a guest daemon only when safe and no daemon exists.
if ! docker info >/dev/null 2>&1 && command -v dockerd >/dev/null 2>&1; then
  if ! pgrep -x dockerd >/dev/null 2>&1; then
    nohup dockerd >/var/log/rgnodes-dockerd.log 2>&1 &
    sleep 2
  fi
fi

for _ in $(seq 1 25); do
  if verify; then printf 'READY\n'; exit 0; fi
  sleep 1
done
printf 'NOT_READY\n'
exit 22
'''
    try:
        output = await _exec_guest_bash(container_name, node_id, script, timeout=210)
        ready = str(output or '').strip().splitlines()[-1:] == ['READY']
        if strict and not ready:
            raise RuntimeError(f'Docker could not be verified inside {container_name}.')
        return ready
    except Exception:
        if strict:
            raise
        return False

async def get_container_disk(container_name: str, node_id: Optional[int] = None):
    stats = await get_container_stats(container_name, node_id)
    return stats['disk']

async def get_container_uptime(container_name: str, node_id: Optional[int] = None):
    stats = await get_container_stats(container_name, node_id)
    return stats['uptime']

def get_uptime():
    """Get system uptime - cross-platform compatible"""
    try:
        import platform
        system = platform.system()
        
        if system == "Windows":
            try:
                result = subprocess.run(['net', 'statistics', 'server'], 
                                      capture_output=True, text=True, timeout=5)
                output = result.stdout
                for line in output.split('\n'):
                    if 'Statistics since' in line:
                        return line.strip()
                return "Unknown"
            except:
                # Fallback: use wmic
                try:
                    result = subprocess.run(['wmic', 'os', 'get', 'lastbootuptime'], 
                                          capture_output=True, text=True, timeout=5)
                    return result.stdout.strip() if result.stdout else "Unknown"
                except:
                    return "Unknown"
        else:
            # Linux/Unix: Use uptime command
            result = subprocess.run(['uptime'], capture_output=True, text=True, timeout=5)
            return result.stdout.strip()
    except Exception as e:
        logger.debug(f"Error getting uptime: {e}")
        return "Unknown"

# Try to detect default storage pool or use common defaults
def get_default_storage_pool():
    try:
        result = subprocess.run(['lxc', 'storage', 'list', '--format', 'csv'],
                              capture_output=True, text=True, timeout=10)
        lines = result.stdout.strip().split('\n')
        if lines and lines[0]:
            # Get first storage pool
            return lines[0].split(',')[0]
    except:
        pass
    return "default"  # Fallback to 'default'

DEFAULT_STORAGE_POOL = os.getenv('DEFAULT_STORAGE_POOL') or get_default_storage_pool()

async def resolve_storage_pool(node_id: int) -> str:
    """Return a usable storage pool on the target LXD node.

    Multi-node installations often use different pool names. Prefer the configured
    pool, then fall back to the first available pool on that node.
    """
    configured = str(DEFAULT_STORAGE_POOL or '').strip()
    if configured:
        try:
            await execute_lxc('', f"storage show {shlex.quote(configured)}", node_id=node_id, timeout=30)
            return configured
        except Exception:
            logger.warning(f"Configured storage pool {configured!r} is unavailable on node {node_id}; discovering a fallback.")

    output = await execute_lxc('', 'storage list --format csv', node_id=node_id, timeout=30)
    names = []
    for line in str(output or '').splitlines():
        line = line.strip()
        if not line:
            continue
        name = line.split(',', 1)[0].strip().strip('\"')
        if name and name not in names:
            names.append(name)
    if not names:
        raise RuntimeError(f"No usable LXD storage pool is available on node {node_id}.")
    return names[0]

# ─────────────────────────────────────────────────────────────────────────────
# RGNODES core policy / deployment helpers
# ─────────────────────────────────────────────────────────────────────────────
def is_admin_user(user_or_member: int | str | object) -> bool:
    obj = user_or_member
    uid = str(getattr(obj, "id", obj))
    if uid == str(MAIN_ADMIN_ID) or uid in {str(x) for x in admin_data.get("admins", [])}:
        return True
    perms = getattr(obj, "guild_permissions", None)
    return bool(perms is not None and getattr(perms, "administrator", False))


def maintenance_enabled() -> bool:
    return str(get_setting("maintenance", "off")).strip().lower() == "on"


def maintenance_applies_to_user(user_id: int | str) -> bool:
    """Maintenance is user-facing; administrators remain fully operational."""
    return maintenance_enabled() and not is_admin_user(user_id)


def user_has_vps(user_id: int | str) -> bool:
    return bool(vps_data.get(str(user_id), []))


def find_vps_record(reference: str | int):
    """Resolve a VPS by container name or numeric persistent VPS ID."""
    wanted = str(reference).strip()
    numeric_id = int(wanted) if wanted.isdigit() else None
    for uid, items in vps_data.items():
        for idx, vps in enumerate(items):
            same_name = str(vps.get("container_name")) == wanted
            same_id = numeric_id is not None and (
                int(vps.get("id", -1) or -1) == numeric_id
                or int(vps.get("vmid", -1) or -1) == numeric_id
            )
            if same_name or same_id:
                return str(uid), idx, vps
    return None, None, None

def suspended_due_to_expiration(vps: Dict[str, Any]) -> bool:
    """Return True only when the latest suspension was caused by expiration."""
    if not vps.get("suspended"):
        return False
    history = vps.get("suspension_history") or []
    if not isinstance(history, list) or not history:
        return False
    latest = history[-1]
    if not isinstance(latest, dict):
        return False
    by = str(latest.get("by") or "").lower()
    reason = str(latest.get("reason") or "").lower()
    return "expiration" in by or "expired" in reason or "expiration" in reason



async def ensure_lxd_remote(remote: str, node_id: int) -> None:
    """Ensure a standard public image remote exists on the target node."""
    remote = str(remote).strip().rstrip(':')
    if not remote:
        return
    try:
        await execute_lxc('', f"remote get-url {shlex.quote(remote)}", node_id=node_id, timeout=20)
        return
    except Exception:
        pass
    urls = {
        'images': ('https://images.linuxcontainers.org', '--protocol=simplestreams'),
        'ubuntu': ('https://cloud-images.ubuntu.com/releases', '--protocol=simplestreams'),
    }
    spec = urls.get(remote)
    if not spec:
        return
    url, proto = spec
    try:
        await execute_lxc('', f"remote add {shlex.quote(remote)} {shlex.quote(url)} {proto} --public", node_id=node_id, timeout=60)
    except Exception as exc:
        logger.debug(f"LXD remote {remote} setup skipped on node {node_id}: {exc}")

async def _image_matches(node_id: int, remote: str, terms: list[str]) -> list[str]:
    """Discover current aliases dynamically instead of trusting stale aliases."""
    for term in terms:
        try:
            out = await execute_lxc('', f"image list {shlex.quote(remote + ':')} {shlex.quote(term)} --format json", node_id=node_id, timeout=90)
            data = json.loads(str(out or '[]'))
            aliases=[]
            for item in data if isinstance(data,list) else []:
                for alias in item.get('aliases') or []:
                    name = alias.get('name') if isinstance(alias,dict) else str(alias)
                    if name and name not in aliases:
                        aliases.append(name)
            if aliases:
                return aliases
        except Exception as exc:
            logger.debug(f"LXD image discovery {remote}:{term} failed: {exc}")
    return []

async def resolve_lxd_image(os_value: str, node_id: int) -> str:
    """Resolve an OS to a real current LXD image alias on the selected node."""
    requested=str(os_value or '').strip()
    wanted=requested.lower()
    family='debian' if 'debian' in wanted else 'ubuntu' if 'ubuntu' in wanted else None
    release_map={'20.04':('20.04','focal'),'22.04':('22.04','jammy'),'24.04':('24.04','noble'),'11':('11','bullseye'),'12':('12','bookworm'),'13':('13','trixie')}
    release=next((k for k in release_map if k in wanted),None)
    if family=='ubuntu':
        remotes=[('ubuntu',release_map.get(release,('',''))),('images',release_map.get(release,('','')))]
    elif family=='debian':
        remotes=[('images',release_map.get(release,('',''))),('debian',release_map.get(release,('','')))]
    else:
        remotes=[(requested.split(':',1)[0] if ':' in requested else '',('',''))]
    errors=[]
    for remote, rel in remotes:
        if not remote:
            continue
        await ensure_lxd_remote(remote,node_id)
        candidates=list(LXD_IMAGE_CANDIDATES.get(requested,[]))
        if rel:
            candidates += [f"{remote}:{rel[0]}",f"{remote}:{rel[1]}",f"{remote}:{rel[0]}/default",f"{remote}:{rel[1]}/default",f"{remote}:{rel[0]}/cloud",f"{remote}:{rel[1]}/cloud"]
        seen=set()
        for candidate in candidates:
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            try:
                await execute_lxc('',f"image info {shlex.quote(candidate)}",node_id=node_id,timeout=60)
                return candidate
            except Exception as exc:
                errors.append(f"{candidate}: {str(exc)[:140]}")
        terms=[]
        if rel:
            terms=[f"{family}/{rel[0]}",rel[0],rel[1]]
        for alias in await _image_matches(node_id,remote,terms):
            a=alias.lower()
            if family not in a or not rel or (rel[0] not in a and rel[1] not in a):
                continue
            candidate=f"{remote}:{alias}" if ':' not in alias else alias
            try:
                await execute_lxc('',f"image info {shlex.quote(candidate)}",node_id=node_id,timeout=60)
                return candidate
            except Exception as exc:
                errors.append(f"{candidate}: {str(exc)[:140]}")
    raise RuntimeError(f"No usable {friendly_os_label(requested)} image was found on node {node_id}. Checked dynamic aliases and standard remotes. Details: {'; '.join(errors[-6:])}")


def friendly_os_label(os_value: str) -> str:
    """Convert LXD image aliases into a compact human-readable OS label."""
    raw = str(os_value or "Unknown").strip()
    aliases = {
        "ubuntu:20.04": "Ubuntu 20.04 LTS",
        "ubuntu:22.04": "Ubuntu 22.04 LTS",
        "ubuntu:24.04": "Ubuntu 24.04 LTS",
        "images:ubuntu/20.04": "Ubuntu 20.04 LTS",
        "images:ubuntu/22.04": "Ubuntu 22.04 LTS",
        "images:ubuntu/24.04": "Ubuntu 24.04 LTS",
        "images:debian/11": "Debian 11",
        "images:debian/12": "Debian 12",
        "images:debian/13": "Debian 13",
        "debian:11": "Debian 11",
        "debian:12": "Debian 12",
        "debian:13": "Debian 13",
    }
    return aliases.get(raw, raw)

def location_flag(location: str) -> str:
    flags = {"India": "🇮🇳", "SG": "🇸🇬", "Singapore": "🇸🇬", "Bangladesh": "🇧🇩", "US": "🇺🇸", "USA": "🇺🇸"}
    return flags.get(str(location or "").strip(), "🌐")


async def check_node_capacity_for_vps(node_id: int, ram_gb: int, cpu_cores: int, disk_gb: int) -> tuple[bool, str]:
    """Conservative admission control: protect the main host from RAM/CPU/disk exhaustion."""
    node=get_node(node_id)
    if not node: return False,f"Node {node_id} not found."
    try: stats=await asyncio.wait_for(get_host_stats(node_id),timeout=15)
    except Exception as exc: return False,f"Node health check failed: {exc}"
    cpu=float(stats.get('cpu') or 0.0); ram_pct=float(stats.get('ram') or 0.0)
    total=int(stats.get('ram_bytes_total') or 0); available=int(stats.get('ram_bytes_available') or max(0,total-int(stats.get('ram_bytes_used') or 0)))
    disk_free=int(stats.get('disk_free') or 0)
    if total:
        requested=int(float(ram_gb)*(1024**3)); reserve=int(HOST_RAM_RESERVE_GB*(1024**3)); max_guest=int(total*MAX_DEPLOY_RAM_SHARE)
        allocated_ram=sum(_parse_gb(v.get("ram", "0GB"), 0) for items in vps_data.values() for v in items if int(v.get("node_id", 1))==int(node_id) and not bool(v.get("suspended", False)))
        allocated_bytes=allocated_ram*(1024**3)
        if requested>max_guest or allocated_bytes+requested+reserve>max_guest:
            return False,f"Host RAM allocation guard blocked deployment: allocated {allocated_ram} GiB + requested {ram_gb} GiB exceeds the safe host budget. {HOST_PROVIDER_NAME} is protected."
        if available < requested+reserve:
            return False,f"Host safety guard blocked deployment: available RAM {available/(1024**3):.1f} GiB; requested {ram_gb} GiB + reserve {HOST_RAM_RESERVE_GB:.1f} GiB."
        if ram_pct > 100.0-MIN_HOST_RAM_FREE_PCT_DEPLOY:
            return False,f"Host RAM is {ram_pct:.1f}% used. Deployment is paused until at least {MIN_HOST_RAM_FREE_PCT_DEPLOY:.0f}% RAM is free."
    cpu_total=int(stats.get('cpu_count') or 0)
    if cpu_total:
        allocated_cpu=sum(_parse_cpu(v.get("cpu", 0), 0) for items in vps_data.values() for v in items if int(v.get("node_id", 1))==int(node_id) and not bool(v.get("suspended", False)))
        if allocated_cpu+int(cpu_cores) > max(1,cpu_total-1):
            return False,f"Host CPU allocation guard blocked deployment: allocated {allocated_cpu} cores + requested {cpu_cores} cores would consume the protected CPU reserve."
    if cpu>=HOST_CPU_MAX_DEPLOY_PCT:
        return False,f"Host CPU is {cpu:.1f}% used. Deployment is paused below {HOST_CPU_MAX_DEPLOY_PCT:.0f}% to protect {HOST_PROVIDER_NAME}."
    if disk_free:
        disk_reserve_bytes=int(HOST_DISK_RESERVE_GB*(1024**3))
        requested_disk_bytes=int(float(disk_gb)*(1024**3))
        allocated_disk=sum(_parse_gb(v.get('storage','0GB'),0) for items in vps_data.values() for v in items if int(v.get('node_id',1))==int(node_id) and not bool(v.get('suspended',False)))
        disk_total=int(stats.get('disk_total') or 0)
        if disk_total and (allocated_disk + float(disk_gb))*(1024**3) + disk_reserve_bytes > disk_total:
            return False,f"Host disk allocation guard blocked deployment: allocated {allocated_disk} GiB + requested {disk_gb} GiB exceeds the protected host budget."
        if disk_free < requested_disk_bytes + disk_reserve_bytes:
            return False,f"Host disk safety guard blocked deployment: only {disk_free/(1024**3):.1f} GiB free; request {disk_gb} GiB + reserve {HOST_DISK_RESERVE_GB:.1f} GiB."
    return True,f"Host healthy • CPU {cpu:.1f}% • RAM {ram_pct:.1f}% • disk reserve active • {HOST_PROVIDER_NAME}."

async def check_node_capacity_for_start(node_id: int, container_name: str, ram_gb: int, cpu_cores: int) -> tuple[bool, str]:
    """Preflight a START operation without double-counting the stopped target VPS."""
    node=get_node(node_id)
    if not node:
        return False, f"Node {node_id} not found."
    try:
        stats=await asyncio.wait_for(get_host_stats(node_id), timeout=12)
    except Exception as exc:
        return False, f"Host health check failed: {exc}"
    cpu=float(stats.get('cpu') or 0.0)
    total=int(stats.get('ram_bytes_total') or 0)
    available=int(stats.get('ram_bytes_available') or max(0,total-int(stats.get('ram_bytes_used') or 0)))
    if total:
        requested=int(float(ram_gb)*(1024**3))
        reserve=int(HOST_RAM_RESERVE_GB*(1024**3))
        if available < requested + reserve:
            return False, f"Start blocked to protect {HOST_PROVIDER_NAME}: only {available/(1024**3):.1f} GiB RAM is available; VPS needs {ram_gb} GiB plus {HOST_RAM_RESERVE_GB:.1f} GiB reserve."
        if float(stats.get('ram') or 0.0) > 100.0-MIN_HOST_RAM_FREE_PCT_DEPLOY:
            return False, f"Start blocked: host RAM is {float(stats.get('ram') or 0.0):.1f}% used."
    if cpu >= HOST_CPU_MAX_DEPLOY_PCT:
        return False, f"Start blocked: host CPU is {cpu:.1f}% used. {HOST_PROVIDER_NAME} safety threshold is {HOST_CPU_MAX_DEPLOY_PCT:.0f}%."
    cpu_total=int(stats.get('cpu_count') or 0)
    if cpu_total:
        allocated=0
        for items in vps_data.values():
            for v in items:
                if int(v.get('node_id',1)) != int(node_id) or bool(v.get('suspended',False)):
                    continue
                if str(v.get('container_name')) == str(container_name):
                    continue
                if str(v.get('status','')).lower() == 'running':
                    allocated += _parse_cpu(v.get('cpu',0),0)
        if allocated + int(cpu_cores) > max(1,cpu_total-1):
            return False, f"Start blocked by CPU allocation guard: {allocated} running cores + {cpu_cores} requested would exceed the protected host CPU reserve."
    return True, f"Host start preflight passed • CPU {cpu:.1f}% • RAM available {available/(1024**3):.1f} GiB."


async def send_progress(interaction: discord.Interaction, title: str, step: int, total: int, detail: str):
    filled = min(total, max(0, step))
    bar = "▰" * filled + "▱" * (total - filled)
    if title.lower().startswith(("vps creating", "vps createing")):
        dots = {1: ".", 2: "..", 3: "...", 4: ".", 5: ".."}.get(step, "...")
        title = f"VPS Createing{dots}"
    embed = create_info_embed(f"{resolve_custom_emoji('loading', '⏳')} {title}", f"`[{bar}]` **{step}/{total}**\n{detail}")
    try:
        await interaction.edit_original_response(embed=embed)
    except Exception:
        pass


async def _background_start_sshx(container_name: str, node_id: int):
    try:
        url = await asyncio.wait_for(start_sshx_session(container_name, node_id), timeout=max(90, SSHX_ACTION_TIMEOUT))
        if url:
            logger.info("✅ SSHX background bootstrap connected for %s: %s", container_name, url)
        else:
            logger.warning("SSHX background bootstrap did not produce a URL for %s; repair loop will retry.", container_name)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.warning("SSHX background bootstrap failed for %s: %s", container_name, exc)


async def _background_start_pinggy(container_name: str, node_id: int):
    try:
        info = await asyncio.wait_for(start_pinggy_session(container_name, node_id), timeout=120)
        if info:
            logger.info("✅ Pinggy background bootstrap connected for %s: %s", container_name, info.get("url"))
        else:
            logger.warning("Pinggy background bootstrap did not produce an endpoint for %s; repair loop will retry.", container_name)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.warning("Pinggy background bootstrap failed for %s: %s", container_name, exc)


async def safe_guest_install(container_name: str, node_id: int):
    """Fast post-boot baseline only; package/tunnel work is deferred to repair workers.

    This function is intentionally kept below the remote node-agent timeout budget so
    creating a VPS cannot fail merely because apt mirrors or tunnel providers are slow.
    """
    await set_guest_hostname(container_name, node_id, VPS_HOSTNAME)
    try:
        await install_anti_mining_guard(container_name, node_id)
    except Exception as exc:
        logger.debug("Anti-mining guard deferred for %s: %s", container_name, exc)
    try:
        await apply_guest_motd(container_name, node_id)
    except Exception as exc:
        logger.debug("MOTD setup deferred for %s: %s", container_name, exc)

async def protection_repair_task():
    """Ensure all currently-running managed VPS have the anti-mining guard installed.

    This repairs VPS created by older bot versions without starting stopped instances.
    The regular Start/Reinstall/Deploy flows also install the guard.
    """
    await bot.wait_until_ready()
    await asyncio.sleep(30)
    while not bot.is_closed():
        try:
            for owner_id, vps_list in list(vps_data.items()):
                for vps in list(vps_list):
                    if bool(vps.get('suspended', False)):
                        continue
                    container = str(vps.get('container_name') or '').strip()
                    if not container:
                        continue
                    node_id = int(vps.get('node_id', 1))
                    try:
                        if str(vps.get('status', 'stopped')).lower() != 'running':
                            continue
                        await install_anti_mining_guard(container, node_id)
                    except asyncio.CancelledError:
                        raise
                    except Exception as e:
                        logger.debug(f"Protection repair skipped for {container}: {e}")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Protection repair task failed: {e}", exc_info=True)
        await asyncio.sleep(12 * 3600)


async def guest_baseline_repair_task():
    """Periodically repair only missing guest baseline dependencies on running VPS."""
    await bot.wait_until_ready()
    await asyncio.sleep(90)
    required = "bash sudo curl ip ss ps python3 test"
    while not bot.is_closed():
        try:
            for _owner_id, items in list(vps_data.items()):
                for vps in list(items):
                    if bool(vps.get('suspended', False)):
                        continue
                    container = str(vps.get('container_name') or '').strip()
                    if not container:
                        continue
                    node_id = int(vps.get('node_id', 1))
                    try:
                        if str(vps.get('status', 'stopped')).lower() != 'running':
                            continue
                        probe = await _exec_guest_bash(
                            container,
                            node_id,
                            "missing=''; for c in bash sudo curl ip ss ps python3; do command -v \"$c\" >/dev/null 2>&1 || missing=\"$missing $c\"; done; test -d /etc/ssh/sshd_config.d || missing=\"$missing sshd-config-dir\"; if [ -n \"$missing\" ]; then printf 'MISSING:%s\\n' \"$missing\"; else printf 'OK\\n'; fi",
                            timeout=25,
                        )
                        if str(probe).strip().startswith('MISSING:'):
                            logger.warning(f"Guest baseline repair required for {container}: {probe.strip()}")
                            await bootstrap_vps_guest(container, node_id)
                            await install_anti_mining_guard(container, node_id)
                            await recreate_port_forwards(container, node_id_override=node_id)
                        # Existing VPS created by older versions also receive the current MOTD.
                        try:
                            await apply_guest_motd(container, node_id)
                        except Exception as motd_exc:
                            logger.debug(f"MOTD baseline repair skipped for {container}: {motd_exc}")
                    except asyncio.CancelledError:
                        raise
                    except Exception as e:
                        logger.debug(f"Guest baseline repair skipped for {container}: {e}")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Guest baseline repair task failed: {e}", exc_info=True)
        await asyncio.sleep(18 * 3600)

async def access_repair_task():
    """Repair only VPSs that actually need SSH setup or a missing port-forward."""
    await bot.wait_until_ready()
    await asyncio.sleep(45)
    while not bot.is_closed():
        try:
            candidates = []
            for owner_id, items in list(vps_data.items()):
                for vps in list(items):
                    if bool(vps.get("suspended", False)):
                        continue
                    container = str(vps.get("container_name") or "").strip()
                    if not container:
                        continue
                    if str(vps.get("status", "stopped")).lower() != "running":
                        continue
                    forwards = [
                        f for f in get_user_forwards(str(owner_id))
                        if str(f.get("vps_container")) == container
                        and int(f.get("vps_port", 0) or 0) == 22
                    ]
                    needs_forward = not forwards
                    needs_ssh = not bool(vps.get("ssh_ready", False))
                    if needs_forward or needs_ssh:
                        candidates.append((str(owner_id), vps, needs_forward, needs_ssh))
            sem = asyncio.Semaphore(MAX_BACKGROUND_REPAIR_CONCURRENCY)
            async def repair_one(owner_id, vps, needs_forward, needs_ssh):
                container = str(vps.get("container_name")); node_id = int(vps.get("node_id", 1))
                async with sem:
                    if needs_ssh:
                        password = str(vps.get("root_password") or generate_strong_password())
                        try:
                            ok, result = await asyncio.wait_for(configure_ssh(container, node_id, password), timeout=105)
                            if ok:
                                vps["root_password"] = password
                                vps["ssh_ready"] = True
                                try:
                                    await apply_guest_motd(container, node_id)
                                except Exception:
                                    pass
                                save_vps_data_immediate()
                            else:
                                logger.debug("SSH repair not ready for %s: %s", container, result)
                        except Exception as exc:
                            logger.debug("SSH repair skipped for %s: %s", container, exc)
                    if needs_forward:
                        try:
                            port = await asyncio.wait_for(create_port_forward(owner_id, container, 22, node_id), timeout=75)
                            if port:
                                logger.info("🔧 Repaired SSH port-forward for %s: host %s -> guest 22", container, port)
                        except Exception as exc:
                            logger.debug("SSH port-forward repair skipped for %s: %s", container, exc)
            for start_idx in range(0, len(candidates), 10):
                await asyncio.gather(*(repair_one(*x) for x in candidates[start_idx:start_idx+10]), return_exceptions=True)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("Access repair task failed: %s", exc, exc_info=True)
        await asyncio.sleep(ACCESS_REPAIR_INTERVAL)


async def tunnel_repair_task():
    """Keep SSHX/Pinggy healthy without probing every VPS with expensive LXC stats."""
    await bot.wait_until_ready()
    await asyncio.sleep(30)
    sem = asyncio.Semaphore(MAX_BACKGROUND_REPAIR_CONCURRENCY)
    async def repair_one(vps):
        if bool(vps.get('suspended', False)) or str(vps.get('status','stopped')).lower() != 'running':
            return
        container = str(vps.get('container_name') or '').strip()
        if not container:
            return
        node_id = int(vps.get('node_id', 1))
        async with sem:
            if SSHX_ENABLED:
                try:
                    _, ok = await asyncio.wait_for(get_sshx_session_info(container, node_id), timeout=12)
                    if not ok:
                        await asyncio.wait_for(start_sshx_session(container, node_id), timeout=120)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    logger.debug("SSHX repair skipped for %s: %s", container, exc)
            if PINGGY_ENABLED and PINGGY_AUTO_START:
                try:
                    _, _, ok = await asyncio.wait_for(get_pinggy_session_info(container, node_id), timeout=12)
                    if not ok:
                        await asyncio.wait_for(start_pinggy_session(container, node_id), timeout=120)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    logger.debug("Pinggy repair skipped for %s: %s", container, exc)
    while not bot.is_closed():
        try:
            all_vps = [vps for items in list(vps_data.values()) for vps in list(items)]
            for batch_start in range(0, len(all_vps), 10):
                await asyncio.gather(*(repair_one(v) for v in all_vps[batch_start:batch_start+10]), return_exceptions=True)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("Tunnel repair task failed: %s", exc, exc_info=True)
        await asyncio.sleep(TUNNEL_REPAIR_INTERVAL)

async def expiration_monitor_task():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            await check_vps_expiration()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Expiration monitor failed: {e}", exc_info=True)
        await asyncio.sleep(3600)

# Bot events
async def runtime_self_repair_task():
    """Low-risk startup repair: sync DB status and restore security/ports."""
    await bot.wait_until_ready()
    await asyncio.sleep(15)
    try:
        for _owner_id, items in list(vps_data.items()):
            for vps in list(items):
                container = str(vps.get('container_name') or '').strip()
                if not container:
                    continue
                node_id = int(vps.get('node_id', 1))
                try:
                    stats = await asyncio.wait_for(get_container_stats(container, node_id), timeout=12)
                    actual = str(stats.get('status', 'unknown')).lower()
                    if actual in {'running', 'stopped'} and actual != str(vps.get('status', 'stopped')).lower():
                        vps['status'] = actual
                        save_vps_data_immediate()
                    if actual == 'running' and not bool(vps.get('suspended', False)):
                        await install_anti_mining_guard(container, node_id)
                        await recreate_port_forwards(container, node_id_override=node_id)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.debug(f'Runtime self-repair skipped for {container}: {e}')
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f'Runtime self-repair failed: {e}', exc_info=True)


def _sanitize_command_for_audit(ctx) -> str:
    try:
        content = str(getattr(getattr(ctx, "message", None), "content", "") or "").strip()
    except Exception:
        content = ""
    if not content:
        return f"{PREFIX}{getattr(getattr(ctx, 'command', None), 'qualified_name', 'unknown')}"
    # Never put obvious secrets/passwords/tokens into the persistent audit log.
    content = re.sub(r'(?i)(password|passwd|token|api[_-]?key|secret)\s+\S+', r'\1 [REDACTED]', content)
    content = content[:700]
    return content

@bot.event
async def on_command_completion(ctx):
    try:
        cmd = getattr(ctx, "command", None)
        cmd_name = getattr(cmd, "qualified_name", None)
        if not cmd_name:
            return
        root_cmd = str(cmd_name).split()[0].lower()
        if root_cmd in AUDIT_NOISY_COMMANDS:
            return
        container = None; node_id = None
        raw_ref = None
        for key, value in getattr(ctx, "kwargs", {}).items():
            if value is None:
                continue
            if isinstance(value, int) and 'node' in key.lower():
                node_id = value
            elif isinstance(value, str) and ('vps' in key.lower() or 'container' in key.lower() or key.lower() in {'reference','container_name'}):
                raw_ref = value
        if raw_ref:
            _, _, vps = find_vps_record(raw_ref)
            if vps:
                container = str(vps.get('container_name'))
                node_id = int(vps.get('node_id', node_id or 1))
        detail = f"Executed by {getattr(ctx.author, 'display_name', ctx.author)} in {getattr(ctx.channel, 'mention', '#channel')}. Command: `{_sanitize_command_for_audit(ctx)}`"
        await record_audit_event("command", f"Command Completed • {PREFIX}{cmd_name}", detail, user_id=ctx.author.id, node_id=node_id, vps_container=container)
    except Exception:
        pass

async def bandwidth_accounting_task():
    """Persist RX+TX accounting for each running VPS with low host overhead."""
    await bot.wait_until_ready()
    await asyncio.sleep(45)
    while not bot.is_closed():
        try:
            vps_items = [v for items in list(vps_data.values()) for v in list(items)
                         if str(v.get("status", "")).lower() == "running" and not v.get("suspended") and v.get("container_name")]
            sem = asyncio.Semaphore(2)

            async def sample(vps):
                container = str(vps.get("container_name")); node_id = int(vps.get("node_id", 1))
                async with sem:
                    try:
                        rx, tx = await get_container_network_counters(container, node_id)
                    except Exception as exc:
                        logger.debug("Bandwidth sample failed for %s: %s", container, exc)
                        return
                now = datetime.now()
                try:
                    start_dt = datetime.fromisoformat(str(vps.get("bandwidth_cycle_start")))
                    reset = (start_dt.year, start_dt.month) != (now.year, now.month)
                except Exception:
                    reset = True
                last_rx = max(0, int(vps.get("bandwidth_last_rx_bytes") or 0))
                last_tx = max(0, int(vps.get("bandwidth_last_tx_bytes") or 0))
                last_sample = vps.get("bandwidth_last_sample_at")
                first_baseline = (
                    last_rx == 0
                    and last_tx == 0
                    and int(vps.get('bandwidth_used_bytes') or 0) == 0
                )
                # Guest counters reset on reboot/interface recreation; never create negative usage.
                if first_baseline:
                    delta_rx = 0
                    delta_tx = 0
                else:
                    delta_rx = rx if rx < last_rx else rx - last_rx
                    delta_tx = tx if tx < last_tx else tx - last_tx
                used = 0 if reset else max(0, int(vps.get("bandwidth_used_bytes") or 0))
                used += delta_rx + delta_tx
                vps["bandwidth_gb"] = VPS_BANDWIDTH_GB
                vps["bandwidth_used_bytes"] = used
                vps["bandwidth_last_rx_bytes"] = rx
                vps["bandwidth_last_tx_bytes"] = tx
                vps["bandwidth_last_sample_at"] = now.isoformat()
                if reset:
                    vps["bandwidth_cycle_start"] = now.isoformat()
                with DB_LOCK:
                    conn = get_db()
                    try:
                        conn.execute(
                            "UPDATE vps SET bandwidth_gb=?, bandwidth_used_bytes=?, bandwidth_cycle_start=?, bandwidth_last_rx_bytes=?, bandwidth_last_tx_bytes=?, bandwidth_last_sample_at=?, last_modified=CURRENT_TIMESTAMP WHERE container_name=?",
                            (VPS_BANDWIDTH_GB, used, vps.get("bandwidth_cycle_start"), rx, tx, vps.get("bandwidth_last_sample_at"), container),
                        )
                        conn.commit()
                    finally:
                        conn.close()

            # Process in small batches: the semaphore limits active samples, while batching
            # avoids constructing thousands of pending coroutine tasks on large installations.
            for batch_start in range(0, len(vps_items), 20):
                batch = vps_items[batch_start:batch_start + 20]
                await asyncio.gather(*(sample(v) for v in batch), return_exceptions=True)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("Bandwidth accounting task failed: %s", exc)
        await asyncio.sleep(BANDWIDTH_SAMPLE_INTERVAL)


async def audit_channel_health_task():
    """Clear a stale/deleted log-channel ID so audit logging never loops on a dead target."""
    await bot.wait_until_ready()
    await asyncio.sleep(60)
    while not bot.is_closed():
        try:
            channel_id = _audit_channel_id()
            if channel_id:
                channel = bot.get_channel(channel_id)
                if channel is None:
                    try:
                        channel = await bot.fetch_channel(channel_id)
                    except (discord.NotFound, discord.Forbidden):
                        set_audit_channel_id(0)
                        logger.warning("Configured audit log channel %s is unavailable; disabled it.", channel_id)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("Audit channel health check failed: %s", exc)
        await asyncio.sleep(900)


async def node_log_health_task():
    await bot.wait_until_ready()
    await asyncio.sleep(20)
    while not bot.is_closed():
        try:
            if _audit_channel_id():
                for node in get_nodes():
                    node_id = int(node.get('id'))
                    try:
                        stats = await asyncio.wait_for(get_host_stats(node_id), timeout=12)
                        cpu = float(stats.get('cpu') or 0.0)
                        ram = float(stats.get('ram') or 0.0)
                        vps_count = sum(1 for items in vps_data.values() for v in items if int(v.get('node_id', 1)) == node_id)
                        total = int(stats.get('ram_bytes_total') or 0)
                        avail = int(stats.get('ram_bytes_available') or 0)
                        memory = f"{avail/(1024**3):.1f} GiB free / {total/(1024**3):.1f} GiB total" if total else "N/A"
                        await record_audit_event("node", "Node Health Snapshot", f"CPU `{cpu:.1f}%` • RAM `{ram:.1f}%` • {memory} • Managed VPS `{vps_count}` • Processor `{HOST_PROCESSOR_NAME}` • Provider `{HOST_PROVIDER_NAME}`.", node_id=node_id)
                    except Exception as exc:
                        await record_audit_event("error", "Node Health Check Failed", str(exc)[:800], node_id=node_id)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("Node log health task failed: %s", exc)
        await asyncio.sleep(LOG_HEALTH_INTERVAL)

@bot.event
async def on_ready():
    global status_task_handle, expiration_task_handle, protection_task_handle, tunnel_repair_task_handle
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f"{BOT_NAME} Bot is ready!")

    if status_task_handle is None or status_task_handle.done():
        status_task_handle = bot.loop.create_task(status_presence_task(), name="rgnodes_presence_task")
    if not any(task.get_name() == 'auto_save_task' for task in asyncio.all_tasks()):
        bot.loop.create_task(auto_save_task(), name="auto_save_task")
    if expiration_task_handle is None or expiration_task_handle.done():
        expiration_task_handle = bot.loop.create_task(expiration_monitor_task(), name="rgnodes_expiration_task")
    if protection_task_handle is None or protection_task_handle.done():
        protection_task_handle = bot.loop.create_task(protection_repair_task(), name="rgnodes_protection_task")
    if tunnel_repair_task_handle is None or tunnel_repair_task_handle.done():
        tunnel_repair_task_handle = bot.loop.create_task(tunnel_repair_task(), name="rgnodes_tunnel_repair_task")
    global access_repair_task_handle
    if access_repair_task_handle is None or access_repair_task_handle.done():
        access_repair_task_handle = bot.loop.create_task(access_repair_task(), name="rgnodes_access_repair_task")
    if not any(task.get_name() == "rgnodes_runtime_repair_task" for task in asyncio.all_tasks()):
        bot.loop.create_task(runtime_self_repair_task(), name="rgnodes_runtime_repair_task")
    if not any(task.get_name() == "rgnodes_guest_repair_task" for task in asyncio.all_tasks()):
        bot.loop.create_task(guest_baseline_repair_task(), name="rgnodes_guest_repair_task")
    if not any(task.get_name() == "rgnodes_node_log_health_task" for task in asyncio.all_tasks()):
        bot.loop.create_task(node_log_health_task(), name="rgnodes_node_log_health_task")
    if not any(task.get_name() == "rgnodes_audit_channel_health_task" for task in asyncio.all_tasks()):
        bot.loop.create_task(audit_channel_health_task(), name="rgnodes_audit_channel_health_task")
    if not any(task.get_name() == "rgnodes_bandwidth_accounting_task" for task in asyncio.all_tasks()):
        bot.loop.create_task(bandwidth_accounting_task(), name="rgnodes_bandwidth_accounting_task")
    if _audit_channel_id():
        bot.loop.create_task(record_audit_event("system", "Bot Ready", f"{BOT_NAME} connected • {HOST_PROVIDER_NAME} • {HOST_PROCESSOR_NAME}.", announce=True), name="rgnodes_ready_audit")
    if AUTO_CREATE_SERVER_EMOJIS:
        for guild in list(bot.guilds):
            bot.loop.create_task(auto_provision_server_emojis(guild), name=f"rgnodes_emoji_provision_{guild.id}")

@bot.check
async def rgnodes_maintenance_command_gate(ctx):
    if not maintenance_enabled() or is_admin_user(getattr(ctx, "author", None)):
        return True
    name = str(getattr(getattr(ctx, "command", None), "name", "") or "").lower()
    if name in MAINTENANCE_SAFE_COMMANDS:
        return True
    raise RGNODESMaintenanceError()

@bot.event
async def on_guild_join(guild: discord.Guild):
    if AUTO_CREATE_SERVER_EMOJIS:
        try:
            await auto_provision_server_emojis(guild)
        except Exception as exc:
            logger.warning(f"Initial emoji provisioning failed for {guild.name}: {exc}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=create_error_embed("Missing Argument", f"Please check command usage with `{PREFIX}help`."))
    elif isinstance(error, commands.BadArgument):
        await ctx.send(embed=create_error_embed("Invalid Argument", "Please check your input and try again."))
    elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, asyncio.TimeoutError):
        await ctx.send(embed=create_warning_embed("⏱️ Operation Timed Out", "The interactive setup wizard expired after 3 minutes. No new VPS/node was created by the timed-out prompt."))
    elif isinstance(error, RGNODESMaintenanceError):
        await ctx.send(embed=create_error_embed("🔴 Under Maintenance", "🔴 **Under Maintenance**\n🛠️ **SOON for Fixing..**\n\nNormal user VPS actions are temporarily unavailable. Administrators remain fully operational."))
    elif isinstance(error, commands.BotMissingPermissions):
        missing = ", ".join(str(p).replace('_', ' ').title() for p in getattr(error, "missing_permissions", [])[:10]) or "required Discord permissions"
        await ctx.send(embed=create_error_embed("🛡️ Bot Permission Missing", f"I need: **{missing}** in this channel/server. Use `{PREFIX}permissions` to audit the current channel."))
    elif isinstance(error, commands.MissingPermissions):
        missing = ", ".join(str(p).replace('_', ' ').title() for p in getattr(error, "missing_permissions", [])[:10]) or "required permissions"
        await ctx.send(embed=create_error_embed("🛡️ Permission Denied", f"Your Discord account is missing: **{missing}**."))
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send(embed=create_error_embed("Server Only", "This command must be used inside a Discord server."))
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(embed=create_warning_embed("⏳ Slow Down", f"Please wait **{error.retry_after:.1f}s** before using this command again."))
    elif isinstance(error, commands.MaxConcurrencyReached):
        await ctx.send(embed=create_warning_embed("⏳ Operation Busy", "This action is already running. Please wait for the current operation to finish."))
    elif isinstance(error, commands.DisabledCommand):
        await ctx.send(embed=create_warning_embed("Command Disabled", "This command is temporarily disabled."))
    elif isinstance(error, commands.CheckFailure):
        error_msg = str(error) if str(error) else "You need RGNODES admin access or the required permission to use this command."
        await ctx.send(embed=create_error_embed("Access Denied", error_msg))
    elif isinstance(error, discord.NotFound):
        await ctx.send(embed=create_error_embed("Error", "The requested resource was not found. Please try again."))
    else:
        logger.error(f"Command error in {getattr(getattr(ctx, 'command', None), 'qualified_name', 'unknown')}: {error}", exc_info=True)
        detail = str(error.original if isinstance(error, commands.CommandInvokeError) else error).strip()
        try:
            await record_audit_event("error", f"Command Failed • {getattr(getattr(ctx, 'command', None), 'qualified_name', 'unknown')}", detail[:800], user_id=getattr(ctx.author, 'id', None), announce=True)
        except Exception:
            pass
        user_message = "The command could not be completed. Please try again; the incident was logged automatically."
        if is_admin_user(getattr(ctx, 'author', None)) and detail:
            user_message += f"\n\n**Technical:** `{detail[:700]}`"
        await ctx.send(embed=create_error_embed("⚠️ Command Failed", user_message))

# Bot commands
@bot.command(name="sshx-health")
@is_admin()
async def sshx_health_command(ctx, container_name: str):
    """Admin-only SSHX health/diagnostic snapshot."""
    uid, _, vps = find_vps_record(container_name)
    if not vps:
        await ctx.send(embed=create_error_embed("VPS Not Found", f"`{container_name}` was not found."))
        return
    node_id = int(vps.get("node_id", 1))
    url, active = await get_sshx_session_info(container_name, node_id)
    diag = await get_sshx_diagnostics(container_name, node_id)
    embed = create_info_embed("🧪 SSHX Health", f"`{container_name}` • Node `{node_id}`")
    add_field(embed, "Status", "🟢 Active" if active else "🔴 Offline", True)
    add_field(embed, "URL", f"<{url}>" if url else "Not generated", False)
    add_field(embed, "Diagnostics", f"```text\n{diag[-3000:]}\n```", False)
    await ctx.send(embed=embed)

@bot.command(name='ping')
async def ping(ctx):
    """Check bot latency"""
    latency = round(bot.latency * 1000)
    embed = create_success_embed(
        "🏓 Pong!",
        f"Bot is responding perfectly!"
    )
    add_field(embed, "Latency", f"`{latency}ms`", inline=True)
    add_field(embed, "Status", "✅ Online", inline=True)
    add_field(embed, "Bot", f"`{BOT_NAME} v{BOT_VERSION}`", inline=True)
    await ctx.send(embed=embed)

@bot.command(name='uptime')
async def uptime(ctx):
    up = get_uptime()
    embed = create_info_embed("Host Uptime", up)
    await ctx.send(embed=embed)

@bot.command(name='thresholds')
@is_admin()
async def thresholds(ctx):
    embed = create_info_embed("Resource Thresholds", f"**CPU:** {CPU_THRESHOLD}%\n**RAM:** {RAM_THRESHOLD}%")
    await ctx.send(embed=embed)

@bot.command(name='set-threshold')
@is_admin()
async def set_threshold(ctx, cpu: int, ram: int):
    global CPU_THRESHOLD, RAM_THRESHOLD
    if cpu < 0 or ram < 0:
        await ctx.send(embed=create_error_embed("Invalid Thresholds", "Thresholds must be non-negative."))
        return
    CPU_THRESHOLD = cpu
    RAM_THRESHOLD = ram
    set_setting('cpu_threshold', str(cpu))
    set_setting('ram_threshold', str(ram))
    embed = create_success_embed("Thresholds Updated", f"**CPU:** {cpu}%\n**RAM:** {ram}%")
    await ctx.send(embed=embed)

@bot.command(name='set-status')
@is_admin()
async def set_status(ctx, activity_type: str, *, name: str):
    types = {
        'playing': discord.ActivityType.playing,
        'watching': discord.ActivityType.watching,
        'listening': discord.ActivityType.listening,
        'streaming': discord.ActivityType.streaming,
    }
    if activity_type.lower() not in types:
        await ctx.send(embed=create_error_embed("Invalid Type", "Valid types: playing, watching, listening, streaming"))
        return
    await bot.change_presence(activity=discord.Activity(type=types[activity_type.lower()], name=name))
    embed = create_success_embed("Status Updated", f"Set to {activity_type}: {name}")
    await ctx.send(embed=embed)

@bot.command(name="myvps")
async def my_vps(ctx):
    user_id = str(ctx.author.id)
    vps_list = vps_data.get(user_id, [])

    # ─── No VPS Case ───────────────────────────────────────────
    if not vps_list:
        embed = create_error_embed(
            "❌ No VPS Found",
            f"You don’t have any **{BOT_NAME} VPS** yet."
        )
        embed.add_field(
            name="🚀 Quick Actions",
            value=(
                f"• `{PREFIX}manage` – Manage VPS\n"
                f"• Contact an admin to request a VPS"
            ),
            inline=False
        )
        await ctx.send(embed=embed)
        return

    # ─── Embed ────────────────────────────────────────────────
    embed = create_info_embed(
        title="🖥️ My VPS Dashboard",
        description="Your personal VPS overview"
    )

    total_vps = len(vps_list)
    running = suspended = whitelisted = 0
    vps_cards = []

    # ─── VPS Processing ───────────────────────────────────────
    for i, vps in enumerate(vps_list, start=1):
        node = get_node(vps.get("node_id"))
        node_name = node["name"] if node else "Unknown"

        config = vps.get("config", "Custom")
        ram = vps.get("ram", "0GB")
        cpu = vps.get("cpu", "0")
        storage = vps.get("storage", "0GB")

        if vps.get("suspended"):
            status = "⛔ SUSPENDED"
            suspended += 1
        elif vps.get("status") == "running":
            status = "🟢 RUNNING"
            running += 1
        else:
            status = "🔴 STOPPED"

        if vps.get("whitelisted"):
            whitelisted += 1

        # Build VPS card
        card = (
            f"**{i}.** `{vps['container_name']}`\n"
            f"{status} • `{config}`\n"
            f"⚙️ `{ram}` RAM • `{cpu}` CPU • `{storage}` Disk\n"
            f"📍 Node: `{node_name}`"
        )
        
        # Add expiration info if set
        if vps.get('expiration_date'):
            expiration_dt = datetime.fromisoformat(vps['expiration_date'])
            days_remaining = (expiration_dt - datetime.now()).days
            
            if days_remaining < 0:
                expiration_badge = "🔴 EXPIRED"
            elif days_remaining <= EXPIRATION_WARNING_DAYS:
                expiration_badge = "🟡 EXPIRING"
            else:
                expiration_badge = "🟢 ACTIVE"
            
            card += f"\n⏰ {expiration_badge} • Expires: `{expiration_dt.strftime('%Y-%m-%d')}`"
        
        vps_cards.append(card)

    # ─── Row 1 : Summary ──────────────────────────────────────
    embed.add_field(
        name="📊 Summary",
        value=(
            f"🖥️ `{total_vps}` VPS\n"
            f"🟢 `{running}` Running\n"
            f"⛔ `{suspended}` Suspended\n"
            f"✅ `{whitelisted}` Whitelisted"
        ),
        inline=True
    )

    embed.add_field(
        name="⚡ Quick Actions",
        value=(
            f"`{PREFIX}manage`\n"
            f"`{PREFIX}reinstall`\n"
            f"`{PREFIX}status`"
        ),
        inline=True
    )

    embed.add_field(
        name="🧭 Tip",
        value="Use **manage** to control your VPS",
        inline=True
    )

    # ─── VPS Cards (Full Width) ───────────────────────────────
    vps_text = "\n\n".join(vps_cards)
    for i in range(0, len(vps_text), 1024):
        embed.add_field(
            name="🖥️ Your VPS",
            value=vps_text[i:i + 1024],
            inline=False
        )

    embed.set_footer(text=f"⚡ RGNODES™ • VPS Control Panel")
    embed.timestamp = ctx.message.created_at

    await ctx.send(embed=embed)

@bot.command(name='lxc-list')
@is_admin()
async def lxc_list(ctx, node_id: int = 1):
    try:
        result = await execute_lxc("", "list", node_id=node_id)
        node = get_node(node_id)
        embed = create_info_embed(f"LXC Containers List on {node['name']}", result)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(embed=create_error_embed("Error", str(e)))

class NodeSelectView(RGNODESView):
    PAGE_SIZE = 25

    def __init__(self, ram: int, cpu: int, disk: int, user: discord.Member, ctx, expiry_days: int = None, page: int = 0):
        super().__init__(timeout=300)
        self.ram, self.cpu, self.disk = ram, cpu, disk
        self.user, self.ctx = user, ctx
        self.expiry_days = expiry_days if expiry_days and expiry_days > 0 else DEFAULT_VPS_EXPIRATION_DAYS
        self.page = max(0, int(page))
        self.nodes = []
        self.total_pages = 1
        self._refresh_nodes()
        self._build()

    def _refresh_nodes(self):
        nodes = []
        for n in get_nodes():
            try:
                node_id = int(n["id"])
                capacity = max(0, int(n.get("total_vps") or 0))
            except (TypeError, ValueError):
                continue
            available = max(0, capacity - get_current_vps_count(node_id))
            if available > 0:
                nodes.append((n, available))
        self.nodes = nodes
        self.total_pages = max(1, (len(nodes) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self.page = min(self.page, self.total_pages - 1)

    def _build(self):
        self.clear_items()
        items = self.nodes[self.page * self.PAGE_SIZE:(self.page + 1) * self.PAGE_SIZE]
        options = []
        for n, available in items:
            loc = str(n.get("location") or "Unknown")
            prefix = "📍" if n.get("is_local") else "🌐"
            options.append(discord.SelectOption(label=f"{str(n.get('name') or 'Node')[:70]} {prefix}", value=str(n["id"]), description=f"{loc[:50]} • {available} slots"[:100]))
        if not options:
            self.add_item(discord.ui.Select(placeholder="No available nodes", disabled=True, options=[discord.SelectOption(label="No capacity available", value="none")]))
            return
        self.select = discord.ui.Select(placeholder=f"Select Node • {self.page + 1}/{self.total_pages}", options=options, row=0)
        self.select.callback = self.select_node
        self.add_item(self.select)
        if self.total_pages > 1:
            prev = discord.ui.Button(label="Previous", emoji="◀️", style=discord.ButtonStyle.secondary, disabled=self.page == 0, row=1)
            nxt = discord.ui.Button(label="Next", emoji="▶️", style=discord.ButtonStyle.secondary, disabled=self.page >= self.total_pages - 1, row=1)
            prev.callback = self.previous_page
            nxt.callback = self.next_page
            self.add_item(prev); self.add_item(nxt)

    async def _move_page(self, interaction: discord.Interaction, page: int):
        if str(interaction.user.id) != str(self.ctx.author.id):
            await interaction.response.send_message(embed=create_error_embed("⛔ Access Denied", "Only the command author can use this selector."), ephemeral=True)
            return
        self.page = page
        self._refresh_nodes()
        self._build()
        await interaction.response.edit_message(view=self)

    async def previous_page(self, interaction: discord.Interaction):
        await self._move_page(interaction, self.page - 1)

    async def next_page(self, interaction: discord.Interaction):
        await self._move_page(interaction, self.page + 1)

    async def select_node(self, interaction: discord.Interaction):
        if str(interaction.user.id) != str(self.ctx.author.id):
            await interaction.response.send_message(embed=create_error_embed("⛔ Access Denied", "Only the command author can select a node."), ephemeral=True)
            return
        node_id = int(self.select.values[0])
        self.select.disabled = True
        await interaction.response.defer(ephemeral=True)
        try:
            ok, reason = await check_node_capacity_for_vps(node_id, self.ram, self.cpu, self.disk)
            if not ok:
                self.select.disabled = False
                await interaction.followup.send(embed=create_error_embed("🛡️ Node Protected", reason), ephemeral=True)
                return
            await interaction.edit_original_response(view=self)
            await interaction.followup.send(
                embed=create_info_embed("💿 Select Operating System", f"Choose the operating system for this VPS.\n\n🛡️ Capacity check: **PASS**\n{reason}"),
                view=OSSelectView(self.ram, self.cpu, self.disk, self.user, self.ctx, node_id, self.expiry_days),
                ephemeral=True,
            )
        except Exception as exc:
            self.select.disabled = False
            logger.warning(f"Node preflight failed for {node_id}: {exc}", exc_info=True)
            await interaction.followup.send(embed=create_error_embed("🛡️ Node Check Failed", "The node health check could not be completed safely. No VPS was created."), ephemeral=True)

class OSSelectView(RGNODESView):
    def __init__(self, ram: int, cpu: int, disk: int, user: discord.Member, ctx, node_id: int, expiry_days: int = None):
        super().__init__(timeout=300)
        self.ram = ram
        self.cpu = cpu
        self.disk = disk
        self.user = user
        self.ctx = ctx
        self.node_id = node_id
        self.expiry_days = expiry_days if expiry_days and expiry_days > 0 else DEFAULT_VPS_EXPIRATION_DAYS
        self.selected_os = None
        self.select = discord.ui.Select(
            placeholder="Select an OS for the VPS",
            options=[discord.SelectOption(label=o["label"], value=o["value"]) for o in OS_OPTIONS]
        )
        self.select.callback = self.select_os
        self.add_item(self.select)

        self.deploy_button = discord.ui.Button(
            label="Deploy VPS",
            emoji="🚀",
            style=discord.ButtonStyle.success,
            disabled=True,
            row=1,
        )
        self.deploy_button.callback = self.deploy_selected
        self.add_item(self.deploy_button)

    async def select_os(self, interaction: discord.Interaction):
        if str(interaction.user.id) != str(self.ctx.author.id):
            await interaction.response.send_message(
                embed=create_error_embed("Access Denied", "Only the command author can select."),
                ephemeral=True,
            )
            return

        selected = self.select.values[0]
        self.selected_os = selected
        self.select.disabled = True
        self.deploy_button.disabled = False

        embed = create_info_embed(
            "🚀 Configure RGNODES™ VPS",
            f"Node: **{get_node(self.node_id)['name'] if get_node(self.node_id) else self.node_id}**\n"
            f"OS: **{next((o['label'] for o in OS_OPTIONS if o['value'] == selected), selected)}**\n"
            "Select both options, then press **Deploy VPS**.\n\n"
            f"**Plan:** {self.ram}GB RAM • {self.cpu} Core(s) • {self.disk}GB Storage\n"
            f"**Hostname:** `{VPS_HOSTNAME}`\n"
            f"**Expiration:** {self.expiry_days} days"
        )
        await interaction.response.edit_message(embed=embed, view=self)

    async def deploy_selected(self, interaction: discord.Interaction):
        if str(interaction.user.id) != str(self.ctx.author.id):
            await interaction.response.send_message(
                embed=create_error_embed("Access Denied", "Only the command author can deploy this VPS."),
                ephemeral=True,
            )
            return

        if not self.selected_os:
            await interaction.response.send_message(
                embed=create_warning_embed("OS Required", "Select an operating system before deploying."),
                ephemeral=True,
            )
            return

        user_id = str(self.user.id)
        if maintenance_enabled() and not is_admin_user(interaction.user):
            await interaction.response.send_message(
                embed=create_warning_embed("Maintenance Mode", "VPS deployment is temporarily disabled."),
                ephemeral=True,
            )
            return
        if user_has_vps(user_id):
            await interaction.response.send_message(
                embed=create_error_embed("VPS Limit Reached", "This account already owns a VPS. Limit: 1."),
                ephemeral=True,
            )
            return
        if user_id in ACTIVE_DEPLOYMENTS:
            await interaction.response.send_message(
                embed=create_warning_embed("Deployment Already Running", "A VPS deployment for this account is already in progress."),
                ephemeral=True,
            )
            return

        ACTIVE_DEPLOYMENTS.add(user_id)
        node_lock = _get_deploy_node_lock(self.node_id) if DEPLOY_NODE_SERIALIZE else None
        if node_lock is not None:
            await node_lock.acquire()
        self.select.disabled = True
        self.deploy_button.disabled = True
        os_version = self.selected_os
        creating_embed = create_info_embed("Creating VPS", f"Deploying {os_version} VPS for {self.user.mention} on node {self.node_id}...")
        try:
            await interaction.response.edit_message(embed=creating_embed, view=self)
        except Exception:
            ACTIVE_DEPLOYMENTS.discard(user_id)
            raise

        # Create shorter container name with GLOBAL VPS ID
        # Reserve a concurrency-safe persistent VMID before container creation.
        # New deployments intentionally never expose Discord usernames in the LXC name.
        global_vps_id = reserve_vps_vmid()
        container_name = f"rgnodes-vps-{global_vps_id}"
        ram_mb = self.ram * 1024
        container_created = False
        record_persisted = False
        sshx_url = None
        try:
            await interaction.edit_original_response(embed=create_info_embed("VPS Createing.", f"Preparing `{container_name}` from **{os_version}**..."))
            await send_progress(interaction, "VPS Creating", 1, 6, "Preparing the VPS environment.")
            storage_pool = await resolve_storage_pool(self.node_id)
            capacity_ok, capacity_reason = await check_node_capacity_for_vps(self.node_id, self.ram, self.cpu, self.disk)
            if not capacity_ok:
                raise RuntimeError(capacity_reason)
            resolved_os = await resolve_lxd_image(os_version, self.node_id)
            await execute_lxc(container_name, f"init {shlex.quote(resolved_os)} {container_name} -s {shlex.quote(storage_pool)}", node_id=self.node_id, timeout=DEPLOY_EXECUTION_TIMEOUT)
            os_version = resolved_os
            container_created = True
            await apply_vps_performance_profile(container_name, self.node_id, ram_mb, self.cpu)
            await execute_lxc(container_name, f"config device set {container_name} root size={self.disk}GB", node_id=self.node_id, timeout=180)
            await send_progress(interaction, "VPS Creating", 2, 6, "Applying virtualization and networking configuration.")
            await apply_lxc_config(container_name, self.node_id)
            await send_progress(interaction, "VPS Creating", 3, 6, "Starting the VPS and preparing network access.")
            await execute_lxc(container_name, f"start {container_name}", node_id=self.node_id)
            await apply_internal_permissions(container_name, self.node_id)
            await send_progress(interaction, "VPS Creating", 4, 6, "Preparing the VPS system services.")
            await safe_guest_install(container_name, self.node_id)
            if DOCKER_INSTALL_ON_DEPLOY:
                await ensure_docker_ready(container_name, self.node_id, strict=DOCKER_STRICT_DEPLOY)
            await send_progress(interaction, "VPS Creating", 5, 6, "Configuring secure remote access.")
            # Don't recreate port forwards here - VPS not in database yet
            # Port forwards will be handled by start_vps command
            
            # Generate strong password
            root_password = generate_strong_password()
            
            # Persist the VPS before optional/slow guest access setup. A transient SSH
            # package/mirror problem must never destroy an otherwise healthy container.
            config_str = f"{self.ram}GB RAM / {self.cpu} CPU / {self.disk}GB Disk"
            vps_info = {
                "container_name": container_name,
                "node_id": self.node_id,
                "ram": f"{self.ram}GB",
                "cpu": str(self.cpu),
                "storage": f"{self.disk}GB",
                "config": config_str,
                "os_version": os_version,
                "status": "running",
                "suspended": False,
                "whitelisted": False,
                "suspension_history": [],
                "created_at": datetime.now().isoformat(),
                "shared_with": [],
                "expiration_date": (datetime.now() + timedelta(days=self.expiry_days)).isoformat(),
                "root_password": root_password,
                "bandwidth_gb": VPS_BANDWIDTH_GB,
                "bandwidth_used_bytes": 0,
                "bandwidth_cycle_start": datetime.now().isoformat(),
                "id": None,
                "vmid": global_vps_id,
                "ssh_ready": False,
                "sshx_url": None,
                "pinggy_host": None,
                "pinggy_port": None,
                "pinggy_url": None
            }
            logger.info(f"🆕 Creating VPS object: {vps_info['container_name']} for user {user_id}")
            if user_id not in vps_data:
                vps_data[user_id] = []
                logger.info(f"   Created new user entry in vps_data for {user_id}")
            vps_data[user_id].append(vps_info)
            logger.info(f"   ✅ VPS added to vps_data. Total VPS for user: {len(vps_data[user_id])}")
            logger.info(f"   Total users in vps_data: {len(vps_data)}")
            
            # Allocate 1 default port per user for SSH access
            try:
                with DB_LOCK:
                    conn = get_db()
                    # Check if user already has port allocation
                    existing = conn.execute(
                        "SELECT allocated_ports FROM port_allocations WHERE user_id = ?",
                        (str(user_id),)
                    ).fetchone()
                    
                    if not existing:
                        # Give each new user the configured forwarding quota.
                        conn.execute(
                            "INSERT INTO port_allocations (user_id, allocated_ports, last_modified) VALUES (?, ?, CURRENT_TIMESTAMP)",
                            (str(user_id), DEFAULT_PORT_QUOTA)
                        )
                        conn.commit()
                        logger.info(f"   ✅ Allocated {DEFAULT_PORT_QUOTA} default port slots for user {user_id}")
                    conn.close()
            except Exception as e:
                logger.warning(f"Could not allocate port for user {user_id}: {e}")
            
            try:
                save_vps_data_immediate()
            except Exception as persist_error:
                raise RuntimeError(
                    f"VPS was created, but its database record could not be persisted safely: {persist_error}"
                ) from persist_error
            record_persisted = True
            logger.info(f"   ✅ VPS database record persisted")
            await record_audit_event(
                "vps", "VPS Created",
                f"Created `{container_name}` • {os_version} • {self.ram}GB RAM • {self.cpu} CPU • {self.disk}GB disk • {VPS_BANDWIDTH_GB}GB bandwidth.",
                user_id=user_id, node_id=self.node_id, vps_container=container_name
            )

            # Allocate the persistent SSH forward first; the guest daemon can be repaired
            # asynchronously without changing the public host port.
            try:
                ssh_port = await create_port_forward(str(user_id), container_name, 22, self.node_id)
            except Exception as ssh_err:
                raise RuntimeError(f"Could not create the mandatory SSH port forward: {ssh_err}") from ssh_err
            if not ssh_port:
                raise RuntimeError("Mandatory SSH port forward could not be allocated.")
            logger.info(f"   ✅ Verified persistent SSH proxy device 22 → host port {ssh_port}")

            # Guest SSH setup is best-effort after persistence. access_repair_task will retry
            # only when ssh_ready is false, preventing a slow package mirror from causing
            # the earlier 120-second 'Creation Failed' behavior.
            try:
                success, result = await configure_ssh(container_name, self.node_id, root_password)
                vps_info["ssh_ready"] = bool(success)
                if success:
                    try:
                        await apply_guest_motd(container_name, self.node_id)
                    except Exception as motd_exc:
                        logger.debug("Post-SSH MOTD apply deferred for %s: %s", container_name, motd_exc)
                else:
                    logger.warning("SSH setup deferred for %s: %s", container_name, result)
                save_vps_data_immediate()
            except Exception as ssh_setup_exc:
                vps_info["ssh_ready"] = False
                logger.warning("SSH setup deferred for %s: %s", container_name, ssh_setup_exc)
                save_vps_data_immediate()
            endpoints = await detect_public_endpoints(self.node_id)
            ssh_access = format_public_ssh_access(endpoints, ssh_port)
            ssh_command = ssh_access.get("ssh_ipv4") or ssh_access.get("ssh_ipv6") or "Public SSH endpoint unavailable"

            # Tunnel startup is deliberately decoupled from the creation request.
            # This prevents a slow external tunnel provider from holding the Discord
            # interaction open and causing the common 120s creation timeout.
            pinggy_info = None
            if SSHX_ENABLED:
                asyncio.create_task(_background_start_sshx(container_name, self.node_id), name=f"rgnodes_sshx_bootstrap_{container_name}")
            if PINGGY_ENABLED and PINGGY_AUTO_START:
                asyncio.create_task(_background_start_pinggy(container_name, self.node_id), name=f"rgnodes_pinggy_bootstrap_{container_name}")
            
            if self.ctx.guild:
                vps_role = await get_or_create_vps_role(self.ctx.guild)
                if vps_role:
                    try:
                        await self.user.add_roles(vps_role, reason=f"{BOT_NAME} VPS ownership granted")
                    except discord.Forbidden:
                        logger.warning(f"Failed to assign VPS role to {self.user.name}")
            success_embed = create_success_embed("VPS Created Successfully")
            add_field(success_embed, "Owner", self.user.mention, True)
            add_field(success_embed, "VPS ID", f"#{global_vps_id}", True)
            add_field(success_embed, "Container", f"`{container_name}`", True)
            add_field(success_embed, "Node", get_node(self.node_id)['name'], True)
            add_field(success_embed, "Resources", f"**RAM:** {self.ram} GB ({int(self.ram * 1024)} MiB hard limit)\n**CPU:** {self.cpu} Cores\n**Storage:** {self.disk} GB\n**Bandwidth:** {VPS_BANDWIDTH_GB} GB", False)
            add_field(success_embed, "OS", friendly_os_label(os_version), True)
            add_field(success_embed, "SSH Configuration", "✅ Configured (PasswordAuth enabled)" if vps_info.get("ssh_ready") else "🟡 Setup queued; automatic access repair is running", True)
            add_field(success_embed, "SSH & Password", ("✅ SSH configured for password authentication" if vps_info.get("ssh_ready") else "🟡 SSH service is being finalized automatically") + "\n🔐 Root password generated and sent via DM\n📧 Check your DMs for SSH credentials!", False)
            add_field(success_embed, "Features", "Nesting, Privileged, FUSE, Kernel Modules (Docker Ready), Unprivileged Ports from 0", False)
            add_field(success_embed, "Disk Note", "Run `sudo resize2fs /` inside VPS if needed to expand filesystem.", False)
            await interaction.followup.send(embed=success_embed)
            dm_embed = create_success_embed('🎉 VPS Deployed!', 'Your free VPS is ready!')
            expires_at = datetime.fromisoformat(vps_info['expiration_date'])
            add_field(dm_embed, '📊 Details', f'**VPS:** `#{global_vps_id}`  **Container:** `{container_name}`\n**OS:** `{friendly_os_label(os_version)}`  **Config:** `{config_str}`\n**Bandwidth:** `{VPS_BANDWIDTH_GB} GB`\n**Expires:** `{expires_at.strftime("%Y-%m-%d %H:%M:%S")}`', False)
            try:
                guest_ips = await asyncio.wait_for(get_container_addresses(container_name, self.node_id), timeout=10)
            except Exception:
                guest_ips = {"ipv4": [], "ipv6": []}
            add_field(dm_embed, '🌐 VPS IPs', f'**Guest IPv4:** `{", ".join(guest_ips.get("ipv4") or []) or "Not assigned"}`\n**Guest IPv6:** `{", ".join(guest_ips.get("ipv6") or []) or "Not assigned"}`\n**Public IPv4:** `{ssh_access.get("ipv4") or "Unavailable"}`\n**Public IPv6:** `{ssh_access.get("ipv6") or "Unavailable"}`', False)
            if sshx_url:
                add_field(dm_embed, '🌐 SSHX Access', f'**SSHX:** <{sshx_url}>\n**Status:** 🟢 Tunnel Active\nUse `-manage` → 🌐 **SSHX** to start a fresh session if needed.', False)
            else:
                add_field(dm_embed, '🌐 SSHX Access', '⚠️ SSHX was not available at deployment time. Use `-manage` → 🌐 **SSHX** to start a fresh session.', False)
            if pinggy_info:
                add_field(dm_embed, '🌐 Pinggy SSH Tunnel', f"**SSH Command:** `ssh root@{pinggy_info['host']} -p {pinggy_info['port']}`\n**Host:** `{pinggy_info['host']}`\n**Port:** `{pinggy_info['port']}`\n**Status:** 🟢 Tunnel Active\nPinggy is started automatically at deployment; use `-manage` → 🔄 **Reconnect Pinggy** for a fresh tunnel.", False)
            else:
                add_field(dm_embed, '🌐 Pinggy SSH Tunnel', '⚪ Pinggy was not connected at deployment time. Use `-manage` → 🔄 **Reconnect Pinggy** to create a fresh tunnel.', False)
            ssh_lines = []
            if ssh_access.get("ssh_ipv4"):
                ssh_lines.append(f"IPv4: `{ssh_access['ssh_ipv4']}`")
            if ssh_access.get("ssh_ipv6"):
                ssh_lines.append(f"IPv6: `{ssh_access['ssh_ipv6']}`")
            if not ssh_lines:
                ssh_lines.append("⚠️ No verified public SSH endpoint is available yet.")
            add_field(dm_embed, '💻 SSH Access', '\n'.join(ssh_lines) + f'\n**Username:** `root`\n**Password:** `{root_password}`\n🔒 Save this password securely.', False)
            add_field(dm_embed, '⚙️ Features', '✅ SSH/SFTP  ✅ Docker-ready LXC (Docker daemon installed when supported)  ✅ Port Forwarding  ✅ KVM-ready when host exposes `/dev/kvm`\n✅ 🛡️ Anti-Mining Protection  ✅ 60-day renewal support  ✅ Hostname: `rgnodes-vps`', False)
            add_field(dm_embed, '📞 Support', f'Use `-manage` for controls. Renewal becomes available in the final **{RENEWAL_WINDOW_DAYS} days** before expiry with `-renew`.', False)
            try:
                await self.user.send(embed=dm_embed)
            except discord.Forbidden:
                await self.ctx.send(embed=create_warning_embed('DM Not Delivered', f"Couldn't DM {self.user.mention}. Enable Discord DMs to receive the VPS password and SSHX access."))
                await self.ctx.send(embed=create_info_embed("Notification Failed", f"Couldn't send DM to {self.user.mention}. Please ensure DMs are enabled."))
        except Exception as e:
            ACTIVE_DEPLOYMENTS.discard(user_id)
            if record_persisted:
                logger.error(f"VPS {container_name} was provisioned but a post-create notification/action failed: {e}", exc_info=True)
                try:
                    await interaction.followup.send(embed=create_warning_embed("VPS Created", f"VPS `{container_name}` was created successfully, but a final notification step failed. Check `{PREFIX}manage` for the VPS."))
                except Exception:
                    pass
                return
            if container_created:
                try:
                    await execute_lxc(container_name, f"delete {container_name} --force", timeout=300, node_id=self.node_id)
                except Exception as cleanup_error:
                    logger.critical(f"Deployment rollback failed for {container_name}: {cleanup_error}", exc_info=True)
            if user_id in vps_data:
                vps_data[user_id] = [v for v in vps_data[user_id] if v.get("container_name") != container_name]
                if not vps_data[user_id]:
                    vps_data.pop(user_id, None)
            save_vps_data_immediate()
            error_embed = create_error_embed("Creation Failed", f"Error: {str(e)}")
            await interaction.followup.send(embed=error_embed)
        finally:
            if node_lock is not None and node_lock.locked():
                node_lock.release()
            # Always release the per-user deployment lock, including successful deployments.
            ACTIVE_DEPLOYMENTS.discard(user_id)

@bot.command(name='deploy')
async def deploy_command(ctx, user: discord.Member = None):
    """Interactive self/admin deployment: OS + node selection, fixed 8GB/2-core/25GB plan."""
    target = user or ctx.author
    caller_is_admin = is_admin_user(ctx.author)
    if user is not None and not caller_is_admin:
        await ctx.send(embed=create_error_embed("Access Denied", "Only admins can deploy a VPS for another account."))
        return
    if maintenance_enabled() and not caller_is_admin:
        await ctx.send(embed=create_warning_embed("Maintenance Mode", "VPS deployment is temporarily disabled while maintenance mode is enabled."))
        return
    if user_has_vps(target.id):
        await ctx.send(embed=create_error_embed("VPS Limit Reached", f"{target.mention} already has a VPS. This system allows **1 VPS per account**."))
        return

    embed = create_info_embed(
        "🚀 Configure RGNODES™ VPS",
        f"OS and node are selected below before deployment.\n\n**Plan**\nRAM: **{DEFAULT_VPS_RAM_GB}GB**\nCPU: **{DEFAULT_VPS_CPU} Core(s)**\nStorage: **{DEFAULT_VPS_STORAGE_GB}GB**\nHostname: `{VPS_HOSTNAME}`\nExpiration: **{DEFAULT_VPS_EXPIRATION_DAYS} days**",
    )
    view = NodeSelectView(DEFAULT_VPS_RAM_GB, DEFAULT_VPS_CPU, DEFAULT_VPS_STORAGE_GB, target, ctx, DEFAULT_VPS_EXPIRATION_DAYS)
    await ctx.send(embed=embed, view=view)


@bot.command(name='create')
@is_admin()
async def create_vps(ctx, ram: int, cpu: int, disk: int, user: discord.Member, expiry_days: int = None):
    if maintenance_enabled() and not is_admin_user(ctx.author):
        await ctx.send(embed=create_warning_embed("Maintenance Mode", "VPS creation is temporarily disabled."))
        return
    if user_has_vps(user.id):
        await ctx.send(embed=create_error_embed("VPS Limit Reached", f"{user.mention} already has a VPS. Only 1 VPS per account is allowed."))
        return
    if ram <= 0 or cpu <= 0 or disk <= 0:
        await ctx.send(embed=create_error_embed("Invalid Specs", "RAM, CPU, and Disk must be positive integers."))
        return
    
    # Validate expiry_days if provided
    if expiry_days is not None and expiry_days <= 0:
        await ctx.send(embed=create_error_embed("Invalid Expiry Days", "Expiry days must be a positive integer."))
        return
    
    expiry_text = f" with {expiry_days} days expiry" if expiry_days else f" with {DEFAULT_VPS_EXPIRATION_DAYS} days expiry (default)"
    embed = create_info_embed("VPS Creation", f"Creating VPS for {user.mention} with {ram}GB RAM, {cpu} CPU cores, {disk}GB Disk{expiry_text}.\nSelect node below.")
    view = NodeSelectView(ram, cpu, disk, user, ctx, expiry_days)
    await ctx.send(embed=embed, view=view)

class ReinstallOSSelectView(RGNODESView):
    def __init__(self, parent_view, container_name, owner_id, actual_idx, ram_gb, cpu, storage_gb, node_id):
        super().__init__(timeout=300)
        self.parent_view = parent_view
        self.container_name = container_name
        self.owner_id = owner_id
        self.actual_idx = actual_idx
        self.ram_gb = ram_gb
        self.cpu = cpu
        self.storage_gb = storage_gb
        self.node_id = node_id
        self.select = discord.ui.Select(
            placeholder="Select an OS for the reinstall",
            options=[discord.SelectOption(label=o["label"], value=o["value"]) for o in OS_OPTIONS]
        )
        self.select.callback = self.select_os
        self.add_item(self.select)

    async def select_os(self, interaction: discord.Interaction):
        os_version = self.select.values[0]
        self.select.disabled = True
        await interaction.response.edit_message(
            embed=create_info_embed(
                "🔄 Reinstalling VPS",
                f"Preparing a safe OS replacement for `{self.container_name}`...\n\n"
                f"New OS: **{friendly_os_label(os_version)}**\n"
                f"Resources: **{self.ram_gb} GB RAM • {self.cpu} Core(s) • {self.storage_gb} GB SSD**"
            ),
            view=self,
        )
        ram_mb = self.ram_gb * 1024
        new_password = generate_strong_password()
        original_name = str(self.container_name)
        suffix = datetime.now().strftime('%Y%m%d%H%M%S')
        target_vps = None
        previous_status = 'stopped'
        previous_suspended = False
        previous_expiration = None
        rollback_name = sanitize_username_for_container(f"{original_name}-rgnodes-backup-{suffix}")[:55]
        staging_name = sanitize_username_for_container(f"rgnodes-reinstall-{suffix}")[:55]
        old_exists = False
        old_was_running = False
        old_renamed = False
        staging_created = False
        swapped = False

        node_lock = _get_deploy_node_lock(self.node_id) if DEPLOY_NODE_SERIALIZE else None
        if node_lock is not None:
            await node_lock.acquire()
        try:
            target_vps = vps_data.get(str(self.owner_id), [])[self.actual_idx]
            if str(target_vps.get('container_name')) != original_name:
                raise RuntimeError('VPS record changed while reinstall was being prepared. Please reopen the dashboard and try again.')
            previous_status = str(target_vps.get('status', 'stopped')).lower()
            previous_suspended = bool(target_vps.get('suspended', False))
            previous_expiration = target_vps.get('expiration_date')

            with DB_LOCK:
                conn = get_db()
                try:
                    forward_rows = conn.execute(
                        'SELECT id, host_port, vps_port FROM port_forwards WHERE vps_container = ? ORDER BY id',
                        (original_name,),
                    ).fetchall()
                finally:
                    conn.close()
            expected_forwards = len(forward_rows)

            await interaction.edit_original_response(
                embed=create_info_embed(
                    "🔄 Reinstall • Safety Check",
                    f"Checking the current VPS `{original_name}` and preparing a rollback point..."
                ),
                view=self,
            )

            try:
                info = await execute_lxc('', f"info {shlex.quote(original_name)}", node_id=self.node_id, timeout=60)
                old_exists = bool(info is not None)
            except Exception:
                old_exists = False

            if old_exists:
                try:
                    current_stats = await get_container_stats(original_name, self.node_id)
                    old_was_running = str(current_stats.get('status', '')).lower() == 'running'
                except Exception:
                    old_was_running = previous_status == 'running'

            # Clear interrupted temporary names from older failed attempts.
            for stale in (rollback_name, staging_name):
                try:
                    await execute_lxc(stale, f'delete {shlex.quote(stale)} --force', node_id=self.node_id, timeout=180)
                except Exception:
                    pass

            # Reinstall builds a second temporary VPS while the old one still exists.
            # Run a conservative admission check so the host never has to absorb two
            # full plans beyond its protected RAM/CPU/disk budget.
            reinstall_ok, reinstall_reason = await check_node_capacity_for_vps(self.node_id, self.ram_gb, self.cpu, self.storage_gb)
            if not reinstall_ok:
                raise RuntimeError(f"Reinstall blocked by host safety guard: {reinstall_reason}")
            storage_pool = await resolve_storage_pool(self.node_id)
            resolved_os = await resolve_lxd_image(os_version, self.node_id)
            os_version = resolved_os

            # Build and fully validate the replacement under a temporary name first.
            await execute_lxc(
                staging_name,
                f'init {shlex.quote(resolved_os)} {shlex.quote(staging_name)} -s {shlex.quote(storage_pool)}',
                node_id=self.node_id,
                timeout=300,
            )
            staging_created = True
            await apply_vps_performance_profile(staging_name, self.node_id, ram_mb, self.cpu)
            await execute_lxc(staging_name, f'config device set {staging_name} root size={self.storage_gb}GB', node_id=self.node_id)
            await apply_lxc_config(staging_name, self.node_id)
            await execute_lxc(staging_name, f'start {staging_name}', node_id=self.node_id, timeout=180)
            await apply_internal_permissions(staging_name, self.node_id)
            await safe_guest_install(staging_name, self.node_id)
            await set_guest_hostname(staging_name, self.node_id, VPS_HOSTNAME)

            ok, ssh_result = await configure_ssh(staging_name, self.node_id, new_password)
            if not ok:
                logger.warning('Replacement VPS %s SSH setup deferred: %s', staging_name, ssh_result)
            try:
                await apply_guest_motd(staging_name, self.node_id)
            except Exception as motd_exc:
                logger.debug('Replacement MOTD deferred for %s: %s', staging_name, motd_exc)
            if ok:
                await _exec_guest_bash(staging_name, self.node_id, "sshd -t", timeout=30)
            else:
                logger.warning("Skipping SSH daemon validation for %s because access repair is pending.", staging_name)
            await _exec_guest_bash(staging_name, self.node_id, "test -x /usr/local/sbin/rgnodes-mining-guard && systemctl is-enabled rgnodes-mining-guard.timer >/dev/null 2>&1 || true", timeout=30)

            # Verify the instance can execute commands before any destructive swap.
            await _exec_guest_bash(staging_name, self.node_id, 'true', timeout=30)
            await execute_lxc(staging_name, f'stop {staging_name} --force', node_id=self.node_id, timeout=120)

            # Stop the old instance before renaming so its host-bound proxy devices are inactive.
            if old_exists:
                try:
                    await execute_lxc(original_name, f'stop {original_name} --force', node_id=self.node_id, timeout=120)
                except Exception as e:
                    msg = str(e).lower()
                    if not any(x in msg for x in ('not running', 'already stopped', 'is stopped')):
                        raise
                await execute_lxc(original_name, f'rename {original_name} {rollback_name}', node_id=self.node_id, timeout=180)
                old_renamed = True

            try:
                await execute_lxc(staging_name, f'rename {staging_name} {original_name}', node_id=self.node_id, timeout=180)
                staging_created = False
                swapped = True
            except Exception:
                if old_renamed:
                    try:
                        await execute_lxc(rollback_name, f'rename {rollback_name} {original_name}', node_id=self.node_id, timeout=180)
                        old_renamed = False
                    except Exception as rollback_error:
                        logger.critical(f'Reinstall rename rollback failed for {original_name}: {rollback_error}', exc_info=True)
                raise

            # Restore desired lifecycle state and persistent ports only after the replacement owns the original name.
            if old_was_running or previous_status == 'running':
                await execute_lxc(original_name, f'start {original_name}', node_id=self.node_id, timeout=180)
                await apply_internal_permissions(original_name, self.node_id)
            else:
                # Intentionally stopped VPS stays stopped after reinstall.
                pass

            readded = await recreate_port_forwards(original_name) if (old_was_running or previous_status == 'running') else 0
            if expected_forwards and (old_was_running or previous_status == 'running') and readded != expected_forwards:
                raise RuntimeError(f'Only {readded}/{expected_forwards} persistent port forwards were restored.')

            # Commit DB only after the replacement has passed validation and runtime checks.
            target_vps['os_version'] = os_version
            target_vps['status'] = 'running' if (old_was_running or previous_status == 'running') else 'stopped'
            target_vps['suspended'] = previous_suspended
            target_vps['root_password'] = new_password
            target_vps['ssh_ready'] = bool(ok)
            target_vps['sshx_url'] = None
            target_vps['sshx_started_at'] = None
            target_vps['config'] = f'{self.ram_gb}GB RAM / {self.cpu} CPU / {self.storage_gb}GB Disk'
            target_vps['expiration_date'] = previous_expiration or (datetime.now() + timedelta(days=DEFAULT_VPS_EXPIRATION_DAYS)).isoformat()
            save_vps_data_immediate()

            # Start a fresh SSHX session when the replacement is running. Failure here does not invalidate the VPS.
            sshx_url = None
            if target_vps['status'] == 'running':
                sshx_url = await start_sshx_session(original_name, self.node_id)

            if old_renamed:
                try:
                    await execute_lxc(rollback_name, f'delete {rollback_name} --force', node_id=self.node_id, timeout=300)
                    old_renamed = False
                except Exception as cleanup_error:
                    logger.warning(f'Reinstall completed but rollback cleanup failed for {rollback_name}: {cleanup_error}')

            result = create_success_embed(
                '🎉 VPS Reinstalled',
                f'`{original_name}` was safely reinstalled with **{friendly_os_label(os_version)}**.'
            )
            add_field(result, '📊 Resources', f'RAM: **{self.ram_gb} GB**\nCPU: **{self.cpu} Core(s)**\nSSD: **{self.storage_gb} GB**\nBandwidth: **{int(target_vps.get("bandwidth_gb") or VPS_BANDWIDTH_GB)} GB**', False)
            add_field(result, '🔐 SSH', f'Username: `root`\nNew password generated\nSSHX: **{"🟢 Connected" if sshx_url else "🟡 Reconnect available"}**', False)
            add_field(result, '🛡️ Protection', 'Anti-Mining Guard: **Enabled**\nLXC nesting / FUSE configuration: **Applied**', False)
            add_field(result, '🌐 Ports', f'Restored: **{readded}/{expected_forwards}**', False)
            await interaction.followup.send(embed=result, ephemeral=True)

            try:
                owner = await bot.fetch_user(int(self.owner_id))
                dm = create_success_embed('🎉 VPS Reinstalled!', f'Your VPS `{original_name}` has been reinstalled and is ready.')
                add_field(dm, '📊 Details', f'**OS:** `{os_version}`\n**Config:** `{self.ram_gb}GB RAM / {self.cpu} CPU / {self.storage_gb}GB Disk`\n**Hostname:** `{VPS_HOSTNAME}`\n**Expires:** `{_safe_fromiso(target_vps["expiration_date"]).strftime("%Y-%m-%d") if target_vps.get("expiration_date") else "N/A"}`', False)
                add_field(dm, '🔐 SSH Access', f'**Username:** `root`\n**Password:** `{new_password}`\n🔒 Save this password securely.', False)
                sshx_dm = f'**SSHX:** <{sshx_url}>\n🟢 Tunnel Active' if sshx_url else '⚠️ SSHX is not connected yet. Use `-manage` → 🌐 **SSHX** to start a fresh session.'
                add_field(dm, '🌐 SSHX', sshx_dm, False)
                await owner.send(embed=dm)
            except Exception as dm_error:
                logger.info(f'Could not DM reinstall credentials for {self.owner_id}: {dm_error}')

        except Exception as e:
            logger.error(f'Safe reinstall failed for {original_name}: {e}', exc_info=True)
            # Roll back the destructive rename whenever possible.
            try:
                if swapped:
                    try:
                        await execute_lxc(original_name, f'stop {original_name} --force', node_id=self.node_id, timeout=120)
                    except Exception:
                        pass
                    try:
                        await execute_lxc(original_name, f'delete {original_name} --force', node_id=self.node_id, timeout=180)
                    except Exception:
                        pass
                    swapped = False
                if old_renamed:
                    await execute_lxc(rollback_name, f'rename {rollback_name} {original_name}', node_id=self.node_id, timeout=180)
                    old_renamed = False
                    if old_was_running:
                        await execute_lxc(original_name, f'start {original_name}', node_id=self.node_id, timeout=180)
                        await recreate_port_forwards(original_name)
                if staging_created:
                    try:
                        await execute_lxc(staging_name, f'delete {staging_name} --force', node_id=self.node_id, timeout=180)
                    except Exception:
                        pass
            except Exception as rollback_error:
                logger.critical(f'REINSTALL ROLLBACK FAILED for {original_name}: {rollback_error}', exc_info=True)
            try:
                await interaction.followup.send(
                    embed=create_error_embed(
                        '❌ Reinstall Failed',
                        f'The original VPS was kept/restored where possible.\n\n`{str(e)[:1000]}`'
                    ),
                    ephemeral=True,
                )
            except Exception:
                pass
        finally:
            if node_lock is not None and node_lock.locked():
                node_lock.release()


class PortAddModal(discord.ui.Modal, title="🌐 Add Port Forward"):
    vps_port = discord.ui.TextInput(
        label="VPS Port",
        placeholder="25565",
        min_length=1,
        max_length=5,
        required=True,
    )

    def __init__(self, owner_id: str, container_name: str, node_id: int):
        super().__init__(timeout=120)
        self.owner_id = str(owner_id)
        self.container_name = str(container_name)
        self.node_id = int(node_id)

    async def on_submit(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.owner_id and not is_admin_user(interaction.user):
            await interaction.response.send_message(embed=create_error_embed("Access Denied", "You do not own this VPS."), ephemeral=True)
            return
        try:
            port = int(str(self.vps_port.value).strip())
            if not 1 <= port <= 65535:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(embed=create_error_embed("Invalid Port", "VPS port must be between 1 and 65535."), ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        try:
            host_port = await create_port_forward(self.owner_id, self.container_name, port, self.node_id)
            if not host_port:
                await interaction.followup.send(
                    embed=create_error_embed(
                        "Port Creation Failed",
                        "No free port/quota is available, or the LXC proxy device could not be created."
                    ),
                    ephemeral=True,
                )
                return
            await interaction.followup.send(
                embed=create_success_embed(
                    "🌐 Port Forward Created",
                    f"**VPS:** `{self.container_name}`\n**VPS Port:** `{port}`\n**Host Port:** `{host_port}`\n**Protocol:** `TCP + UDP`\n\n🔌 Forward is persistent across VPS restarts/reboots."
                ),
                ephemeral=True,
            )
        except Exception as e:
            logger.error(f"Port modal failed for {self.container_name}: {e}", exc_info=True)
            await interaction.followup.send(embed=create_error_embed("Port Error", str(e)[:900]), ephemeral=True)


class PortsView(RGNODESView):
    """Persistent port-forward control panel for one VPS."""
    def __init__(self, owner_id: str, container_name: str, node_id: int):
        super().__init__(timeout=300)
        self.owner_id = str(owner_id)
        self.container_name = str(container_name)
        self.node_id = int(node_id)
        self._rebuild_items()

    def _rebuild_items(self):
        self.clear_items()
        add_btn = discord.ui.Button(label="Add Port", emoji="➕", style=discord.ButtonStyle.secondary, row=0)
        add_btn.callback = self.add_port
        refresh_btn = discord.ui.Button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.secondary, row=0)
        refresh_btn.callback = self.refresh
        close_btn = discord.ui.Button(label="Close", emoji="❌", style=discord.ButtonStyle.secondary, row=0)
        close_btn.callback = self.close
        self.add_item(add_btn)
        self.add_item(refresh_btn)
        self.add_item(close_btn)

        forwards = [f for f in get_user_forwards(self.owner_id) if str(f.get("vps_container")) == self.container_name]
        if forwards:
            options = [
                discord.SelectOption(
                    label=f"Remove ID {f['id']}",
                    description=f"Host {f['host_port']} → VPS {f['vps_port']} TCP/UDP",
                    value=str(f["id"]),
                ) for f in forwards[:25]
            ]
            select = discord.ui.Select(placeholder="🗑️ Select a forward to remove", options=options, row=1)
            select.callback = self.remove
            self.add_item(select)

    def _embed(self):
        forwards = [f for f in get_user_forwards(self.owner_id) if str(f.get("vps_container")) == self.container_name]
        quota = get_user_allocation(self.owner_id)
        lines = [f"• `{f['id']}` → host `{f['host_port']}` ⇢ VPS `{f['vps_port']}` • TCP/UDP" for f in forwards]
        body = (
            f"**VPS:** `{self.container_name}`\n"
            f"**Usage:** `{len(forwards)}/{quota}`\n\n"
            + ("\n".join(lines) if lines else "None configured")
            + "\n\nHost ports are allocated automatically and persisted in the bot database."
        )
        return create_info_embed("🌐 Port Forwarding", body)

    async def add_port(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.owner_id and not is_admin_user(interaction.user):
            await interaction.response.send_message(embed=create_error_embed("Access Denied", "You do not own this VPS."), ephemeral=True)
            return
        await interaction.response.send_modal(PortAddModal(self.owner_id, self.container_name, self.node_id))

    async def remove(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.owner_id and not is_admin_user(interaction.user):
            await interaction.response.send_message(embed=create_error_embed("Access Denied", "You do not own this VPS."), ephemeral=True)
            return
        select = interaction.data.get("values", []) if isinstance(interaction.data, dict) else []
        if not select:
            await interaction.response.send_message(embed=create_error_embed("No Port Selected", "Select a forwarding rule first."), ephemeral=True)
            return
        try:
            fid = int(select[0])
        except ValueError:
            await interaction.response.send_message(embed=create_error_embed("Invalid Forward", "The selected forwarding rule is invalid."), ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        ok, owner = await remove_port_forward(fid, requester_id=str(interaction.user.id), is_admin=is_admin_user(interaction.user))
        await interaction.followup.send(
            embed=create_success_embed("🗑️ Port Removed", f"Forward ID `{fid}` was removed.") if ok else create_error_embed("Remove Failed", "That forward does not exist, is not yours, or could not be fully removed."),
            ephemeral=True,
        )
        await self.refresh(interaction, from_followup=True)

    async def refresh(self, interaction: discord.Interaction, from_followup: bool = False):
        self._rebuild_items()
        try:
            if not from_followup and not interaction.response.is_done():
                await interaction.response.edit_message(embed=self._embed(), view=self)
            elif interaction.message:
                await interaction.message.edit(embed=self._embed(), view=self)
        except Exception as e:
            logger.debug(f"Port view refresh failed: {e}")

    async def close(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.owner_id and not is_admin_user(interaction.user):
            await interaction.response.send_message(embed=create_error_embed("Access Denied", "You do not own this VPS."), ephemeral=True)
            return
        await interaction.response.edit_message(view=None)
        self.stop()

class ManageView(RGNODESView):
    """Primary owner/admin VPS dashboard with live state, access, ports and lifecycle controls."""
    def __init__(self, user_id, vps_list, is_shared=False, owner_id=None, is_admin=False, actual_index: Optional[int] = None):
        super().__init__(timeout=1800)
        self.user_id = str(user_id)
        self.vps_list = list(vps_list)
        self.selected_index = 0 if len(self.vps_list) == 1 else None
        self.is_shared = bool(is_shared)
        self.owner_id = str(owner_id or user_id)
        self.is_admin = bool(is_admin)
        self.actual_index = actual_index
        self.indices = list(range(len(self.vps_list)))
        if self.is_shared and self.actual_index is None:
            raise ValueError("actual_index required for shared views")

        if len(self.vps_list) > 1:
            options = []
            for i, vps in enumerate(self.vps_list):
                vmid = vps.get("vmid") or vps.get("id") or (i + 1)
                options.append(discord.SelectOption(
                    label=f"VPS #{vmid}",
                    description=f"{str(vps.get('os_version', 'Unknown'))[:70]} • {vps.get('ram', '?')} RAM",
                    value=str(i),
                ))
            self.select = discord.ui.Select(placeholder="🖥️ Select a VPS", options=options, row=0)
            self.select.callback = self.select_vps
            self.add_item(self.select)
            self.initial_embed = create_info_embed(
                "🖥️ RGNODES™ VPS Management",
                "Select a VPS from the menu below to open its live control panel.",
            )
        else:
            self.initial_embed = None
            self.add_action_buttons()

    async def get_initial_embed(self):
        if self.initial_embed is not None:
            return self.initial_embed
        return await self.create_vps_embed(self.selected_index)

    async def _pinggy_block(self, container_name: str, node_id: int) -> str:
        try:
            host, port, active = await asyncio.wait_for(
                get_pinggy_session_info(container_name, node_id), timeout=10
            )
        except Exception:
            host, port, active = None, None, False
        if host and port and active:
            command = f"ssh root@{host} -p {port}"
            return (
                f"Status: {resolve_custom_emoji('pinggy', '🟢')} Tunnel Active\n"
                f"SSH Command: `{command}`\n"
                f"Host: `{host}`\n"
                f"Port: `{port}`\n"
                f"Use {resolve_custom_emoji('refresh', '🔄')} **Reconnect Pinggy** if disconnected."
            )
        return (
            f"Status: {resolve_custom_emoji('pinggy_offline', '🟡')} Not Connected\n"
            f"Pinggy starts automatically after deployment. Use {resolve_custom_emoji('refresh', '🔄')} **Reconnect Pinggy** to create a fresh session."
        )

    async def create_vps_embed(self, index):
        if index is None or index < 0 or index >= len(self.vps_list):
            raise IndexError("Invalid VPS selection")
        vps = self.vps_list[index]
        node_id = int(vps.get("node_id", 1))
        node = get_node(node_id) or {}
        container_name = str(vps.get("container_name", "unknown"))

        try:
            stats = await asyncio.wait_for(get_container_stats(container_name, node_id), timeout=15)
        except Exception as e:
            logger.debug(f"Manage stats failed for {container_name}: {e}")
            stats = {"status": "unknown", "cpu": 0.0, "ram": {"used": 0, "total": 0, "pct": 0.0}, "disk": "N/A", "uptime": "N/A"}

        observed = str(stats.get("status") or "unknown").lower()
        if observed in {"running", "stopped", "frozen"}:
            vps["status"] = "running" if observed == "running" else "stopped"
        status = str(vps.get("status", observed)).lower()
        suspended = bool(vps.get("suspended", False))
        status_label = "SUSPENDED" if suspended else status.upper()
        viewer_under_maintenance = maintenance_applies_to_user(self.owner_id) and not self.is_admin
        status_emoji = resolve_custom_emoji("status", "🟢") if status == "running" and not suspended else (resolve_custom_emoji("warning", "🟡") if suspended else resolve_custom_emoji("error", "🔴"))
        if viewer_under_maintenance:
            status_label = "🔴 Under Maintenance\n🛠️ SOON for Fixing.."
            status_emoji = "🔴"
        vmid = int(vps.get("vmid") or vps.get("id") or (index + 1))

        forwards = [f for f in get_user_forwards(self.owner_id) if str(f.get("vps_container")) == container_name]
        port_used = len(forwards)
        port_quota = max(0, get_user_allocation(self.owner_id))
        slot_used = len(vps_data.get(self.owner_id, []))

        networks = {}
        addresses = {"ipv4": [], "ipv6": []}
        rx_text, tx_text = "N/A", "N/A"
        docker_text = "⚪ Offline"
        if status == "running":
            try:
                addresses = await asyncio.wait_for(get_container_addresses(container_name, node_id), timeout=10)
                networks = {f"iface{i}": ip for i, ip in enumerate(addresses.get("ipv4", []), 1)}
            except Exception:
                addresses = {"ipv4": [], "ipv6": []}
            try:
                rx_text, tx_text = await asyncio.wait_for(get_container_network_usage(container_name, node_id), timeout=10)
            except Exception:
                pass
            try:
                docker_text = await asyncio.wait_for(get_container_docker_status(container_name, node_id), timeout=8)
            except Exception:
                docker_text = "⚪ Unknown"

        ram = stats.get("ram") if isinstance(stats.get("ram"), dict) else {}
        plan_mb = _parse_gb(vps.get('ram', f'{DEFAULT_VPS_RAM_GB}GB'), DEFAULT_VPS_RAM_GB) * 1024
        memory_text = f"{ram.get('used', 0)} MB / {plan_mb} MB hard limit ({plan_mb/1024:.0f} GB plan)"
        cpu_value = stats.get("cpu")
        try:
            cpu_text = f"{float(cpu_value):.1f}%" if cpu_value is not None else "N/A"
        except Exception:
            cpu_text = "N/A"

        expiration_raw = vps.get("expiration_date")
        if expiration_raw:
            try:
                expiration_dt = datetime.fromisoformat(str(expiration_raw))
                seconds_left = (expiration_dt - datetime.now()).total_seconds()
                days_left = int(seconds_left // 86400)
                if seconds_left <= 0:
                    expiration_block = f"Status: 🔴 EXPIRED\nExpires: `{expiration_dt.strftime('%Y-%m-%d %H:%M:%S')}`\nDays Left: **0 days**"
                elif seconds_left <= RENEWAL_WINDOW_DAYS * 86400:
                    expiration_block = f"Status: 🟡 EXPIRING SOON\nExpires: `{expiration_dt.strftime('%Y-%m-%d %H:%M:%S')}`\nDays Left: **{max(0, days_left)} days**\n🔄 Renew opens now: `{PREFIX}renew {vmid}` (+{VPS_RENEWAL_DAYS} days)"
                else:
                    expiration_block = f"Status: 🟢 ACTIVE\nExpires: `{expiration_dt.strftime('%Y-%m-%d %H:%M:%S')}`\nDays Left: **{max(0, days_left)} days**"
            except Exception:
                expiration_block = "Status: ⚠️ INVALID DATE\nRenewal requires admin support."
        else:
            expiration_block = "Status: 🔵 NO EXPIRATION\nExpires: `Never`"

        sshx_url = vps.get("sshx_url")
        sshx_active = False
        if status == "running" and not suspended:
            try:
                current_url, sshx_active = await get_sshx_session_info(container_name, node_id)
                sshx_url = current_url or sshx_url
            except Exception:
                pass
        if sshx_url and sshx_active:
            sshx_block = f"Status: 🟢 Tunnel Active\nSSHX: <{sshx_url}>\nUse 🌐 **SSHX** to start a fresh session if needed."
        elif sshx_url:
            sshx_block = f"Status: 🟡 Disconnected\nLast session: <{sshx_url}>\nUse 🌐 **SSHX** to start a fresh session."
        else:
            sshx_block = "Status: ⚪ Not Connected\nUse 🌐 **SSHX** to start a session."

        pinggy_block = await self._pinggy_block(container_name, node_id) if PINGGY_ENABLED else "Status: ⚪ Disabled in configuration"

        node_text = f"{node.get('name', HOST_PROVIDER_NAME)} {location_flag(node.get('location', 'Unknown'))}"
        processor_text = HOST_PROCESSOR_NAME
        try:
            if node.get('is_local'):
                cpu_model = subprocess.check_output(['bash','-lc',"awk -F: '/^model name/{print $2; exit}' /proc/cpuinfo"], text=True, timeout=2).strip()
                if cpu_model:
                    processor_text = cpu_model
        except Exception:
            pass
        try:
            public_endpoints = await asyncio.wait_for(detect_public_endpoints(node_id), timeout=6)
        except Exception:
            public_endpoints = {"ipv4": "", "ipv6": ""}
        public_v4 = public_endpoints.get("ipv4") or "Unavailable"
        public_v6 = public_endpoints.get("ipv6") or "Unavailable"
        maintenance_banner = ""
        if viewer_under_maintenance:
            maintenance_banner = "🔴 **Under Maintenance**\n🛠️ **SOON for Fixing..**\n\n"
        description = (
            maintenance_banner +
            f"{status_emoji} **{status_label}** • **VMID: {vmid}**\n\n"
            f"📦 **Resources**\n"
            f"╭ **RAM:** {vps.get('ram', f'{DEFAULT_VPS_RAM_GB} GB')}\n"
            f"├ **CPU:** {vps.get('cpu', DEFAULT_VPS_CPU)} Core(s)\n"
            f"├ **SSD:** {vps.get('storage', f'{DEFAULT_VPS_STORAGE_GB} GB')}\n"
            f"├ **Bandwidth:** {int(vps.get('bandwidth_gb') or VPS_BANDWIDTH_GB)} GB\n"
            f"├ **OS:** {friendly_os_label(vps.get('os_version', 'Unknown'))}\n"
            f"╰ **Node:** {node_text}\n"
            f"🧠 **Processor:** {processor_text}\n\n"
            f"⚙️ **Configuration**\n"
            f"╭ **Slots:** {slot_used}/1 used\n"
            f"├ **Uptime:** {stats.get('uptime', 'N/A') or 'N/A'}\n"
            f"├ **Hostname:** `{VPS_HOSTNAME}`\n"
            f"├ **Guest IPv4:** {', '.join(addresses.get('ipv4') or []) or 'Not assigned'}\n"
            f"├ **Guest IPv6:** {', '.join(addresses.get('ipv6') or []) or 'Not assigned'}\n"
            f"├ **Public IPv4:** `{public_v4}`\n"
            f"├ **Public IPv6:** `{public_v6}`\n"
            f"╰ **Docker:** {docker_text}\n\n"
            f"📈 **Live Stats**\n"
            f"💻 **CPU:** {cpu_text} used / {vps.get('cpu', DEFAULT_VPS_CPU)} limit\n"
            f"🧠 **Memory:** {memory_text}\n"
            f"💾 **Disk:** {stats.get('disk', 'N/A')} • Plan {vps.get('storage', f'{DEFAULT_VPS_STORAGE_GB} GB')}\n"
            f"🌐 **Network:** RX {rx_text} • TX {tx_text}\n\n"
            f"⏰ **Expiration**\n{expiration_block}\n\n"
            f"🌐 **SSHX Tunnel**\n{sshx_block}\n\n"
            f"🌐 **Pinggy SSH Tunnel**\n{pinggy_block}\n\n"
            f"🌐 **Public Access**\n├ IPv4: `{public_v4}`\n╰ IPv6: `{public_v6}`\n\n"
            f"🌐 **Port Forwarding • {port_used}/{port_quota}**\n{self._port_summary(forwards)}\n\n"
            f"🎮 **Action**\nUse the buttons below to control your VPS."
        )
        return create_embed(f"{resolve_custom_emoji('vps', '🖥️')} VPS #{vmid}", description)

    @staticmethod
    def _ssh_host_port(container_name, forwards):
        for fwd in forwards:
            try:
                if int(fwd.get("vps_port")) == 22:
                    return int(fwd.get("host_port"))
            except Exception:
                continue
        return None

    @staticmethod
    def _port_summary(forwards):
        if not forwards:
            return "None configured"
        lines = [f"• ID `{f['id']}` → `{f['host_port']}` ⇢ VPS `{f['vps_port']}` TCP/UDP" for f in forwards[:8]]
        if len(forwards) > 8:
            lines.append(f"• +{len(forwards) - 8} more")
        return "\n".join(lines)

    async def _refresh_dashboard(self, interaction: discord.Interaction):
        try:
            if interaction.message:
                await interaction.message.edit(embed=await self.create_vps_embed(self.selected_index), view=self)
        except Exception as e:
            logger.debug(f"Dashboard refresh failed: {e}")

    def add_action_buttons(self):
        user_maintenance = maintenance_applies_to_user(self.owner_id) and not self.is_admin

        def add(label, key, fallback, style, action, row, maintenance_allowed=False):
            btn = discord.ui.Button(
                label=label,
                emoji=resolve_custom_emoji(key, fallback),
                style=style,
                row=row,
                disabled=(user_maintenance and not maintenance_allowed),
            )
            async def _callback(inter: discord.Interaction, a=action):
                await self.action_callback(inter, a)
            btn.callback = _callback
            self.add_item(btn)

        add("Start", "start", "▶️", discord.ButtonStyle.secondary, "start", 0)
        add("Stop", "stop", "⏸️", discord.ButtonStyle.secondary, "stop", 0)
        add("Stats", "stats", "📊", discord.ButtonStyle.secondary, "stats", 0, True)
        add("Reset Password", "password", resolve_custom_emoji("password", "🔐"), discord.ButtonStyle.secondary, "regen_password", 1)
        add("SSHX", "sshx", resolve_custom_emoji("sshx", "🌐"), discord.ButtonStyle.secondary, "sshx", 1)
        add("SSH", "ssh", resolve_custom_emoji("ssh", "💻"), discord.ButtonStyle.secondary, "ssh", 2)
        add("Reconnect Pinggy", "refresh", resolve_custom_emoji("refresh", "🔄"), discord.ButtonStyle.secondary, "reconnect_pinggy", 2)
        add("Ports", "ports", resolve_custom_emoji("ports", "🔌"), discord.ButtonStyle.secondary, "ports", 3)
        add("Renew", "renew", resolve_custom_emoji("renew", "⏰"), discord.ButtonStyle.secondary, "renew", 3, True)
        if not self.is_shared:
            add("Reinstall", "reinstall", "♻️", discord.ButtonStyle.secondary, "reinstall", 4)
        if not self.is_shared and not self.is_admin:
            add("Delete", "delete", "🗑️", discord.ButtonStyle.secondary, "delete", 4)

    async def select_vps(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id and not self.is_admin:
            await interaction.response.send_message(embed=create_error_embed("Access Denied", "This VPS selector belongs to another user."), ephemeral=True)
            return
        try:
            self.selected_index = int(self.select.values[0])
            self.clear_items()
            self.add_action_buttons()
            await interaction.response.defer()
            embed = await self.create_vps_embed(self.selected_index)
            await interaction.edit_original_response(embed=embed, view=self)
        except Exception as e:
            logger.error(f"VPS selector failed: {e}", exc_info=True)
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=create_error_embed("⚠️ Selection Failed", "The live VPS panel could not be loaded. Please try again."), ephemeral=True)
                else:
                    await interaction.followup.send(embed=create_error_embed("⚠️ Selection Failed", "The live VPS panel could not be loaded. Please try again."), ephemeral=True)
            except Exception:
                pass

    async def action_callback(self, interaction: discord.Interaction, action: str):
        try:
            if str(interaction.user.id) != self.user_id and not self.is_admin:
                await interaction.response.send_message(embed=create_error_embed("Access Denied", "This is not your VPS."), ephemeral=True)
                return
            if self.selected_index is None:
                await interaction.response.send_message(embed=create_error_embed("No VPS Selected", "Please select a VPS first."), ephemeral=True)
                return
            actual_idx = self.actual_index if self.is_shared else self.indices[self.selected_index]
            owner_items = vps_data.get(str(self.owner_id), [])
            if actual_idx is None or actual_idx >= len(owner_items):
                await interaction.response.send_message(embed=create_error_embed("VPS Not Found", "This VPS record is no longer available. Reopen the dashboard."), ephemeral=True)
                return
            target_vps = owner_items[actual_idx]
            container_name = str(target_vps["container_name"])
            node_id = int(target_vps.get("node_id", 1))
            suspended = bool(target_vps.get("suspended", False))

            if maintenance_applies_to_user(self.owner_id) and not self.is_admin and action not in {"stats", "renew"}:
                await interaction.response.send_message(embed=create_warning_embed("🔧 Maintenance Mode", "VPS control actions are temporarily disabled."), ephemeral=True)
                return
            if suspended and not self.is_admin and action not in {"stats", "renew"}:
                await interaction.response.send_message(embed=create_error_embed("⛔ VPS Suspended", "This VPS is suspended. Use Renew if it expired, or contact support."), ephemeral=True)
                return

            await interaction.response.defer()
            # Record dashboard actions with their real VPS/node context so the configured log channel
            # shows user-facing VPS operations as well as command completions.
            await record_audit_event(
                "vps",
                f"VPS Action • {str(action).replace('_', ' ').title()} Started",
                f"Dashboard action requested by <@{interaction.user.id}>.",
                user_id=interaction.user.id,
                node_id=node_id,
                vps_container=container_name,
            )

            if action == "stats":
                stats = await get_container_stats(container_name, node_id)
                rx, tx = await get_container_network_usage(container_name, node_id) if str(stats.get("status")) == "running" else ("N/A", "N/A")
                ram = stats.get("ram", {}) if isinstance(stats.get("ram"), dict) else {}
                e = create_info_embed("📈 Live VPS Statistics", f"`{container_name}` • VMID `{target_vps.get('vmid') or target_vps.get('id')}`")
                add_field(e, "🟢 Status", str(stats.get("status", "unknown")).upper(), True)
                add_field(e, "💻 CPU", f"{float(stats.get('cpu', 0)):.1f}% / {target_vps.get('cpu', DEFAULT_VPS_CPU)} cores", True)
                plan_mb = _parse_gb(target_vps.get("ram", "0GB"), DEFAULT_VPS_RAM_GB) * 1024
                add_field(e, "🧠 Memory", f"{ram.get('used', 0)} MB used / {plan_mb} MB limit", True)
                add_field(e, "💾 Disk", str(stats.get("disk", "N/A")), True)
                add_field(e, "🌐 Network", f"RX {rx} • TX {tx}", True)
                add_field(e, "⏱️ Uptime", str(stats.get("uptime", "N/A")), False)
                await interaction.followup.send(embed=e, ephemeral=True)
                await self._refresh_dashboard(interaction)
                return

            if action == "renew":
                ok, message = await process_vps_renewal(target_vps, VPS_RENEWAL_DAYS, user_initiated=not self.is_admin)
                await interaction.followup.send(embed=create_success_embed("⏰ VPS Renewed", message) if ok else create_warning_embed("⏰ Renewal Unavailable", message), ephemeral=True)
                if ok:
                    try:
                        owner = await bot.fetch_user(int(self.owner_id))
                        await owner.send(embed=create_success_embed("⏰ VPS Renewed!", f"Your VPS `{container_name}` has been extended by **{VPS_RENEWAL_DAYS} days**.\n\n{message}"))
                    except Exception:
                        pass
                await self._refresh_dashboard(interaction)
                return

            if action == "reconnect_pinggy":
                if suspended:
                    await interaction.followup.send(embed=create_error_embed("⛔ Access Denied", "Cannot access a suspended VPS."), ephemeral=True)
                    return
                try:
                    current = await get_container_stats(container_name, node_id)
                    runtime_status = str(current.get("status") or "unknown").lower()
                    recorded_status = str(target_vps.get("status") or "unknown").lower()
                    if runtime_status not in {"running", "unknown"} and recorded_status != "running":
                        await interaction.followup.send(embed=create_warning_embed("VPS Not Running", "Start the VPS before opening Pinggy."), ephemeral=True)
                        return
                    info = await asyncio.wait_for(start_pinggy_session(container_name, node_id), timeout=100)
                    if not info:
                        raise RuntimeError("Pinggy did not return a public tunnel endpoint. Try Reconnect Pinggy again.")
                    access = create_info_embed("🌐 RGNODES™ Pinggy SSH Tunnel", f"`{container_name}` • `{VPS_HOSTNAME}`")
                    add_field(access, "🌐 Pinggy SSH Tunnel", f"**SSH Command:** `ssh root@{info['host']} -p {info['port']}`\n**Host:** `{info['host']}`\n**Port:** `{info['port']}`\n**Status:** 🟢 Tunnel Active", False)
                    add_field(access, "🔗 Separation", "Pinggy is independent from normal SSH and SSHX. This action creates Pinggy only.", False)
                    add_field(access, "⚠️ Free Tunnel", "Pinggy free tunnels are temporary and reconnecting can create a new public endpoint.", False)
                    try:
                        owner = await bot.fetch_user(int(self.owner_id))
                        await owner.send(embed=access)
                        await interaction.followup.send(embed=create_success_embed("📨 Pinggy Sent", "Pinggy-only access details were sent to your DM."), ephemeral=True)
                    except discord.Forbidden:
                        await interaction.followup.send(embed=access, ephemeral=True)
                except Exception as e:
                    await interaction.followup.send(embed=create_error_embed("🌐 Pinggy Failed", str(e)[:900]), ephemeral=True)
                await self._refresh_dashboard(interaction)
                return

            if action in {"ssh", "sshx"}:
                if suspended:
                    await interaction.followup.send(embed=create_error_embed("⛔ Access Denied", "Cannot access a suspended VPS."), ephemeral=True)
                    return
                try:
                    current = await get_container_stats(container_name, node_id)
                    runtime_status = str(current.get("status") or "unknown").lower()
                    recorded_status = str(target_vps.get("status") or "unknown").lower()
                    if runtime_status not in {"running", "unknown"} and recorded_status != "running":
                        await interaction.followup.send(embed=create_warning_embed("VPS Not Running", "Start the VPS before opening SSH/SSHX."), ephemeral=True)
                        return
                    if action == "sshx":
                        sshx_url = await start_sshx_session(container_name, node_id)
                        access = create_info_embed("🌐 RGNODES™ SSHX", f"`{container_name}` • `{VPS_HOSTNAME}`")
                        if not sshx_url:
                            add_field(access, "🌐 SSHX", "🔴 Session URL was not generated. SSH/Pinggy remain independent and available.", False)
                            if self.is_admin:
                                diag = await get_sshx_diagnostics(container_name, node_id)
                                add_field(access, "🧪 Admin Diagnostics", f"```text\n{diag[-1800:]}\n```", False)
                            await interaction.followup.send(
                                embed=create_error_embed(
                                    "🌐 SSHX Unavailable",
                                    "SSHX could not establish a session URL. The supervisor has been left in automatic retry mode."
                                ),
                                ephemeral=True,
                            )
                            await record_audit_event("error", "SSHX Unavailable", "Dashboard SSHX session URL was not produced; supervisor remains in retry mode.", user_id=interaction.user.id, node_id=node_id, vps_container=container_name)
                            await self._refresh_dashboard(interaction)
                            return
                        add_field(access, "🌐 SSHX", f"<{sshx_url}>\n🟢 Tunnel Active", False)
                        try:
                            owner = await bot.fetch_user(int(self.owner_id))
                            await owner.send(embed=access)
                            await interaction.followup.send(embed=create_success_embed("✅ SSHX Sent", "SSHX access was sent to your DM."), ephemeral=True)
                        except discord.Forbidden:
                            await interaction.followup.send(embed=access, ephemeral=True)
                        await self._refresh_dashboard(interaction)
                        return

                    # SSH action intentionally does NOT start SSHX.
                    forwards = get_user_forwards(self.owner_id)
                    ssh_port = self._ssh_host_port(container_name, forwards)
                    if not ssh_port:
                        ssh_port = await create_port_forward(self.owner_id, container_name, 22, node_id)
                    endpoints = await detect_public_endpoints(node_id)
                    ssh_v4 = endpoints.get('ipv4') or ''
                    ssh_v6 = endpoints.get('ipv6') or ''
                    access = create_info_embed("💻 RGNODES™ SSH", f"`{container_name}` • `{VPS_HOSTNAME}`")
                    if ssh_port and ssh_v4:
                        add_field(access, "💻 SSH IPv4", f"```bash\nssh root@{ssh_v4} -p {ssh_port}\n```", False)
                    elif ssh_port:
                        add_field(access, "💻 SSH IPv4", "🟡 Public IPv4 unavailable. Configure `PUBLIC_IPV4`.", False)
                    if ssh_v6:
                        add_field(access, "🌐 SSH IPv6", f"```bash\nssh -6 root@[{ssh_v6}] -p {ssh_port}\n```", False)
                    else:
                        add_field(access, "🌐 SSH IPv6", "⚪ Public IPv6 unavailable on this node.", False)
                    add_field(access, "🔐 Credentials", f"Username: `root`\nPassword: `{target_vps.get('root_password') or 'not available'}`", False)
                    try:
                        owner = await bot.fetch_user(int(self.owner_id))
                        await owner.send(embed=access)
                        await interaction.followup.send(embed=create_success_embed("✅ SSH Sent", "SSH access details were sent to your DM."), ephemeral=True)
                    except discord.Forbidden:
                        await interaction.followup.send(embed=access, ephemeral=True)
                except Exception as e:
                    await interaction.followup.send(embed=create_error_embed("SSH Error", str(e)[:800]), ephemeral=True)
                await self._refresh_dashboard(interaction)
                return

            if action == "ports":
                forwards = get_user_forwards(self.owner_id)
                e = create_info_embed("🌐 Port Forwarding", f"**VPS:** `{container_name}`\n**Usage:** {len([f for f in forwards if str(f.get('vps_container')) == container_name])}/{get_user_allocation(self.owner_id)}")
                add_field(e, "Current Forwards", self._port_summary([f for f in forwards if str(f.get('vps_container')) == container_name]), False)
                await interaction.followup.send(embed=e, view=PortsView(self.owner_id, container_name, node_id), ephemeral=True)
                return

            if action == "regen_password":
                if suspended and not self.is_admin:
                    await interaction.followup.send(embed=create_error_embed("⛔ Access Denied", "Cannot reset a suspended VPS password."), ephemeral=True)
                    return
                new_password = generate_strong_password()
                success, result = await configure_ssh(container_name, node_id, new_password)
                if not success:
                    await interaction.followup.send(embed=create_error_embed("🔐 Password Reset Failed", str(result)[:900]), ephemeral=True)
                    return
                target_vps["root_password"] = new_password
                save_vps_data_immediate()
                e = create_success_embed("🔐 Password Reset", f"A new root password was generated for `{container_name}`.")
                add_field(e, "New Password", f"`{new_password}`\n🔒 Save this password securely.", False)
                await interaction.followup.send(embed=e, ephemeral=True)
                try:
                    owner = await bot.fetch_user(int(self.owner_id))
                    dm = create_success_embed("🔐 VPS Password Reset", f"Your VPS `{container_name}` has a new root password.")
                    add_field(dm, "Password", f"`{new_password}`\n🔒 Save this password securely.", False)
                    await owner.send(embed=dm)
                except Exception:
                    pass
                await self._refresh_dashboard(interaction)
                return

            if action == "reinstall":
                if self.is_shared:
                    await interaction.followup.send(embed=create_error_embed("Access Denied", "Reinstall is unavailable from a shared VPS view. Use the owner/admin management view."), ephemeral=True)
                    return
                if suspended:
                    await interaction.followup.send(embed=create_error_embed("⛔ Cannot Reinstall", "Unsuspend the VPS first."), ephemeral=True)
                    return
                try:
                    ram_gb = int(str(target_vps.get("ram", DEFAULT_VPS_RAM_GB)).lower().replace("gb", "").strip())
                    cpu = int(target_vps.get("cpu", DEFAULT_VPS_CPU))
                    storage_gb = int(str(target_vps.get("storage", DEFAULT_VPS_STORAGE_GB)).lower().replace("gb", "").strip())
                except Exception:
                    await interaction.followup.send(embed=create_error_embed("Invalid VPS Configuration", "The saved resource values are invalid. Contact support."), ephemeral=True)
                    return
                confirm_embed = create_warning_embed(
                    "⚠️ Reinstall VPS",
                    f"This will replace the OS on `{container_name}`. User data on the current OS will be erased.\n\n"
                    "The replacement is built and validated before the old container is removed, and persistent port rules are retained."
                )
                class ConfirmView(discord.ui.View):
                    def __init__(self, parent):
                        super().__init__(timeout=60)
                        self.parent = parent
                        self.owner_id = str(parent.owner_id)
                    @discord.ui.button(label="✅ Continue", style=discord.ButtonStyle.danger)
                    async def confirm(self, inter: discord.Interaction, button: discord.ui.Button):
                        if str(inter.user.id) != self.parent.user_id:
                            await inter.response.send_message(embed=create_error_embed("Access Denied", "Only the VPS owner can confirm."), ephemeral=True)
                            return
                        await inter.response.send_message(embed=create_info_embed("💿 Select OS", "Choose the new operating system. The old VPS is not deleted until the OS is selected."), view=ReinstallOSSelectView(self.parent, container_name, self.owner_id, actual_idx, ram_gb, cpu, storage_gb, node_id), ephemeral=True)
                        self.stop()
                    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
                    async def cancel(self, inter: discord.Interaction, button: discord.ui.Button):
                        if str(inter.user.id) != self.parent.user_id:
                            await inter.response.send_message(embed=create_error_embed("Access Denied", "Only the VPS owner can cancel."), ephemeral=True)
                            return
                        await inter.response.edit_message(content=None, embed=await self.parent.create_vps_embed(self.parent.selected_index), view=self.parent)
                        self.stop()
                await interaction.followup.send(embed=confirm_embed, view=ConfirmView(self), ephemeral=True)
                return

            if action == "start":
                if suspended:
                    await interaction.followup.send(embed=create_error_embed("⛔ VPS Suspended", "Use Renew for expiration suspension or ask an admin to unsuspend it."), ephemeral=True)
                    return
                try:
                    start_ram=_parse_gb(target_vps.get('ram', f'{DEFAULT_VPS_RAM_GB}GB'), DEFAULT_VPS_RAM_GB)
                    start_cpu=_parse_cpu(target_vps.get('cpu', DEFAULT_VPS_CPU), DEFAULT_VPS_CPU)
                    safe_start, start_reason = await check_node_capacity_for_start(node_id, container_name, start_ram, start_cpu)
                    if not safe_start:
                        await interaction.followup.send(embed=create_error_embed("🛡️ Start Blocked", start_reason), ephemeral=True)
                        return
                    await execute_lxc(container_name, f"start {container_name}", timeout=180, node_id=node_id)
                except Exception as e:
                    msg = str(e).lower()
                    if "already running" not in msg and "is running" not in msg:
                        raise
                target_vps["status"] = "running"
                save_vps_data_immediate()
                try:
                    ram_mb_now = int(str(target_vps.get("ram", DEFAULT_VPS_RAM_GB)).lower().replace("gb", "").strip()) * 1024
                    await apply_vps_performance_profile(container_name, node_id, ram_mb_now, int(target_vps.get("cpu", DEFAULT_VPS_CPU)))
                except Exception as perf_error:
                    logger.debug(f"Performance profile refresh skipped for {container_name}: {perf_error}")
                await apply_internal_permissions(container_name, node_id)
                await install_anti_mining_guard(container_name, node_id)
                await apply_guest_motd(container_name, node_id)
                if DOCKER_INSTALL_ON_DEPLOY:
                    await ensure_docker_ready(container_name, node_id, strict=False)
                readded = await recreate_port_forwards(container_name)
                if not any(int(f.get("vps_port", 0)) == 22 for f in get_user_forwards(self.owner_id) if str(f.get("vps_container")) == container_name):
                    await create_port_forward(self.owner_id, container_name, 22, node_id)
                await interaction.followup.send(embed=create_success_embed("▶️ VPS Started", f"`{container_name}` is running.\n🔌 Restored **{readded}** port forwards."), ephemeral=True)
                await record_audit_event("vps", "VPS Started", f"Restored `{readded}` port forwards.", user_id=interaction.user.id, node_id=node_id, vps_container=container_name)
                await self._refresh_dashboard(interaction)
                return

            if action == "stop":
                try:
                    await execute_lxc(container_name, f"stop {container_name} --force", timeout=180, node_id=node_id)
                except Exception as e:
                    msg = str(e).lower()
                    if not any(x in msg for x in ("not running", "already stopped", "is stopped")):
                        raise
                target_vps["status"] = "stopped"
                save_vps_data_immediate()
                await interaction.followup.send(embed=create_success_embed("⏸️ VPS Stopped", f"`{container_name}` is stopped."), ephemeral=True)
                await record_audit_event("vps", "VPS Stopped", "Dashboard stop completed.", user_id=interaction.user.id, node_id=node_id, vps_container=container_name)
                await self._refresh_dashboard(interaction)
                return

            if action == "delete":
                if self.is_shared or self.is_admin:
                    await interaction.followup.send(embed=create_error_embed("Access Denied", "Delete from this dashboard is owner-only."), ephemeral=True)
                    return
                class DeleteConfirm(discord.ui.View):
                    def __init__(self, parent):
                        super().__init__(timeout=45)
                        self.parent = parent
                        self.confirmed = False
                    @discord.ui.button(label="🗑️ Delete VPS", style=discord.ButtonStyle.danger)
                    async def confirm(self, inter: discord.Interaction, button: discord.ui.Button):
                        if str(inter.user.id) != self.parent.user_id:
                            await inter.response.send_message(embed=create_error_embed("Access Denied", "Only the owner can delete this VPS."), ephemeral=True)
                            return
                        self.confirmed = True
                        await inter.response.defer()
                        self.stop()
                    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
                    async def cancel(self, inter: discord.Interaction, button: discord.ui.Button):
                        if str(inter.user.id) != self.parent.user_id:
                            await inter.response.send_message(embed=create_error_embed("Access Denied", "Only the owner can cancel."), ephemeral=True)
                            return
                        await inter.response.edit_message(embed=await self.parent.create_vps_embed(self.parent.selected_index), view=self.parent)
                        self.stop()
                confirm = DeleteConfirm(self)
                await interaction.followup.send(embed=create_warning_embed("⚠️ Delete VPS", f"Permanently delete `{container_name}` and its forwarding rules? **This cannot be undone.**"), view=confirm, ephemeral=True)
                await confirm.wait()
                if not confirm.confirmed:
                    return
                try:
                    backup_database()
                    await execute_lxc(container_name, f"delete {container_name} --force", timeout=300, node_id=node_id)
                    with DB_LOCK:
                        conn = get_db()
                        try:
                            conn.execute("DELETE FROM port_forwards WHERE vps_container = ?", (container_name,))
                            conn.execute("DELETE FROM vps WHERE container_name = ?", (container_name,))
                            conn.commit()
                        finally:
                            conn.close()
                    owner_list = [v for v in vps_data.get(self.owner_id, []) if str(v.get("container_name")) != container_name]
                    if owner_list:
                        vps_data[self.owner_id] = owner_list
                    else:
                        vps_data.pop(self.owner_id, None)
                    save_vps_data_immediate()
                    await interaction.followup.send(embed=create_success_embed("🗑️ VPS Deleted", f"`{container_name}` has been deleted."), ephemeral=True)
                    await record_audit_event("vps", "VPS Deleted", "Dashboard deletion completed.", user_id=interaction.user.id, node_id=node_id, vps_container=container_name)
                    try:
                        await interaction.message.edit(embed=create_info_embed("🗑️ VPS Deleted", "This VPS no longer exists."), view=None)
                    except Exception:
                        pass
                except Exception as e:
                    await interaction.followup.send(embed=create_error_embed("❌ Delete Failed", str(e)[:1000]), ephemeral=True)
                return

            await interaction.followup.send(embed=create_error_embed("Unknown Action", f"Unsupported dashboard action: `{action}`"), ephemeral=True)
        except Exception as e:
            error_id = secrets.token_hex(4).upper()
            logger.error(f"Manage action {action} failed for VPS: {container_name if 'container_name' in locals() else 'unknown'} [{error_id}]: {e}", exc_info=True)
            safe_message = "The requested action could not be completed. The operation was stopped safely and logged."
            detail = str(e).strip()
            if self.is_admin and detail:
                safe_message += f"\n\n**Debug:** `{detail[:700]}`\n**Error ID:** `{error_id}`"
            else:
                safe_message += f"\n**Error ID:** `{error_id}`"
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=create_error_embed("⚠️ Action Failed", safe_message), ephemeral=True)
                else:
                    await interaction.followup.send(embed=create_error_embed("⚠️ Action Failed", safe_message), ephemeral=True)
            except Exception:
                try:
                    await interaction.followup.send(embed=create_error_embed("⚠️ Action Failed", safe_message), ephemeral=True)
                except Exception:
                    pass

@bot.command(name='manage')
async def manage_vps(ctx, user: discord.Member = None):
    if user:
        if not is_admin_user(ctx.author):
            await ctx.send(embed=create_error_embed("Access Denied", "Only admins can manage other users' VPS."))
            return
        user_id = str(user.id)
        vps_list = vps_data.get(user_id, [])
        if not vps_list:
            await ctx.send(embed=create_error_embed("No VPS Found", f"{user.mention} doesn't have any {BOT_NAME} VPS."))
            return
        view = ManageView(str(ctx.author.id), vps_list, is_admin=True, owner_id=user_id)
        await ctx.send(embed=create_info_embed(f"Managing {user.name}'s VPS", f"Managing VPS for {user.mention}"), view=view)
    else:
        user_id = str(ctx.author.id)
        vps_list = vps_data.get(user_id, [])
        if not vps_list:
            embed = create_error_embed("No VPS Found", f"You don't have any {BOT_NAME} VPS. Contact an admin to create one.")
            add_field(embed, "Quick Actions", f"• `{PREFIX}manage` - Manage VPS\n• Contact admin for VPS creation", False)
            await ctx.send(embed=embed)
            return
        view = ManageView(user_id, vps_list, is_admin=is_admin_user(ctx.author))
        embed = await view.get_initial_embed()
        await ctx.send(embed=embed, view=view)

async def get_node_status(node_id: int) -> str:
    node = get_node(node_id)
    if not node:
        return "❓ Unknown"
    if node['is_local']:
        return "🟢 Online (Local)"
    # Remote nodes - check connectivity but don't spam errors
    try:
        response = await asyncio.to_thread(requests.get, str(node['url']).rstrip('/') + '/api/ping', headers={'X-API-Key': str(node['api_key'])}, timeout=5)
        if response.status_code == 200:
            return "🟢 Online"
        else:
            return "🔴 Offline (Network unreachable)"
    except requests.exceptions.ConnectionError:
        return "🔴 Unreachable (Network issue)"
    except requests.exceptions.Timeout:
        return "🔴 No response"
    except Exception:
        return "🔴 Offline"


def get_host_disk_usage():
    """Get host disk usage - cross-platform compatible"""
    try:
        import platform
        system = platform.system()
        
        if system == "Windows":
            # Windows: Use wmic or psutil
            try:
                import psutil
                disk = psutil.disk_usage('/')
                return f"{disk.used // (1024**3)} GB / {disk.total // (1024**3)} GB ({disk.percent}%)"
            except ImportError:
                # Fallback for Windows without psutil
                try:
                    result = subprocess.run(['wmic', 'LogicalDisk', 'get', 'Size,FreeSpace'], 
                                          capture_output=True, text=True, timeout=5)
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        values = lines[1].split()
                        if len(values) >= 2:
                            size = int(values[0]) // (1024**3)
                            free = int(values[1]) // (1024**3)
                            used = size - free
                            percent = (used / size * 100) if size > 0 else 0
                            return f"{used} GB / {size} GB ({percent:.0f}%)"
                except:
                    pass
                return "Unknown"
        else:
            # Linux/Unix: Use df command
            result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=10)
            lines = result.stdout.splitlines()
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 5:
                    used = parts[2]
                    size = parts[1]
                    perc = parts[4]
                    return f"{used}/{size} ({perc})"
            return "Unknown"
    except Exception as e:
        logger.debug(f"Error getting disk usage: {e}")
        return "Unknown"




@bot.command(name='vps-list')
@is_admin()
async def vps_list(ctx, node_id: int = 1):
    node = get_node(node_id)
    if not node:
        await ctx.send(embed=create_error_embed("Node Not Found", f"Node ID {node_id} not found."))
        return

    # Get node status
    status = await get_node_status(node_id)
    is_online = status.startswith("🟢")

    # Get node resource stats (will use defaults if offline)
    stats = await get_host_stats(node_id)
    cpu_usage = stats.get('cpu', 0.0)
    ram_usage = stats.get('ram', 0.0)
    disk_usage = stats.get('disk', 'Unknown')

    # Resources field text (modern: compact inline stats with progress-like emojis)
    if is_online:
        resources_text = (
            f"**CPU** {cpu_usage:.0f}% {'█' * int(cpu_usage / 5) + '░' * (20 - int(cpu_usage / 5))} "
            f"\n**RAM** {ram_usage:.0f}% {'█' * int(ram_usage / 5) + '░' * (20 - int(ram_usage / 5))} "
            f"\n**Disk** {disk_usage}"
        )
    else:
        resources_text = "⚠️ Resources unavailable (Offline)"

    # Get VPS capacity
    current_vps = get_current_vps_count(node_id)
    total_capacity = node['total_vps']
    capacity_percent = (current_vps / total_capacity * 100) if total_capacity > 0 else 0
    capacity_text = f"{current_vps}/{total_capacity} ({capacity_percent:.0f}%)"

    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM vps WHERE node_id = ?', (node_id,))
    rows = cur.fetchall()
    conn.close()

    total_vps = len(rows)

    # Modern counters: use more intuitive emojis and clean layout
    running = 0
    stopped = 0
    suspended = 0
    other = 0
    vps_info = []
    for i, row in enumerate(rows, 1):
        vps = dict(row)
        user_id = vps['user_id']
        try:
            user = await bot.fetch_user(int(user_id))
            username = user.name
        except:
            username = f"Unknown ({user_id})"

        status = vps.get('status', 'unknown')
        suspended_flag = vps.get('suspended', False)

        # Count logic: suspended first, then status if not suspended
        if suspended_flag:
            suspended += 1
        elif status == 'running':
            running += 1
        elif status == 'stopped':
            stopped += 1
        else:
            other += 1

        # Modern emoji: vibrant and status-specific
        status_emoji = "🟢" if status == 'running' and not suspended_flag else "🟡" if suspended_flag else "🔴"
        vps_status = status.upper()
        if suspended_flag:
            vps_status += " (SUSPENDED)"
        if vps.get('whitelisted', False):
            vps_status += " (WHITELISTED)"
        config = vps.get('config', 'Custom')
        
        # Add expiration info
        expiration_info = ""
        if vps.get('expiration_date'):
            expiration_dt = datetime.fromisoformat(vps['expiration_date'])
            days_remaining = (expiration_dt - datetime.now()).days
            if days_remaining < 0:
                expiration_info = " | 🔴 EXPIRED"
            elif days_remaining <= EXPIRATION_WARNING_DAYS:
                expiration_info = f" | 🟡 EXPIRES({days_remaining}d)"
            else:
                expiration_info = f" | 🟢 ({days_remaining}d)"
        else:
            expiration_info = " | ⏰ No exp"
        
        vps_info.append(f"{status_emoji} **{i}.** {username} • `{vps['container_name']}`\n _{vps_status} | {config}{expiration_info}_")

    # Create main embed (modern: gradient-inspired colors, clean typography)
    embed = create_embed(
        title=f"🖥️ VPS Dashboard - {node['name']}",
        description=f"**ID:** `{node_id}` | **Region:** {node['location']}\n*Updated: <t:{int(datetime.now().timestamp())}:R>*"
    )
    embed.set_thumbnail(url=node.get('thumbnail_url', None))

    # Inline status and capacity for compact top row
    add_field(embed, "📡 **Status**", status, True)
    add_field(embed, "🗄️ **Capacity**", capacity_text, True)

    # Resources field with modern bar visualization
    add_field(embed, "📊 **Resources**", resources_text, False)

    # Summary field (modern: compact bullet-like with inline emojis)
    summary_text = (
        f"**Total:** {total_vps} 📊\n"
        f"**Running:** {running} 🟢\n"
        f"**Stopped:** {stopped} ⏸️\n"
        f"**Suspended:** {suspended} 🟡"
    )
    if other > 0:
        summary_text += f"\n**Other:** {other} ⚠️"
    add_field(embed, "📈 **Summary**", summary_text, True)

    # VPS List - chunked embeds with modern pagination
    if vps_info:
        chunk_size = 6  # Smaller chunks for cleaner mobile-friendly embeds
        chunks = [vps_info[i:i + chunk_size] for i in range(0, len(vps_info), chunk_size)]
        first_chunk_text = "\n".join(chunks[0])
        add_field(embed, "📋 **Active VPS (1/{len(chunks)})**", f"```{first_chunk_text}```", False)

        # Paginated follow-ups with consistent styling
        for idx, chunk in enumerate(chunks[1:], 2):
            page_embed = create_embed(
                title=f"🖥️ VPS Dashboard - {node['name']} (Page {idx}/{len(chunks)})",
                description=f"**ID:** `{node_id}` | **Region:** {node['location']}\n*Updated: <t:{int(datetime.now().timestamp())}:R>*"
            )
            chunk_text = "\n".join(chunk)
            add_field(page_embed, "📋 **VPS List**", f"```{chunk_text}```", False)
            page_embed.set_footer(text=f"⚡ RGNODES™ • {len(vps_info)} VPS shown")
            await ctx.send(embed=page_embed)
    else:
        add_field(embed, "📋 **VPS List**", "No deployments yet. Launch one! 🚀", False)

    embed.set_footer(text=f"⚡ RGNODES™ • Total: {len(vps_info)} VPS")
    await ctx.send(embed=embed)

@bot.command(name='list-all')
@is_admin()
async def list_all_vps(ctx):
    total_vps = 0
    total_users = len(vps_data)
    running_vps = 0
    stopped_vps = 0
    suspended_vps = 0
    whitelisted_vps = 0
    vps_info = []
    user_summary = []
    for user_id, vps_list in vps_data.items():
        try:
            user = await bot.fetch_user(int(user_id))
            user_vps_count = len(vps_list)
            user_running = sum(1 for vps in vps_list if vps.get('status') == 'running' and not vps.get('suspended', False))
            user_stopped = sum(1 for vps in vps_list if vps.get('status') == 'stopped')
            user_suspended = sum(1 for vps in vps_list if vps.get('suspended', False))
            user_whitelisted = sum(1 for vps in vps_list if vps.get('whitelisted', False))
            total_vps += user_vps_count
            running_vps += user_running
            stopped_vps += user_stopped
            suspended_vps += user_suspended
            whitelisted_vps += user_whitelisted
            user_summary.append(f"**{user.name}** ({user.mention}) - {user_vps_count} VPS ({user_running} running, {user_suspended} suspended, {user_whitelisted} whitelisted)")
            for i, vps in enumerate(vps_list):
                node = get_node(vps['node_id'])
                node_name = node['name'] if node else "Unknown"
                status_emoji = "🟢" if vps.get('status') == 'running' and not vps.get('suspended', False) else "🟡" if vps.get('suspended', False) else "🔴"
                status_text = vps.get('status', 'unknown').upper()
                if vps.get('suspended', False):
                    status_text += " (SUSPENDED)"
                if vps.get('whitelisted', False):
                    status_text += " (WHITELISTED)"
                
                # Add expiration info
                expiration_text = ""
                if vps.get('expiration_date'):
                    expiration_dt = datetime.fromisoformat(vps['expiration_date'])
                    days_remaining = (expiration_dt - datetime.now()).days
                    if days_remaining < 0:
                        expiration_text = " • 🔴 EXPIRED"
                    elif days_remaining <= EXPIRATION_WARNING_DAYS:
                        expiration_text = f" • 🟡 EXPIRING({days_remaining}d)"
                    else:
                        expiration_text = f" • 🟢 ({days_remaining}d)"
                else:
                    expiration_text = " • ⏰ No exp"
                
                vps_info.append(f"{status_emoji} **{user.name}** - VPS {i+1}: `{vps['container_name']}` - {vps.get('config', 'Custom')} - {status_text} (Node: {node_name}){expiration_text}")
        except discord.NotFound:
            vps_info.append(f"❓ Unknown User ({user_id}) - {len(vps_list)} VPS")
    embed = create_embed("All VPS Information", "Complete overview of all VPS deployments and user statistics", 0x1a1a1a)
    add_field(embed, "System Overview", f"**Total Users:** {total_users}\n**Total VPS:** {total_vps}\n**Running:** {running_vps}\n**Stopped:** {stopped_vps}\n**Suspended:** {suspended_vps}\n**Whitelisted:** {whitelisted_vps}", False)
    await ctx.send(embed=embed)
    if user_summary:
        embed = create_embed("User Summary", f"Summary of all users and their VPS", 0x1a1a1a)
        summary_text = "\n".join(user_summary)
        chunks = [summary_text[i:i+1024] for i in range(0, len(summary_text), 1024)]
        for idx, chunk in enumerate(chunks, 1):
            add_field(embed, f"Users (Part {idx})", chunk, False)
        await ctx.send(embed=embed)
    if vps_info:
        vps_text = "\n".join(vps_info)
        chunks = [vps_text[i:i+1024] for i in range(0, len(vps_text), 1024)]
        for idx, chunk in enumerate(chunks, 1):
            embed = create_embed(f"VPS Details (Part {idx})", "List of all VPS deployments", 0x1a1a1a)
            add_field(embed, "VPS List", chunk, False)
            await ctx.send(embed=embed)

@bot.command(name='manage-shared')
async def manage_shared_vps(ctx, owner: discord.Member, vps_number: int):
    owner_id = str(owner.id)
    user_id = str(ctx.author.id)
    if owner_id not in vps_data or vps_number < 1 or vps_number > len(vps_data[owner_id]):
        await ctx.send(embed=create_error_embed("Invalid VPS", "Invalid VPS number or owner doesn't have a VPS."))
        return
    vps = vps_data[owner_id][vps_number - 1]
    if user_id not in vps.get("shared_with", []):
        await ctx.send(embed=create_error_embed("Access Denied", "You do not have access to this VPS."))
        return
    view = ManageView(user_id, [vps], is_shared=True, owner_id=owner_id, is_admin=is_admin_user(ctx.author), actual_index=vps_number - 1)
    embed = await view.get_initial_embed()
    await ctx.send(embed=embed, view=view)

@bot.command(name='share-user')
async def share_user(ctx, shared_user: discord.Member, vps_number: int):
    user_id = str(ctx.author.id)
    shared_user_id = str(shared_user.id)
    if user_id not in vps_data or vps_number < 1 or vps_number > len(vps_data[user_id]):
        await ctx.send(embed=create_error_embed("Invalid VPS", "Invalid VPS number or you don't have a VPS."))
        return
    vps = vps_data[user_id][vps_number - 1]
    if "shared_with" not in vps:
        vps["shared_with"] = []
    if shared_user_id in vps["shared_with"]:
        await ctx.send(embed=create_error_embed("Already Shared", f"{shared_user.mention} already has access to this VPS!"))
        return
    vps["shared_with"].append(shared_user_id)
    save_vps_data_immediate()
    await ctx.send(embed=create_success_embed("VPS Shared", f"VPS #{vps_number} shared with {shared_user.mention}!"))
    try:
        await shared_user.send(embed=create_embed("VPS Access Granted", f"You have access to VPS #{vps_number} from {ctx.author.mention}. Use `{PREFIX}manage-shared {ctx.author.mention} {vps_number}`", 0x00ff88))
    except discord.Forbidden:
        await ctx.send(embed=create_info_embed("Notification Failed", f"Could not DM {shared_user.mention}"))

@bot.command(name='share-ruser')
async def revoke_share(ctx, shared_user: discord.Member, vps_number: int):
    user_id = str(ctx.author.id)
    shared_user_id = str(shared_user.id)
    if user_id not in vps_data or vps_number < 1 or vps_number > len(vps_data[user_id]):
        await ctx.send(embed=create_error_embed("Invalid VPS", "Invalid VPS number or you don't have a VPS."))
        return
    vps = vps_data[user_id][vps_number - 1]
    if "shared_with" not in vps:
        vps["shared_with"] = []
    if shared_user_id not in vps["shared_with"]:
        await ctx.send(embed=create_error_embed("Not Shared", f"{shared_user.mention} doesn't have access to this VPS!"))
        return
    vps["shared_with"].remove(shared_user_id)
    save_vps_data_immediate()
    await ctx.send(embed=create_success_embed("Access Revoked", f"Access to VPS #{vps_number} revoked from {shared_user.mention}!"))
    try:
        await shared_user.send(embed=create_embed("VPS Access Revoked", f"Your access to VPS #{vps_number} by {ctx.author.mention} has been revoked.", 0xff3366))
    except discord.Forbidden:
        await ctx.send(embed=create_info_embed("Notification Failed", f"Could not DM {shared_user.mention}"))

@bot.command(name='ports-add-user')
@is_admin()
async def ports_add_user(ctx, amount: int, user: discord.Member):
    if amount <= 0:
        await ctx.send(embed=create_error_embed("Invalid Amount", "Amount must be a positive integer."))
        return
    user_id = str(user.id)
    allocate_ports(user_id, amount)
    embed = create_success_embed("Ports Allocated", f"Allocated {amount} port slots to {user.mention}.")
    add_field(embed, "Quota", f"Total: {get_user_allocation(user_id)} slots", False)
    await ctx.send(embed=embed)
    try:
        dm_embed = create_info_embed("Port Slots Allocated", f"You have been granted {amount} additional port forwarding slots by an admin.\nUse `{PREFIX}ports list` to view your quota and active forwards.")
        await user.send(embed=dm_embed)
    except discord.Forbidden:
        await ctx.send(embed=create_info_embed("DM Failed", f"Could not notify {user.mention} via DM."))

@bot.command(name='ports-remove-user')
@is_admin()
async def ports_remove_user(ctx, amount: int, user: discord.Member):
    if amount <= 0:
        await ctx.send(embed=create_error_embed("Invalid Amount", "Amount must be a positive integer."))
        return
    user_id = str(user.id)
    current = get_user_allocation(user_id)
    if amount > current:
        amount = current
    deallocate_ports(user_id, amount)
    remaining = get_user_allocation(user_id)
    embed = create_success_embed("Ports Deallocated", f"Removed {amount} port slots from {user.mention}.")
    add_field(embed, "Remaining Quota", f"{remaining} slots", False)
    await ctx.send(embed=embed)
    try:
        dm_embed = create_warning_embed("Port Slots Reduced", f"Your port forwarding quota has been reduced by {amount} slots by an admin.\nRemaining: {remaining} slots.")
        await user.send(embed=dm_embed)
    except discord.Forbidden:
        await ctx.send(embed=create_info_embed("DM Failed", f"Could not notify {user.mention} via DM."))

@bot.command(name='ports-revoke')
@is_admin()
async def ports_revoke(ctx, forward_id: int):
    success, user_id = await remove_port_forward(forward_id, is_admin=True)
    if success and user_id:
        try:
            user = await bot.fetch_user(int(user_id))
            dm_embed = create_warning_embed("Port Forward Revoked", f"One of your port forwards (ID: {forward_id}) has been revoked by an admin.")
            await user.send(embed=dm_embed)
        except:
            pass
        await ctx.send(embed=create_success_embed("Revoked", f"Port forward ID {forward_id} revoked."))
    else:
        await ctx.send(embed=create_error_embed("Failed", "Port forward ID not found or removal failed."))

@bot.command(name='ports')
async def ports_command(ctx, subcmd: str = None, *args):
    user_id = str(ctx.author.id)
    allocated = ensure_user_port_allocation(user_id) if user_has_vps(user_id) else get_user_allocation(user_id)
    used = get_user_used_ports(user_id)
    available = allocated - used
    if subcmd is None:
        embed = create_info_embed("Port Forwarding Help", f"**Your Quota:** Allocated: {allocated}, Used: {used}, Available: {available}")
        add_field(embed, "Commands", f"{PREFIX}ports add <vps_num> <port>\n{PREFIX}ports list\n{PREFIX}ports remove <id>", False)
        await ctx.send(embed=embed)
        return
    if subcmd == 'add':
        if len(args) < 2:
            await ctx.send(embed=create_error_embed("Usage", f"Usage: {PREFIX}ports add <vps_number> <vps_port>"))
            return
        try:
            vps_num = int(args[0])
            vps_port = int(args[1])
            if vps_port < 1 or vps_port > 65535:
                raise ValueError
        except ValueError:
            await ctx.send(embed=create_error_embed("Invalid Input", "VPS number and port must be positive integers (port: 1-65535)."))
            return
        vps_list = vps_data.get(user_id, [])
        if vps_num < 1 or vps_num > len(vps_list):
            await ctx.send(embed=create_error_embed("Invalid VPS", f"Invalid VPS number (1-{len(vps_list)}). Use {PREFIX}myvps to list."))
            return
        vps = vps_list[vps_num - 1]
        container = vps['container_name']
        node_id = vps['node_id']
        if used >= allocated:
            await ctx.send(embed=create_error_embed("Quota Exceeded", f"No available slots. Allocated: {allocated}, Used: {used}. Contact admin for more."))
            return
        host_port = await create_port_forward(user_id, container, vps_port, node_id)
        if host_port:
            endpoints = await detect_public_endpoints(int(node_id))
            v4 = endpoints.get("ipv4") or "Unavailable"
            v6 = endpoints.get("ipv6") or "Unavailable"
            embed = create_success_embed("🌐 Port Forward Created", f"VPS #{vps_num} port {vps_port} (TCP/UDP) forwarded to host port {host_port}.")
            add_field(embed, "🌐 Public Access", f"IPv4: `{v4}:{host_port}`\nIPv6: `{v6}:{host_port}`", False)
            add_field(embed, "🎯 Target", f"VPS `{container}` → port `{vps_port}` (TCP + UDP)", False)
            add_field(embed, "Quota Update", f"Used: {used + 1}/{allocated}", False)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=create_error_embed("Failed", "Could not assign host port. Try again later."))
    elif subcmd == 'list':
        forwards = get_user_forwards(user_id)
        embed = create_info_embed("Your Port Forwards", f"**Quota:** Allocated: {allocated}, Used: {used}, Available: {available}")
        if not forwards:
            add_field(embed, "Forwards", "No active port forwards.", False)
        else:
            text = []
            for f in forwards:
                vps_num = next((i+1 for i, v in enumerate(vps_data.get(user_id, [])) if v['container_name'] == f['vps_container']), 'Unknown')
                created = datetime.fromisoformat(f['created_at']).strftime('%Y-%m-%d %H:%M')
                text.append(f"**ID {f['id']}** - VPS #{vps_num}: {f['vps_port']} (TCP/UDP) → {f['host_port']} (Created: {created})")
            add_field(embed, "Active Forwards", "\n".join(text[:10]), False)
            if len(forwards) > 10:
                add_field(embed, "Note", f"Showing 10 of {len(forwards)}. Remove unused with {PREFIX}ports remove <id>.")
        await ctx.send(embed=embed)
    elif subcmd == 'remove':
        if len(args) < 1:
            await ctx.send(embed=create_error_embed("Usage", f"Usage: {PREFIX}ports remove <forward_id>"))
            return
        try:
            fid = int(args[0])
        except ValueError:
            await ctx.send(embed=create_error_embed("Invalid ID", "Forward ID must be an integer."))
            return
        success, _ = await remove_port_forward(fid, requester_id=user_id, is_admin=is_admin_user(ctx.author))
        if success:
            embed = create_success_embed("Removed", f"Port forward {fid} removed (TCP & UDP).")
            add_field(embed, "Quota Update", f"Used: {max(0, used - 1)}/{allocated}", False)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=create_error_embed("Not Found", "Forward ID not found. Use !ports list."))
    else:
        await ctx.send(embed=create_error_embed("Invalid Subcommand", f"Use: add <vps_num> <port>, list, remove <id>"))

class ConfirmDeleteView(RGNODESView):
    """Confirmation dialog for VPS deletion"""
    def __init__(self, admin_id: str, vps_id: int, container_name: str, vps_number: int):
        super().__init__(timeout=60)  # 60 seconds to confirm
        self.admin_id = admin_id  # Admin who initiated the delete command
        self.vps_id = vps_id
        self.container_name = container_name
        self.vps_number = vps_number
        self.confirmed = False
    
    @discord.ui.button(label="✅ Confirm Delete", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Allow only the admin who initiated the delete command to confirm
        if str(interaction.user.id) != self.admin_id:
            await interaction.response.send_message(
                embed=create_error_embed("Access Denied", "Only the admin who initiated the deletion can confirm!"),
                ephemeral=True
            )
            return
        
        self.confirmed = True
        await interaction.response.defer()
        self.stop()
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Allow only the admin who initiated the delete command to cancel
        if str(interaction.user.id) != self.admin_id:
            await interaction.response.send_message(
                embed=create_error_embed("Access Denied", "Only the admin who initiated the deletion can cancel!"),
                ephemeral=True
            )
            return
        
        await interaction.response.send_message(
            embed=create_info_embed("Deletion Cancelled", f"VPS deletion for {self.container_name} has been cancelled."),
            ephemeral=True
        )
        self.stop()

@bot.command(name='delete-vps')
@is_admin()
async def delete_vps(ctx, user: discord.Member, vps_number: int, *, reason: str = "No reason"):
    user_id = str(user.id)

    if user_id not in vps_data or vps_number < 1 or vps_number > len(vps_data[user_id]):
        await ctx.send(embed=create_error_embed(
            "Invalid VPS",
            "Invalid VPS number or user doesn't have that VPS."
        ))
        return

    vps = vps_data[user_id][vps_number - 1]
    container_name = vps["container_name"]
    vps_id = vps.get("id", vps_number)
    node_id = vps.get("node_id", 1)

    # Create confirmation embed with clearer info
    confirm_embed = create_embed("⚠️ Confirm VPS Deletion", f"Are you sure you want to delete this VPS?", 0xff3366)
    add_field(confirm_embed, "VPS Details", 
        f"**VPS ID:** #{vps_id}\n"
        f"**Container:** `{container_name}`\n"
        f"**Owner:** {user.mention}\n"
        f"**Config:** {vps.get('config', 'Custom')}\n"
        f"**Status:** {vps.get('status', 'unknown').upper()}", 
        False)
    add_field(confirm_embed, "Action", "Click **✅ Confirm Delete** to permanently delete this VPS, or **❌ Cancel** to abort.", False)
    add_field(confirm_embed, "Reason", reason, False)
    
    confirmation_view = ConfirmDeleteView(str(ctx.author.id), vps_id, container_name, vps_number)
    confirmation_msg = await ctx.send(embed=confirm_embed, view=confirmation_view)
    
    # Wait for confirmation
    await confirmation_view.wait()
    
    if not confirmation_view.confirmed:
        return  # User cancelled or timeout
    
    # Proceed with deletion
    await ctx.send(embed=create_info_embed(
        "🗑️ Deleting VPS",
        f"Removing VPS #{vps_id} for {user.mention}..."
    ))

    node_result = "Not checked"

    # Re-resolve the record after confirmation because another admin action could
    # have changed the owner's VPS list while the confirmation dialog was open.
    current_user_id, current_index, current_vps = find_vps_record(container_name)
    if not current_vps or str(current_user_id) != user_id:
        await ctx.send(embed=create_error_embed("Deletion Aborted", "This VPS record changed or was removed while waiting for confirmation."))
        return
    vps = current_vps
    node_id = int(vps.get("node_id", node_id))

    # 1️⃣ Delete the real LXC first. A failed remote/local deletion must NOT
    # silently erase the DB record and leave an unmanaged running container.
    container_missing = False
    try:
        await execute_lxc(container_name, f"delete {container_name} --force", timeout=300, node_id=node_id)
        node_result = "Container deleted successfully."
    except Exception as e:
        err = str(e).lower()
        if any(x in err for x in ["not found", "does not exist", "no such container"]):
            container_missing = True
            node_result = "Container was already absent; database cleanup continued."
        else:
            await ctx.send(embed=create_error_embed("Deletion Failed", f"The LXC container could not be deleted, so its database record was kept.\n\n{str(e)[:1200]}"))
            return

    # 2️⃣ Remove persistent database records only after the container operation
    # succeeded or the container was confirmed absent. Keep a recovery snapshot first.
    backup_database()
    try:
        with DB_LOCK:
            conn = get_db()
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM port_forwards WHERE vps_container = ?", (container_name,))
                cur.execute("DELETE FROM vps WHERE container_name = ?", (container_name,))
                if cur.rowcount != 1:
                    raise RuntimeError("VPS database record was not found at commit time.")
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
    except Exception as db_error:
        # The LXC is already gone here; keep a recovery-style message because the
        # instance can no longer be operated. The DB failure is logged loudly.
        logger.critical(f"Container {container_name} deleted but DB cleanup failed: {db_error}", exc_info=True)
        await ctx.send(embed=create_error_embed("Database Cleanup Failed", "The LXC was deleted, but the database cleanup did not complete. Check the bot logs and database backup before retrying."))
        return

    # 3️⃣ Remove the exact record from memory.
    try:
        vps_data[user_id] = [v for v in vps_data.get(user_id, []) if v.get("container_name") != container_name]
        if not vps_data[user_id]:
            del vps_data[user_id]
            if ctx.guild:
                role = await get_or_create_vps_role(ctx.guild)
                if role and role in user.roles:
                    try:
                        await user.remove_roles(role, reason="No VPS ownership")
                    except discord.Forbidden:
                        logger.warning(f"Failed to remove VPS role from {user.name}")
    finally:
        save_vps_data_immediate()

    # 4️⃣ Success embed
    embed = create_success_embed("✅ VPS Deleted Successfully")
    add_field(embed, "VPS ID", f"#{vps_id}", True)
    add_field(embed, "Owner", user.mention, True)
    add_field(embed, "Container", container_name, False)
    add_field(embed, "Node Result", node_result, False)
    add_field(embed, "Reason", reason, False)

    await ctx.send(embed=embed)

@bot.command(name='add-resources')
@is_admin()
async def add_resources(ctx, vps_id: str, ram: int = None, cpu: int = None, disk: int = None):
    if ram is None and cpu is None and disk is None:
        await ctx.send(embed=create_error_embed("Missing Parameters", "Please specify at least one resource to add (ram, cpu, or disk)"))
        return
    user_id, vps_index, found_vps = find_vps_record(vps_id)
    if not found_vps:
        await ctx.send(embed=create_error_embed("VPS Not Found", f"No VPS found with ID/name: `{vps_id}`"))
        return
    vps_id = found_vps['container_name']
    node_id = int(found_vps.get('node_id', 1))
    was_running = found_vps.get('status') == 'running' and not found_vps.get('suspended', False)
    disk_changed = disk is not None
    if was_running:
        await ctx.send(embed=create_info_embed("Stopping VPS", f"Stopping VPS `{vps_id}` to apply resource changes..."))
        try:
            await execute_lxc(vps_id, f"stop {vps_id}", node_id=node_id)
            found_vps['status'] = 'stopped'
            save_vps_data_immediate()
        except Exception as e:
            await ctx.send(embed=create_error_embed("Stop Failed", f"Error stopping VPS: {str(e)}"))
            return
    changes = []
    try:
        current_ram_gb = int(found_vps['ram'].replace('GB', ''))
        current_cpu = int(found_vps['cpu'])
        current_disk_gb = int(found_vps['storage'].replace('GB', ''))
        new_ram_gb = current_ram_gb
        new_cpu = current_cpu
        new_disk_gb = current_disk_gb
        if ram is not None and ram > 0:
            new_ram_gb += ram
            ram_mb = new_ram_gb * 1024
            await execute_lxc(vps_id, f"config set {vps_id} limits.memory {ram_mb}MB", node_id=node_id)
            changes.append(f"RAM: +{ram}GB (New total: {new_ram_gb}GB)")
        if cpu is not None and cpu > 0:
            new_cpu += cpu
            await execute_lxc(vps_id, f"config set {vps_id} limits.cpu {new_cpu}", node_id=node_id)
            changes.append(f"CPU: +{cpu} cores (New total: {new_cpu} cores)")
        if disk is not None and disk > 0:
            new_disk_gb += disk
            await execute_lxc(vps_id, f"config device set {vps_id} root size={new_disk_gb}GB", node_id=node_id)
            changes.append(f"Disk: +{disk}GB (New total: {new_disk_gb}GB)")
        found_vps['ram'] = f"{new_ram_gb}GB"
        found_vps['cpu'] = str(new_cpu)
        found_vps['storage'] = f"{new_disk_gb}GB"
        found_vps['config'] = f"{new_ram_gb}GB RAM / {new_cpu} CPU / {new_disk_gb}GB Disk"
        vps_data[user_id][vps_index] = found_vps
        save_vps_data_immediate()
        if was_running:
            await execute_lxc(vps_id, f"start {vps_id}", node_id=node_id)
            found_vps['status'] = 'running'
            save_vps_data_immediate()
            await apply_internal_permissions(vps_id, node_id)
            await recreate_port_forwards(vps_id)
        embed = create_success_embed("Resources Added", f"Successfully added resources to VPS `{vps_id}`")
        add_field(embed, "Changes Applied", "\n".join(changes), False)
        if disk is not None and disk > 0:
            add_field(embed, "Disk Note", "Run `sudo resize2fs /` inside the VPS to expand the filesystem if the guest filesystem does not auto-grow.", False)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(embed=create_error_embed("Resource Addition Failed", f"Error: {str(e)}"))


@bot.command(name='permissions')
@is_admin()
async def permissions_check_command(ctx, channel: discord.TextChannel = None):
    """Audit the bot's effective Discord permissions in a target channel."""
    if ctx.guild is None:
        await ctx.send(embed=create_error_embed("Invalid Context", "Use this command inside a Discord server."))
        return
    target = channel or ctx.channel
    me = ctx.guild.me
    if me is None:
        await ctx.send(embed=create_error_embed("Permission Audit Failed", "Discord has not provided the bot member object yet."))
        return
    perms = target.permissions_for(me)
    required = {
        "View Channel": perms.view_channel,
        "Send Messages": perms.send_messages,
        "Embed Links": perms.embed_links,
        "Attach Files": perms.attach_files,
        "Read Message History": perms.read_message_history,
        "Manage Messages": perms.manage_messages,
        "Manage Channels": perms.manage_channels,
        "Manage Roles": perms.manage_roles,
        "Manage Webhooks": perms.manage_webhooks,
    }
    lines = [f"{'✅' if ok else '❌'} **{name}**" for name, ok in required.items()]
    missing = [name for name, ok in required.items() if not ok]
    embed = create_info_embed("🛡️ RGNODES Permission Audit", f"Effective permissions for the bot in {target.mention}.")
    add_field(embed, "Core Logging", "\n".join(lines[:5]), False)
    add_field(embed, "Management", "\n".join(lines[5:]), False)
    add_field(embed, "Result", "✅ Core permissions are available." if not missing else f"⚠️ Missing: {', '.join(missing)}", False)
    await ctx.send(embed=embed)

@bot.group(name='update', invoke_without_command=True)
@commands.guild_only()
@is_admin()
async def update_group(ctx):
    await ctx.send(embed=create_info_embed("⚙️ Update Center", f"Use `{PREFIX}update logs #channel` to configure the VPS/node log channel."))

@update_group.command(name='logs')
@is_admin()
async def update_logs(ctx, channel: discord.TextChannel):
    if ctx.guild is None or ctx.guild.me is None:
        await ctx.send(embed=create_error_embed("Invalid Context", "Use this command inside a Discord server."))
        return
    perms=channel.permissions_for(ctx.guild.me)
    missing=[name for name,ok in (("View Channel",perms.view_channel),("Send Messages",perms.send_messages),("Embed Links",perms.embed_links),("Attach Files",perms.attach_files)) if not ok]
    if missing:
        await ctx.send(embed=create_error_embed("Permission Check Failed", f"I need: {', '.join(missing)} in {channel.mention}."))
        return
    set_audit_channel_id(channel.id)
    await record_audit_event("system", "Logs Channel Updated", f"VPS + node logs are now published to {channel.mention}.", user_id=ctx.author.id, announce=False)
    await ctx.send(embed=create_success_embed("✅ Logs Channel Updated", f"VPS + node logs will now be sent to {channel.mention}.\n\nRequired bot permissions were verified: **View Channel • Send Messages • Embed Links**."))
    try:
        await channel.send(
            embed=create_success_embed(
                "📝 RGNODES Logging Active",
                "VPS and node operational events will appear here.\n\n"
                "✅ VPS audit events\n"
                "✅ Node health snapshots\n"
                "✅ Detailed `log-vps` / `node-logs` snapshots\n"
                "✅ Secrets are redacted from command-audit text."
            ),
            allowed_mentions=discord.AllowedMentions.none(),
        )
    except Exception:
        pass

@bot.command(name='update-logs')
@commands.guild_only()
@is_admin()
async def update_logs_alias(ctx, channel: discord.TextChannel):
    """Convenience alias for `update logs #channel`."""
    await update_logs.callback(ctx, channel)

@bot.command(name='log-channel')
@commands.guild_only()
@is_admin()
async def log_channel_command(ctx, action: str = 'show'):
    """Show or test the configured operational log channel."""
    action = str(action or 'show').lower().strip()
    channel_id = _audit_channel_id()
    if action in {'show','status'}:
        if not channel_id:
            await ctx.send(embed=create_warning_embed("📝 Logs Channel", f"No log channel is configured. Use `{PREFIX}update logs #channel`."))
            return
        try:
            channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
            await ctx.send(embed=create_info_embed("📝 Logs Channel", f"Configured channel: {getattr(channel, 'mention', f'`{channel_id}`')}\n\nVPS + node event logging is active."))
        except Exception:
            await ctx.send(embed=create_warning_embed("📝 Logs Channel", f"Configured channel ID `{channel_id}` is not currently reachable. Use `{PREFIX}update logs #channel` to repair it."))
        return
    if action in {'test','check'}:
        await logs_test_command.callback(ctx)
        return
    await ctx.send(embed=create_error_embed("Invalid Action", f"Use `{PREFIX}log-channel show` or `{PREFIX}log-channel test`."))

@bot.group(name='add', invoke_without_command=True)
@commands.guild_only()
@is_admin()
async def add_group(ctx):
    await ctx.send(embed=create_info_embed("➕ Admin Add", f"Use `{PREFIX}add slots @user amount`."))

@add_group.command(name='slots')
@is_admin()
async def add_group_slots(ctx, user: discord.Member, amount: int):
    if amount <= 0 or amount > 1000:
        await ctx.send(embed=create_error_embed("Invalid Amount", "Slots must be between 1 and 1000."))
        return
    before=get_user_allocation(str(user.id))
    allocate_ports(str(user.id), amount)
    after=get_user_allocation(str(user.id))
    await record_audit_event("vps", "Port Slots Added", f"Allocated `{amount}` slots. Quota `{before}` → `{after}`.", user_id=ctx.author.id)
    await ctx.send(embed=create_success_embed("✅ Slots Added", f"Added **{amount}** port-forwarding slots to {user.mention}.\n**New quota:** `{after}`"))
    try:
        await user.send(embed=create_info_embed("🌐 Port Slots Updated", f"An administrator added **{amount}** port-forwarding slots to your account.\n**New quota:** `{after}`"))
    except discord.Forbidden:
        pass

@bot.command(name='add-slots')
@commands.guild_only()
@is_admin()
async def add_slots_alias(ctx, user: discord.Member, amount: int):
    """Convenience alias for `add slots @user amount`."""
    await add_group_slots.callback(ctx, user, amount)

@bot.command(name='slots')
async def slots_command(ctx, user: discord.Member = None):
    """Show a user's port-slot quota. Admins may inspect another user."""
    if user is not None and str(user.id) != str(ctx.author.id) and not is_admin_user(ctx.author):
        await ctx.send(embed=create_error_embed("Access Denied", "You can only inspect your own slot quota unless you are an administrator."))
        return
    target = user or ctx.author
    allocated = get_user_allocation(str(target.id))
    used = get_user_used_ports(str(target.id))
    available = max(0, allocated - used)
    embed = create_info_embed("🌐 Port Slot Quota", f"Slot allocation for {target.mention}.")
    add_field(embed, "Allocated", f"`{allocated}` slots", True)
    add_field(embed, "Used", f"`{used}` slots", True)
    add_field(embed, "Available", f"`{available}` slots", True)
    await ctx.send(embed=embed)

@bot.command(name='log-vps')
async def log_vps_command(ctx, container_name: str, lines: int = LOG_CHANNEL_SNAPSHOT_LINES):
    """Fetch VPS guest logs and mirror the result to the configured log channel."""
    await vps_logs.callback(ctx, container_name, lines)

@bot.command(name='log-node')
@is_admin()
async def log_node_command(ctx, node_id: int, limit: int = LOG_CHANNEL_SNAPSHOT_LINES):
    """Fetch node diagnostics and mirror the result to the configured log channel."""
    await node_logs_command.callback(ctx, node_id, limit)

@bot.command(name='logs-test')
@commands.guild_only()
@is_admin()
async def logs_test_command(ctx):
    """Verify the configured log channel and permissions without changing anything."""
    channel_id = _audit_channel_id()
    if not channel_id:
        await ctx.send(embed=create_warning_embed("📝 Logs Not Configured", f"Use `{PREFIX}update logs #channel` first."))
        return
    try:
        channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
        if ctx.guild and isinstance(channel, discord.TextChannel) and ctx.guild.me:
            perms = channel.permissions_for(ctx.guild.me)
            missing = [name for name, ok in (("View Channel", perms.view_channel),("Send Messages", perms.send_messages),("Embed Links", perms.embed_links)) if not ok]
            if missing:
                await ctx.send(embed=create_error_embed("Permission Check Failed", f"Missing in {channel.mention}: {', '.join(missing)}"))
                return
        probe = create_success_embed("🧪 RGNODES Logs Test", f"Log delivery is working for {getattr(channel, 'mention', channel_id)}.")
        await channel.send(embed=probe, allowed_mentions=discord.AllowedMentions.none())
        await ctx.send(embed=create_success_embed("✅ Logs Channel Healthy", f"A test event was delivered to {getattr(channel, 'mention', f'`{channel_id}`')}."))
    except Exception as exc:
        await ctx.send(embed=create_error_embed("❌ Logs Test Failed", str(exc)[:900]))

@bot.command(name='bandwidth')
async def bandwidth_command(ctx, vps_ref: str = None):
    target=vps_ref
    if target:
        owner_id,_,vps=find_vps_record(target)
    else:
        owner_id=str(ctx.author.id)
        items=vps_data.get(owner_id,[])
        vps=items[0] if len(items)==1 else None
    if not vps:
        await ctx.send(embed=create_error_embed("VPS Not Found", f"Use `{PREFIX}bandwidth <vps-id|container>` as an administrator, or own exactly one VPS.")); return
    if str(ctx.author.id)!=str(owner_id) and not is_admin_user(ctx.author):
        await ctx.send(embed=create_error_embed("Access Denied", "You can only view your own VPS bandwidth unless you are an administrator.")); return
    rx,tx=await get_container_network_usage(str(vps.get('container_name')),int(vps.get('node_id',1)))
    embed=create_info_embed("🌐 VPS Bandwidth",f"`{vps.get('container_name')}` • **RGNODES fixed 50GB/month plan**")
    quota_gb = VPS_BANDWIDTH_GB
    used_bytes = int(vps.get('bandwidth_used_bytes') or 0)
    used_gb = used_bytes / 1024**3
    remaining_gb = max(0.0, quota_gb - used_gb)
    add_field(embed,"Monthly Quota",f"**{quota_gb} GB**",True)
    add_field(embed,"Accounted Usage",f"**{used_gb:.2f} GB**",True)
    add_field(embed,"Remaining",f"**{remaining_gb:.2f} GB**",True)
    add_field(embed,"Live RX / TX",f"RX `{rx}` • TX `{tx}`",False)
    add_field(embed,"Cycle",f"`{str(vps.get('bandwidth_cycle_start') or 'current')[:19]}`",True)
    await ctx.send(embed=embed)

@bot.command(name='node-capacity')
@is_admin()
async def node_capacity_command(ctx, node_id: int = 1):
    """Low-overhead host capacity snapshot used before provisioning."""
    node = get_node(node_id)
    if not node:
        await ctx.send(embed=create_error_embed("Node Not Found", f"Node `{node_id}` was not found."))
        return
    try:
        stats = await asyncio.wait_for(get_host_stats(node_id), timeout=12)
        total_ram = int(stats.get('ram_bytes_total') or 0)
        available_ram = int(stats.get('ram_bytes_available') or 0)
        used_ram = max(0, total_ram - available_ram)
        disk = stats.get('disk') or {}
        cpu = float(stats.get('cpu') or 0.0)
        ram_pct = (used_ram / total_ram * 100.0) if total_ram else float(stats.get('ram') or 0.0)
        disk_pct = float(disk.get('percent', 0) or 0) if isinstance(disk, dict) else 0.0
        embed = create_info_embed("🧠 Node Capacity", f"**{node.get('name','Node')}** • `{node_id}`\nProvider: **{HOST_PROVIDER_NAME}** • CPU: **{HOST_PROCESSOR_NAME}**")
        add_field(embed, "CPU", f"`{cpu:.1f}%` used • deploy ceiling `{HOST_CPU_MAX_DEPLOY_PCT:.0f}%`", True)
        add_field(embed, "RAM", f"`{available_ram/(1024**3):.2f} GiB` free / `{total_ram/(1024**3):.2f} GiB` total • `{ram_pct:.1f}%` used", True)
        add_field(embed, "Disk", f"`{disk_pct:.1f}%` used • reserve `{HOST_DISK_RESERVE_GB:.1f} GiB`", True)
        add_field(embed, "Allocation Policy", f"RAM share ≤ `{MAX_DEPLOY_RAM_SHARE*100:.0f}%` • RAM reserve `{HOST_RAM_RESERVE_GB:.1f} GiB` • swap guests `{'ON' if VPS_SWAP_ENABLED else 'OFF'}`", False)
        await ctx.send(embed=embed)
    except Exception as exc:
        await ctx.send(embed=create_error_embed("Node Capacity Failed", str(exc)[:900]))

@bot.command(name='node-logs')
@commands.guild_only()
@is_admin()
async def node_logs_command(ctx, node_id: int, limit: int = 25):
    """Admin node diagnostics, local LXD journal (when available), and audit snapshots."""
    limit = max(5, min(50, int(limit)))
    node = get_node(node_id)
    if not node:
        await ctx.send(embed=create_error_embed("Node Not Found", f"Node `{node_id}` was not found."))
        return
    await ctx.send(embed=create_info_embed("🧩 Gathering Node Logs", f"Checking `{node.get('name','Node')}`..."))
    try:
        stats = await asyncio.wait_for(get_host_stats(node_id), timeout=12)
        cpu = float(stats.get("cpu") or 0)
        ram = float(stats.get("ram") or 0)
        disk = stats.get("disk") or {}
        if isinstance(disk, dict):
            disk_text = f"{float(disk.get('percent',0) or 0):.1f}% used • {int(disk.get('free',0) or 0)/(1024**3):.1f} GiB free"
        else:
            disk_text = str(disk)
        health = f"CPU `{cpu:.1f}%` • RAM `{ram:.1f}%` • Disk `{disk_text}`"
    except Exception as exc:
        health = f"Health check failed: {exc}"

    journal = "Remote node journal unavailable through the current node-agent contract."
    if node.get('is_local'):
        try:
            def _read_local_node_journal() -> str:
                proc = subprocess.run(
                    ['journalctl', '--no-pager', '-n', str(min(limit, 50)), '-u', 'lxd.service', '-u', 'lxd-agent.service'],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=12, check=False,
                )
                return proc.stdout or "No local LXD service journal entries."
            journal = await asyncio.to_thread(_read_local_node_journal)
        except Exception as exc:
            journal = f"Local node journal unavailable: {exc}"

    rows = get_recent_audit_logs(limit, node_id=node_id)
    lines_text = "\n".join(
        f"{r.get('created_at','')[:19]} | {r.get('kind','system')} | {r.get('action','Event')} | {r.get('detail','')}"
        for r in rows
    ) or "No node audit events recorded yet."
    embed=create_info_embed("🧩 Node Logs",f"**{node.get('name','Node')}** • Node `{node_id}`\n{health}")
    add_field(embed,"Node Service Logs",f"```text\n{journal[-2400:]}\n```",False)
    add_field(embed,"Recent RGNODES Events",f"```text\n{lines_text[-2600:]}\n```",False)
    await ctx.send(embed=embed)

    # Also publish the diagnostic to the configured log channel so the operator has
    # one central place for VPS/node operational history. Avoid duplicate posting.
    channel_id = _audit_channel_id()
    if channel_id and (not getattr(ctx.channel, 'id', None) or int(ctx.channel.id) != int(channel_id)):
        try:
            target = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
            raw_bundle = f"RGNODES NODE LOG SNAPSHOT\nNode: {node.get('name','Node')}\nNode ID: {node_id}\nGenerated: {datetime.now().isoformat()}\nHealth: {health}\n\n=== NODE SERVICE LOGS ===\n{journal}\n\n=== RGNODES AUDIT ===\n{lines_text}\n"
            if hasattr(target, 'send'):
                await _publish_log_bundle(target, embed, raw_bundle, f"node-{node_id}-logs.txt")
        except Exception as exc:
            logger.debug('Failed to publish node diagnostics to log channel: %s', exc)
    await record_audit_event("node", "Node Logs Viewed", f"Diagnostic snapshot requested ({limit} events).", user_id=ctx.author.id, node_id=node_id)

@bot.command(name='logs')
@commands.guild_only()
@is_admin()
async def logs_command(ctx, limit: int = 25):
    rows=get_recent_audit_logs(limit)
    lines="\n".join(f"`{str(r.get('created_at',''))[:19]}` • **{r.get('kind','system').upper()} / {r.get('action','Event')}** — {r.get('detail','')}" for r in rows[:25]) or "No audit events recorded yet."
    channel_id=_audit_channel_id()
    await ctx.send(embed=create_info_embed("📝 RGNODES Audit Logs",f"Configured channel: `{channel_id or 'Not configured'}`\n\n{lines[:3800]}"))

@bot.command(name='log-config')
@is_admin()
async def log_config_command(ctx):
    channel_id = _audit_channel_id()
    channel = bot.get_channel(channel_id) if channel_id else None
    label = channel.mention if channel else (f"`{channel_id}`" if channel_id else "Not configured")
    await ctx.send(embed=create_info_embed("📝 Log Channel", f"VPS + node operational logs are sent to: **{label}**\nUse `{PREFIX}update logs #channel` to change it.\n\nAutomatic: VPS actions + node health. Detailed: `{PREFIX}log-vps <vps>` / `{PREFIX}log-node <node>`."))

@bot.command(name='node-log')
@is_admin()
async def node_log_alias(ctx, node_id: int, limit: int = 25):
    await node_logs_command.callback(ctx, node_id, limit)

@bot.command(name='vps-log')
async def vps_log_alias(ctx, container_name: str, lines: int = 50):
    owner_id, _, vps = find_vps_record(container_name)
    if not vps:
        await ctx.send(embed=create_error_embed("VPS Not Found", f"`{container_name}` was not found.")); return
    if str(ctx.author.id) != str(owner_id) and not is_admin_user(ctx.author):
        await ctx.send(embed=create_error_embed("Access Denied", "You can only view logs for your own VPS.")); return
    await vps_logs.callback(ctx, container_name, lines)

@bot.command(name='motd')
@commands.guild_only()
@is_admin()
async def motd_command(ctx, action: str = 'show', *, text: str = ''):
    action=str(action or 'show').lower().strip()
    if action=='show':
        current = get_motd_text()
        status = "🟢 Enabled" if current else "⚪ Disabled"
        body = current or "MOTD is currently disabled."
        await ctx.send(embed=create_info_embed("📜 Current MOTD",f"**Status:** {status}\n\n```text\n{body[:1800]}\n```")); return
    if action in {'clear','off','disable'}:
        set_setting('motd_text','')
        ok,failed=await apply_motd_to_all_running_vps()
        await record_audit_event("system","MOTD Disabled",f"Cleared on `{ok}` running VPS; `{failed}` failed.",user_id=ctx.author.id)
        await ctx.send(embed=create_success_embed("✅ MOTD Disabled",f"Cleared on **{ok}** running VPS. Failed: **{failed}**.")); return
    if action in {'set','on','enable'}:
        text=text.strip()[:1200]
        if not text:
            await ctx.send(embed=create_error_embed("Missing MOTD",f"Usage: `{PREFIX}motd set Your message here`")); return
        set_setting('motd_text',text)
        await ctx.send(embed=create_info_embed("📜 Applying MOTD","Saving the new MOTD and applying it to running VPS..."))
        ok,failed=await apply_motd_to_all_running_vps()
        await record_audit_event("system","MOTD Updated",f"Applied to `{ok}` running VPS; `{failed}` failed.",user_id=ctx.author.id)
        await ctx.send(embed=create_success_embed("✅ MOTD Updated",f"Applied to **{ok}** running VPS. Failed: **{failed}**.")); return
    await ctx.send(embed=create_error_embed("Invalid MOTD Action",f"Use `{PREFIX}motd show`, `{PREFIX}motd set <text>`, or `{PREFIX}motd clear`."))

@bot.command(name='status')
@is_admin()
async def system_status(ctx):
    """
    Show complete system status including:
    - Bot uptime
    - Total nodes & their status
    - Running/stopped nodes count
    - Total RAM/CPU/DISK allocated vs free
    - Total VPS & users
    - Running/stopped/suspended VPS counts
    - Total admin users
    - Whitelisted VPS
    """
    
    # Start timing for response time
    start_time = time.time()
    
    # Get bot uptime
    bot_start_time = datetime.now() - datetime.fromtimestamp(start_time - bot.latency)
    bot_uptime = str(bot_start_time).split('.')[0]  # Remove microseconds
    
    # Get total nodes
    nodes = get_nodes()
    total_nodes = len(nodes)
    
    # Node status counters
    running_nodes = 0
    stopped_nodes = 0
    local_nodes = 0
    remote_nodes = 0
    
    # Node resource tracking
    total_node_cpu_allocated = 0
    total_node_ram_allocated = 0
    total_node_disk_allocated = 0
    total_node_cpu_free = 0
    total_node_ram_free = 0
    total_node_disk_free = 0
    
    # VPS counters
    total_vps = 0
    total_users = len(vps_data)
    running_vps = 0
    stopped_vps = 0
    suspended_vps = 0
    whitelisted_vps = 0
    
    # Admin counters
    total_admins = len(admin_data.get("admins", []))
    
    # Port statistics
    with DB_LOCK:
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("SELECT SUM(allocated_ports) FROM port_allocations")
            total_ports_allocated = cur.fetchone()[0] or 0
            cur.execute("SELECT COUNT(*) FROM port_forwards")
            total_ports_used = cur.fetchone()[0] or 0
        finally:
            conn.close()
    
    # Resource counters for all VPS
    total_ram_allocated = 0
    total_cpu_allocated = 0
    total_disk_allocated = 0
    
    # Process all VPS data
    for user_id, vps_list in vps_data.items():
        total_vps += len(vps_list)
        
        for vps in vps_list:
            # Count status
            if vps.get('suspended', False):
                suspended_vps += 1
            elif vps.get('status') == 'running':
                running_vps += 1
            else:
                stopped_vps += 1
            
            # Count whitelisted
            if vps.get('whitelisted', False):
                whitelisted_vps += 1
            
            # Calculate allocated resources
            try:
                ram_gb = int(vps['ram'].replace('GB', ''))
                total_ram_allocated += ram_gb
            except:
                pass
            
            try:
                cpu_cores = int(vps['cpu'])
                total_cpu_allocated += cpu_cores
            except:
                pass
            
            try:
                disk_gb = int(vps['storage'].replace('GB', ''))
                total_disk_allocated += disk_gb
            except:
                pass
    
    # Check node status and calculate free resources
    node_statuses = []
    
    for node in nodes:
        # Determine node type
        if node['is_local']:
            local_nodes += 1
            node_type = "🖥️ Local"
        else:
            remote_nodes += 1
            node_type = "🌐 Remote"
        
        # Check node status
        if node['is_local']:
            status = "🟢 Online"
            running_nodes += 1
            
            # Get local resources (approximate) - cross-platform
            try:
                import platform
                system = platform.system()
                
                if system == "Windows":
                    # Windows: Use psutil
                    try:
                        import psutil
                        mem = psutil.virtual_memory()
                        total_ram_gb = mem.total / (1024**3)
                        free_ram_gb = mem.available / (1024**3)
                        
                        cpu_count = psutil.cpu_count()
                        total_cpu = cpu_count if cpu_count else 0
                        
                        disk = psutil.disk_usage('C:\\' if 'C:\\' else '/')
                        total_disk = disk.total / (1024**3)
                    except ImportError:
                        # Fallback for Windows without psutil
                        try:
                            result = await asyncio.to_thread(subprocess.run, ['wmic', 'OS', 'get', 'TotalVisibleMemorySize,FreePhysicalMemory'], capture_output=True, text=True, timeout=5)
                            lines = result.stdout.strip().split('\n')
                            if len(lines) > 1:
                                values = lines[1].split()
                                total_ram_gb = int(values[0]) / (1024**2)
                                free_ram_gb = int(values[1]) / (1024**2)
                            else:
                                total_ram_gb = 0
                                free_ram_gb = 0
                            
                            result = await asyncio.to_thread(subprocess.run, ['wmic', 'os', 'get', 'numberofprocessors'], capture_output=True, text=True, timeout=5)
                            total_cpu = int(result.stdout.strip().split('\n')[-1]) if result.stdout else 0
                            
                            total_disk = 0  # Approximate
                        except:
                            total_ram_gb = 0
                            free_ram_gb = 0
                            total_cpu = 0
                            total_disk = 0
                else:
                    # Linux/Unix: Use traditional commands
                    # Get system memory
                    mem_result = await asyncio.to_thread(subprocess.run, ['free', '-m'], capture_output=True, text=True, timeout=10)
                    mem_lines = mem_result.stdout.splitlines()
                    if len(mem_lines) > 1:
                        mem = mem_lines[1].split()
                        total_ram_mb = int(mem[1])
                        used_ram_mb = int(mem[2])
                        free_ram_mb = total_ram_mb - used_ram_mb
                        total_ram_gb = total_ram_mb / 1024
                        free_ram_gb = free_ram_mb / 1024
                    else:
                        total_ram_gb = 0
                        free_ram_gb = 0
                    
                    # Get CPU cores
                    cpu_result = await asyncio.to_thread(subprocess.run, ['nproc'], capture_output=True, text=True, timeout=10)
                    total_cpu = int(cpu_result.stdout.strip()) if cpu_result.stdout.strip() else 0
                    
                    # Get disk space
                    disk_result = await asyncio.to_thread(subprocess.run, ['df', '-h', '/'], capture_output=True, text=True, timeout=10)
                    disk_lines = disk_result.stdout.splitlines()
                    if len(disk_lines) > 1:
                        disk_parts = disk_lines[1].split()
                        total_disk_str = disk_parts[1]
                        # Convert to GB
                        if 'T' in total_disk_str:
                            total_disk = float(total_disk_str.replace('T', '')) * 1024
                        elif 'G' in total_disk_str:
                            total_disk = float(total_disk_str.replace('G', ''))
                        elif 'M' in total_disk_str:
                            total_disk = float(total_disk_str.replace('M', '')) / 1024
                        else:
                            total_disk = 0
                    else:
                        total_disk = 0
                
                # Calculate free resources (simplified - actual would need more complex logic)
                free_cpu = max(0, total_cpu - (total_cpu_allocated // total_nodes)) if total_nodes > 0 else 0
                free_disk = max(0, total_disk - (total_disk_allocated // total_nodes)) if total_nodes > 0 else 0
                
                # Update totals
                if total_ram_gb > 0:
                    total_node_ram_allocated += total_ram_gb - free_ram_gb
                    total_node_ram_free += free_ram_gb
                if total_cpu > 0:
                    total_node_cpu_allocated += total_cpu - free_cpu
                    total_node_cpu_free += free_cpu
                if total_disk > 0:
                    total_node_disk_allocated += total_disk - free_disk
                    total_node_disk_free += free_disk
                
            except Exception as e:
                logger.debug(f"Error getting local node resources: {e}")
                status = "⚠️ Unknown"
                # Don't reset to 0, just skip this node's resources
        else:
            # Check remote node status
            try:
                response = await asyncio.to_thread(requests.get, str(node['url']).rstrip('/') + '/api/ping', headers={'X-API-Key': str(node['api_key'])}, timeout=5)
                if response.status_code == 200:
                    status = "🟢 Online"
                    running_nodes += 1
                else:
                    status = "🔴 Offline"
                    stopped_nodes += 1
            except:
                status = "🔴 Offline"
                stopped_nodes += 1
        
        # Get current VPS count on this node
        node_vps_count = get_current_vps_count(node['id'])
        capacity = node['total_vps']
        usage_percentage = (node_vps_count / capacity * 100) if capacity > 0 else 0
        
        node_statuses.append(
            f"**{node['name']}** ({node_type})\n"
            f"📍 {node['location']} • 📊 {node_vps_count}/{capacity} VPS ({usage_percentage:.0f}%)\n"
            f"Status: {status}"
        )
    
    # Calculate response time
    response_time = (time.time() - start_time) * 1000
    
    # Create main embed
    embed = create_embed(
        title="📊 System Status Dashboard",
        description=f"**{BOT_NAME}** - Complete System Overview\n*Generated in {response_time:.0f}ms*"
    )
    
    # Bot & Uptime Section
    add_field(embed, "🤖 Bot Status", 
        f"**Provider:** {HOST_PROVIDER_NAME}\n"
        f"**Uptime:** {bot_uptime}\n"
        f"**Latency:** {round(bot.latency * 1000)}ms\n"
        f"**Version:** {BOT_VERSION}\n"
        f"**Developer:** {BOT_DEVELOPER}", 
        True)
    
    # Nodes Section
    add_field(embed, "🌐 Nodes Overview",
        f"**Total Nodes:** {total_nodes}\n"
        f"**Running:** {running_nodes} 🟢\n"
        f"**Stopped:** {stopped_nodes} 🔴\n"
        f"**Local/Remote:** {local_nodes}/{remote_nodes}",
        True)
    
    # VPS & Users Section
    add_field(embed, "👥 Users & VPS",
        f"**Total Users:** {total_users}\n"
        f"**Total VPS:** {total_vps}\n"
        f"**Running:** {running_vps} 🟢\n"
        f"**Stopped:** {stopped_vps} 🔴\n"
        f"**Suspended:** {suspended_vps} 🟡\n"
        f"**Whitelisted:** {whitelisted_vps} ✅",
        True)
    
    # Resources Section - Allocated vs Free
    add_field(embed, "💾 Resource Allocation",
        f"**RAM Allocated:** {total_ram_allocated} GB\n"
        f"**RAM Free:** {total_node_ram_free:.1f} GB\n"
        f"**CPU Allocated:** {total_cpu_allocated} Cores\n"
        f"**CPU Free:** {total_node_cpu_free:.1f} Cores\n"
        f"**Disk Allocated:** {total_disk_allocated} GB\n"
        f"**Disk Free:** {total_node_disk_free:.1f} GB",
        True)
    
    # System & Admin Section
    add_field(embed, "⚙️ System Information",
        f"**Total Admins:** {total_admins}\n"
        f"**Main Admin:** <@{MAIN_ADMIN_ID}>\n"
        f"**Ports Allocated:** {total_ports_allocated}\n"
        f"**Ports In Use:** {total_ports_used}\n"
        f"**Ports Available:** {total_ports_allocated - total_ports_used}",
        True)
    
    # Node Details Section (if any nodes exist)
    if node_statuses:
        # Split node statuses into chunks if too long
        node_text = "\n\n".join(node_statuses)
        chunks = [node_text[i:i+1024] for i in range(0, len(node_text), 1024)]
        
        for idx, chunk in enumerate(chunks, 1):
            title = "📡 Node Details" if idx == 1 else f"📡 Node Details (Part {idx})"
            add_field(embed, title, chunk, False)
    
    # Expiration Status Section
    expiring_soon_count = 0
    expired_count = 0
    active_exp_count = 0
    no_exp_count = 0
    
    for user_id, vps_list in vps_data.items():
        for vps in vps_list:
            if vps.get('expiration_date'):
                expiration_dt = datetime.fromisoformat(vps['expiration_date'])
                days_remaining = (expiration_dt - datetime.now()).days
                if days_remaining < 0:
                    expired_count += 1
                elif days_remaining <= EXPIRATION_WARNING_DAYS:
                    expiring_soon_count += 1
                else:
                    active_exp_count += 1
            else:
                no_exp_count += 1
    
    add_field(embed, "⏰ VPS Expiration Status",
        f"**🟢 Active:** {active_exp_count} VPS\n"
        f"**🟡 Expiring Soon:** {expiring_soon_count} VPS\n"
        f"**🔴 Expired:** {expired_count} VPS\n"
        f"**🔵 No Expiration:** {no_exp_count} VPS",
        True)
    
    # System Health Indicator
    health_status = "✅ Excellent"
    health_color = 0x00ff88
    
    if running_nodes == 0:
        health_status = "🔴 Critical - No nodes running"
        health_color = 0xff3366
    elif stopped_nodes > 0:
        health_status = "🟡 Warning - Some nodes offline"
        health_color = 0xffaa00
    elif total_vps == 0:
        health_status = "ℹ️ No VPS deployed"
        health_color = 0x00ccff
    
    add_field(embed, "🏥 System Health", health_status, False)
    
    # Footer with current time
    embed.set_footer(text=f"⚡ RGNODES™ • System Status • Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    icon_url=BOT_ICON_URL)
    
    await ctx.send(embed=embed)


@bot.command(name='status-summary')
@is_admin()
async def status_summary(ctx):
    """
    Quick summary of system status
    """
    # Get quick stats
    nodes = get_nodes()
    total_nodes = len(nodes)
    running_nodes = 0
    
    for node in nodes:
        if node['is_local']:
            running_nodes += 1
        else:
            try:
                response = await asyncio.to_thread(requests.get, str(node['url']).rstrip('/') + '/api/ping', headers={'X-API-Key': str(node['api_key'])}, timeout=3)
                if response.status_code == 200:
                    running_nodes += 1
            except:
                pass
    
    total_vps = sum(len(vps_list) for vps_list in vps_data.values())
    total_users = len(vps_data)
    
    # Count VPS status
    running_vps = 0
    stopped_vps = 0
    suspended_vps = 0
    
    for vps_list in vps_data.values():
        for vps in vps_list:
            if vps.get('suspended', False):
                suspended_vps += 1
            elif vps.get('status') == 'running':
                running_vps += 1
            else:
                stopped_vps += 1
    
    embed = create_success_embed(
        "📈 Quick Status Summary",
        f"**Nodes:** {running_nodes}/{total_nodes} 🟢\n"
        f"**VPS:** {total_vps} total\n"
        f"• Running: {running_vps} 🟢\n"
        f"• Stopped: {stopped_vps} 🔴\n"
        f"• Suspended: {suspended_vps} 🟡\n"
        f"**Users:** {total_users} 👥\n"
        f"**Bot Latency:** {round(bot.latency * 1000)}ms"
    )
    
    embed.set_footer(text=f"Use '{PREFIX}status' for detailed information")
    await ctx.send(embed=embed)

@bot.command(name='admin-add')
@is_main_admin()
async def admin_add(ctx, user: discord.Member):
    user_id = str(user.id)
    if user_id == str(MAIN_ADMIN_ID):
        await ctx.send(embed=create_error_embed("Already Admin", "This user is already the main admin!"))
        return
    if user_id in admin_data.get("admins", []):
        await ctx.send(embed=create_error_embed("Already Admin", f"{user.mention} is already an admin!"))
        return
    admin_data["admins"].append(user_id)
    save_admin_data()
    await ctx.send(embed=create_success_embed("Admin Added", f"{user.mention} is now an admin!"))
    try:
        await user.send(embed=create_embed("🎉 Admin Role Granted", f"You are now an admin by {ctx.author.mention}", 0x00ff88))
    except discord.Forbidden:
        await ctx.send(embed=create_info_embed("Notification Failed", f"Could not DM {user.mention}"))

@bot.command(name='admin-remove')
@is_main_admin()
async def admin_remove(ctx, user: discord.Member):
    user_id = str(user.id)
    if user_id == str(MAIN_ADMIN_ID):
        await ctx.send(embed=create_error_embed("Cannot Remove", "You cannot remove the main admin!"))
        return
    if user_id not in admin_data.get("admins", []):
        await ctx.send(embed=create_error_embed("Not Admin", f"{user.mention} is not an admin!"))
        return
    admin_data["admins"].remove(user_id)
    save_admin_data()
    await ctx.send(embed=create_success_embed("Admin Removed", f"{user.mention} is no longer an admin!"))
    try:
        await user.send(embed=create_embed("⚠️ Admin Role Revoked", f"Your admin role was removed by {ctx.author.mention}", 0xff3366))
    except discord.Forbidden:
        await ctx.send(embed=create_info_embed("Notification Failed", f"Could not DM {user.mention}"))

@bot.command(name='admin-list')
@is_main_admin()
async def admin_list(ctx):
    admins = admin_data.get("admins", [])
    main_admin = await bot.fetch_user(MAIN_ADMIN_ID)
    embed = create_embed("👑 Admin Team", "Current administrators:", 0x1a1a1a)
    add_field(embed, "🔰 Main Admin", f"{main_admin.mention} (ID: {MAIN_ADMIN_ID})", False)
    if admins:
        admin_list = []
        for admin_id in admins:
            try:
                admin_user = await bot.fetch_user(int(admin_id))
                admin_list.append(f"• {admin_user.mention} (ID: {admin_id})")
            except:
                admin_list.append(f"• Unknown User (ID: {admin_id})")
        admin_text = "\n".join(admin_list)
        add_field(embed, "🛡️ Admins", admin_text, False)
    else:
        add_field(embed, "🛡️ Admins", "No additional admins", False)
    await ctx.send(embed=embed)

@bot.command(name="userinfo")
@is_admin()
async def user_info(ctx, user: discord.Member):
    user_id = str(user.id)
    vps_list = vps_data.get(user_id, [])

    # ─── Embed ─────────────────────────────────────────────────
    embed = create_embed(
        title="👤 User Dashboard",
        description=f"Statistics & resources for {user.mention}"
    )

    # ─── Row 1 : User Info ─────────────────────────────────────
    embed.add_field(
        name="👤 User",
        value=(
            f"**Name:** `{user.name}`\n"
            f"**ID:** `{user.id}`\n"
            f"**Joined:** `{user.joined_at.strftime('%Y-%m-%d') if user.joined_at else 'Unknown'}`"
        ),
        inline=True
    )

    target_is_admin = is_admin_user(user)
    embed.add_field(
        name="🛡️ Admin",
        value="✅ Yes" if target_is_admin else "❌ No",
        inline=True
    )

    embed.add_field(
        name="🖥️ VPS Count",
        value=f"`{len(vps_list)}` VPS",
        inline=True
    )

    # ─── If VPS Exists ─────────────────────────────────────────
    if vps_list:
        total_ram = total_cpu = total_storage = 0
        running = suspended = whitelisted = 0

        vps_lines = []

        for i, vps in enumerate(vps_list, start=1):
            node = get_node(vps.get("node_id"))
            node_name = node["name"] if node else "Unknown"

            ram = int(vps.get("ram", "0GB").replace("GB", ""))
            storage = int(vps.get("storage", "0GB").replace("GB", ""))
            cpu = int(vps.get("cpu", 0))

            total_ram += ram
            total_storage += storage
            total_cpu += cpu

            if vps.get("suspended"):
                status = "⛔ SUSPENDED"
                suspended += 1
            elif vps.get("status") == "running":
                status = "🟢 RUNNING"
                running += 1
            else:
                status = "🔴 STOPPED"

            if vps.get("whitelisted"):
                whitelisted += 1

            vps_lines.append(
                f"**{i}.** `{vps['container_name']}`\n"
                f"{status} | `{ram}GB` RAM • `{cpu}` CPU • `{storage}GB` Disk\n"
                f"📍 Node: `{node_name}`" + 
                (f"\n⏰ {('🔴 EXPIRED' if (datetime.fromisoformat(vps['expiration_date']) - datetime.now()).days < 0 else '🟡 EXPIRING' if (datetime.fromisoformat(vps['expiration_date']) - datetime.now()).days <= EXPIRATION_WARNING_DAYS else '🟢 ACTIVE')} • {(datetime.fromisoformat(vps['expiration_date']).strftime('%Y-%m-%d'))} ({max(0, (datetime.fromisoformat(vps['expiration_date']) - datetime.now()).days)}d)" if vps.get('expiration_date') else "\n⏰ No expiration set")
            )

        # ─── Row 2 : VPS Summary ────────────────────────────────
        embed.add_field(
            name="📊 VPS Summary",
            value=(
                f"🖥️ `{len(vps_list)}` Total\n"
                f"🟢 `{running}` Running\n"
                f"⛔ `{suspended}` Suspended\n"
                f"✅ `{whitelisted}` Whitelisted"
            ),
            inline=True
        )

        embed.add_field(
            name="📈 Resources",
            value=(
                f"**RAM:** `{total_ram} GB`\n"
                f"**CPU:** `{total_cpu} Cores`\n"
                f"**Disk:** `{total_storage} GB`"
            ),
            inline=True
        )

        port_quota = get_user_allocation(user_id)
        port_used = get_user_used_ports(user_id)

        embed.add_field(
            name="🌐 Ports",
            value=f"`{port_used}/{port_quota}` Used",
            inline=True
        )

        # ─── VPS List (Split if needed) ────────────────────────
        vps_text = "\n\n".join(vps_lines)
        for i in range(0, len(vps_text), 1024):
            embed.add_field(
                name="📋 VPS List",
                value=vps_text[i:i + 1024],
                inline=False
            )

    else:
        embed.add_field(
            name="🖥️ VPS",
            value="❌ No VPS assigned",
            inline=False
        )

    embed.set_footer(text="⚡ RGNODES™ • User Resource Dashboard")
    embed.timestamp = ctx.message.created_at

    await ctx.send(embed=embed)

@bot.command(name="serverstats")
@is_admin()
async def server_stats(ctx):
    # ─── Counts ────────────────────────────────────────────────
    total_users = len(vps_data)
    total_admins = len(admin_data.get("admins", [])) + 1
    total_vps = sum(len(vps_list) for vps_list in vps_data.values())

    total_ram = total_cpu = total_storage = 0
    running_vps = suspended_vps = stopped_vps = 0
    whitelisted_vps = 0

    # ─── VPS Data ──────────────────────────────────────────────
    for vps_list in vps_data.values():
        for vps in vps_list:
            total_ram += int(vps.get("ram", "0GB").replace("GB", ""))
            total_storage += int(vps.get("storage", "0GB").replace("GB", ""))
            total_cpu += int(vps.get("cpu", 0))

            if vps.get("status") == "running":
                if vps.get("suspended", False):
                    suspended_vps += 1
                else:
                    running_vps += 1
            else:
                stopped_vps += 1

            if vps.get("whitelisted", False):
                whitelisted_vps += 1

    # ─── Ports ─────────────────────────────────────────────────
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT SUM(allocated_ports) FROM port_allocations")
    total_ports_allocated = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM port_forwards")
    total_ports_used = cur.fetchone()[0] or 0
    conn.close()

    # ─── Embed ─────────────────────────────────────────────────
    embed = create_embed(
        title="📊 Server Statistics",
        description="**Live Infrastructure Dashboard**"
    )

    # ── Row 1 ──────────────────────────────────────────────────
    embed.add_field(
        name="👥 Users",
        value=f"`{total_users}` Users\n`{total_admins}` Admins",
        inline=True
    )

    embed.add_field(
        name="🖥️ VPS",
        value=(
            f"Total: `{total_vps}`\n"
            f"🟢 `{running_vps}` Running\n"
            f"⛔ `{suspended_vps}` Suspended"
        ),
        inline=True
    )

    embed.add_field(
        name="📌 Status",
        value=(
            f"🔴 `{stopped_vps}` Stopped\n"
            f"✅ `{whitelisted_vps}` Whitelisted"
        ),
        inline=True
    )

    # ── Row 2 ──────────────────────────────────────────────────
    embed.add_field(
        name="📈 RAM",
        value=f"`{total_ram} GB`",
        inline=True
    )

    embed.add_field(
        name="⚙️ CPU",
        value=f"`{total_cpu} Cores`",
        inline=True
    )

    embed.add_field(
        name="💾 Storage",
        value=f"`{total_storage} GB`",
        inline=True
    )

    # ─── Expiration Counts ─────────────────────────────────────
    expiring_soon_count = 0
    expired_count = 0
    active_exp_count = 0
    no_exp_count = 0
    
    for vps_list in vps_data.values():
        for vps in vps_list:
            if vps.get('expiration_date'):
                expiration_dt = datetime.fromisoformat(vps['expiration_date'])
                days_remaining = (expiration_dt - datetime.now()).days
                if days_remaining < 0:
                    expired_count += 1
                elif days_remaining <= EXPIRATION_WARNING_DAYS:
                    expiring_soon_count += 1
                else:
                    active_exp_count += 1
            else:
                no_exp_count += 1

    # ── Row 3 ──────────────────────────────────────────────────
    embed.add_field(
        name="⏰ Expiration",
        value=(
            f"🟢 `{active_exp_count}` Active\n"
            f"🟡 `{expiring_soon_count}` Expiring Soon\n"
            f"🔴 `{expired_count}` Expired\n"
            f"🔵 `{no_exp_count}` No Exp"
        ),
        inline=True
    )

    embed.add_field(
        name="🌐 Ports Allocated",
        value=f"`{total_ports_allocated}`",
        inline=True
    )

    embed.add_field(
        name="🔌 Ports In Use",
        value=f"`{total_ports_used}`",
        inline=True
    )

    # ── Row 4 ──────────────────────────────────────────────────

    # ── Row 4 ──────────────────────────────────────────────────
    embed.add_field(
        name="📊 Port Utilization",
        value=(
            f"`{total_ports_used}/{total_ports_allocated}`"
            if total_ports_allocated else "`N/A`"
        ),
        inline=True
    )

    embed.set_footer(text="⚡ RGNODES™ • Real-Time Monitoring")
    embed.timestamp = ctx.message.created_at

    await ctx.send(embed=embed)

@bot.command(name='vpsinfo')
@is_admin()
async def vps_info(ctx, container_name: str = None):
    if not container_name:
        all_vps = []
        for user_id, vps_list in vps_data.items():
            try:
                user = await bot.fetch_user(int(user_id))
                for i, vps in enumerate(vps_list):
                    node = get_node(vps['node_id'])
                    node_name = node['name'] if node else "Unknown"
                    status_text = vps.get('status', 'unknown').upper()
                    if vps.get('suspended', False):
                        status_text += " (SUSPENDED)"
                    if vps.get('whitelisted', False):
                        status_text += " (WHITELISTED)"
                    
                    # Add expiration info
                    expiration_text = ""
                    if vps.get('expiration_date'):
                        expiration_dt = datetime.fromisoformat(vps['expiration_date'])
                        days_remaining = (expiration_dt - datetime.now()).days
                        if days_remaining < 0:
                            expiration_text = " • 🔴 EXPIRED"
                        elif days_remaining <= EXPIRATION_WARNING_DAYS:
                            expiration_text = f" • 🟡 EXPIRING ({days_remaining}d)"
                        else:
                            expiration_text = f" • 🟢 ({days_remaining}d)"
                    
                    all_vps.append(f"**{user.name}** - VPS {i+1}: `{vps['container_name']}` - {status_text} (Node: {node_name}){expiration_text}")
            except:
                pass
        vps_text = "\n".join(all_vps)
        chunks = [vps_text[i:i+1024] for i in range(0, len(vps_text), 1024)]
        for idx, chunk in enumerate(chunks, 1):
            embed = create_embed(f"🖥️ All VPS (Part {idx}/{len(chunks)})", f"Complete list of all VPS deployments with expiration status", 0x2ecc71)
            add_field(embed, "VPS Inventory", chunk, False)
            embed.set_footer(text=f"⚡ RGNODES™ • VPS Information System")
            await ctx.send(embed=embed)
    else:
        found_vps = None
        found_user = None
        for user_id, vps_list in vps_data.items():
            for vps in vps_list:
                if vps['container_name'] == container_name:
                    found_vps = vps
                    found_user = await bot.fetch_user(int(user_id))
                    break
            if found_vps:
                break
        if not found_vps:
            await ctx.send(embed=create_error_embed("VPS Not Found", f"No VPS found with container name: `{container_name}`"))
            return
        node = get_node(found_vps['node_id'])
        node_name = node['name'] if node else "Unknown"
        
        # Determine status color based on expiration and suspension
        status_color = 0x1a1a1a
        if found_vps.get('suspended', False):
            status_color = 0xffaa00
        elif found_vps.get('expiration_date'):
            expiration_dt = _safe_fromiso(found_vps['expiration_date'])
            if expiration_dt == datetime.max:
                add_field(embed, 'Status', '⚠️ INVALID EXPIRATION DATA', True)
                await ctx.send(embed=embed)
                return
            days_remaining = (expiration_dt - datetime.now()).days
            if days_remaining < 0:
                status_color = 0xff3366
            elif days_remaining <= EXPIRATION_WARNING_DAYS:
                status_color = 0xffaa00
            else:
                status_color = 0x2ecc71
        
        suspended_text = " (SUSPENDED)" if found_vps.get('suspended', False) else ""
        whitelisted_text = " (WHITELISTED)" if found_vps.get('whitelisted', False) else ""
        embed = create_embed(f"🖥️ VPS Information - {container_name}", f"Detailed VPS profile owned by {found_user.mention}{suspended_text}{whitelisted_text}")
        
        add_field(embed, "👤 Owner", f"**Name:** {found_user.name}\n**ID:** `{found_user.id}`\n**Mention:** {found_user.mention}", False)
        
        add_field(embed, "🌐 Location & Node", f"**Node:** {node_name}\n**Node Type:** {'📍 Local' if node.get('is_local') else '🌐 Remote'}\n**Node ID:** `{found_vps.get('node_id', 1)}`", True)
        
        add_field(embed, "📊 Specifications", f"**RAM:** `{found_vps['ram']}`\n**CPU:** `{found_vps['cpu']}` Cores\n**Storage:** `{found_vps['storage']}`\n**Config:** {found_vps.get('config', 'Custom')}", True)
        
        # Status information
        status_info = f"**Current Status:** `{found_vps.get('status', 'unknown').upper()}`\n"
        status_info += f"**Suspended:** {'🟡 Yes' if found_vps.get('suspended', False) else '🟢 No'}\n"
        status_info += f"**Whitelisted:** {'✅ Yes' if found_vps.get('whitelisted', False) else '❌ No'}\n"
        status_info += f"**Created:** `{found_vps.get('created_at', 'Unknown')}`"
        add_field(embed, "📈 Status", status_info, False)
        
        # Expiration information
        if found_vps.get('expiration_date'):
            expiration_dt = datetime.fromisoformat(found_vps['expiration_date'])
            days_remaining = (expiration_dt - datetime.now()).days
            
            if days_remaining < 0:
                exp_status = "🔴 EXPIRED"
                exp_color = "FF3366"
            elif days_remaining <= EXPIRATION_WARNING_DAYS:
                exp_status = "🟡 EXPIRING SOON"
                exp_color = "FFAA00"
            else:
                exp_status = "🟢 ACTIVE"
                exp_color = "2ECC71"
            
            exp_info = f"**Status:** {exp_status}\n"
            exp_info += f"**Expires On:** `{expiration_dt.strftime('%Y-%m-%d %H:%M:%S')}`\n"
            exp_info += f"**Days Remaining:** `{max(0, days_remaining)}` days\n"
            exp_info += f"**Time Left:** `{max(0, days_remaining)} days` from today"
            add_field(embed, "⏰ Expiration", exp_info, False)
        else:
            add_field(embed, "⏰ Expiration", f"**Status:** 🔵 No expiration date set\n**Action:** Use `{PREFIX}set-expiration` to configure", False)
        
        if found_vps.get('shared_with'):
            shared_users = []
            for shared_id in found_vps['shared_with']:
                try:
                    shared_user = await bot.fetch_user(int(shared_id))
                    shared_users.append(f"• {shared_user.mention} (`{shared_id}`)")
                except:
                    shared_users.append(f"• Unknown User (`{shared_id}`)")
            shared_text = "\n".join(shared_users)
            add_field(embed, "🔗 Shared Access", shared_text, False)
        
        # Port forwarding info
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM port_forwards WHERE vps_container = ?', (container_name,))
        port_count = cur.fetchone()[0]
        cur.execute('SELECT * FROM port_forwards WHERE vps_container = ? LIMIT 5', (container_name,))
        ports = cur.fetchall()
        conn.close()
        
        if port_count > 0:
            port_info = f"**Total:** `{port_count}` forwarded ports (TCP & UDP)\n"
            if ports:
                port_info += "**Active Forwards:**\n"
                for p in ports:
                    port_info += f"  • `{p['host_port']}` → VPS:`{p['vps_port']}`\n"
                if port_count > 5:
                    port_info += f"  • ... +{port_count - 5} more"
            add_field(embed, "🌐 Port Forwarding", port_info, False)
        else:
            add_field(embed, "🌐 Port Forwarding", "**Status:** No active port forwards", False)
        
        # OS information
        add_field(embed, "🐧 Operating System", f"`{found_vps.get('os_version', 'ubuntu:22.04')}`", True)
        
        embed.set_footer(text=f"⚡ RGNODES™ • VPS Information System • Container: {container_name}")
        await ctx.send(embed=embed)

@bot.command(name='restart-vps')
@is_admin()
async def restart_vps(ctx, container_name: str):
    node_id = find_node_id_for_container(container_name)
    _, _, target = find_vps_record(container_name)
    if not target:
        await ctx.send(embed=create_error_embed("VPS Not Found", f"`{container_name}` was not found."))
        return
    if target.get('suspended', False):
        await ctx.send(embed=create_error_embed("VPS Suspended", "This VPS is suspended. Use the appropriate unsuspend/renew command first."))
        return
    await ctx.send(embed=create_info_embed("Restarting VPS", f"Restarting VPS `{container_name}`..."))
    try:
        await execute_lxc(container_name, f"restart {container_name}", node_id=node_id)
        for user_id, vps_list in vps_data.items():
            for vps in vps_list:
                if vps['container_name'] == container_name:
                    vps['status'] = 'running'
                    save_vps_data_immediate()
                    break
        await apply_internal_permissions(container_name, node_id)
        await install_anti_mining_guard(container_name, node_id)
        await apply_guest_motd(container_name, node_id)
        await recreate_port_forwards(container_name)
        await ctx.send(embed=create_success_embed("VPS Restarted", f"VPS `{container_name}` has been restarted successfully!"))
    except Exception as e:
        await ctx.send(embed=create_error_embed("Restart Failed", f"Error: {str(e)}"))

@bot.command(name='exec')
@is_admin()
async def execute_command(ctx, container_name: str, *, command: str):
    node_id = find_node_id_for_container(container_name)
    await ctx.send(embed=create_info_embed("Executing Command", f"Running command in VPS `{container_name}`..."))
    try:
        output = await _exec_guest_bash(container_name, node_id, command, timeout=300)
        embed = create_embed(f"Command Output - {container_name}", f"Command: `{command}`")
        if output.strip():
            if len(output) > 1000:
                output = output[:1000] + "\n... (truncated)"
            add_field(embed, "📤 Output", f"```\n{output}\n```", False)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(embed=create_error_embed("Execution Failed", f"Error: {str(e)}"))

@bot.command(name='stop-vps-all')
@is_admin()
async def stop_all_vps(ctx):
    embed = create_warning_embed("Stopping All VPS", "⚠️ **WARNING:** This will stop all **bot-managed** running VPS across all configured nodes.\n\nUnmanaged LXC instances are not touched. Continue?")
    class ConfirmView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)

        @discord.ui.button(label="Stop All VPS", style=discord.ButtonStyle.danger)
        async def confirm(self, interaction: discord.Interaction, item: discord.ui.Button):
            if str(interaction.user.id) != str(ctx.author.id):
                await interaction.response.send_message(embed=create_error_embed("Access Denied", "Only the admin who started this operation can confirm it."), ephemeral=True)
                return
            await interaction.response.defer()
            try:
                stopped_count = 0
                failed = []
                for user_id, vps_list in list(vps_data.items()):
                    for vps in list(vps_list):
                        container = str(vps.get('container_name') or '')
                        if not container:
                            continue
                        node_id = int(vps.get('node_id', 1))
                        try:
                            await execute_lxc(container, f"stop {container} --force", timeout=180, node_id=node_id)
                        except Exception as e:
                            msg = str(e).lower()
                            if not any(x in msg for x in ("not running", "already stopped", "is stopped")):
                                failed.append(f"{container}: {str(e)[:180]}")
                                continue
                        if vps.get('status') != 'stopped':
                            stopped_count += 1
                        vps['status'] = 'stopped'
                save_vps_data_immediate()
                description = f"Ensured **{stopped_count}** managed VPS instances are stopped."
                if failed:
                    description += f"\n\n**Failures:** {len(failed)}\n" + "\n".join(f"• {x}" for x in failed[:8])
                embed = create_success_embed("All Managed VPS Stopped", description)
                await interaction.followup.send(embed=embed)
            except Exception as e:
                embed = create_error_embed("Error", f"Error stopping VPS: {str(e)}")
                await interaction.followup.send(embed=embed)

        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
        async def cancel(self, interaction: discord.Interaction, item: discord.ui.Button):
            if str(interaction.user.id) != str(ctx.author.id):
                await interaction.response.send_message(embed=create_error_embed("Access Denied", "Only the admin who started this operation can cancel it."), ephemeral=True)
                return
            await interaction.response.edit_message(embed=create_info_embed("Operation Cancelled", "The stop all VPS operation has been cancelled."))

    await ctx.send(embed=embed, view=ConfirmView())

@bot.command(name='cpu-monitor')
@is_admin()
async def resource_monitor_control(ctx, action: str = "status"):
    global resource_monitor_active
    if action.lower() == "status":
        status = "Active" if resource_monitor_active else "Inactive"
        embed = create_embed("Resource Monitor Status", f"Resource monitoring is currently **{status}** (logs only; no auto-stop)", 0x00ccff if resource_monitor_active else 0xffaa00)
        add_field(embed, "Thresholds", f"{CPU_THRESHOLD}% CPU / {RAM_THRESHOLD}% RAM usage", True)
        add_field(embed, "Check Interval", f"60 seconds (all nodes)", True)
        await ctx.send(embed=embed)
    elif action.lower() == "enable":
        resource_monitor_active = True
        await ctx.send(embed=create_success_embed("Resource Monitor Enabled", "Resource monitoring has been enabled."))
    elif action.lower() == "disable":
        resource_monitor_active = False
        await ctx.send(embed=create_warning_embed("Resource Monitor Disabled", "Resource monitoring has been disabled."))
    else:
        await ctx.send(embed=create_error_embed("Invalid Action", f"Use: `{PREFIX}cpu-monitor <status|enable|disable>`"))

@bot.command(name='resize-vps')
@is_admin()
async def resize_vps(ctx, container_name: str, ram: int = None, cpu: int = None, disk: int = None):
    if ram is None and cpu is None and disk is None:
        await ctx.send(embed=create_error_embed("Missing Parameters", "Please specify at least one resource to resize (ram, cpu, or disk)"))
        return
    found_vps = None
    user_id = None
    vps_index = None
    for uid, vps_list in vps_data.items():
        for i, vps in enumerate(vps_list):
            if vps['container_name'] == container_name:
                found_vps = vps
                user_id = uid
                vps_index = i
                break
        if found_vps:
            break
    if not found_vps:
        await ctx.send(embed=create_error_embed("VPS Not Found", f"No VPS found with container name: `{container_name}`"))
        return
    node_id = found_vps['node_id']
    was_running = found_vps.get('status') == 'running' and not found_vps.get('suspended', False)
    disk_changed = disk is not None
    if was_running:
        await ctx.send(embed=create_info_embed("Stopping VPS", f"Stopping VPS `{container_name}` to apply resource changes..."))
        try:
            await execute_lxc(container_name, f"stop {container_name}", node_id=node_id)
            found_vps['status'] = 'stopped'
            save_vps_data_immediate()
        except Exception as e:
            await ctx.send(embed=create_error_embed("Stop Failed", f"Error stopping VPS: {str(e)}"))
            return
    changes = []
    try:
        new_ram = int(found_vps['ram'].replace('GB', ''))
        new_cpu = int(found_vps['cpu'])
        new_disk = int(found_vps['storage'].replace('GB', ''))
        if ram is not None and ram > 0:
            new_ram = ram
            ram_mb = ram * 1024
            await execute_lxc(container_name, f"config set {container_name} limits.memory {ram_mb}MB", node_id=node_id)
            changes.append(f"RAM: {ram}GB")
        if cpu is not None and cpu > 0:
            new_cpu = cpu
            await execute_lxc(container_name, f"config set {container_name} limits.cpu {cpu}", node_id=node_id)
            changes.append(f"CPU: {cpu} cores")
        if disk is not None and disk > 0:
            new_disk = disk
            await execute_lxc(container_name, f"config device set {container_name} root size={disk}GB", node_id=node_id)
            changes.append(f"Disk: {disk}GB")
        found_vps['ram'] = f"{new_ram}GB"
        found_vps['cpu'] = str(new_cpu)
        found_vps['storage'] = f"{new_disk}GB"
        found_vps['config'] = f"{new_ram}GB RAM / {new_cpu} CPU / {new_disk}GB Disk"
        vps_data[user_id][vps_index] = found_vps
        save_vps_data_immediate()
        if was_running:
            await execute_lxc(container_name, f"start {container_name}", node_id=node_id)
            found_vps['status'] = 'running'
            save_vps_data_immediate()
            await apply_internal_permissions(container_name, node_id)
            await recreate_port_forwards(container_name)
        embed = create_success_embed("VPS Resized", f"Successfully resized resources for VPS `{container_name}`")
        add_field(embed, "Changes Applied", "\n".join(changes), False)
        if disk_changed:
            add_field(embed, "Disk Note", "Run `sudo resize2fs /` inside the VPS to expand the filesystem.", False)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(embed=create_error_embed("Resize Failed", f"Error: {str(e)}"))

@bot.command(name='clone-vps')
@is_admin()
async def clone_vps(ctx, container_name: str, new_name: str = None):
    """Clone a managed VPS using the same canonical rgnodes-vps-{VMID} naming scheme."""
    source_node_id = find_node_id_for_container(container_name)
    found_vps = None
    user_id = None
    for uid, vps_list in vps_data.items():
        for vps in vps_list:
            if str(vps.get('container_name')) == container_name:
                found_vps, user_id = vps, str(uid)
                break
        if found_vps:
            break
    if not found_vps:
        await ctx.send(embed=create_error_embed('🖥️ VPS Not Found', f'No VPS found with container name: `{container_name}`'))
        return
    new_vmid = reserve_vps_vmid()
    new_name = f'{VPS_HOSTNAME}-{new_vmid}'
    await ctx.send(embed=create_info_embed('📋 VPS Clone', f'Preparing `{new_name}` from `{container_name}`.'))
    created = False
    try:
        await execute_lxc(container_name, f'copy {container_name} {new_name}', node_id=source_node_id)
        created = True
        await apply_lxc_config(new_name, source_node_id)
        await execute_lxc(new_name, f'start {new_name}', node_id=source_node_id)
        await apply_internal_permissions(new_name, source_node_id)
        await safe_guest_install(new_name, source_node_id)
        if DOCKER_INSTALL_ON_DEPLOY:
            await ensure_docker_ready(new_name, source_node_id, strict=DOCKER_STRICT_DEPLOY)
        clone_password = generate_strong_password()
        clone_ssh_ok, clone_ssh_result = await configure_ssh(new_name, source_node_id, clone_password)
        if not clone_ssh_ok:
            logger.warning('Cloned VPS %s SSH setup deferred: %s', new_name, clone_ssh_result)
        new_vps = dict(found_vps)
        new_vps.update({
            'container_name': new_name, 'status': 'running', 'suspended': False,
            'whitelisted': False, 'suspension_history': [], 'created_at': datetime.now().isoformat(),
            'shared_with': [], 'id': None, 'vmid': new_vmid, 'root_password': clone_password,
            'sshx_url': None, 'sshx_started_at': None, 'ssh_ready': bool(clone_ssh_ok),
            'pinggy_host': None, 'pinggy_port': None, 'pinggy_url': None, 'pinggy_pid': None,
            'bandwidth_gb': VPS_BANDWIDTH_GB, 'bandwidth_used_bytes': 0,
            'bandwidth_cycle_start': datetime.now().isoformat(), 'bandwidth_last_rx_bytes': 0,
            'bandwidth_last_tx_bytes': 0, 'bandwidth_last_sample_at': None,
        })
        vps_data.setdefault(user_id, []).append(new_vps)
        try:
            save_vps_data()
        except Exception as exc:
            vps_data[user_id].remove(new_vps)
            if created:
                try:
                    await execute_lxc(new_name, f'delete {new_name} --force', timeout=180, node_id=source_node_id)
                except Exception:
                    logger.critical(f'Clone rollback failed for {new_name}', exc_info=True)
            raise RuntimeError(f'Clone was created but database persistence failed: {exc}') from exc
        await create_port_forward(user_id, new_name, 22, source_node_id)
        endpoints = await detect_public_endpoints(source_node_id)
        ssh_forward = next((int(f['host_port']) for f in get_user_forwards(user_id) if str(f.get('vps_container')) == new_name and int(f.get('vps_port',0)) == 22), None)
        access = format_public_ssh_access(endpoints, ssh_forward)
        embed = create_success_embed('✅ VPS Cloned', f'Created `{new_name}` from `{container_name}`.')
        add_field(embed, '🖥️ VPS', f'VMID: `{new_vmid}`\nHostname: `{VPS_HOSTNAME}`\nNode: `{(get_node(source_node_id) or {}).get("name", "Unknown")}`', False)
        add_field(embed, '📦 Resources', f'RAM: `{new_vps["ram"]}`\nCPU: `{new_vps["cpu"]}` Core(s)\nSSD: `{new_vps["storage"]}`\nBandwidth: `{int(new_vps.get("bandwidth_gb") or VPS_BANDWIDTH_GB)} GB`', False)
        add_field(embed, '💻 SSH IPv4', f'`{access["ssh_ipv4"]}`' if access['ssh_ipv4'] else 'Unavailable', False)
        add_field(embed, '🌐 SSH IPv6', f'`{access["ssh_ipv6"]}`' if access['ssh_ipv6'] else 'Unavailable', False)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(embed=create_error_embed('❌ Clone Failed', str(e)[:900]))

@bot.command(name='migrate-vps')
@is_admin()
async def migrate_vps(ctx, container_name: str, target_node_id: int):
    """Safely refuse unsupported cross-node migration rather than risking source loss."""
    source_node_id = find_node_id_for_container(container_name)
    source_node = get_node(source_node_id)
    target_node = get_node(target_node_id)
    if not source_node or not target_node:
        await ctx.send(embed=create_error_embed("🌐 Invalid Node", "Source or target node does not exist."))
        return
    if int(source_node_id) == int(target_node_id):
        await ctx.send(embed=create_warning_embed("🌐 Same Node", "The VPS is already on the selected node."))
        return
    await ctx.send(embed=create_warning_embed(
        "🛡️ Migration Blocked Safely",
        "Cross-node migration is disabled with the current node-agent contract because the target cannot safely access the source container.\n\n"
        "The previous implementation could stop the source before the copy was actually possible. No VPS data was changed.",
    ))

@bot.command(name='vps-stats')
@is_admin()
async def vps_stats(ctx, container_name: str):
    node_id = find_node_id_for_container(container_name)
    await ctx.send(embed=create_info_embed("Gathering Statistics", f"Collecting statistics for VPS `{container_name}`..."))
    try:
        stats = await get_container_stats(container_name, node_id)
        embed = create_embed(f"📊 VPS Statistics - {container_name}", f"Resource usage statistics", 0x1a1a1a)
        add_field(embed, "📈 Status", f"**{stats['status'].upper()}**", False)
        add_field(embed, "💻 CPU Usage", f"**{stats['cpu']:.1f}%**", True)
        add_field(embed, "🧠 Memory Usage", f"**{stats['ram']['used']}/{stats['ram']['total']} MB ({stats['ram']['pct']:.1f}%)**", True)
        add_field(embed, "💾 Disk Usage", f"**{stats['disk']}**", True)
        add_field(embed, "⏱️ Uptime", f"**{stats['uptime']}**", True)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(embed=create_error_embed("Statistics Failed", f"Error: {str(e)}"))


@bot.command(name='node-check')
@is_admin()
async def node_check(ctx, node_id: int):
    """Check node status and available storage pools"""
    node = get_node(node_id)
    if not node:
        await ctx.send(embed=create_error_embed("Node Not Found", f"Node ID {node_id} not found."))
        return
    
    embed = create_info_embed(f"Node Check - {node['name']}", 
                             f"Checking status and configuration of node {node['name']}...")
    
    # Check if node is reachable
    status = await get_node_status(node_id)
    add_field(embed, "📡 Connection Status", status, False)
    
    if status.startswith("🟢"):
        # Try to get storage pools
        try:
            pools_output = await execute_lxc("", "storage list", node_id=node_id, timeout=30)
            add_field(embed, "💾 Available Storage Pools", f"```{pools_output}```", False)
            
            # Try to get default profile
            try:
                profile_output = await execute_lxc("", "profile list", node_id=node_id, timeout=30)
                add_field(embed, "📋 Available Profiles", f"```{profile_output[:500]}...```", False)
            except Exception as e:
                add_field(embed, "📋 Profiles", f"Error: {str(e)[:200]}", False)
                
        except Exception as e:
            add_field(embed, "💾 Storage Pools", f"Error: {str(e)[:200]}", False)
        
        # Check remote API endpoint
        try:
            test_response = await asyncio.to_thread(requests.get, str(node['url']).rstrip('/') + '/api/ping', headers={'X-API-Key': str(node['api_key'])}, timeout=5)
            add_field(embed, "🔌 API Endpoint", f"✅ Reachable\nURL: {node['url']}", False)
        except Exception as e:
            add_field(embed, "🔌 API Endpoint", f"❌ Unreachable\nError: {str(e)[:200]}", False)
    else:
        add_field(embed, "⚠️ Status", "Node is offline or unreachable", False)
    
    await ctx.send(embed=embed)

@bot.command(name='vps-network')
@is_admin()
async def vps_network(ctx, container_name: str, action: str, value: str = None):
    node_id = find_node_id_for_container(container_name)
    if action.lower() not in ["list", "add", "remove", "limit"]:
        await ctx.send(embed=create_error_embed("Invalid Action", f"Use: `{PREFIX}vps-network <container> <list|add|remove|limit> [value]`"))
        return
    try:
        if action.lower() == "list":
            output = await execute_lxc(container_name, f"exec {container_name} -- ip addr", node_id=node_id)
            if len(output) > 1000:
                output = output[:1000] + "\n... (truncated)"
            embed = create_embed(f"🌐 Network Interfaces - {container_name}", "Network configuration", 0x1a1a1a)
            add_field(embed, "Interfaces", f"```\n{output}\n```", False)
            await ctx.send(embed=embed)
        elif action.lower() == "limit" and value:
            await execute_lxc(container_name, f"config device set {container_name} eth0 limits.egress {value}", node_id=node_id)
            await execute_lxc(container_name, f"config device set {container_name} eth0 limits.ingress {value}", node_id=node_id)
            await ctx.send(embed=create_success_embed("Network Limited", f"Set network limit to {value} for `{container_name}`"))
        elif action.lower() == "add" and value:
            await execute_lxc(container_name, f"config device add {container_name} eth1 nic nictype=bridged parent={value}", node_id=node_id)
            await ctx.send(embed=create_success_embed("Network Added", f"Added network interface to VPS `{container_name}` with bridge `{value}`"))
        elif action.lower() == "remove" and value:
            await execute_lxc(container_name, f"config device remove {container_name} {value}", node_id=node_id)
            await ctx.send(embed=create_success_embed("Network Removed", f"Removed network interface `{value}` from VPS `{container_name}`"))
        else:
            await ctx.send(embed=create_error_embed("Invalid Parameters", "Please provide valid parameters for the action"))
    except Exception as e:
        await ctx.send(embed=create_error_embed("Network Management Failed", f"Error: {str(e)}"))

@bot.command(name='vps-processes')
@is_admin()
async def vps_processes(ctx, container_name: str):
    node_id = find_node_id_for_container(container_name)
    await ctx.send(embed=create_info_embed("Gathering Processes", f"Listing processes in VPS `{container_name}`..."))
    try:
        output = await execute_lxc(container_name, f"exec {container_name} -- ps aux", node_id=node_id)
        if len(output) > 1000:
            output = output[:1000] + "\n... (truncated)"
        embed = create_embed(f"⚙️ Processes - {container_name}", "Running processes", 0x1a1a1a)
        add_field(embed, "Process List", f"```\n{output}\n```", False)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(embed=create_error_embed("Process Listing Failed", f"Error: {str(e)}"))

@bot.command(name='vps-logs')
async def vps_logs(ctx, container_name: str, lines: int = 50):
    """Show real guest logs plus RGNODES audit events for an owned/admin VPS."""
    lines = max(5, min(100, int(lines)))
    owner_id, _, vps = find_vps_record(container_name)
    if not vps:
        await ctx.send(embed=create_error_embed("VPS Not Found", f"`{container_name}` was not found."))
        return
    if str(ctx.author.id) != str(owner_id) and not is_admin_user(ctx.author):
        await ctx.send(embed=create_error_embed("Access Denied", "You can only view logs for your own VPS unless you are an administrator."))
        return
    container = str(vps.get("container_name"))
    node_id = int(vps.get("node_id", 1))
    await ctx.send(embed=create_info_embed("📋 Gathering VPS Logs", f"Fetching `{lines}` lines from `{container}`..."))
    guest = ""
    try:
        guest = str(await execute_lxc(container, f"exec {shlex.quote(container)} -- bash -lc 'if command -v journalctl >/dev/null 2>&1; then journalctl -n {lines} --no-pager -o short-iso; elif [ -f /var/log/syslog ]; then tail -n {lines} /var/log/syslog; else dmesg | tail -n {lines}; fi'", node_id=node_id, timeout=40) or "")
    except Exception as exc:
        guest = f"Guest log retrieval failed: {exc}"
    rows = get_recent_audit_logs(min(20, lines), vps_container=container)
    audit = "\n".join(f"{r.get('created_at','')[:19]} | {r.get('action','Event')} | {r.get('detail','')}" for r in rows) or "No RGNODES audit events yet."
    guest = guest[-2200:] if guest else "No guest log output."
    audit = audit[-1600:]
    embed = create_info_embed("📋 VPS Logs", f"`{container}` • Owner `{owner_id}` • Node `{node_id}`")
    add_field(embed, "Guest System Logs", f"```text\n{guest}\n```", False)
    add_field(embed, "RGNODES Audit", f"```text\n{audit}\n```", False)
    await ctx.send(embed=embed)
    channel_id = _audit_channel_id()
    if channel_id and (not getattr(ctx.channel, 'id', None) or int(ctx.channel.id) != int(channel_id)):
        try:
            target = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
            raw_bundle = f"RGNODES VPS LOG SNAPSHOT\nVPS: {container}\nOwner: {owner_id}\nNode: {node_id}\nGenerated: {datetime.now().isoformat()}\n\n=== GUEST SYSTEM LOGS ===\n{guest}\n\n=== RGNODES AUDIT ===\n{audit}\n"
            if hasattr(target, 'send'):
                await _publish_log_bundle(target, embed, raw_bundle, f"vps-{container}-logs.txt")
        except Exception as exc:
            logger.debug('Failed to publish VPS logs to log channel: %s', exc)
    await record_audit_event("vps", "VPS Logs Viewed", f"Fetched guest + audit logs ({lines} lines).", user_id=ctx.author.id, node_id=node_id, vps_container=container)

@bot.command(name='vps-uptime')
@is_admin()
async def vps_uptime(ctx, container_name: str):
    node_id = find_node_id_for_container(container_name)
    uptime = await get_container_uptime(container_name, node_id)
    embed = create_info_embed("VPS Uptime", f"Uptime for `{container_name}`: {uptime}")
    await ctx.send(embed=embed)

@bot.command(name='vps-password')
@is_admin()
async def vps_password(ctx, container_name: str = None):
    """View or manage VPS root passwords"""
    if not container_name:
        # Show all passwords for all VPS
        password_list = []
        for user_id, vps_list in vps_data.items():
            try:
                user = await bot.fetch_user(int(user_id))
                for vps in vps_list:
                    password = vps.get('root_password', 'Not Set')
                    if password == 'Not Set':
                        password_display = "❌ Not Set"
                    else:
                        password_display = f"🔐 `{password}`"
                    password_list.append(f"**{user.name}** - `{vps['container_name']}`: {password_display}")
            except:
                pass
        
        if not password_list:
            await ctx.send(embed=create_info_embed("No Passwords", "No VPS passwords found in database."))
            return
        
        password_text = "\n".join(password_list)
        chunks = [password_text[i:i+1024] for i in range(0, len(password_text), 1024)]
        for idx, chunk in enumerate(chunks, 1):
            embed = create_embed(f"🔐 VPS Root Passwords (Part {idx}/{len(chunks)})", "Root passwords for all VPS", 0xff6b6b)
            add_field(embed, "Passwords", chunk, False)
            add_field(embed, "⚠️ Security Notice", "These passwords are sensitive. Do not share them publicly.", False)
            embed.set_footer(text=f"⚡ RGNODES™ • Password Management")
            await ctx.send(embed=embed)
    else:
        # Show password for specific VPS
        found_vps = None
        found_user = None
        for user_id, vps_list in vps_data.items():
            for vps in vps_list:
                if vps['container_name'] == container_name:
                    found_vps = vps
                    found_user = await bot.fetch_user(int(user_id))
                    break
            if found_vps:
                break
        
        if not found_vps:
            await ctx.send(embed=create_error_embed("VPS Not Found", f"No VPS found with container name: `{container_name}`"))
            return
        
        password = found_vps.get('root_password', 'Not Set')
        if password == 'Not Set':
            embed = create_info_embed("Password Not Set", f"VPS `{container_name}` does not have a stored password.")
        else:
            embed = create_success_embed("VPS Password", f"Root password for VPS `{container_name}`")
            add_field(embed, "Owner", f"{found_user.mention}", True)
            add_field(embed, "Container", f"`{container_name}`", True)
            add_field(embed, "🔐 Password", f"`{password}`", False)
            add_field(embed, "Usage", f"SSH as `root` with this password", False)
        
        embed.set_footer(text=f"⚡ RGNODES™ • Password Information")
        await ctx.send(embed=embed)

@bot.command(name='suspend-vps')
@is_admin()
async def suspend_vps(ctx, container_name: str, *, reason: str = "Admin action"):
    node_id = find_node_id_for_container(container_name)
    found = False
    for uid, lst in vps_data.items():
        for vps in lst:
            if vps['container_name'] == container_name:
                if vps.get('status') != 'running':
                    await ctx.send(embed=create_error_embed("Cannot Suspend", "VPS must be running to suspend."))
                    return
                try:
                    await execute_lxc(container_name, f"stop {container_name}", node_id=node_id)
                    vps['status'] = 'stopped'
                    vps['suspended'] = True
                    if 'suspension_history' not in vps:
                        vps['suspension_history'] = []
                    vps['suspension_history'].append({
                        'time': datetime.now().isoformat(),
                        'reason': reason,
                        'by': f"{ctx.author.name} ({ctx.author.id})"
                    })
                    save_vps_data_immediate()
                except Exception as e:
                    await ctx.send(embed=create_error_embed("Suspend Failed", str(e)))
                    return
                try:
                    owner = await bot.fetch_user(int(uid))
                    embed = create_warning_embed("🚨 VPS Suspended", f"Your VPS `{container_name}` has been suspended by an admin.\n\n**Reason:** {reason}\n\nContact an admin to unsuspend.")
                    await owner.send(embed=embed)
                except Exception as dm_e:
                    logger.error(f"Failed to DM owner {uid}: {dm_e}")
                await ctx.send(embed=create_success_embed("VPS Suspended", f"VPS `{container_name}` suspended. Reason: {reason}"))
                found = True
                break
        if found:
            break
    if not found:
        await ctx.send(embed=create_error_embed("Not Found", f"VPS `{container_name}` not found."))

@bot.command(name='unsuspend-vps')
@is_admin()
async def unsuspend_vps(ctx, container_name: str):
    node_id = find_node_id_for_container(container_name)
    found = False
    for uid, lst in vps_data.items():
        for vps in lst:
            if vps['container_name'] == container_name:
                if not vps.get('suspended', False):
                    await ctx.send(embed=create_error_embed("Not Suspended", "VPS is not suspended."))
                    return
                try:
                    try:
                        await execute_lxc(container_name, f"start {container_name}", node_id=node_id)
                    except Exception as start_error:
                        msg = str(start_error).lower()
                        if "already running" not in msg and "is running" not in msg:
                            raise
                    await apply_internal_permissions(container_name, node_id)
                    await install_anti_mining_guard(container_name, node_id)
                    await recreate_port_forwards(container_name)
                    vps['suspended'] = False
                    vps['status'] = 'running'
                    save_vps_data_immediate()
                    await ctx.send(embed=create_success_embed("VPS Unsuspended", f"VPS `{container_name}` unsuspended and started."))
                    found = True
                except Exception as e:
                    await ctx.send(embed=create_error_embed("Start Failed", str(e)))
                try:
                    owner = await bot.fetch_user(int(uid))
                    embed = create_success_embed("🟢 VPS Unsuspended", f"Your VPS `{container_name}` has been unsuspended by an admin.\nYou can now manage it again.")
                    await owner.send(embed=embed)
                except Exception as dm_e:
                    logger.error(f"Failed to DM owner {uid} about unsuspension: {dm_e}")
                break
        if found:
            break
    if not found:
        await ctx.send(embed=create_error_embed("Not Found", f"VPS `{container_name}` not found."))

@bot.command(name='suspension-logs')
@is_admin()
async def suspension_logs(ctx, container_name: str = None):
    if container_name:
        found = None
        for lst in vps_data.values():
            for vps in lst:
                if vps['container_name'] == container_name:
                    found = vps
                    break
            if found:
                break
        if not found:
            await ctx.send(embed=create_error_embed("Not Found", f"VPS `{container_name}` not found."))
            return
        history = found.get('suspension_history', [])
        if not history:
            await ctx.send(embed=create_info_embed("No Suspensions", f"No suspension history for `{container_name}`."))
            return
        embed = create_embed("Suspension History", f"For `{container_name}`")
        text = []
        for h in sorted(history, key=lambda x: x['time'], reverse=True)[:10]:
            t = datetime.fromisoformat(h['time']).strftime('%Y-%m-%d %H:%M:%S')
            text.append(f"**{t}** - {h['reason']} (by {h['by']})")
        add_field(embed, "History", "\n".join(text), False)
        if len(history) > 10:
            add_field(embed, "Note", "Showing last 10 entries.")
        await ctx.send(embed=embed)
    else:
        all_logs = []
        for uid, lst in vps_data.items():
            for vps in lst:
                h = vps.get('suspension_history', [])
                for event in sorted(h, key=lambda x: x['time'], reverse=True):
                    t = datetime.fromisoformat(event['time']).strftime('%Y-%m-%d %H:%M')
                    all_logs.append(f"**{t}** - VPS `{vps['container_name']}` (Owner: <@{uid}>) - {event['reason']} (by {event['by']})")
        if not all_logs:
            await ctx.send(embed=create_info_embed("No Suspensions", "No suspension events recorded."))
            return
        logs_text = "\n".join(all_logs)
        chunks = [logs_text[i:i+1024] for i in range(0, len(logs_text), 1024)]
        for idx, chunk in enumerate(chunks, 1):
            embed = create_embed(f"Suspension Logs (Part {idx})", f"Global suspension events (newest first)")
            add_field(embed, "Events", chunk, False)
            await ctx.send(embed=embed)

@bot.command(name='docker-repair')
async def docker_repair_cmd(ctx):
    target=next(iter(vps_data.get(str(ctx.author.id), [])), None)
    if not target:
        await ctx.send(embed=create_error_embed('🐳 No VPS', 'This account does not have a managed VPS.'))
        return
    if maintenance_enabled() and not is_admin_user(ctx.author):
        await ctx.send(embed=create_warning_embed('🟠 Under maintenance', 'User VPS actions are temporarily disabled.'))
        return
    container=str(target.get('container_name') or '')
    node_id=int(target.get('node_id',1))
    try:
        repaired=await ensure_docker_ready(container,node_id,strict=False)
        status=await get_container_docker_status(container,node_id)
        add=create_info_embed('🐳 Docker Repair', f'`{container}`')
        add_field(add,'Status',status,False)
        add_field(add,'Repair', '✅ Verified and ready.' if repaired else '⚠️ Docker could not be verified on this nested guest.', False)
        await ctx.send(embed=add)
    except Exception as e:
        await ctx.send(embed=create_error_embed('🐳 Docker Repair Failed',str(e)[:900]))

@bot.command(name='apply-permissions')
@is_admin()
async def apply_permissions(ctx, container_name: str):
    node_id = find_node_id_for_container(container_name)
    await ctx.send(embed=create_info_embed("Applying Permissions", f"Applying advanced permissions to `{container_name}`..."))
    try:
        status = await get_container_status(container_name, node_id)
        was_running = status == 'running'
        if was_running:
            await execute_lxc(container_name, f"stop {container_name}", node_id=node_id)
        await apply_lxc_config(container_name, node_id)
        await execute_lxc(container_name, f"start {container_name}", node_id=node_id)
        await apply_internal_permissions(container_name, node_id)
        await recreate_port_forwards(container_name)
        for user_id, vps_list in vps_data.items():
            for vps in vps_list:
                if vps['container_name'] == container_name:
                    vps['status'] = 'running'
                    vps['suspended'] = False
                    save_vps_data_immediate()
                    break
        await ctx.send(embed=create_success_embed("Permissions Applied", f"Advanced permissions applied to VPS `{container_name}`. Docker-ready with unprivileged ports!"))
    except Exception as e:
        await ctx.send(embed=create_error_embed("Apply Failed", f"Error: {str(e)}"))

@bot.command(name='resource-check')
@is_admin()
async def resource_check(ctx):
    suspended_count = 0
    embed = create_info_embed("Resource Check", "Checking all running VPS for high resource usage...")
    msg = await ctx.send(embed=embed)
    for user_id, vps_list in vps_data.items():
        for vps in vps_list:
            if vps.get('status') == 'running' and not vps.get('suspended', False) and not vps.get('whitelisted', False):
                container = vps['container_name']
                node_id = vps['node_id']
                stats = await get_container_stats(container, node_id)
                cpu = stats['cpu']
                ram = stats['ram']['pct']
                if cpu > CPU_THRESHOLD or ram > RAM_THRESHOLD:
                    reason = f"High resource usage: CPU {cpu:.1f}%, RAM {ram:.1f}% (threshold: {CPU_THRESHOLD}% CPU / {RAM_THRESHOLD}% RAM)"
                    logger.warning(f"Suspending {container}: {reason}")
                    try:
                        await execute_lxc(container, f"stop {container}", node_id=node_id)
                        vps['status'] = 'stopped'
                        vps['suspended'] = True
                        if 'suspension_history' not in vps:
                            vps['suspension_history'] = []
                        vps['suspension_history'].append({
                            'time': datetime.now().isoformat(),
                            'reason': reason,
                            'by': 'Manual Resource Check'
                        })
                        save_vps_data_immediate()
                        try:
                            owner = await bot.fetch_user(int(user_id))
                            warn_embed = create_warning_embed("🚨 VPS Auto-Suspended", f"Your VPS `{container}` has been suspended due to high resource usage.\n\n**Reason:** {reason}\n\nContact admin to unsuspend and address the issue.")
                            await owner.send(embed=warn_embed)
                        except Exception as dm_e:
                            logger.error(f"Failed to DM owner {user_id}: {dm_e}")
                        suspended_count += 1
                    except Exception as e:
                        logger.error(f"Failed to suspend {container}: {e}")
    final_embed = create_info_embed("Resource Check Complete", f"Checked all VPS. Suspended {suspended_count} high-usage VPS.")
    await msg.edit(embed=final_embed)

@bot.command(name='whitelist-vps')
@is_admin()
async def whitelist_vps(ctx, container_name: str, action: str):
    if action.lower() not in ['add', 'remove']:
        await ctx.send(embed=create_error_embed("Invalid Action", f"Use: `{PREFIX}whitelist-vps <container> <add|remove>`"))
        return
    found = False
    for user_id, vps_list in vps_data.items():
        for vps in vps_list:
            if vps['container_name'] == container_name:
                if action.lower() == 'add':
                    vps['whitelisted'] = True
                    msg = "added to whitelist (exempt from auto-suspension)"
                else:
                    vps['whitelisted'] = False
                    msg = "removed from whitelist"
                save_vps_data_immediate()
                await ctx.send(embed=create_success_embed("Whitelist Updated", f"VPS `{container_name}` {msg}."))
                found = True
                break
        if found:
            break
    if not found:
        await ctx.send(embed=create_error_embed("Not Found", f"VPS `{container_name}` not found."))

@bot.command(name='maintenance')
@is_admin()
async def maintenance_command(ctx, action: str = "status"):
    action = action.lower().strip()
    if action == "status":
        if maintenance_enabled():
            await ctx.send(embed=create_error_embed("🔴 Under Maintenance", "🔴 **Under Maintenance**\n🛠️ **SOON for Fixing..**\n\nThis maintenance state applies to users only. Administrators remain fully operational."))
        else:
            await ctx.send(embed=create_success_embed("🟢 Service Operational", "Maintenance mode is **OFF**. User dashboards have returned to the VPS's live runtime status."))
        return
    if action not in {"on", "off"}:
        await ctx.send(embed=create_error_embed("Usage", f"Use `{PREFIX}maintenance on`, `{PREFIX}maintenance off`, or `{PREFIX}maintenance status`"))
        return
    set_setting("maintenance", action)
    if action == "on":
        await record_audit_event("system", "Maintenance ON", "Maintenance enabled for normal users; administrators remain operational.", user_id=ctx.author.id)
        await ctx.send(embed=create_error_embed("🔴 Under Maintenance", "Maintenance mode is now **ON** for users.\n\n🔴 **Under Maintenance**\n🛠️ **SOON for Fixing..**\n\nAdministrators remain fully operational."))
        return

    await record_audit_event("system", "Maintenance OFF", "Maintenance disabled; normal user VPS access restored.", user_id=ctx.author.id)
    await ctx.send(embed=create_success_embed("🟢 Service Operational", "Maintenance mode is now **OFF**. User dashboards have returned to the VPS live runtime status."))


@bot.command(name='setexpire')
@is_admin()
async def setexpire(ctx, container_name: str, days: int):
    if days <= 0:
        await ctx.send(embed=create_error_embed("Invalid Days", "Days must be greater than 0."))
        return
    uid, idx, vps = find_vps_record(container_name)
    if not vps:
        await ctx.send(embed=create_error_embed("VPS Not Found", f"`{container_name}` was not found."))
        return
    actual_container = str(vps['container_name'])
    old_key = (actual_container, str(vps.get('expiration_date'))) if vps.get('expiration_date') else None
    vps['expiration_date'] = (datetime.now() + timedelta(days=days)).isoformat()
    if old_key:
        EXPIRATION_WARNING_SENT.discard(old_key)
        EXPIRATION_EXPIRED_NOTICE_SENT.discard(old_key)
    save_vps_data_immediate()
    await ctx.send(embed=create_success_embed("Expiration Set", f"`{actual_container}` now expires in **{days} days**."))


@bot.command(name='extendexpire')
@is_admin()
async def extendexpire(ctx, container_name: str, days: int):
    if days <= 0:
        await ctx.send(embed=create_error_embed("Invalid Days", "Days must be greater than 0."))
        return
    uid, idx, vps = find_vps_record(container_name)
    if not vps:
        await ctx.send(embed=create_error_embed("VPS Not Found", f"`{container_name}` was not found."))
        return
    actual_container = str(vps['container_name'])
    current = _safe_fromiso(vps.get('expiration_date')) if vps.get('expiration_date') else datetime.now()
    if current == datetime.max:
        current = datetime.now()
    old_key = (actual_container, str(vps.get('expiration_date'))) if vps.get('expiration_date') else None
    vps['expiration_date'] = (max(current, datetime.now()) + timedelta(days=days)).isoformat()
    auto_unsuspended = False
    if suspended_due_to_expiration(vps):
        try:
            node_id = int(vps.get('node_id', 1))
            try:
                await execute_lxc(actual_container, f"start {actual_container}", node_id=node_id)
            except Exception as start_error:
                msg = str(start_error).lower()
                if 'already running' not in msg and 'is running' not in msg:
                    raise
            vps['status'] = 'running'
            vps['suspended'] = False
            await apply_internal_permissions(actual_container, node_id)
            await recreate_port_forwards(actual_container)
            auto_unsuspended = True
        except Exception as e:
            logger.warning(f"Could not auto-unsuspend {actual_container}: {e}")
    if old_key:
        EXPIRATION_WARNING_SENT.discard(old_key)
        EXPIRATION_EXPIRED_NOTICE_SENT.discard(old_key)
    save_vps_data_immediate()
    suspension_state = "Auto-unsuspended" if auto_unsuspended else "Preserved"
    await ctx.send(embed=create_success_embed("Expiration Extended", f"`{actual_container}` was extended by **{days} days**.\n\nSuspension: **{suspension_state}**"))


@bot.command(name='removeexpire')
@is_admin()
async def removeexpire(ctx, container_name: str):
    uid, idx, vps = find_vps_record(container_name)
    if not vps:
        await ctx.send(embed=create_error_embed("VPS Not Found", f"`{container_name}` was not found."))
        return
    actual_container = str(vps['container_name'])
    old_key = (actual_container, str(vps.get('expiration_date'))) if vps.get('expiration_date') else None
    vps['expiration_date'] = None
    if old_key:
        EXPIRATION_WARNING_SENT.discard(old_key)
        EXPIRATION_EXPIRED_NOTICE_SENT.discard(old_key)
    save_vps_data_immediate()
    await ctx.send(embed=create_success_embed("Expiration Removed", f"`{actual_container}` now has no expiration date."))


async def _resolve_backup_path(container_name: str, requested: Optional[str] = None) -> Optional[Path]:
    safe_prefix = sanitize_username_for_container(container_name)
    if requested:
        p = (VPS_BACKUP_DIR / Path(requested).name).resolve()
        try:
            p.relative_to(VPS_BACKUP_DIR.resolve())
        except ValueError:
            return None
        return p if p.is_file() else None
    candidates = sorted(VPS_BACKUP_DIR.glob(f"{safe_prefix}_*.tar.gz"))
    return candidates[-1] if candidates else None


@bot.command(name='backup-vps')
@is_admin()
async def backup_vps(ctx, container_name: str):
    uid, idx, vps = find_vps_record(container_name)
    if not vps:
        await ctx.send(embed=create_error_embed("VPS Not Found", f"`{container_name}` was not found."))
        return
    container_name = str(vps['container_name'])
    node = get_node(vps.get('node_id', 1))
    if not node or not node.get('is_local'):
        await ctx.send(embed=create_error_embed("Unsupported Node", "VPS backups currently require a local LXD node."))
        return
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup_file = VPS_BACKUP_DIR / f"{sanitize_username_for_container(container_name)}_{stamp}.tar.gz"
    await ctx.send(embed=create_info_embed("📦 VPS Backup", f"Exporting `{container_name}` to `{backup_file.name}`..."))
    try:
        await execute_lxc(container_name, f"export {container_name} {shlex.quote(str(backup_file))} --instance-only", timeout=1800, node_id=vps.get('node_id', 1))
        if not backup_file.exists() or backup_file.stat().st_size < 1024:
            raise RuntimeError("LXC export returned without a usable backup file.")
        await ctx.send(embed=create_success_embed("Backup Complete", f"Created `{backup_file.name}` ({backup_file.stat().st_size / 1024 / 1024:.1f} MiB)."))
    except Exception as e:
        await ctx.send(embed=create_error_embed("Backup Failed", str(e)[:1000]))


@bot.command(name='restore-vps')
@is_admin()
async def restore_vps(ctx, container_name: str, backup_file: str = None):
    """Safely restore a local-LXD VPS using a validated temporary instance and rollback rename."""
    uid, idx, vps = find_vps_record(container_name)
    if not vps:
        await ctx.send(embed=create_error_embed("VPS Not Found", f"`{container_name}` was not found."))
        return
    container_name = str(vps['container_name'])
    node_id = int(vps.get('node_id', 1))
    node = get_node(node_id)
    if not node or not node.get('is_local'):
        await ctx.send(embed=create_error_embed("Unsupported Node", "VPS restore currently requires a local LXD node."))
        return

    path = await _resolve_backup_path(container_name, backup_file)
    if not path:
        await ctx.send(embed=create_error_embed("Backup Not Found", "No valid backup file was found in the VPS backup directory."))
        return

    class RestoreView(discord.ui.View):
        def __init__(self, admin_id):
            super().__init__(timeout=60)
            self.admin_id = str(admin_id)
            self.confirmed = False
        @discord.ui.button(label="✅ Confirm Restore", style=discord.ButtonStyle.danger)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            if str(interaction.user.id) != self.admin_id:
                await interaction.response.send_message(embed=create_error_embed("Access Denied", "Only the admin who started the restore can confirm."), ephemeral=True)
                return
            self.confirmed = True
            await interaction.response.defer()
            self.stop()
        @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
        async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
            if str(interaction.user.id) != self.admin_id:
                await interaction.response.send_message(embed=create_error_embed("Access Denied", "Only the admin who started the restore can cancel."), ephemeral=True)
                return
            await interaction.response.edit_message(embed=create_info_embed("Restore Cancelled", "No changes were made."), view=None)
            self.stop()

    previous_status = str(vps.get('status', 'stopped')).lower()
    previous_suspended = bool(vps.get('suspended', False))
    should_run_after_restore = previous_status == 'running' and not previous_suspended
    temp_name = sanitize_username_for_container(f"rgnodes-restore-{int(vps.get('vmid', vps.get('id', 0)) or 0)}-{datetime.now().strftime('%H%M%S')}")[:55]
    rollback_name = sanitize_username_for_container(f"{container_name}-rollback-{datetime.now().strftime('%H%M%S')}")[:55]
    if temp_name == container_name:
        temp_name = sanitize_username_for_container(f"rgnodes-restore-{datetime.now().strftime('%Y%m%d%H%M%S')}")[:55]

    confirm_embed = create_warning_embed(
        "⚠️ Restore VPS",
        f"A validated temporary LXC will be imported first. The existing `{container_name}` stays untouched until validation succeeds.\n\nBackup: `{path.name}`\nPrevious state: **{('SUSPENDED' if previous_suspended else previous_status.upper())}**"
    )
    view = RestoreView(ctx.author.id)
    await ctx.send(embed=confirm_embed, view=view)
    await view.wait()
    if not view.confirmed:
        return

    await ctx.send(embed=create_info_embed("Restoring VPS", f"Validating `{path.name}` in temporary instance `{temp_name}`..."))
    original_exists = False
    rollback_created = False
    new_instance_ready = False
    password = vps.get('root_password') or generate_strong_password()

    try:
        try:
            await execute_lxc('', f"info {container_name}", node_id=node_id)
            original_exists = True
        except Exception:
            original_exists = False

        # Remove stale temporary/rollback names if an earlier interrupted restore left them behind.
        for stale in (temp_name, rollback_name):
            try:
                await execute_lxc(stale, f"delete {stale} --force", node_id=node_id)
            except Exception:
                pass

        # Import while the real VPS is still intact.
        storage_pool = await resolve_storage_pool(node_id)
        await execute_lxc(
            temp_name,
            f"import {shlex.quote(str(path))} {temp_name} --storage {shlex.quote(storage_pool)}",
            timeout=1800,
            node_id=node_id,
        )

        # Imported snapshots/config may contain old RGNODES proxy devices. Remove the known
        # persistent forwarding devices before validation so the temporary instance cannot
        # collide with the current host ports.
        with DB_LOCK:
            conn = get_db()
            try:
                forward_rows = conn.execute(
                    "SELECT host_port FROM port_forwards WHERE vps_container = ? ORDER BY host_port",
                    (container_name,),
                ).fetchall()
            finally:
                conn.close()
        for row in forward_rows:
            hp = int(row[0])
            for proto in ("tcp", "udp"):
                try:
                    await execute_lxc(temp_name, f"config device remove {temp_name} rgnodes-pf-{proto}-{hp}", node_id=node_id)
                except Exception:
                    pass

        await apply_lxc_config(temp_name, node_id)
        await execute_lxc(temp_name, f"start {temp_name}", timeout=180, node_id=node_id)
        await safe_guest_install(temp_name, node_id)
        ok, result = await configure_ssh(temp_name, node_id, password)
        if not ok:
            raise RuntimeError(f"SSH validation failed: {result}")
        await set_guest_hostname(temp_name, node_id, VPS_HOSTNAME)
        await execute_lxc(temp_name, f"exec {temp_name} -- bash -lc 'true'", timeout=60, node_id=node_id)
        await execute_lxc(temp_name, f"stop {temp_name} --force", timeout=120, node_id=node_id)
        new_instance_ready = True

        # Atomic-ish same-host swap with rollback: rename old -> rollback, temp -> original.
        if original_exists:
            try:
                await execute_lxc(container_name, f"stop {container_name} --force", timeout=120, node_id=node_id)
            except Exception:
                pass
            await execute_lxc(container_name, f"rename {container_name} {rollback_name}", timeout=180, node_id=node_id)
            rollback_created = True

        try:
            await execute_lxc(temp_name, f"rename {temp_name} {container_name}", timeout=180, node_id=node_id)
        except Exception:
            if rollback_created:
                try:
                    await execute_lxc(rollback_name, f"rename {rollback_name} {container_name}", timeout=180, node_id=node_id)
                except Exception:
                    pass
            raise

        # Restore original lifecycle state instead of forcing every restore to RUNNING.
        if should_run_after_restore:
            await execute_lxc(container_name, f"start {container_name}", timeout=180, node_id=node_id)
            await apply_internal_permissions(container_name, node_id)
            readded = await recreate_port_forwards(container_name)
        else:
            readded = 0
            if not previous_suspended:
                # The VPS was intentionally stopped, so keep it stopped; no active proxy devices.
                readded = 0

        await set_guest_hostname(container_name, node_id, VPS_HOSTNAME)
        vps['status'] = 'running' if should_run_after_restore else 'stopped'
        vps['suspended'] = previous_suspended
        vps['root_password'] = password
        save_vps_data_immediate()

        if rollback_created:
            try:
                await execute_lxc(rollback_name, f"delete {rollback_name} --force", timeout=300, node_id=node_id)
            except Exception as cleanup_error:
                logger.warning(f"Restored VPS but could not delete rollback instance {rollback_name}: {cleanup_error}")

        if previous_suspended:
            await ctx.send(embed=create_success_embed("Restore Complete", f"`{container_name}` restored successfully and remains **SUSPENDED** to preserve its previous state."))
        else:
            await ctx.send(embed=create_success_embed("Restore Complete", f"`{container_name}` restored successfully from `{path.name}`. State preserved: **{'RUNNING' if should_run_after_restore else 'STOPPED'}**. Port forwards restored: **{readded}**."))

    except Exception as e:
        logger.error(f"Restore failed for {container_name}: {e}", exc_info=True)

        # If the new instance was swapped in but failed during finalization, restore rollback.
        try:
            if rollback_created:
                try:
                    await execute_lxc(container_name, f"stop {container_name} --force", timeout=120, node_id=node_id)
                except Exception:
                    pass
                try:
                    await execute_lxc(container_name, f"delete {container_name} --force", timeout=180, node_id=node_id)
                except Exception:
                    pass
                await execute_lxc(rollback_name, f"rename {rollback_name} {container_name}", timeout=180, node_id=node_id)
                if should_run_after_restore:
                    await execute_lxc(container_name, f"start {container_name}", timeout=180, node_id=node_id)
                    await recreate_port_forwards(container_name)
        except Exception as rollback_error:
            logger.critical(f"ROLLBACK FAILED for {container_name}: {rollback_error}", exc_info=True)

        try:
            await execute_lxc(temp_name, f"delete {temp_name} --force", timeout=180, node_id=node_id)
        except Exception:
            pass
        vps['status'] = previous_status if previous_status in {'running', 'stopped'} else 'stopped'
        vps['suspended'] = previous_suspended
        save_vps_data_immediate()
        await ctx.send(embed=create_error_embed("Restore Failed", f"The restore was not committed safely. Original VPS state was preserved where possible.\n\n`{str(e)[:1000]}`"))


@bot.command(name='backup-db')
@is_admin()
async def backup_db(ctx):
    try:
        backup_database()
        backup_files = sorted(DB_BACKUP_DIR.glob("vps_backup_*.db"))
        latest = backup_files[-1].name if backup_files else "backup"
        await ctx.send(
            embed=create_success_embed(
                "DB Backup Created",
                f"Consistent SQLite backup created: `{latest}`"
            )
        )
    except Exception as e:
        await ctx.send(embed=create_error_embed("Backup Failed", f"Error: {str(e)}"))

@bot.command(name='repair-ports')
@is_admin()
async def repair_ports(ctx, container_name: str):
    await ctx.send(embed=create_info_embed("Repairing Ports", f"Re-adding port forward devices for `{container_name}`..."))
    try:
        readded = await recreate_port_forwards(container_name)
        await ctx.send(embed=create_success_embed("Ports Repaired", f"Re-added {readded} port forwards for `{container_name}`."))
    except Exception as e:
        await ctx.send(embed=create_error_embed("Repair Failed", f"Error: {str(e)}"))

@bot.command(name='set-expiration')
@is_admin()
async def set_expiration(ctx, container_name: str, days: int):
    """Set VPS expiration date (admin only)"""
    if days <= 0:
        await ctx.send(embed=create_error_embed("Invalid Days", "Days must be a positive number."))
        return
    
    found_vps = None
    user_id = None
    vps_index = None
    
    for uid, vps_list in vps_data.items():
        for i, vps in enumerate(vps_list):
            if vps['container_name'] == container_name:
                found_vps = vps
                user_id = uid
                vps_index = i
                break
        if found_vps:
            break
    
    if not found_vps:
        await ctx.send(embed=create_error_embed("VPS Not Found", f"No VPS found with container name: `{container_name}`"))
        return
    
    # Calculate expiration date
    expiration_date = (datetime.now() + timedelta(days=days)).isoformat()
    found_vps['expiration_date'] = expiration_date
    vps_data[user_id][vps_index] = found_vps
    save_vps_data_immediate()
    
    # Get owner info
    try:
        owner = await bot.fetch_user(int(user_id))
        owner_mention = owner.mention
    except:
        owner_mention = f"User {user_id}"
    
    embed = create_success_embed("Expiration Date Set", 
        f"VPS `{container_name}` expiration date set for {days} days from now")
    add_field(embed, "Owner", owner_mention, True)
    add_field(embed, "Expires On", datetime.fromisoformat(expiration_date).strftime('%Y-%m-%d %H:%M:%S'), True)
    add_field(embed, "Days Remaining", str(days), True)
    
    await ctx.send(embed=embed)
    
    # Notify owner
    try:
        owner = await bot.fetch_user(int(user_id))
        dm_embed = create_info_embed("⏰ VPS Expiration Date Set",
            f"Your VPS `{container_name}` will expire in {days} days.\n\n"
            f"**Expires:** {datetime.fromisoformat(expiration_date).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Contact admin to renew your VPS before it expires.")
        await owner.send(embed=dm_embed)
    except:
        pass

async def process_vps_renewal(vps: Dict[str, Any], requested_days: int = None, user_initiated: bool = False) -> tuple[bool, str]:
    '''Central renewal logic: owner can renew in the last two days or after expiry; admins can renew anytime.'''
    days = int(requested_days or VPS_RENEWAL_DAYS)
    if days <= 0:
        return False, 'Renewal duration must be greater than zero.'
    now = datetime.now()
    raw = vps.get('expiration_date')
    try:
        current = datetime.fromisoformat(str(raw)) if raw else now
    except (TypeError, ValueError):
        current = now
    seconds_left = (current - now).total_seconds()
    window = max(0, RENEWAL_WINDOW_DAYS) * 86400
    if user_initiated and seconds_left > window:
        left = max(1, int(seconds_left // 86400))
        return False, f'Renewal opens during the final **{RENEWAL_WINDOW_DAYS} days** before expiry. Your VPS still has about **{left} days** remaining.'

    container = str(vps['container_name'])
    old_key = (container, str(raw)) if raw else None
    was_expiry_suspended = suspended_due_to_expiration(vps)
    new_expiration = max(current, now) + timedelta(days=days)
    if was_expiry_suspended:
        node_id = int(vps.get('node_id', 1))
        try:
            try:
                await execute_lxc(container, f'start {container}', timeout=180, node_id=node_id)
            except Exception as e:
                msg = str(e).lower()
                if 'already running' not in msg and 'is running' not in msg:
                    raise
            vps['status'] = 'running'
            vps['suspended'] = False
            await apply_internal_permissions(container, node_id)
            await install_anti_mining_guard(container, node_id)
            await recreate_port_forwards(container)
        except Exception as e:
            return False, f'The VPS could not be safely restarted, so renewal was not committed: `{str(e)[:600]}`'
    vps['expiration_date'] = new_expiration.isoformat()
    if old_key:
        EXPIRATION_WARNING_SENT.discard(old_key)
        EXPIRATION_EXPIRED_NOTICE_SENT.discard(old_key)
    save_vps_data_immediate()
    state = '✅ Auto-unsuspended' if was_expiry_suspended and not vps.get('suspended') else '✅ State preserved'
    return True, f'`{container}` renewed for **{days} days**.\n**New expiry:** `{new_expiration.strftime("%Y-%m-%d %H:%M:%S")}`\n**Suspension:** {state}'


@bot.command(name='renew')
async def renew_user(ctx, container_name: str = None):
    '''User renewal command. Adds 60 days during the final two-day window.'''
    owner_id = str(ctx.author.id)
    owned = list(vps_data.get(owner_id, []))
    if not owned:
        await ctx.send(embed=create_error_embed('No VPS Found', 'You do not currently own a VPS.'))
        return
    if container_name:
        wanted = str(container_name).strip()
        target = next((v for v in owned if str(v.get('container_name')) == wanted or str(v.get('id')) == wanted or str(v.get('vmid')) == wanted), None)
    elif len(owned) == 1:
        target = owned[0]
    else:
        await ctx.send(embed=create_warning_embed('Select a VPS', f'Usage: `{PREFIX}renew <vps-id-or-name>`'))
        return
    if not target:
        await ctx.send(embed=create_error_embed('VPS Not Found', 'That VPS does not belong to your account.'))
        return
    ok, message = await process_vps_renewal(target, VPS_RENEWAL_DAYS, user_initiated=True)
    if not ok:
        await ctx.send(embed=create_warning_embed('Renewal Unavailable', message))
        return
    await ctx.send(embed=create_success_embed('⏰ VPS Renewed', message))
    try:
        await ctx.author.send(embed=create_success_embed('⏰ VPS Renewed', message))
    except Exception:
        pass


@bot.command(name='renew-vps')
@is_admin()
async def renew_vps(ctx, container_name: str, additional_days: int = None):
    try:
        days = int(additional_days if additional_days is not None else VPS_RENEWAL_DAYS)
    except (TypeError, ValueError):
        await ctx.send(embed=create_error_embed('Invalid Days', 'Renewal days must be a positive integer.'))
        return
    if days <= 0:
        await ctx.send(embed=create_error_embed('Invalid Days', 'Renewal days must be greater than 0.'))
        return
    uid, idx, vps = find_vps_record(container_name)
    if not vps:
        await ctx.send(embed=create_error_embed('VPS Not Found', f'No VPS found with ID/name: `{container_name}`'))
        return
    ok, message = await process_vps_renewal(vps, days, user_initiated=False)
    if not ok:
        await ctx.send(embed=create_error_embed('Renewal Failed', message))
        return
    await ctx.send(embed=create_success_embed('⏰ VPS Renewed', message))
    try:
        owner = await bot.fetch_user(int(uid))
        await owner.send(embed=create_success_embed('⏰ VPS Renewed', message))
    except Exception:
        pass


@bot.command(name='dm-mass')
@is_admin()
async def dm_mass(ctx, *, message: str = None):
    """Send an admin announcement only to users who currently own managed VPS records."""
    message = (message or '').strip()
    if not message:
        await ctx.send(embed=create_error_embed('📢 Message Required', f'Usage: `{PREFIX}dm-mass <message>`'))
        return
    if len(message) > 1800:
        await ctx.send(embed=create_error_embed('📏 Message Too Long', 'Keep the announcement below 1800 characters.'))
        return

    recipients = []
    seen = set()
    for owner_id, items in vps_data.items():
        if not items:
            continue
        try:
            uid = int(owner_id)
        except (TypeError, ValueError):
            continue
        if uid not in seen:
            seen.add(uid)
            recipients.append(uid)

    if not recipients:
        await ctx.send(embed=create_warning_embed('📢 No VPS Users', 'No users currently own a managed VPS.'))
        return

    confirm = create_warning_embed(
        '📢 VPS User Announcement',
        f'This will DM **{len(recipients)}** current VPS owner(s).\n\n**Message:**\n{message}\n\nContinue?',
    )

    class DMConfirmView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.confirmed = False

        @discord.ui.button(label='✅ Send', style=discord.ButtonStyle.secondary)
        async def send_now(self, interaction: discord.Interaction, button: discord.ui.Button):
            if str(interaction.user.id) != str(ctx.author.id):
                await interaction.response.send_message(embed=create_error_embed('⛔ Access Denied', 'Only the admin who started this announcement can confirm it.'), ephemeral=True)
                return
            self.confirmed = True
            await interaction.response.defer()
            self.stop()
            sent = failed = 0
            announcement = create_info_embed('📢 RGNODES™ Announcement', message)
            add_field(announcement, 'ℹ️ Scope', 'Sent only to users with a managed VPS record.', False)
            for uid in recipients:
                try:
                    user = await bot.fetch_user(uid)
                    await user.send(embed=announcement)
                    sent += 1
                except (discord.Forbidden, discord.NotFound, discord.HTTPException) as e:
                    failed += 1
                    logger.warning(f'DM mass delivery failed for {uid}: {e}')
                await asyncio.sleep(1.0)
            await interaction.followup.send(embed=create_success_embed(
                '📨 Announcement Complete',
                f'✅ Sent: **{sent}**\n⚠️ Failed/blocked: **{failed}**\n👥 Eligible: **{len(recipients)}**',
            ))

        @discord.ui.button(label='❌ Cancel', style=discord.ButtonStyle.secondary)
        async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
            if str(interaction.user.id) != str(ctx.author.id):
                await interaction.response.send_message(embed=create_error_embed('⛔ Access Denied', 'Only the admin who started this announcement can cancel it.'), ephemeral=True)
                return
            await interaction.response.edit_message(embed=create_info_embed('📢 Announcement Cancelled', 'No DMs were sent.'), view=None)
            self.stop()

    await ctx.send(embed=confirm, view=DMConfirmView())


@bot.command(name="ssh")
async def ssh_command(ctx, container_name: str = None):
    """Open normal SSH access only. This command never starts SSHX."""
    caller_id = str(ctx.author.id)
    if maintenance_enabled() and not is_admin_user(ctx.author):
        await ctx.send(embed=create_warning_embed('🟠 Under maintenance', 'User VPS actions are temporarily disabled.'))
        return
    admin = is_admin_user(ctx.author)
    owned = list(vps_data.get(caller_id, []))
    target_user_id = caller_id
    target = None
    if container_name:
        target_user_id, _, target = find_vps_record(container_name)
        if not target:
            await ctx.send(embed=create_error_embed("🖥️ VPS Not Found", f"No VPS was found for `{container_name}`."))
            return
        if not admin and str(target_user_id) != caller_id:
            await ctx.send(embed=create_error_embed("⛔ Access Denied", "You can only open SSH for your own VPS."))
            return
    elif len(owned) == 1:
        target = owned[0]
    else:
        await ctx.send(embed=create_warning_embed("🖥️ Select a VPS", f"Usage: `{PREFIX}ssh <vmid|container-name>`"))
        return
    container = str(target.get("container_name") or "")
    node_id = int(target.get("node_id", 1))
    if target.get("suspended"):
        await ctx.send(embed=create_error_embed("⛔ VPS Suspended", "Renew or ask support to unsuspend this VPS."))
        return
    try:
        stats = await asyncio.wait_for(get_container_stats(container, node_id), timeout=20)
        if str(stats.get("status", "")).lower() != "running":
            await ctx.send(embed=create_warning_embed("⏸️ VPS Not Running", f"`{container}` is stopped. Start it first."))
            return
        forwards = get_user_forwards(target_user_id)
        ssh_port = next((int(f["host_port"]) for f in forwards if str(f.get("vps_container")) == container and int(f.get("vps_port",0)) == 22), None)
        if not ssh_port:
            ssh_port = await create_port_forward(target_user_id, container, 22, node_id)
        endpoints = await detect_public_endpoints(node_id)
        access_info = format_public_ssh_access(endpoints, ssh_port)
        access = create_success_embed("💻 RGNODES™ SSH", f"`{container}` • `{VPS_HOSTNAME}`")
        if access_info.get("ssh_ipv4"):
            add_field(access, "💻 SSH IPv4", f"```bash\n{access_info['ssh_ipv4']}\n```", False)
        else:
            add_field(access, "💻 SSH IPv4", "⚠️ Public IPv4 unavailable on this node.", False)
        if access_info.get("ssh_ipv6"):
            add_field(access, "🌐 SSH IPv6", f"```bash\n{access_info['ssh_ipv6']}\n```", False)
        else:
            add_field(access, "🌐 SSH IPv6", "⚪ Public IPv6 unavailable on this node.", False)
        add_field(access, "🔐 Credentials", f"Username: `root`\nPassword: `{target.get('root_password') or 'not available'}`", False)
        add_field(access, "🔗 Separation", "This is normal SSH access only. SSHX is available separately through 🌐 SSHX.", False)
        try:
            recipient = await bot.fetch_user(int(target_user_id))
            await recipient.send(embed=access)
            await ctx.send(embed=create_success_embed("📨 SSH Sent", "SSH-only access details were sent to your DM."))
        except discord.Forbidden:
            await ctx.send(embed=access)
    except Exception as e:
        logger.error(f"SSH command failed for {container}: {e}", exc_info=True)
        await ctx.send(embed=create_error_embed("💻 SSH Failed", str(e)[:900]))

@bot.command(name='sshx')
async def sshx_command(ctx, container_name: str = None):
    caller_id = str(ctx.author.id)
    if maintenance_enabled() and not is_admin_user(ctx.author):
        await ctx.send(embed=create_warning_embed('🟠 Under maintenance', 'User VPS actions are temporarily disabled.'))
        return
    admin = is_admin_user(ctx.author)
    owned = list(vps_data.get(caller_id, []))
    target_user_id = caller_id
    if container_name:
        target_user_id, _, target = find_vps_record(container_name)
        if not target:
            await ctx.send(embed=create_error_embed("🖥️ VPS Not Found", f"No VPS was found for `{container_name}`."))
            return
        if not admin and str(target_user_id) != caller_id:
            await ctx.send(embed=create_error_embed("⛔ Access Denied", "You can only open SSHX for your own VPS."))
            return
    elif len(owned) == 1:
        target = owned[0]
    else:
        await ctx.send(embed=create_warning_embed("🖥️ Select a VPS", f"Usage: `{PREFIX}sshx <vmid|container-name>`"))
        return
    container = str(target.get("container_name") or "")
    node_id = int(target.get("node_id", 1))
    if target.get("suspended"):
        await ctx.send(embed=create_error_embed("⛔ VPS Suspended", "Renew or ask support to unsuspend this VPS."))
        return
    try:
        stats = await asyncio.wait_for(get_container_stats(container, node_id), timeout=20)
        if str(stats.get("status", "")).lower() != "running":
            await ctx.send(embed=create_warning_embed("⏸️ VPS Not Running", f"`{container}` is stopped. Start it first."))
            return
        sshx_url = await asyncio.wait_for(start_sshx_session(container, node_id), timeout=SSHX_ACTION_TIMEOUT)
        if not sshx_url:
            detail = "SSHX did not return a public session URL. The tunnel supervisor remains active and will retry automatically."
            if admin:
                diag = await get_sshx_diagnostics(container, node_id)
                detail += f"\n\nDiagnostics:\n```text\n{diag[-1800:]}\n```"
            raise RuntimeError(detail)
        access = create_success_embed("🌐 RGNODES™ SSHX Connected", f"`{container}` • `{VPS_HOSTNAME}`")
        add_field(access, "🌐 SSHX", f"<{sshx_url}>\n🟢 Tunnel Active", False)
        add_field(access, "🧭 Usage", f"SSHX is separate from normal SSH. Use `{PREFIX}sshx` or the 🌐 SSHX button for SSHX only.", False)
        add_field(access, "🔒 Security", "Do not share the SSHX URL publicly.", False)
        try:
            recipient = await bot.fetch_user(int(target_user_id))
            await recipient.send(embed=access)
            await ctx.send(embed=create_success_embed("📨 SSHX Sent", "SSHX-only access details were sent to your DM."))
        except discord.Forbidden:
            await ctx.send(embed=access)
    except Exception as e:
        logger.error(f"SSHX command failed for {container}: {e}", exc_info=True)
        await ctx.send(embed=create_error_embed("🌐 SSHX Failed", str(e)[:900]))

@bot.command(name="pinggy")
async def pinggy_command(ctx, container_name: str = None):
    """Open Pinggy SSH tunnel only."""
    caller_id = str(ctx.author.id)
    if maintenance_enabled() and not is_admin_user(ctx.author):
        await ctx.send(embed=create_warning_embed('🟠 Under maintenance', 'User VPS actions are temporarily disabled.'))
        return
    admin = is_admin_user(ctx.author)
    target_user_id = caller_id
    target = None
    if container_name:
        target_user_id, _, target = find_vps_record(container_name)
        if not target:
            await ctx.send(embed=create_error_embed("🖥️ VPS Not Found", f"No VPS was found for `{container_name}`."))
            return
        if not admin and str(target_user_id) != caller_id:
            await ctx.send(embed=create_error_embed("⛔ Access Denied", "You can only open Pinggy for your own VPS."))
            return
    else:
        owned = list(vps_data.get(caller_id, []))
        if len(owned) != 1:
            await ctx.send(embed=create_warning_embed("🖥️ Select a VPS", f"Usage: `{PREFIX}pinggy <vmid|container-name>`"))
            return
        target = owned[0]
    container = str(target.get("container_name") or "")
    node_id = int(target.get("node_id", 1))
    if target.get("suspended"):
        await ctx.send(embed=create_error_embed("⛔ VPS Suspended", "Renew or ask support to unsuspend this VPS."))
        return
    try:
        stats = await asyncio.wait_for(get_container_stats(container, node_id), timeout=20)
        if str(stats.get("status", "")).lower() != "running":
            await ctx.send(embed=create_warning_embed("⏸️ VPS Not Running", f"`{container}` is stopped. Start it first."))
            return
        info = await asyncio.wait_for(start_pinggy_session(container, node_id), timeout=100)
        if not info:
            raise RuntimeError("Pinggy returned no public endpoint. Try again or use Reconnect Pinggy.")
        e = create_success_embed("🌐 RGNODES™ Pinggy Connected", f"`{container}` • `{VPS_HOSTNAME}`")
        add_field(e, "🌐 Pinggy SSH Tunnel", f"**SSH Command:** `ssh root@{info['host']} -p {info['port']}`\n**Host:** `{info['host']}`\n**Port:** `{info['port']}`\n**Status:** 🟢 Tunnel Active", False)
        add_field(e, "🔗 Separation", "Pinggy only. Normal SSH and SSHX are not started by this command.", False)
        try:
            recipient = await bot.fetch_user(int(target_user_id))
            await recipient.send(embed=e)
            await ctx.send(embed=create_success_embed("📨 Pinggy Sent", "Pinggy-only access details were sent to your DM."))
        except discord.Forbidden:
            await ctx.send(embed=e)
    except Exception as e:
        await ctx.send(embed=create_error_embed("🌐 Pinggy Failed", str(e)[:900]))

@bot.command(name="reconnect-pinggy")
async def reconnect_pinggy_command(ctx, container_name: str = None):
    """Reconnect Pinggy only; never creates SSHX or normal SSH."""
    await pinggy_command.callback(ctx, container_name)

@bot.command(name='vps-expiration')
@is_admin()
async def check_expiration(ctx, container_name: str = None):
    """Check VPS expiration status (admin only)"""
    if container_name:
        # Check specific VPS
        found_vps = None
        user_id = None
        
        for uid, vps_list in vps_data.items():
            for vps in vps_list:
                if vps['container_name'] == container_name:
                    found_vps = vps
                    user_id = uid
                    break
            if found_vps:
                break
        
        if not found_vps:
            await ctx.send(embed=create_error_embed("VPS Not Found", f"No VPS found with container name: `{container_name}`"))
            return
        
        # Get owner info
        try:
            owner = await bot.fetch_user(int(user_id))
            owner_mention = owner.mention
        except:
            owner_mention = f"User {user_id}"
        
        embed = create_info_embed("VPS Expiration Status", f"Details for `{container_name}`")
        add_field(embed, "Owner", owner_mention, True)
        add_field(embed, "Container", f"`{container_name}`", True)
        
        if found_vps.get('expiration_date'):
            expiration_dt = datetime.fromisoformat(found_vps['expiration_date'])
            days_remaining = (expiration_dt - datetime.now()).days
            
            if days_remaining < 0:
                status = "🔴 EXPIRED"
            elif days_remaining <= EXPIRATION_WARNING_DAYS:
                status = "🟡 EXPIRING SOON"
            else:
                status = "🟢 ACTIVE"

            add_field(embed, "Status", status, True)
            add_field(embed, "Expiration Date", expiration_dt.strftime('%Y-%m-%d %H:%M:%S'), True)
            add_field(embed, "Days Remaining", str(max(0, days_remaining)), True)
        else:
            add_field(embed, "Status", "🔵 NO EXPIRATION SET", False)
        
        await ctx.send(embed=embed)
    else:
        # List all VPS with expiration status
        embed = create_info_embed("📋 All VPS Expiration Status", "Global expiration overview")
        
        expiring_soon = []
        expired = []
        active = []
        no_expiration = []
        
        for user_id, vps_list in vps_data.items():
            try:
                owner = await bot.fetch_user(int(user_id))
                owner_name = owner.name
            except:
                owner_name = f"Unknown ({user_id})"
            
            for vps in vps_list:
                if vps.get('expiration_date'):
                    expiration_dt = datetime.fromisoformat(vps['expiration_date'])
                    days_remaining = (expiration_dt - datetime.now()).days
                    
                    status_line = f"**{owner_name}** - `{vps['container_name']}`\n" \
                                 f"Expires: {expiration_dt.strftime('%Y-%m-%d')} ({days_remaining} days)"
                    
                    if days_remaining < 0:
                        expired.append(status_line)
                    elif days_remaining <= EXPIRATION_WARNING_DAYS:
                        expiring_soon.append(status_line)
                    else:
                        active.append(status_line)
                else:
                    no_expiration.append(f"**{owner_name}** - `{vps['container_name']}`")
        
        if expiring_soon:
            add_field(embed, "🟡 Expiring Soon", "\n\n".join(expiring_soon), False)
        if expired:
            add_field(embed, "🔴 Expired", "\n\n".join(expired), False)
        if active:
            add_field(embed, "🟢 Active", "\n\n".join(active[:10]), False)
            if len(active) > 10:
                add_field(embed, "Note", f"Showing 10 of {len(active)} active VPS", False)
        if no_expiration:
            add_field(embed, "🔵 No Expiration Set", "\n".join(no_expiration[:5]), False)
            if len(no_expiration) > 5:
                add_field(embed, "Note", f"Total {len(no_expiration)} VPS without expiration date", False)
        
        await ctx.send(embed=embed)

@bot.command(name='about')
async def about(ctx):
    total_users = len(vps_data)
    total_vps = sum(len(vps_list) for vps_list in vps_data.values())
    latency = round(bot.latency * 1000)
    main_admin = await bot.fetch_user(MAIN_ADMIN_ID)
    embed = create_info_embed(f"About {BOT_NAME}", f"Bot information and statistics")
    add_field(embed, "Bot Name", BOT_NAME, True)
    add_field(embed, "Main Owner", main_admin.mention, True)
    add_field(embed, "Developer", BOT_DEVELOPER, True)
    add_field(embed, "Host Provider", HOST_PROVIDER_NAME, True)
    add_field(embed, "Ping", f"{latency}ms", True)
    add_field(embed, "Version", BOT_VERSION, True)
    add_field(embed, "Total VPS", str(total_vps), True)
    add_field(embed, "Total Users", str(total_users), True)
    await ctx.send(embed=embed)


@bot.command(name='quickhelp')
async def quick_help(ctx):
    """Show quick reference for common tasks"""
    user_id = str(ctx.author.id)
    is_admin_access = is_admin_user(ctx.author)
    
    embed = create_info_embed("🚀 Quick Help Reference", 
        f"Quick reference for common tasks. Use `{PREFIX}help` for complete command list.")
    
    # Common user tasks
    add_field(embed, "👤 For Users", 
        f"• `{PREFIX}myvps` - List your VPS\n"
        f"• `{PREFIX}manage` - Start/stop/manage VPS\n"
        f"• `{PREFIX}ports` - Manage port forwarding\n"
        f"• `{PREFIX}share-user @user 1` - Share VPS #1\n"
        f"• `{PREFIX}about` - Bot information", False)
    
    # VPS management
    add_field(embed, "🖥️ VPS Control", 
        f"• In `{PREFIX}manage`: Click ▶ to start VPS\n"
        f"• In `{PREFIX}manage`: Click ⏸ to stop VPS\n"
        f"• In `{PREFIX}manage`: Click 🔑 for SSH access\n"
        f"• In `{PREFIX}manage`: Click 📊 for live stats\n"
        f"• In `{PREFIX}manage`: Click 🔄 to reinstall OS", False)
    
    # Troubleshooting
    add_field(embed, "🔧 Common Issues", 
        f"• Ports not working? Use `{PREFIX}repair-ports <container>` (admin)\n"
        "• VPS suspended? Contact admin to unsuspend\n"
        "• Need more resources? Contact admin for upgrade\n"
        "• SSH not working? Try reinstall with different OS", False)
    
    if is_admin_access:
        add_field(embed, "🛡️ Admin Quick Actions", 
            f"• `{PREFIX}create 2 2 20 @user` - Create 2GB/2CPU/20GB VPS\n"
            f"• `{PREFIX}userinfo @user` - Check user details\n"
            f"• `{PREFIX}node list` - List all nodes\n"
            f"• `{PREFIX}serverstats` - System overview\n"
            f"• `{PREFIX}suspend-vps <container> <reason>` - Suspend VPS", False)
    
    embed.set_footer(text=f"⚡ RGNODES™ • Use {PREFIX}help for complete command list")
    await ctx.send(embed=embed)

@bot.command(name='help-search')
async def help_search(ctx, *, search_term: str = None):
    """Search for commands"""
    if not search_term:
        await show_help.callback(ctx)
        return
    
    search_term = search_term.lower()
    user_id = str(ctx.author.id)
    is_admin_access = is_admin_user(ctx.author)
    is_main_admin_user = user_id == str(MAIN_ADMIN_ID)
    
    # Build complete command list based on permissions
    all_commands = []
    
    # User commands (always available)
    user_categories = ["user", "vps", "ports", "system", "bot"]
    for cat in user_categories:
        all_commands.extend(HelpView(ctx).command_categories[cat]["commands"])
    
    # Admin commands
    if is_admin_access:
        all_commands.extend(HelpView(ctx).command_categories["admin"]["commands"])
        all_commands.extend(HelpView(ctx).command_categories["nodes"]["commands"])
    
    # Main admin commands
    if is_main_admin_user:
        all_commands.extend(HelpView(ctx).command_categories["main_admin"]["commands"])
    
    # Search through commands
    matches = []
    for cmd, desc in all_commands:
        if (search_term in cmd.lower() or search_term in desc.lower()):
            matches.append((cmd, desc))
    
    if not matches:
        embed = create_info_embed("🔍 No Results Found",
            f"No commands found matching '{search_term}'. Try a different search term.")
        await ctx.send(embed=embed)
        return
    
    # Show results
    embed = create_info_embed(f"🔍 Search Results for '{search_term}'",
        f"Found {len(matches)} command(s) matching your search.")
    
    # Group matches by category
    results_text = "\n".join([f"**{cmd}** - {desc}" for cmd, desc in matches[:15]])
    add_field(embed, "Matching Commands", results_text, False)
    
    if len(matches) > 15:
        add_field(embed, "Note", f"Showing 15 of {len(matches)} matches. Try a more specific search.", False)
    
    embed.set_footer(text=f"⚡ RGNODES™ • Use {PREFIX}help for complete list")
    await ctx.send(embed=embed)    

@bot.command(name='node')
@is_admin()
async def node_cmd(ctx, sub: str, *args):
    if sub == 'create':
        await ctx.send("Enter node name:")
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        name = (await asyncio.wait_for(bot.wait_for('message', check=check), timeout=180)).content.strip()
        await ctx.send("Enter location:")
        location = (await asyncio.wait_for(bot.wait_for('message', check=check), timeout=180)).content.strip()
        await ctx.send("Enter total VPS capacity:")
        total_vps_str = (await asyncio.wait_for(bot.wait_for('message', check=check), timeout=180)).content.strip()
        try:
            total_vps = int(total_vps_str)
        except ValueError:
            await ctx.send(embed=create_error_embed("Invalid Input", "Total VPS must be an integer."))
            return
        await ctx.send("Enter tags (comma separated):")
        tags_str = (await asyncio.wait_for(bot.wait_for('message', check=check), timeout=180)).content.strip()
        tags = [t.strip() for t in tags_str.split(',') if t.strip()]
        tags_json = json.dumps(tags)
        await ctx.send("Enter node URL (e.g., http://ip:port or https://ip:port) or leave blank for local:")
        url_str = (await asyncio.wait_for(bot.wait_for('message', check=check), timeout=180)).content.strip()
        
        # Normalize URL if provided
        if url_str:
            if not url_str.startswith('http://') and not url_str.startswith('https://'):
                url_str = f'http://{url_str}'
            url = url_str
        else:
            url = None
        
        is_local = 1 if not url else 0
        api_key = None if is_local else secrets.token_hex(16)
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO nodes (name, location, total_vps, tags, api_key, url, is_local) VALUES (?, ?, ?, ?, ?, ?, ?)',
                        (name, location, total_vps, tags_json, api_key, url, is_local))
            conn.commit()
            node_id = cur.lastrowid
            embed = create_success_embed("Node Created", f"ID: {node_id}\nName: {name}\nLocation: {location}\nCapacity: {total_vps}\nTags: {', '.join(tags)}")
            if not is_local:
                add_field(embed, "API Key", api_key, False)
                add_field(embed, "URL", url, False)
                add_field(embed, "Setup", f"Run `python node-agent.py --api_key={api_key} --port=PORT` on the node server.")
            await ctx.send(embed=embed)
        except sqlite3.IntegrityError:
            await ctx.send(embed=create_error_embed("Error", "Node name already exists."))
        conn.close()
    elif sub == 'list':
        nodes = get_nodes()
        embed = create_info_embed("Nodes List", "")
        for n in nodes:
            status = "Local" if n['is_local'] else "Down"
            if not n['is_local']:
                try:
                    response = await asyncio.to_thread(requests.get, str(n['url']).rstrip('/') + '/api/ping', headers={'X-API-Key': str(n['api_key'])}, timeout=5)
                    status = "Up" if response.status_code == 200 else "Down"
                except:
                    pass
            field = f"ID: {n['id']}\nName: {n['name']}\nLocation: {n['location']}\nCapacity: {n['total_vps']}\nTags: {', '.join(n['tags'])}\nStatus: {status}"
            if not n['is_local']:
                field += f"\nURL: {n['url']}"
            add_field(embed, f"Node {n['id']}", field, False)
        await ctx.send(embed=embed)
    elif sub == 'edit':
        if not args:
            await ctx.send(embed=create_error_embed("Usage", f"{PREFIX}node edit <id>"))
            return
        try:
            node_id = int(args[0])
        except ValueError:
            await ctx.send(embed=create_error_embed("Invalid ID", "Node ID must be an integer."))
            return
        node = get_node(node_id)
        if not node:
            await ctx.send(embed=create_error_embed("Not Found", "Node not found."))
            return
        await ctx.send(f"Editing node {node['name']}. Enter new name ( . to skip):")
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        new_name = (await asyncio.wait_for(bot.wait_for('message', check=check), timeout=180)).content.strip()
        if new_name != '.':
            node['name'] = new_name
        await ctx.send("New location ( . to skip):")
        new_loc = (await asyncio.wait_for(bot.wait_for('message', check=check), timeout=180)).content.strip()
        if new_loc != '.':
            node['location'] = new_loc
        await ctx.send("New total VPS capacity ( . to skip):")
        new_total = (await asyncio.wait_for(bot.wait_for('message', check=check), timeout=180)).content.strip()
        if new_total != '.':
            node['total_vps'] = int(new_total)
        await ctx.send("New tags (comma separated, . to skip):")
        new_tags = (await asyncio.wait_for(bot.wait_for('message', check=check), timeout=180)).content.strip()
        if new_tags != '.':
            node['tags'] = [t.strip() for t in new_tags.split(',') if t.strip()]
        
        # NEW: Add conversion option between Local and Dynamic
        if node['is_local']:
            await ctx.send("Convert Local Node to Dynamic URL-based Node? (y/n):")
            convert = (await asyncio.wait_for(bot.wait_for('message', check=check), timeout=180)).content.strip().lower()
            if convert == 'y':
                await ctx.send("Enter node URL (e.g., http://ip:port or https://ip:port):")
                url_str = (await asyncio.wait_for(bot.wait_for('message', check=check), timeout=180)).content.strip()
                if not url_str:
                    await ctx.send(embed=create_error_embed("Error", "URL cannot be empty for dynamic node."))
                    return
                
                # Normalize URL - add http:// if not present
                if not url_str.startswith('http://') and not url_str.startswith('https://'):
                    url_str = f'http://{url_str}'
                
                node['url'] = url_str
                node['is_local'] = 0
                node['api_key'] = secrets.token_hex(16)
                await ctx.send(f"✅ Node converted to Dynamic!\n\n**URL:** `{url_str}`\n**Generated API Key:** `{node['api_key']}`\n\n**Setup Command:**\n```\npython node-agent.py --api_key={node['api_key']} --port=PORT\n```")
        else:
            await ctx.send("Convert Dynamic Node to Local? (y/n):")
            convert = (await asyncio.wait_for(bot.wait_for('message', check=check), timeout=180)).content.strip().lower()
            if convert == 'y':
                node['url'] = None
                node['api_key'] = None
                node['is_local'] = 1
                await ctx.send("✅ Node converted to Local!")
            else:
                await ctx.send("New URL ( . to skip):")
                new_url = (await asyncio.wait_for(bot.wait_for('message', check=check), timeout=180)).content.strip()
                if new_url != '.':
                    # Normalize URL - add http:// if not present
                    if not new_url.startswith('http://') and not new_url.startswith('https://'):
                        new_url = f'http://{new_url}'
                    node['url'] = new_url
                await ctx.send("Regenerate API key? (y/n):")
                regen = (await asyncio.wait_for(bot.wait_for('message', check=check), timeout=180)).content.strip().lower()
                if regen == 'y':
                    node['api_key'] = secrets.token_hex(16)
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute('UPDATE nodes SET name=?, location=?, total_vps=?, tags=?, api_key=?, url=?, is_local=? WHERE id=?',
                    (node['name'], node['location'], node['total_vps'], json.dumps(node['tags']), node.get('api_key'), node.get('url'), node['is_local'], node_id))
        conn.commit()
        conn.close()
        embed = create_success_embed("Node Updated", f"ID: {node_id}\nName: {node['name']}\nLocation: {node['location']}\nCapacity: {node['total_vps']}\nTags: {', '.join(node['tags'])}\nType: {'Local' if node['is_local'] else 'Dynamic'}")
        if not node['is_local']:
            add_field(embed, "API Key", node['api_key'], False)
            add_field(embed, "URL", node['url'], False)
        await ctx.send(embed=embed)
    
    # NEW: Add delete subcommand
    elif sub == 'delete':
        if not args:
            await ctx.send(embed=create_error_embed("Usage", f"{PREFIX}node delete <id> [force]"))
            return
        
        try:
            node_id = int(args[0])
        except ValueError:
            await ctx.send(embed=create_error_embed("Invalid ID", "Node ID must be an integer."))
            return
        
        force = False
        if len(args) > 1 and args[1].lower() == 'force':
            force = True
        elif len(args) > 1:
            await ctx.send(embed=create_error_embed("Invalid Argument", "Optional argument must be 'force'."))
            return
        
        node = get_node(node_id)
        if not node:
            await ctx.send(embed=create_error_embed("Not Found", "Node not found."))
            return
        
        # Check if this is the local node
        if node['is_local']:
            await ctx.send(embed=create_error_embed("Cannot Delete", "Cannot delete the local node."))
            return
        
        # Check if node has any VPS assigned
        vps_count = get_current_vps_count(node_id)
        if not force and vps_count > 0:
            await ctx.send(embed=create_error_embed("Cannot Delete", 
                f"Node has {vps_count} VPS assigned. Migrate or delete them first, or use 'force' to delete all VPS and the node."))
            return
        
        # Prepare warning message
        warning_msg = f"Are you sure you want to delete node **{node['name']}** (ID: {node_id})?\n\n"
        warning_msg += f"**Location:** {node['location']}\n"
        warning_msg += f"**Tags:** {', '.join(node['tags'])}\n\n"
        if force and vps_count > 0:
            warning_msg += f"**WARNING: Force mode will delete all {vps_count} VPS on this node first!**\n\n"
        warning_msg += "This action cannot be undone!"
        
        embed = create_warning_embed("⚠️ Delete Node", warning_msg)
        
        class ConfirmDelete(discord.ui.View):
            def __init__(self, node_id, node_name, force, vps_count):
                super().__init__(timeout=60)
                self.node_id = node_id
                self.node_name = node_name
                self.force = force
                self.vps_count = vps_count
            
            @discord.ui.button(label="Delete Node", style=discord.ButtonStyle.danger)
            async def confirm(self, inter: discord.Interaction, item: discord.ui.Button):
                if str(inter.user.id) != str(ctx.author.id):
                    await inter.response.send_message(
                        embed=create_error_embed("Access Denied", "Only the command author can confirm."),
                        ephemeral=True
                    )
                    return
                
                await inter.response.defer()
                
                # Force-deleting a node must delete the real LXC containers first.
                # Never remove DB records for containers that could not be deleted,
                # otherwise they become unmanaged/orphaned VPS instances.
                if self.force and self.vps_count > 0:
                    with DB_LOCK:
                        conn = get_db()
                        try:
                            rows = conn.execute(
                                "SELECT container_name FROM vps WHERE node_id = ? ORDER BY id",
                                (self.node_id,),
                            ).fetchall()
                        finally:
                            conn.close()

                    failed = []
                    for row in rows:
                        container = str(row["container_name"])
                        try:
                            await execute_lxc(
                                container,
                                f"delete {container} --force",
                                timeout=300,
                                node_id=self.node_id,
                            )
                        except Exception as delete_error:
                            failed.append(f"{container}: {delete_error}")

                    if failed:
                        detail = "\n".join(f"• {x}" for x in failed[:8])
                        await inter.followup.send(
                            embed=create_error_embed(
                                "Node Deletion Aborted",
                                "One or more LXC containers could not be deleted, so the database records were kept intact.\n\n" + detail,
                            )
                        )
                        return

                # Keep a recoverable DB snapshot before a destructive node purge.
                backup_database()
                with DB_LOCK:
                    conn = get_db()
                    try:
                        if self.force and self.vps_count > 0:
                            cur = conn.cursor()
                            cur.execute(
                                "DELETE FROM port_forwards WHERE vps_container IN (SELECT container_name FROM vps WHERE node_id = ?)",
                                (self.node_id,),
                            )
                            cur.execute("DELETE FROM vps WHERE node_id = ?", (self.node_id,))
                        cur = conn.cursor()
                        cur.execute("DELETE FROM nodes WHERE id = ?", (self.node_id,))
                        if cur.rowcount != 1:
                            raise RuntimeError("Node disappeared before deletion was committed.")
                        conn.commit()
                    except Exception:
                        conn.rollback()
                        raise
                    finally:
                        conn.close()

                if self.force and self.vps_count > 0:
                    deleted_containers = {str(row["container_name"]) for row in rows}
                    for owner_id in list(vps_data):
                        vps_data[owner_id] = [
                            v for v in vps_data[owner_id]
                            if str(v.get("container_name")) not in deleted_containers
                        ]
                        if not vps_data[owner_id]:
                            del vps_data[owner_id]
                msg = f"Node **{self.node_name}** (ID: {self.node_id}) has been deleted."
                if self.force and self.vps_count > 0:
                    msg += f" All {self.vps_count} VPS and their LXC containers were deleted."

                success_embed = create_success_embed("Node Deleted", msg)
                await inter.followup.send(embed=success_embed)
                self.stop()
            
            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
            async def cancel(self, inter: discord.Interaction, item: discord.ui.Button):
                if str(inter.user.id) != str(ctx.author.id):
                    await inter.response.send_message(
                        embed=create_error_embed("Access Denied", "Only the command author can cancel."),
                        ephemeral=True
                    )
                    return
                
                await inter.response.edit_message(
                    embed=create_info_embed("Deletion Cancelled", "Node deletion was cancelled."),
                    view=None
                )
                self.stop()
        
        await ctx.send(embed=embed, view=ConfirmDelete(node_id, node['name'], force, vps_count))
    
    elif sub == 'status':
        # New: Check node status
        if not args:
            await ctx.send(embed=create_error_embed("Usage", f"{PREFIX}node status <id>"))
            return
        
        try:
            node_id = int(args[0])
        except ValueError:
            await ctx.send(embed=create_error_embed("Invalid ID", "Node ID must be an integer."))
            return
        
        node = get_node(node_id)
        if not node:
            await ctx.send(embed=create_error_embed("Not Found", "Node not found."))
            return
        
        embed = create_info_embed(f"Node Status - {node['name']}")
        
        if node['is_local']:
            status = "🟢 Local Node"
            cpu_usage = get_host_cpu_usage()
            ram_usage = get_host_ram_usage()
            add_field(embed, "Status", status, True)
            add_field(embed, "CPU Usage", f"{cpu_usage:.1f}%", True)
            add_field(embed, "RAM Usage", f"{ram_usage:.1f}%", True)
        else:
            try:
                response = await asyncio.to_thread(requests.get, str(node['url']).rstrip('/') + '/api/ping', headers={'X-API-Key': str(node['api_key'])}, timeout=5)
                if response.status_code == 200:
                    status = "🟢 Online"
                    try:
                        stats_response = await asyncio.to_thread(requests.get, str(node['url']).rstrip('/') + '/api/get_host_stats', 
                                                    headers={'X-API-Key': str(node['api_key'])}, 
                                                    timeout=5)
                        if stats_response.status_code == 200:
                            stats = stats_response.json()
                            cpu_usage = stats.get('cpu', 0.0)
                            ram_usage = stats.get('ram', 0.0)
                            add_field(embed, "CPU Usage", f"{cpu_usage:.1f}%", True)
                            add_field(embed, "RAM Usage", f"{ram_usage:.1f}%", True)
                    except:
                        cpu_usage = "Unknown"
                        ram_usage = "Unknown"
                else:
                    status = "🔴 Offline"
            except:
                status = "🔴 Offline"
            
            add_field(embed, "Status", status, True)
        
        vps_count = get_current_vps_count(node_id)
        capacity = node['total_vps']
        usage_percentage = (vps_count / capacity * 100) if capacity > 0 else 0
        
        add_field(embed, "VPS Capacity", f"{vps_count}/{capacity} ({usage_percentage:.1f}%)", True)
        add_field(embed, "Location", node['location'], True)
        add_field(embed, "Tags", ", ".join(node['tags']), True)
        
        if not node['is_local']:
            add_field(embed, "URL", node['url'], False)
        
        await ctx.send(embed=embed)
    
    elif sub == 'regen-key':
        # NEW: Regenerate API key for dynamic node
        if not args:
            await ctx.send(embed=create_error_embed("Usage", f"{PREFIX}node regen-key <id>"))
            return
        
        try:
            node_id = int(args[0])
        except ValueError:
            await ctx.send(embed=create_error_embed("Invalid ID", "Node ID must be an integer."))
            return
        
        node = get_node(node_id)
        if not node:
            await ctx.send(embed=create_error_embed("Not Found", "Node not found."))
            return
        
        # Check if node is local
        if node['is_local']:
            await ctx.send(embed=create_error_embed("Error", "Cannot regenerate API key for Local nodes. Only Dynamic nodes have API keys."))
            return
        
        # Confirm regeneration
        warning_embed = create_warning_embed("⚠️ Regenerate API Key", 
            f"You are about to regenerate the API key for node **{node['name']}**.\n\n"
            f"**Current API Key:** `{node['api_key']}`\n\n"
            f"**This action will:**\n"
            f"• Generate a new 32-character API key\n"
            f"• Invalidate the old API key\n"
            f"• Require updating the remote node agent\n\n"
            f"Are you sure you want to continue?")
        
        class ConfirmRegenKey(discord.ui.View):
            def __init__(self, node_id, node):
                super().__init__(timeout=60)
                self.node_id = node_id
                self.node = node
            
            @discord.ui.button(label="Regenerate Key", style=discord.ButtonStyle.danger)
            async def confirm(self, inter: discord.Interaction, item: discord.ui.Button):
                if str(inter.user.id) != str(ctx.author.id):
                    await inter.response.send_message(
                        embed=create_error_embed("Access Denied", "Only the command author can confirm."),
                        ephemeral=True
                    )
                    return
                
                await inter.response.defer()
                
                # Generate new API key
                new_api_key = secrets.token_hex(16)
                
                # Update database
                conn = get_db()
                cur = conn.cursor()
                cur.execute('UPDATE nodes SET api_key=? WHERE id=?', (new_api_key, self.node_id))
                conn.commit()
                conn.close()
                
                # Create success embed with new key
                success_embed = create_success_embed("✅ API Key Regenerated", 
                    f"Node **{self.node['name']}** (ID: {self.node_id})")
                
                add_field(success_embed, "Old API Key", f"`{self.node['api_key']}`", False)
                add_field(success_embed, "New API Key", f"`{new_api_key}`", False)
                add_field(success_embed, "Node URL", self.node['url'], True)
                
                setup_command = f"python node-agent.py --api_key={new_api_key} --port=PORT"
                add_field(success_embed, "Update Remote Agent", 
                    f"SSH to the remote server and restart with:\n```\n{setup_command}\n```", False)
                
                add_field(success_embed, "⚠️ Important", 
                    "The old API key is now invalid. Update your remote node agent immediately.", False)
                
                await inter.followup.send(embed=success_embed)
                self.stop()
            
            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
            async def cancel(self, inter: discord.Interaction, item: discord.ui.Button):
                if str(inter.user.id) != str(ctx.author.id):
                    await inter.response.send_message(
                        embed=create_error_embed("Access Denied", "Only the command author can cancel."),
                        ephemeral=True
                    )
                    return
                
                await inter.response.edit_message(
                    embed=create_info_embed("Cancelled", "API key regeneration was cancelled."),
                    view=None
                )
                self.stop()
        
        await ctx.send(embed=warning_embed, view=ConfirmRegenKey(node_id, node))
    
    else:
        # Show help for node command
        embed = create_info_embed("Node Management", 
            f"Manage multi-node infrastructure for {BOT_NAME}")

class HelpView(RGNODESView):
    def __init__(self, ctx):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.current_category = "user"
        # Command categories
        self.command_categories = {
            "user": {
                "name": "👤 User Commands",
                "commands": [
                    (f"{PREFIX}ping", "Check bot latency"),
                    (f"{PREFIX}uptime", "Show host uptime"),
                    (f"{PREFIX}deploy", "Deploy the free 8GB / 2-core / 25GB VPS"),
                    (f"{PREFIX}myvps", "List your VPS"),
                    (f"{PREFIX}manage [@user]", "Manage your VPS or another user's VPS (Admin only)"),
                    (f"{PREFIX}share-user @user <vps_number>", "Share VPS access"),
                    (f"{PREFIX}share-ruser @user <vps_number>", "Revoke VPS access"),
                    (f"{PREFIX}manage-shared @owner <vps_number>", "Manage shared VPS"),
                    (f"{PREFIX}renew [vps-id]", "Renew your VPS in the final 2 days or after expiration; adds 60 days"),
                    (f"{PREFIX}ssh [vps-id]", "Receive normal SSH access only (no SSHX session)"),
                    (f"{PREFIX}sshx [vps-id]", "Open an SSHX session only and receive the SSHX URL by DM"),
                    (f"{PREFIX}reconnect-tunnel [vps-id]", "Reconnect the SSHX tunnel only"),
                    (f"{PREFIX}pinggy [vps-id]", "Open Pinggy SSH tunnel only"),
                    (f"{PREFIX}reconnect-pinggy [vps-id]", "Reconnect Pinggy tunnel only"),
                    (f"{PREFIX}bandwidth [vps-id]", "View the fixed 50GB monthly bandwidth plan and usage"),
                    (f"{PREFIX}vps-log <vps-id> [lines]", "View your VPS system/audit logs")
                ]
            },
            "vps": {
                "name": "🖥️ VPS Management",
                "commands": [
                    (f"{PREFIX}myvps", "List your VPS"),
                    (f"{PREFIX}vpsinfo [vps-id]", "Get VPS information by ID"),
                    (f"{PREFIX}vps-stats <vps-id>", "Get VPS resource stats"),
                    (f"{PREFIX}vps-uptime <vps-id>", "Get VPS uptime"),
                    (f"{PREFIX}vps-processes <vps-id>", "List running processes in VPS"),
                    (f"{PREFIX}vps-logs <vps-id> [lines]", "Admin: view guest system + RGNODES audit logs"),
                    (f"{PREFIX}vps-log <vps-id> [lines]", "View your VPS logs"),
                    (f"{PREFIX}restart-vps <vps-id>", "Restart VPS"),
                    (f"{PREFIX}clone-vps <vps-id> [new_name]", "Clone VPS by ID"),
                    (f"{PREFIX}vps-password <vps-id>", "Get/reset VPS root password"),
                    (f"{PREFIX}vps-network <vps-id>", "Show VPS network configuration"),
                    (f"{PREFIX}status <vps-id>", "Get VPS status (running/stopped)")
                ]
            },
            "ports": {
                "name": "🔌 Port Forwarding",
                "commands": [
                    (f"{PREFIX}ports [add <vps_num> <port> | list | remove <id>]", "Manage port forwards (TCP/UDP)"),
                    (f"{PREFIX}ports-add-user <amount> @user", "Allocate port slots to user (Admin only)"),
                    (f"{PREFIX}ports-remove-user <amount> @user", "Deallocate port slots from user (Admin only)"),
                    (f"{PREFIX}ports-revoke <id>", "Revoke specific port forward (Admin only)")
                ]
            },
            "system": {
                "name": "⚙️ System Commands",
                "commands": [
                    (f"{PREFIX}serverstats", "Server statistics"),
                    (f"{PREFIX}resource-check", "Check and suspend high-usage VPS (Admin only)"),
                    (f"{PREFIX}cpu-monitor <status|enable|disable>", "Resource monitor control (logging only)"),
                    (f"{PREFIX}thresholds", "View resource thresholds"),
                    (f"{PREFIX}set-threshold <cpu> <ram>", "Set resource thresholds (Admin only)"),
                    (f"{PREFIX}set-status <type> <name>", "Set bot status (Admin only)"),
                    (f"{PREFIX}log-config", "Show the configured VPS/node logging channel (Admin only)"),
                    (f"{PREFIX}log-channel <show|test>", "Show or test the configured logging channel (Admin only)"),
                    (f"{PREFIX}permissions [#channel]", "Audit the bot's Discord permissions (Admin only)"),
                    (f"{PREFIX}node-capacity [node_id]", "Low-overhead node capacity snapshot (Admin only)"),
                    (f"{PREFIX}update logs #channel", "Publish VPS/node logs to a channel (Admin only)"),
                    (f"{PREFIX}motd <show|set|clear>", "Manage the SSH MOTD on running VPS (Admin only)")
                ]
            },
            "nodes": {
                "name": "🌐 Node Management",
                "commands": [
                    (f"{PREFIX}node create", "Create a new node (Admin only)"),
                    (f"{PREFIX}node list", "List all nodes (Admin only)"),
                    (f"{PREFIX}node status <id>", "Check node status (Admin only)"),
                    (f"{PREFIX}node edit <id>", "Edit node details or convert Local↔Dynamic (Admin only)"),
                    (f"{PREFIX}node regen-key <id>", "Regenerate API key for Dynamic node (Admin only)"),
                    (f"{PREFIX}node delete <id>", "Delete a node (Admin only)"),
                    (f"{PREFIX}node migrate <from> <to>", "Migrate VPS between nodes (Admin only)"),
                    (f"{PREFIX}lxc-list [node_id]", "List LXC containers on node (Admin only)")
                ],
                "admin_only": True
            },
            "bot": {
                "name": "🤖 Bot Control",
                "commands": [
                    (f"{PREFIX}ping", "Check bot latency"),
                    (f"{PREFIX}uptime", "Show host uptime"),
                    (f"{PREFIX}help", "Show this help menu"),
                    (f"{PREFIX}set-status <type> <name>", "Set bot status (Admin only)")
                ]
            },
            "admin": {
                "name": "🛡️ Admin Commands",
                "commands": [
                    (f"{PREFIX}lxc-list", "List all LXC containers"),
                    (f"{PREFIX}deploy [@user]", "Open OS + node selection and deploy the fixed 8GB/2-core/25GB VPS"),
                    (f"{PREFIX}create <ram_gb> <cpu_cores> <disk_gb> @user [expiry_days]", "Admin VPS creation with OS selection (optional expiry)"),
                    (f"{PREFIX}delete-vps @user <vps-id> [reason]", "Delete user's VPS by ID"),
                    (f"{PREFIX}add-resources <vps-id> [ram] [cpu] [disk]", "Add resources to VPS"),
                    (f"{PREFIX}resize-vps <vps-id> [ram] [cpu] [disk]", "Resize VPS resources"),
                    (f"{PREFIX}suspend-vps <vps-id> [reason]", "Suspend VPS by ID"),
                    (f"{PREFIX}unsuspend-vps <vps-id>", "Unsuspend VPS by ID"),
                    (f"{PREFIX}suspension-logs [vps-id]", "View suspension logs"),
                    (f"{PREFIX}whitelist-vps <vps-id> <add|remove>", "Whitelist VPS from auto-suspend"),
                    (f"{PREFIX}userinfo @user", "User information"),
                    (f"{PREFIX}list-all", "List all VPS"),
                    (f"{PREFIX}exec <vps-id> <command>", "Execute command in VPS"),
                    (f"{PREFIX}stop-vps-all", "Stop all VPS on system"),
                    (f"{PREFIX}backup-vps <vps>", "Export a VPS LXC backup (Admin only)"),
                    (f"{PREFIX}restore-vps <vps> [backup]", "Restore a VPS LXC backup (Admin only)"),
                    (f"{PREFIX}maintenance <on|off|status>", "Toggle VPS maintenance mode (Admin only)"),
                    (f"{PREFIX}migrate-vps <vps-id> <pool>", "Migrate VPS to different storage pool"),
                    (f"{PREFIX}vps-network <vps-id> <action> [value]", "Network management and configuration"),
                    (f"{PREFIX}apply-permissions <vps-id>", "Apply Docker-ready permissions to VPS"),
                    (f"{PREFIX}vps-password <vps-id>", "Get/reset VPS password by ID"),
                    (f"{PREFIX}node-check <node_id>", "Check node health and status"),
                    (f"{PREFIX}status <vps-id>", "Get VPS status"),
                    (f"{PREFIX}status-summary", "Get summary of all VPS status"),
                    (f"{PREFIX}repair-ports", "Repair port forwarding configuration"),
                    (f"{PREFIX}resource-check", "Check and suspend high-usage VPS"),
                    (f"{PREFIX}node-logs <node_id> [limit]", "View node health/audit history"),
                    (f"{PREFIX}logs [limit]", "View recent VPS/node audit logs"),
                    (f"{PREFIX}log-config", "Show configured log channel"),
                    (f"{PREFIX}update logs #channel", "Set the VPS/node log channel"),
                    (f"{PREFIX}update-logs #channel", "Alias for update logs #channel"),
                    (f"{PREFIX}add slots @user amount", "Add port slots to a user"),
                    (f"{PREFIX}bandwidth <vps-id>", "View 50GB monthly bandwidth usage"),
                    (f"{PREFIX}motd <show|set|clear>", "Manage VPS SSH MOTD")
                ],
                "admin_only": True
            },
            "expiration": {
                "name": "⏰ VPS Expiration",
                "commands": [
                    (f"{PREFIX}renew [vps-id]", "Owner renewal in the final 2 days; adds 60 days"),
                    (f"{PREFIX}setexpire <vps-id> <days>", "Set VPS expiration date (Admin only)"),
                    (f"{PREFIX}extendexpire <vps-id> <days>", "Extend VPS expiration (Admin only)"),
                    (f"{PREFIX}removeexpire <vps-id>", "Remove VPS expiration (Admin only)"),
                    (f"{PREFIX}set-expiration <vps-id> <days>", "Legacy alias for setexpire"),
                    (f"{PREFIX}renew <vps-id>", "Owner renewal in final 2-day window (adds 60 days)"),
                    (f"{PREFIX}renew-vps <vps-id> [days]", "Renew VPS expiration (Admin only)"),
                    (f"{PREFIX}vps-expiration [vps-id]", "Check VPS expiration status (Admin only)")
                ],
                "admin_only": True
            },
            "maintenance": {
                "name": "🔧 Maintenance & Monitoring",
                "commands": [
                    (f"{PREFIX}cpu-monitor <status|enable|disable>", "Resource monitor control (logging only)"),
                    (f"{PREFIX}backup-db", "Backup VPS database (Admin only)"),
                    (f"{PREFIX}backup-vps <vps>", "Backup a VPS LXC instance (Admin only)"),
                    (f"{PREFIX}restore-vps <vps> [backup]", "Restore a VPS LXC instance (Admin only)"),
                    (f"{PREFIX}maintenance <on|off|status>", "Maintenance control (Admin only)"),
                    (f"{PREFIX}repair-ports", "Repair port forwarding configuration (Admin only)"),
                    (f"{PREFIX}node-check <node_id>", "Check node health and status (Admin only)"),
                    (f"{PREFIX}resource-check", "Check and suspend high-usage VPS (Admin only)"),
                    (f"{PREFIX}node-logs <node_id> [limit]", "View node health/audit history"),
                    (f"{PREFIX}node-log <node_id> [limit]", "Alias for node-logs"),
                    (f"{PREFIX}logs [limit]", "View recent audit log history"),
                    (f"{PREFIX}log-config", "Show configured logs channel"),
                    (f"{PREFIX}update logs #channel", "Set the VPS/node log channel"),
                    (f"{PREFIX}add slots @user amount", "Add port-forwarding slots to a user"),
                    (f"{PREFIX}bandwidth <vps-id>", "View 50GB monthly bandwidth accounting"),
                    (f"{PREFIX}motd <show|set|clear>", "Manage guest SSH MOTD")
                ],
                "admin_only": True
            },
            "main_admin": {
                "name": "👑 Main Admin Commands",
                "commands": [
                    (f"{PREFIX}admin-add @user", "Add admin"),
                    (f"{PREFIX}admin-remove @user", "Remove admin"),
                    (f"{PREFIX}admin-list", "List admins")
                ],
                "admin_only": True,
                "main_admin_only": True
            }
        }
        self.update_select()
        self.update_embed()
        self.add_item(self.select)

    def update_select(self):
        """Update the category selection dropdown based on user permissions"""
        self.select = discord.ui.Select(placeholder="Select Category", options=[])
        user_id = str(self.ctx.author.id)
        admin_access = is_admin_user(self.ctx.author)
        is_main_admin_user = user_id == str(MAIN_ADMIN_ID)
       
        # Add all categories that user has access to
        options = []
        # Always show basic categories
        basic_categories = ["user", "vps", "ports", "system", "bot"]
        for category in basic_categories:
            options.append(discord.SelectOption(
                label=self.command_categories[category]["name"],
                value=category,
                emoji=self.get_category_emoji(category)
            ))
       
        # Add nodes category if admin
        if admin_access:
            options.append(discord.SelectOption(
                label=self.command_categories["nodes"]["name"],
                value="nodes",
                emoji=self.get_category_emoji("nodes")
            ))
       
        # Add admin categories if user has permissions
        if admin_access:
            options.append(discord.SelectOption(
                label=self.command_categories["admin"]["name"],
                value="admin",
                emoji=self.get_category_emoji("admin")
            ))
            options.append(discord.SelectOption(
                label=self.command_categories["expiration"]["name"],
                value="expiration",
                emoji=self.get_category_emoji("expiration")
            ))
            options.append(discord.SelectOption(
                label=self.command_categories["maintenance"]["name"],
                value="maintenance",
                emoji=self.get_category_emoji("maintenance")
            ))
       
        if is_main_admin_user:
            options.append(discord.SelectOption(
                label=self.command_categories["main_admin"]["name"],
                value="main_admin",
                emoji=self.get_category_emoji("main_admin")
            ))
       
        self.select.options = options
        self.select.callback = self.select_callback
   
    async def select_callback(self, interaction: discord.Interaction):
        """Handle category selection"""
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This menu is not for you!", ephemeral=True)
            return
        
        self.current_category = interaction.data['values'][0]
        self.update_embed()
        await interaction.response.edit_message(embed=self.embed, view=self)

    def get_category_emoji(self, category):
        """Get emoji for each category"""
        emojis = {
            "user": "👤",
            "vps": "🖥️",
            "ports": "🔌",
            "system": "⚙️",
            "bot": "🤖",
            "nodes": "🌐",
            "admin": "🛡️",
            "expiration": "⏰",
            "maintenance": "🔧",
            "main_admin": "👑"
        }
        return emojis.get(category, "📁")
   
    def update_embed(self):
        """Update the embed based on current category and user permissions"""
        category_data = self.command_categories[self.current_category]
        # Create embed with category-specific styling
        colors = {
            "user": 0x3498db, # Blue
            "vps": 0x2ecc71, # Green
            "ports": 0xe74c3c, # Red
            "system": 0xf39c12, # Orange
            "bot": 0x9b59b6, # Purple
            "nodes": 0x1abc9c, # Teal
            "admin": 0xe67e22, # Carrot
            "expiration": 0xff6b6b, # Coral red for expiration
            "maintenance": 0x34495e, # Dark gray for maintenance
            "main_admin": 0xf1c40f # Yellow
        }
        color = colors.get(self.current_category, 0x1a1a1a)
       
        title = f"📚 {BOT_NAME} Command Help - {category_data['name']}"
        description = f"**{category_data['name']}**\nUse the dropdown below to switch categories."
       
        # Add helpful tips based on category
        tips = {
            "user": f"Tip: Use `{PREFIX}myvps` to see all your VPS and `{PREFIX}manage` to control them.",
            "vps": f"Tip: Use `{PREFIX}manage` to control your VPS from Discord.",
            "ports": "Tip: Port forwards work for both TCP and UDP protocols.",
            "system": "Tip: Set thresholds to monitor resource usage across nodes.",
            "nodes": f"Tip: Use `{PREFIX}node list` to see all available nodes and their status.",
            "admin": f"Tip: Always check `{PREFIX}userinfo @user` before modifying VPS.",
            "expiration": "Tip: VPS are automatically suspended when they expire. Renew them to unsuspend.",
            "maintenance": f"Tip: Use `{PREFIX}backup-db` regularly to backup your VPS database.",
            "main_admin": "Tip: Be careful when adding/removing admin privileges."
        }
       
        if self.current_category in tips:
            description += f"\n\n💡 {tips[self.current_category]}"
       
        self.embed = create_embed(title, description, color)
       
        # Add commands to embed
        commands_text = "\n".join([f"**{cmd}** - {desc}" for cmd, desc in category_data["commands"]])
        add_field(self.embed, "Commands", commands_text, False)
       
        # Add appropriate footer based on category
        footers = {
            "user": f"{BOT_NAME} VPS Manager • User Commands • Need help? Contact admin",
            "vps": f"{BOT_NAME} VPS Manager • VPS Management • Cloning",
            "ports": f"{BOT_NAME} VPS Manager • Port Forwarding • TCP/UDP Support",
            "system": f"{BOT_NAME} VPS Manager • System Monitoring • Resource Management",
            "nodes": f"{BOT_NAME} VPS Manager • Multi-Node Management • Distributed Infrastructure",
            "bot": f"{BOT_NAME} VPS Manager • Bot Control • Status Management",
            "admin": f"{BOT_NAME} VPS Manager • Admin Panel • Restricted Access",
            "expiration": f"{BOT_NAME} VPS Manager • VPS Expiration • Auto-Suspension",
            "maintenance": f"{BOT_NAME} VPS Manager • System Maintenance • Database Backup & Repair",
            "main_admin": f"{BOT_NAME} VPS Manager • Main Admin • Full System Control"
        }
       
        self.embed.set_footer(text=footers.get(self.current_category, f"{BOT_NAME} VPS Manager"))


@bot.command(name='help')
async def show_help(ctx):
    """Display the interactive help menu"""
    view = HelpView(ctx)
    await ctx.send(embed=view.embed, view=view)


# Command aliases for typos and convenience
@bot.command(name='mangage')
async def manage_typo(ctx):
    await ctx.send(embed=create_info_embed("Command Correction", f"Did you mean `{PREFIX}manage`? Use the correct command."))


@bot.command(name='commands')
async def commands_alias(ctx):
    """Alias for help command"""
    await show_help.callback(ctx)


@bot.command(name='stats')
async def stats_alias(ctx):
    if is_admin_user(ctx.author):
        await server_stats.callback(ctx)
    else:
        await ctx.send(embed=create_error_embed("Access Denied", "This command requires admin privileges."))


@bot.command(name='info')
async def info_alias(ctx, user: discord.Member = None):
    if is_admin_user(ctx.author):
        if user:
            await user_info.callback(ctx, user)
        else:
            await ctx.send(embed=create_error_embed("Usage", f"Please specify a user: `{PREFIX}info @user`"))
    else:
        await ctx.send(embed=create_error_embed("Access Denied", "This command requires admin privileges."))
# Run the bot
if __name__ == "__main__":
    if not DISCORD_TOKEN or DISCORD_TOKEN.strip() == '' or DISCORD_TOKEN == 'your_discord_bot_token_here':
        logger.error("❌ ERROR: No valid Discord token found!")
        logger.error("Please update your .env file with a valid Discord bot token.")
        logger.error("DISCORD_TOKEN in .env is currently set to: " + str(DISCORD_TOKEN))
        exit(1)
    restart_delay = max(3, int(os.getenv("BOT_RESTART_DELAY", "8")))
    auto_restart = str(os.getenv("BOT_AUTO_RESTART", "true")).strip().lower() in {"1", "true", "yes", "on"}
    while True:
        try:
            bot.run(DISCORD_TOKEN)
            break
        except discord.errors.LoginFailure as e:
            logger.error(f"❌ ERROR: Failed to login with Discord token: {e}")
            logger.error("Please check your DISCORD_TOKEN in the .env file.")
            break
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.critical("🔥 Fatal bot process error: %s", e, exc_info=True)
            if not auto_restart:
                break
            logger.warning("♻️ Auto-restarting RGNODES™ bot process in %ss.", restart_delay)
            time.sleep(restart_delay)

