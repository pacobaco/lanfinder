LANFinder - README.md
# LANFinder

**Complete Local Area Network Discovery, Relationship Mapping, Alert System & Web Dashboard**

A powerful, all-in-one Python tool for discovering devices on your LAN, tracking known persons/devices, modeling relationships with degrees of separation, and receiving instant alerts when targets join the network.

---

## ✨ Features

- **Fast ARP Network Scanning** — Auto-detects your LAN subnet and lists active devices (IP, MAC, hostname, vendor)
- **Persistent Known Devices** — SQLite database with history (first/last seen, active status)
- **B+Tree Person Index** — Ultra-fast on-disk lookup and storage for persons using the third-party `bplustree` library
- **Relationship Graph & Degrees of Separation** — NetworkX-powered graph for employees, LAN accessors, household family members, and known associates
- **Smart Alert System** — Desktop notifications (plyer), logs, and cooldowns when targets access the LAN
- **Simple Web Dashboard** — Flask-based UI with live stats, device tables, person search, alert management, and monitoring controls
- **CLI + Web** — Full-featured command line and browser interface
- **Cross-platform** — Works on Windows, Linux, macOS (with Npcap on Windows)

---

## 🚀 Quick Start

### 1. Installation

```bash
pip install scapy ifcfg rich networkx bplustree plyer flask mac-vendor-lookup
Windows users: Install Npcap for raw packet support.
2. Run the Tool
# Launch web dashboard (recommended)
python lanfinder.py dashboard

# Or use CLI
python lanfinder.py scan
python lanfinder.py monitor
Open http://localhost:5000 in your browser for the dashboard.

📋 Usage Examples
CLI Commands
python lanfinder.py scan                    # Scan and update devices
python lanfinder.py lookup-person "Alice"   # B+Tree lookup + degree info
python lanfinder.py set-alert --target "Alice Chen" --type person --notify desktop
python lanfinder.py add-relationship "You" "Alice Chen" family
python lanfinder.py degrees "Alice Chen" "Bob"
python lanfinder.py monitor                 # Background monitoring with alerts
Web Dashboard
	•	Home — Overview cards, active devices, monitoring status
	•	Scan Now button — Triggers immediate ARP scan
	•	Start/Stop Monitoring — Controls background alerts
	•	Persons & Alerts pages — Manage everything visually

🛠️ Architecture & Tech Stack
	•	Scanning: Scapy (ARP) + ifcfg (subnet detection)
	•	Storage: SQLite (devices, relationships, targets) + B+Tree (bplustree) for persons
	•	Graph: NetworkX for degrees of separation
	•	UI: Flask + Bootstrap 5 (dashboard) + Rich (CLI tables)
	•	Alerts: Plyer (desktop notifications) + logging
	•	Monitoring: Background thread with configurable interval
Files created:
	•	lanfinder.db — SQLite database
	•	persons.btree — Fast person index
	•	lanfinder_alerts.log — Alert history

📸 Dashboard Preview
The web UI includes:
	•	Live device tables
	•	Person search with B+Tree
	•	Relationship and degree overview
	•	Alert configuration
	•	One-click monitoring toggle
(Beautiful, responsive Bootstrap design with real-time stats)

⚙️ Configuration Tips
	•	Edit DEFAULT_INTERVAL in the script for scan frequency
	•	Add multiple targets with different notification methods
	•	Use add-relationship to build your social/professional graph
	•	For production monitoring, run the dashboard or monitor command in the background (systemd, Task Scheduler, etc.)

🔒 Security & Notes
	•	All data stays local on your machine
	•	Requires admin/root privileges for ARP scanning
	•	Only scan networks you own or have permission to monitor
	•	Desktop alerts require the script to be running

📝 License
MIT License — feel free to modify and extend.

🤝 Contributing
Pull requests welcome! Ideas:
	•	More notification channels (Telegram, email templates)
	•	Interactive graph visualization (vis.js)
	•	Docker support
	•	Export reports (CSV/PDF)

Made with ❤️ for network awareness and relationship mapping.
Enjoy using LANFinder!
---

### How to Use This README

1. Copy the content above into a new file named **`README.md`** in your project folder.
2. Update any paths or details if you customize the script.
3. Commit it to your repo for a professional presentation.

Would you like a **more detailed technical README**, a **screenshot mockup** (via generated image), or additions like installation troubleshooting / FAQ section? Let me know!
