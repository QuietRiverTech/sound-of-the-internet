"""Sound of the Internet — Backend server for Shodan data proxying."""

import os
import random
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load API key from env or ~/.hermes/.env
load_dotenv()
load_dotenv(Path.home() / ".hermes" / ".env")

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

SHODAN_API_KEY = os.getenv("SHODAN_API_KEY", "")


def simulated_hosts(query, count=12):
    """Generate fake host data when no Shodan API key is available."""
    protocols = ["http", "ssh", "ftp", "telnet", "smtp", "modbus", "dnp3", "rtsp", "dicom", "https"]
    orgs = ["CloudCorp", "MedDevice Inc", "IndustrialSys", "HomeNet IoT", "BigBank Ltd", "UniNetwork"]
    countries = ["US", "DE", "JP", "BR", "KR", "GB", "IN", "AU", "FR", "CN"]
    hosts = []
    for i in range(count):
        num_ports = random.randint(1, 8)
        ports = random.sample(range(20, 9000), num_ports)
        cvss = [round(random.uniform(0, 10), 1) for _ in range(random.randint(0, 3))]
        hosts.append({
            "ip": f"{random.randint(1,254)}.{random.randint(0,254)}.{random.randint(0,254)}.{random.randint(1,254)}",
            "ports": sorted(ports),
            "protocols": random.sample(protocols, min(num_ports, len(protocols))),
            "org": random.choice(orgs),
            "country": random.choice(countries),
            "vulns": [{"id": f"CVE-2025-{random.randint(1000,9999)}", "cvss": c} for c in cvss],
            "lat": round(random.uniform(-60, 70), 2),
            "lon": round(random.uniform(-170, 170), 2),
        })
    return hosts


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/api/shodan")
def shodan_search():
    query = request.args.get("query", "webcam")

    if not SHODAN_API_KEY:
        return jsonify({"source": "simulated", "query": query, "hosts": simulated_hosts(query)})

    try:
        import shodan
        api = shodan.Shodan(SHODAN_API_KEY)
        results = api.search(query, limit=20)
        hosts = []
        for match in results.get("matches", []):
            vulns = match.get("vulns", {})
            cvss_list = [{"id": v, "cvss": vulns[v].get("cvss", 0) if isinstance(vulns[v], dict) else 0} for v in vulns]
            hosts.append({
                "ip": match.get("ip_str", ""),
                "ports": [match.get("port", 0)],
                "protocols": [match.get("transport", "tcp")],
                "org": match.get("org", "Unknown"),
                "country": match.get("location", {}).get("country_code", ""),
                "vulns": cvss_list,
                "lat": match.get("location", {}).get("latitude", 0),
                "lon": match.get("location", {}).get("longitude", 0),
            })
        return jsonify({"source": "shodan", "query": query, "hosts": hosts})
    except Exception as e:
        return jsonify({"source": "simulated", "query": query, "error": str(e), "hosts": simulated_hosts(query)})


if __name__ == "__main__":
    print("🎵 Sound of the Internet — server running on http://localhost:5003")
    app.run(host="0.0.0.0", port=5003, debug=True)
