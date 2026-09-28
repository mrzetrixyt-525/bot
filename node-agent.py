#!/usr/bin/env python3
"""RGNODES™ LXD remote node agent.

Stdlib-only HTTP API compatible with bot.py:
  GET  /api/ping
  GET  /api/get_host_stats
  GET  /api/get_access_info
  POST /api/get_container_stats JSON: {"container":"name"}
  POST /api/execute   JSON: {"command":"lxc ..."}

Authentication: X-API-Key or Authorization: Bearer ...
The agent never invokes a shell; only the lxc executable is accepted.
"""
from __future__ import annotations

import argparse
import hmac
import json
import os
import shutil
import shlex
import socket
import subprocess
import time
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def read_cpu():
    def snap():
        with open('/proc/stat', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('cpu '):
                    vals = [int(x) for x in line.split()[1:]]
                    idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
                    return sum(vals), idle
        return 0, 0
    a_total, a_idle = snap()
    time.sleep(0.15)
    b_total, b_idle = snap()
    total = b_total - a_total
    idle = b_idle - a_idle
    return round(max(0.0, min(100.0, (total - idle) * 100.0 / total)), 1) if total > 0 else 0.0


def read_ram():
    total = available = 0
    try:
        with open('/proc/meminfo', 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2 and parts[0] == 'MemTotal:':
                    total = int(parts[1]) * 1024
                elif len(parts) >= 2 and parts[0] == 'MemAvailable:':
                    available = int(parts[1]) * 1024
    except OSError:
        return {"used": 0, "total": 0, "percent": 0.0}
    used = max(0, total - available)
    percent = round((used / total * 100.0), 1) if total else 0.0
    return {"used": used, "total": total, "percent": percent}


def host_stats():
    disk = shutil.disk_usage('/')
    uptime = 0.0
    try:
        uptime = float(Path('/proc/uptime').read_text().split()[0])
    except Exception:
        pass
    return {
        "cpu": read_cpu(),
        "ram": read_ram()["percent"],
        "ram_bytes_used": read_ram()["used"],
        "ram_bytes_total": read_ram()["total"],
        "disk": {
            "used": disk.used,
            "total": disk.total,
            "free": disk.free,
            "percent": round((disk.used / disk.total * 100.0), 1) if disk.total else 0.0,
        },
        "uptime": uptime,
        "hostname": socket.gethostname(),
    }


def api_key_from_request(handler: BaseHTTPRequestHandler) -> str:
    supplied = handler.headers.get('X-API-Key', '')
    if not supplied:
        auth = handler.headers.get('Authorization', '')
        if auth.lower().startswith('bearer '):
            supplied = auth[7:].strip()
    return supplied.strip()


def command_json(argv, timeout=30):
    try:
        proc = subprocess.run(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return 127, '', 'command not found'
    except subprocess.TimeoutExpired:
        return 124, '', 'command timed out'


def discover_public_endpoints():
    public_ipv4 = os.getenv('RGNODES_PUBLIC_IPV4', '').strip()
    public_ipv6 = os.getenv('RGNODES_PUBLIC_IPV6', '').strip()
    try:
        import ipaddress
        ip4 = ipaddress.ip_address(public_ipv4) if public_ipv4 else None
        ip6 = ipaddress.ip_address(public_ipv6) if public_ipv6 else None
        if ip4 and not (ip4.version == 4 and ip4.is_global):
            public_ipv4 = ''
        if ip6 and not (ip6.version == 6 and ip6.is_global):
            public_ipv6 = ''
    except Exception:
        public_ipv4, public_ipv6 = '', ''
    if not public_ipv4:
        rc, out, _ = command_json(['ip', '-4', 'route', 'get', '1.1.1.1'])
        if rc == 0:
            parts = out.split()
            if 'src' in parts:
                candidate = parts[parts.index('src') + 1]
                try:
                    import ipaddress
                    ip = ipaddress.ip_address(candidate)
                    if ip.version == 4 and ip.is_global:
                        public_ipv4 = candidate
                except Exception:
                    pass
    if not public_ipv4:
        try:
            from urllib.request import Request, urlopen
            req = Request('https://api4.ipify.org', headers={'User-Agent': 'RGNODES-node-agent/1.0'})
            with urlopen(req, timeout=2.5) as resp:
                candidate = resp.read(64).decode('ascii', 'ignore').strip()
            import ipaddress
            if ipaddress.ip_address(candidate).version == 4 and ipaddress.ip_address(candidate).is_global:
                public_ipv4 = candidate
        except Exception:
            pass

    if not public_ipv6:
        rc, out, _ = command_json(['ip', '-6', '-o', 'addr', 'show', 'scope', 'global'])
        if rc == 0:
            for token in out.split():
                if '/' not in token:
                    continue
                candidate = token.split('/',1)[0]
                try:
                    import ipaddress
                    ip = ipaddress.ip_address(candidate)
                    if ip.version == 6 and ip.is_global:
                        public_ipv6 = candidate
                        break
                except Exception:
                    continue
    if not public_ipv6:
        try:
            from urllib.request import Request, urlopen
            req = Request('https://api6.ipify.org', headers={'User-Agent': 'RGNODES-node-agent/1.0'})
            with urlopen(req, timeout=2.5) as resp:
                candidate = resp.read(128).decode('ascii', 'ignore').strip()
            import ipaddress
            if ipaddress.ip_address(candidate).version == 6 and ipaddress.ip_address(candidate).is_global:
                public_ipv6 = candidate
        except Exception:
            pass
    return public_ipv4, public_ipv6


def container_stats(name):
    # Status and limits from LXD info.
    rc, info_out, info_err = command_json(['lxc', 'info', name], timeout=30)
    if rc != 0:
        return {'status':'unknown', 'cpu':0.0, 'ram':{'used':0,'total':0,'pct':0.0}, 'disk':'Unknown', 'uptime':'Unknown', 'error':info_err[-500:]}
    status = 'unknown'
    for line in info_out.splitlines():
        if line.startswith('Status:'):
            status = line.split(':',1)[1].strip().lower()
            break
    rc, free_out, _ = command_json(['lxc','exec',name,'--','free','-m'], timeout=20)
    ram = {'used':0,'total':0,'pct':0.0}
    if rc == 0:
        for line in free_out.splitlines():
            if line.lower().startswith('mem:'):
                parts=line.split()
                if len(parts)>=3:
                    total=int(parts[1]); used=int(parts[2]); ram={'used':used,'total':total,'pct':round(used*100/total,1) if total else 0.0}
                    break
    rc, df_out, _ = command_json(['lxc','exec',name,'--','df','-h','/'], timeout=20)
    disk='Unknown'
    used_text = total_text = percent_text = ''
    if rc == 0:
        lines=df_out.splitlines()
        if len(lines)>=2:
            parts=lines[-1].split()
            if len(parts)>=5:
                used_text, total_text, percent_text = parts[2], parts[1], parts[4]
    rc, quota_out, _ = command_json(['lxc','config','device','get',name,'root','size'], timeout=15)
    if rc == 0 and quota_out.strip():
        disk = f'{used_text}/{quota_out.strip()} ({percent_text})' if used_text else quota_out.strip()
    elif used_text:
        disk = f'{used_text}/{total_text} ({percent_text})'
    rc, up_out, _ = command_json(['lxc','exec',name,'--','uptime'], timeout=20)
    uptime=up_out.strip() if rc==0 else 'Unknown'
    # Use /proc/stat sampling inside the guest for a bounded CPU reading.
    cpu_script = r'''set -- $(awk '/^cpu /{print $2+$3+$4+$5+$6+$7+$8+$9,$5+$6;exit}' /proc/stat)
ta=$1; ia=$2
sleep 0.15
set -- $(awk '/^cpu /{print $2+$3+$4+$5+$6+$7+$8+$9,$5+$6;exit}' /proc/stat)
tb=$1; ib=$2
awk -v t=$((tb-ta)) -v i=$((ib-ia)) 'BEGIN{if(t>0)printf "%.1f",((t-i)*100/t); else print "0.0"}'
'''
    rc, cpu_out, _ = command_json(['lxc','exec',name,'--','bash','-lc',cpu_script], timeout=20)
    cpu = float(cpu_out.strip() or 0) if rc==0 else 0.0
    return {'status':status,'cpu':cpu,'ram':ram,'disk':disk,'uptime':uptime}


class DualStackHTTPServer(ThreadingHTTPServer):
    address_family = socket.AF_INET6

    def server_bind(self):
        try:
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        except OSError:
            pass
        super().server_bind()


def build_server(host, port):
    if ':' in host:
        try:
            return DualStackHTTPServer((host, port), Handler)
        except OSError:
            pass
    return ThreadingHTTPServer((host, port), Handler)


class Handler(BaseHTTPRequestHandler):
    server_version = 'RGNODES-NodeAgent/1.0'

    def log_message(self, fmt, *args):
        # Avoid logging credentials/query strings.
        print(f"[{self.address_string()}] {fmt % args}", flush=True)

    def send_json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def authorized(self):
        expected = self.server.api_key  # type: ignore[attr-defined]
        supplied = api_key_from_request(self)
        return bool(expected) and hmac.compare_digest(supplied, expected)

    def do_GET(self):
        path = self.path.split('?', 1)[0].rstrip('/')
        if not self.authorized():
            self.send_json(401, {"error": "unauthorized"})
            return
        if path == '/api/ping':
            self.send_json(200, {"status": "ok", "service": "rgnodes-node-agent", "hostname": socket.gethostname()})
            return
        if path == '/api/get_host_stats':
            self.send_json(200, host_stats())
            return
        if path == '/api/get_access_info':
            ipv4, ipv6 = discover_public_endpoints()
            self.send_json(200, {
                'public_ipv4': ipv4,
                'public_ipv6': ipv6,
                'hostname': socket.gethostname(),
            })
            return
        if path == '/health':
            self.send_json(200, {"status": "ok"})
            return
        self.send_json(404, {"error": "not_found"})

    def do_POST(self):
        path = self.path.split('?', 1)[0].rstrip('/')
        if not self.authorized():
            self.send_json(401, {"error": "unauthorized"})
            return
        if path == '/api/get_container_stats':
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if length <= 0 or length > 32 * 1024:
                    raise ValueError('invalid content length')
                payload = json.loads(self.rfile.read(length).decode('utf-8'))
                name = str(payload.get('container', '')).strip()
                if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,63}', name):
                    raise ValueError('invalid container name')
                self.send_json(200, container_stats(name))
            except (ValueError, json.JSONDecodeError) as exc:
                self.send_json(400, {'error': str(exc)})
            return
        if path != '/api/execute':
            self.send_json(404, {"error": "not_found"})
            return

        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length <= 0 or length > 128 * 1024:
                raise ValueError('invalid content length')
            body = self.rfile.read(length)
            payload = json.loads(body.decode('utf-8'))
            command = str(payload.get('command', '')).strip()
            if not command:
                raise ValueError('command is required')
            if len(command) > 12000:
                raise ValueError('command too long')
            argv = shlex.split(command)
            if not argv or argv[0] != 'lxc':
                self.send_json(400, {"error": "only lxc commands are accepted"})
                return
            lxc = shutil.which('lxc') or '/snap/bin/lxc'
            if not os.path.exists(lxc):
                self.send_json(503, {"error": "lxc executable is unavailable"})
                return
            proc = subprocess.run(
                [lxc, *argv[1:]],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=900,
                check=False,
            )
            self.send_json(200, {
                "returncode": proc.returncode,
                "stdout": proc.stdout[-100000:],
                "stderr": proc.stderr[-100000:],
            })
        except subprocess.TimeoutExpired:
            self.send_json(408, {"error": "command timed out"})
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_json(400, {"error": str(exc)})
        except Exception as exc:
            self.send_json(500, {"error": str(exc)})


def main():
    parser = argparse.ArgumentParser(description='RGNODES™ LXD remote node agent')
    parser.add_argument('--host', default=os.getenv('RGNODES_AGENT_HOST', '::'))
    parser.add_argument('--port', type=int, default=int(os.getenv('RGNODES_AGENT_PORT', '18443')))
    parser.add_argument('--api_key', default=os.getenv('RGNODES_NODE_API_KEY', ''))
    args = parser.parse_args()
    if not args.api_key or len(args.api_key) < 24:
        raise SystemExit('A strong --api_key (24+ characters) is required.')
    if not (1 <= args.port <= 65535):
        raise SystemExit('Port must be 1-65535.')

    server = build_server(args.host, args.port)
    server.daemon_threads = True
    server.api_key = args.api_key  # type: ignore[attr-defined]
    print(f'RGNODES™ node agent listening on {args.host}:{args.port}', flush=True)
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
