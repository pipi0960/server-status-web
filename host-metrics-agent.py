#!/usr/bin/env python3
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import psutil

TOKEN = os.getenv("HOST_METRICS_TOKEN", "").strip()
HOST = os.getenv("HOST_METRICS_BIND", "127.0.0.1")
PORT = int(os.getenv("HOST_METRICS_PORT", "19100"))
BOOT_TIME = psutil.boot_time()


def bytes_to_human(num: float) -> str:
    step = 1024.0
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    value = float(num)
    for unit in units:
        if value < step:
            return f"{value:.2f} {unit}"
        value /= step
    return f"{value:.2f} EB"


def uptime_human(seconds: float) -> str:
    sec = int(seconds)
    days, sec = divmod(sec, 86400)
    hours, sec = divmod(sec, 3600)
    minutes, sec = divmod(sec, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{sec}s")
    return " ".join(parts)


def build_status() -> dict:
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    loadavg = os.getloadavg() if hasattr(os, "getloadavg") else (0.0, 0.0, 0.0)
    return {
        "time": int(time.time()),
        "hostname": os.uname().nodename,
        "uptime": uptime_human(time.time() - BOOT_TIME),
        "cpu": {
            "percent": psutil.cpu_percent(interval=0.2),
            "cores_logical": psutil.cpu_count(logical=True),
            "cores_physical": psutil.cpu_count(logical=False),
            "loadavg": [round(x, 2) for x in loadavg],
        },
        "memory": {
            "percent": vm.percent,
            "used": bytes_to_human(vm.used),
            "total": bytes_to_human(vm.total),
            "swap_percent": swap.percent,
            "swap_used": bytes_to_human(swap.used),
            "swap_total": bytes_to_human(swap.total),
        },
        "disk": {
            "percent": disk.percent,
            "used": bytes_to_human(disk.used),
            "total": bytes_to_human(disk.total),
            "free": bytes_to_human(disk.free),
        },
        "network": {
            "bytes_sent": bytes_to_human(net.bytes_sent),
            "bytes_recv": bytes_to_human(net.bytes_recv),
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
        },
    }


class Handler(BaseHTTPRequestHandler):
    def _write(self, code: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path != "/api/host-status":
            self._write(404, {"error": "not found"})
            return
        if TOKEN and self.headers.get("X-Metrics-Token", "") != TOKEN:
            self._write(401, {"error": "unauthorized"})
            return
        self._write(200, build_status())

    def log_message(self, *_args):
        return


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), Handler)
    print(f"host-metrics-agent listening on http://{HOST}:{PORT}/api/host-status")
    server.serve_forever()
