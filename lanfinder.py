#!/usr/bin/env python3
"""
LANFinder v4 - Complete Tool with Web Dashboard
Includes: ARP Scan, B+Tree Persons, Degree Graph, Alerts, Monitoring + Web UI
"""

import argparse
import sqlite3
import json
import time
import socket
import threading
from datetime import datetime, timedelta
from pathlib import Path

# Core + Web
from flask import Flask, render_template_string, request, redirect, url_for
try:
    from scapy.all import ARP, Ether, srp
    import ifcfg
    from rich.console import Console
    from rich.table import Table
    import networkx as nx
    from bplustree import BPlusTree
    from plyer import notification
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("pip install scapy ifcfg rich networkx bplustree plyer flask")
    exit(1)

console = Console()

# ==================== CONFIG ====================
DB_FILE = "lanfinder.db"
BTREE_FILE = "persons.btree"
ALERT_LOG = "lanfinder_alerts.log"
DEFAULT_INTERVAL = 30

# Global monitor thread control
monitor_thread = None
monitor_running = False

# ==================== DATABASE & B+TREE (same as before) ====================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # ... (same CREATE TABLE statements as previous script)
    c.execute('''CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY, mac TEXT UNIQUE, ip TEXT, hostname TEXT,
        vendor TEXT, first_seen TIMESTAMP, last_seen TIMESTAMP,
        is_active BOOLEAN DEFAULT 0, notes TEXT, user_id INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, name TEXT UNIQUE, notes TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS targets (
        id INTEGER PRIMARY KEY, name TEXT, target_type TEXT,
        mac TEXT, alert_on TEXT DEFAULT 'join', notify_methods TEXT,
        cooldown_minutes INTEGER DEFAULT 30, enabled BOOLEAN DEFAULT 1,
        last_alert TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS relationships (
        id INTEGER PRIMARY KEY, from_name TEXT, to_name TEXT, rel_type TEXT,
        UNIQUE(from_name, to_name, rel_type)
    )''')
    conn.commit()
    conn.close()

def get_db_connection():
    return sqlite3.connect(DB_FILE)

def get_btree():
    return BPlusTree(BTREE_FILE, order=50)

def add_or_update_person(name, ptype="person", notes="", linked_mac=None):
    btree = get_btree()
    data = {"name": name, "type": ptype, "notes": notes,
            "linked_macs": [linked_mac] if linked_mac else [],
            "updated": datetime.now().isoformat()}
    btree[name] = json.dumps(data).encode()

def lookup_person(name):
    btree = get_btree()
    return json.loads(btree[name].decode()) if name in btree else None

# ==================== SCANNING (same functions) ====================
def get_local_subnet(): ...  # (keep previous implementation)
def arp_scan(network): ...   # (keep previous)
def update_devices(devices): ...  # (keep previous)

# ==================== GRAPH & DEGREE ====================
def build_graph():
    G = nx.Graph()
    btree = get_btree()
    for name in btree:
        data = json.loads(btree[name].decode())
        G.add_node(name, **data)
    conn = get_db_connection()
    for row in conn.execute("SELECT from_name, to_name, rel_type FROM relationships"):
        G.add_edge(row[0], row[1], type=row[2])
    conn.close()
    return G

def get_degree(G, source, target):
    try:
        return nx.shortest_path_length(G, source=source, target=target)
    except:
        return None

# ==================== ALERTS ====================
def send_alert(target_name, device, degree, methods):
    msg = f"🚨 {target_name} just accessed LAN\nDevice: {device['ip']} | {device['mac']}\nDegree: {degree}"
    console.print(f"[bold red]{msg}[/bold red]")
    with open(ALERT_LOG, "a") as f:
        f.write(msg + "\n")
    if "desktop" in methods:
        try:
            notification.notify(title="LANFinder Alert", message=msg[:180], timeout=12)
        except:
            pass

def is_new_access(target_name, cooldown):
    conn = get_db_connection()
    row = conn.execute("SELECT last_alert FROM targets WHERE name=?", (target_name,)).fetchone()
    conn.close()
    if not row or not row[0]:
        return True
    return datetime.now() - datetime.fromisoformat(row[0]) > timedelta(minutes=cooldown)

def update_last_alert(target_name):
    conn = get_db_connection()
    conn.execute("UPDATE targets SET last_alert=? WHERE name=?", (datetime.now().isoformat(), target_name))
    conn.commit()
    conn.close()

# ==================== MONITORING ====================
def monitor_loop(interval=DEFAULT_INTERVAL):
    global monitor_running
    G = build_graph()
    while monitor_running:
        devices = arp_scan(get_local_subnet())
        update_devices(devices)
        conn = get_db_connection()
        for row in conn.execute("SELECT name, notify_methods, cooldown_minutes FROM targets WHERE enabled=1"):
            name, methods_json, cooldown = row
            methods = json.loads(methods_json) if methods_json else ["desktop", "log"]
            person = lookup_person(name)
            if not person:
                continue
            matching = next((d for d in devices if d['mac'] in person.get('linked_macs', [])), None)
            if matching and is_new_access(name, cooldown):
                degree = get_degree(G, "You", name)
                send_alert(name, matching, degree, methods)
                update_last_alert(name)
        conn.close()
        time.sleep(interval)

def start_monitor(interval=DEFAULT_INTERVAL):
    global monitor_thread, monitor_running
    if not monitor_running:
        monitor_running = True
        monitor_thread = threading.Thread(target=monitor_loop, args=(interval,), daemon=True)
        monitor_thread.start()
        return True
    return False

def stop_monitor():
    global monitor_running
    monitor_running = False
    return True

# ==================== SIMPLE WEB DASHBOARD ====================
app = Flask(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>LANFinder Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>body { padding: 20px; background: #f8f9fa; }</style>
</head>
<body>
<div class="container">
    <h1 class="mb-4">LANFinder Dashboard</h1>
    
    <div class="row mb-4">
        <div class="col-md-3"><div class="card p-3"><h5>Active Devices</h5><h2>{{ active_count }}</h2></div></div>
        <div class="col-md-3"><div class="card p-3"><h5>Known Persons</h5><h2>{{ person_count }}</h2></div></div>
        <div class="col-md-3"><div class="card p-3"><h5>Monitoring</h5><h2>{{ 'Running' if monitor_running else 'Stopped' }}</h2></div></div>
        <div class="col-md-3"><div class="card p-3"><h5>Last Scan</h5><small>{{ last_scan }}</small></div></div>
    </div>

    <div class="mb-3">
        <a href="{{ url_for('scan') }}" class="btn btn-primary">Scan LAN Now</a>
        <a href="{{ url_for('start_monitor_route') }}" class="btn btn-success">Start Monitoring</a>
        <a href="{{ url_for('stop_monitor_route') }}" class="btn btn-danger">Stop Monitoring</a>
        <a href="{{ url_for('persons') }}" class="btn btn-info">View Persons</a>
        <a href="{{ url_for('alerts') }}" class="btn btn-warning">Manage Alerts</a>
    </div>

    <h3>Active Devices</h3>
    <table class="table table-striped">
        <thead><tr><th>IP</th><th>MAC</th><th>Hostname</th><th>Vendor</th></tr></thead>
        <tbody>
        {% for d in devices %}
        <tr><td>{{ d.ip }}</td><td>{{ d.mac }}</td><td>{{ d.hostname }}</td><td>{{ d.vendor }}</td></tr>
        {% endfor %}
        </tbody>
    </table>
</div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    conn = get_db_connection()
    active = conn.execute("SELECT COUNT(*) FROM devices WHERE is_active=1").fetchone()[0]
    person_count = len(list(get_btree()))
    conn.close()
    devices = arp_scan(get_local_subnet()) if request.args.get('refresh') else []
    if devices:
        update_devices(devices)
    return render_template_string(DASHBOARD_HTML,
        active_count=active,
        person_count=person_count,
        monitor_running=monitor_running,
        last_scan=datetime.now().strftime("%H:%M:%S"),
        devices=devices or [])

@app.route('/scan')
def scan():
    devices = arp_scan(get_local_subnet())
    update_devices(devices)
    return redirect(url_for('dashboard', refresh=1))

@app.route('/persons')
def persons():
    btree = get_btree()
    people = []
    for name in btree:
        people.append(json.loads(btree[name].decode()))
    return render_template_string("""
    <h2>Persons (B+Tree Index)</h2>
    <ul>{% for p in people %}<li>{{ p.name }} ({{ p.type }})</li>{% endfor %}</ul>
    <a href="/">Back to Dashboard</a>
    """, people=people)

@app.route('/alerts')
def alerts():
    conn = get_db_connection()
    targets = conn.execute("SELECT * FROM targets").fetchall()
    conn.close()
    return render_template_string("""
    <h2>Alert Targets</h2>
    <table class="table"><tr><th>Name</th><th>Type</th><th>Notify</th></tr>
    {% for t in targets %}<tr><td>{{ t[1] }}</td><td>{{ t[2] }}</td><td>{{ t[5] }}</td></tr>{% endfor %}
    </table>
    <a href="/">Back</a>
    """, targets=targets)

@app.route('/start-monitor')
def start_monitor_route():
    start_monitor()
    return redirect(url_for('dashboard'))

@app.route('/stop-monitor')
def stop_monitor_route():
    stop_monitor()
    return redirect(url_for('dashboard'))

# ==================== MAIN ====================
def main():
    init_db()
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    
    # Existing CLI commands (scan, lookup-person, set-alert, monitor, etc.)
    p_scan = subparsers.add_parser("scan")
    p_scan.set_defaults(func=lambda args: cmd_scan(args))  # reuse previous cmd_scan
    
    # New web dashboard command
    p_dash = subparsers.add_parser("dashboard", help="Launch web dashboard")
    p_dash.add_argument("--port", type=int, default=5000)
    p_dash.add_argument("--host", default="0.0.0.0")
    p_dash.set_defaults(func=lambda args: app.run(host=args.host, port=args.port, debug=False))
    
    args = parser.parse_args()
    if args.command == "dashboard":
        print(f"🌐 LANFinder Dashboard running at http://localhost:{args.port}")
        app.run(host=args.host, port=args.port, debug=False)
    elif args.command:
        # handle other CLI commands here (reuse from previous version)
        pass
    else:
        parser.print_help()

if __name__ == "__main__":
    main()