from flask import Flask, request, render_template, redirect, Response, jsonify, make_response
from functools import wraps
import subprocess
import re
import json
import os
import socket
import sys
sys.path.insert(0, '/etc/Tailscale-Route-Manager')
from config import USERNAME, PASSWORD

app = Flask(__name__, template_folder='templates', static_folder='static')

ROUTE_FILE = "/etc/Tailscale-Route-Manager/routes.json"
TAILSCALE_CMD = ["sudo", "/usr/bin/tailscale"]
CONFIG_PATH = "/etc/Tailscale-Route-Manager/config.py"

if not os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "w") as f:
        f.write('USERNAME = "admin"\nPASSWORD = "changeme"\n')
    os.chmod(CONFIG_PATH, 0o600)

def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def authenticate():
    return Response(
        "Authentication required", 401,
        {"WWW-Authenticate": 'Basic realm="Tailscale Route Manager"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def get_routes():
    if not os.path.exists(ROUTE_FILE):
        try:
            with open(ROUTE_FILE, "w") as f:
                json.dump([], f)
        except Exception as e:
            print(f"Error creating {ROUTE_FILE}: {e}")
            return []
    try:
        with open(ROUTE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_routes(routes):
    with open(ROUTE_FILE, "w") as f:
        json.dump(routes, f)

def update_advertised_routes():
    routes = get_routes()
    advertised = [entry["route"] for entry in routes]
    advertise_arg = ",".join(advertised)
    subprocess.call([*TAILSCALE_CMD, "up", f"--advertise-routes={advertise_arg}", "--accept-routes=false"])

def get_connected_devices():
    try:
        json_output = subprocess.check_output(
            [*TAILSCALE_CMD, "status", "--json"],
            timeout=2
        ).decode()
        status = json.loads(json_output)

        raw_output = subprocess.check_output(
            [*TAILSCALE_CMD, "status"],
            timeout=2
        ).decode()

        ip_user_map = {}
        ip_hostname_map = {}
        ip_os_map = {}
        ip_conn_map = {}

        for line in raw_output.strip().splitlines():
            parts = line.split()
            if len(parts) >= 5:
                ip = parts[0]
                hostname = parts[1]
                user = parts[2].replace("@", "") if parts[2] != "-" else ""
                os_type = parts[3]
                connection_details = " ".join(parts[4:])

                # Determine connection type and details
                if "direct" in connection_details:
                    match = re.search(r"direct ([\d\.]+)", connection_details)
                    conn = f"direct ({match.group(1)})" if match else "direct"
                elif "relay" in connection_details:
                    match = re.search(r'relay "([^"]+)"', connection_details)
                    conn = f'relay ({match.group(1)})' if match else "relay"
                else:
                    conn = ""

                ip_user_map[ip] = user
                ip_hostname_map[ip] = hostname
                ip_os_map[ip] = os_type
                ip_conn_map[ip] = conn

        devices = []

        self_info = status.get("Self", {})
        self_ip = self_info.get("TailscaleIPs", ["N/A"])[0]
        devices.append({
            "hostname": ip_hostname_map.get(self_ip, "self") + " (self)",
            "ip": self_ip,
            "online": self_info.get("Online", True),
            "status": "Online" if self_info.get("Online", True) else "Offline",
            "user": ip_user_map.get(self_ip, ""),
            "os": ip_os_map.get(self_ip, ""),
            "connection": ip_conn_map.get(self_ip, "")
        })

        for peer in status.get("Peer", {}).values():
            ip = peer.get("TailscaleIPs", ["N/A"])[0]
            devices.append({
                "hostname": ip_hostname_map.get(ip, "unknown"),
                "ip": ip,
                "online": peer.get("Online", False),
                "status": "Online" if peer.get("Online", False) else "Offline",
                "user": ip_user_map.get(ip, ""),
                "os": ip_os_map.get(ip, ""),
                "connection": ip_conn_map.get(ip, "") if peer.get("Online", False) else ""
            })

        return devices

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError):
        return []

def get_tailscale_running_status():
    try:
        output = subprocess.check_output([*TAILSCALE_CMD, "status"], timeout=2).decode().strip()
        if "Tailscale is stopped." in output:
            return "stopped"
        return "running"
    except Exception:
        return "unknown"

def get_lsb_info():
    try:
        output = subprocess.check_output(["lsb_release", "-a"], stderr=subprocess.DEVNULL).decode()
        lines = output.strip().splitlines()
        info = {}
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                info[key.strip()] = value.strip()
        return f"{info.get('Description', '')} ({info.get('Codename', '')})"
    except Exception:
        return "Unknown OS Version"

@app.route("/")
@requires_auth
def index():
    routes = get_routes()
    devices = get_connected_devices()
    hostname = socket.gethostname()
    lsb_info = get_lsb_info()
    tailscale_status = get_tailscale_running_status()

    response = make_response(render_template(
        "index.html",
        routes=routes,
        devices=devices,
        tailscale_status=tailscale_status,
        server_hostname=hostname,
        server_os=lsb_info
    ))
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route("/add", methods=["POST"])
@requires_auth
def add_route():
    new_route = request.form.get("route", "").strip()
    description = request.form.get("description", "").strip()

    if not re.match(r"^\d{1,3}(\.\d{1,3}){3}/\d{1,2}$", new_route):
        return "Invalid route format", 400

    routes = get_routes()
    if not any(entry["route"] == new_route for entry in routes):
        routes.append({"route": new_route, "description": description})
        save_routes(routes)
        update_advertised_routes()

    return redirect("/")

@app.route("/remove", methods=["POST"])
@requires_auth
def remove_route():
    route_to_remove = request.form.get("route", "").strip()
    routes = get_routes()
    routes = [entry for entry in routes if entry["route"] != route_to_remove]
    save_routes(routes)
    update_advertised_routes()
    return redirect("/")

@app.route("/start", methods=["POST"])
@requires_auth
def start_tailscale():
    update_advertised_routes()
    return redirect("/")

@app.route("/stop", methods=["POST"])
@requires_auth
def stop_tailscale():
    subprocess.Popen(
        [*TAILSCALE_CMD, "down"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    return redirect("/")

@app.route("/devices")
@requires_auth
def devices_api():
    devices = get_connected_devices()

    # Ensure only the necessary fields are passed (optional, but safe)
    sanitized_devices = []
    for d in devices:
        sanitized_devices.append({
            "hostname": d.get("hostname", ""),
            "ip": d.get("ip", ""),
            "status": d.get("status", ""),
            "user": d.get("user", ""),
            "os": d.get("os", ""),
            "connection": d.get("connection", "")
        })

    response = jsonify(devices=sanitized_devices)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response