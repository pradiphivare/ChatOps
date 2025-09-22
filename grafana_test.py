import os
import requests
from dotenv import load_dotenv

load_dotenv()

GRAFANA_URL = os.getenv("GRAFANA_URL")
GRAFANA_API_TOKEN = os.getenv("GRAFANA_API_TOKEN")
DASHBOARD_UID = os.getenv("DASHBOARD_UID")

HEADERS = {
    "Authorization": f"Bearer {GRAFANA_API_TOKEN}",
    "Content-Type": "application/json"
}

def test_grafana():
    url = f"{GRAFANA_URL}/api/dashboards/uid/{DASHBOARD_UID}"
    try:
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        dashboard = resp.json().get("dashboard", {})
        title = dashboard.get("title", "Unknown")
        panels = dashboard.get("panels", [])
        print(f"✅ Grafana Dashboard title: {title}")
        print(f"✅ Dashboard UID: {DASHBOARD_UID}")
        print(f"✅ Number of panels: {len(panels)}")
    except Exception as e:
        print(f"❌ Grafana test failed: {e}")

if __name__ == "__main__":
    test_grafana()
