import os
import time
from functools import wraps
from urllib.error import URLError
from urllib.request import Request, urlopen
import json

import psutil
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-me-please")

USERNAME = os.getenv("DASHBOARD_USERNAME", "admin")
PASSWORD_PLAIN = os.getenv("DASHBOARD_PASSWORD", "admin123")
PASSWORD_HASH = os.getenv("DASHBOARD_PASSWORD_HASH", "")

if PASSWORD_HASH:
    STORED_PASSWORD_HASH = PASSWORD_HASH
else:
    STORED_PASSWORD_HASH = generate_password_hash(PASSWORD_PLAIN)

BOOT_TIME = psutil.boot_time()
HOST_METRICS_URL = os.getenv("HOST_METRICS_URL", "").strip()
HOST_METRICS_TOKEN = os.getenv("HOST_METRICS_TOKEN", "").strip()


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)

    return wrapper


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


@app.route("/")
def index():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == USERNAME and check_password_hash(STORED_PASSWORD_HASH, password):
            session["logged_in"] = True
            session["username"] = username
            next_url = request.args.get("next") or url_for("dashboard")
            return redirect(next_url)
        error = "用户名或密码错误"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=session.get("username", USERNAME))


@app.route("/api/status")
@login_required
def api_status():
    host_metrics_error = None
    if HOST_METRICS_URL:
        try:
            req = Request(HOST_METRICS_URL, method="GET")
            if HOST_METRICS_TOKEN:
                req.add_header("X-Metrics-Token", HOST_METRICS_TOKEN)
            with urlopen(req, timeout=2.5) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            payload["source"] = "host-agent"
            return jsonify(payload)
        except (URLError, TimeoutError, ValueError) as err:
            host_metrics_error = f"failed to fetch host metrics: {err}"

    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    loadavg = os.getloadavg() if hasattr(os, "getloadavg") else (0.0, 0.0, 0.0)

    status = {
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
        "source": "container",
    }
    if host_metrics_error:
        status["warning"] = host_metrics_error
        status["source"] = "container-fallback"
    return jsonify(status)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
