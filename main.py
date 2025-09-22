import requests
import json
from datetime import datetime, timezone

# ------------------ Configuration ------------------
GRAFANA_URL = "http://localhost:3000"
GRAFANA_API_TOKEN = "glsa_pmeJqOWJCjevjGua33wI6HTsbWqy3hGc_16461a03"
DASHBOARD_UID = "IV0hu1m7z"

SLACK_BOT_TOKEN = "xoxb-4283369281543-9540607100839-XpjkvPoumQDyS2E6mcBHHCot"
SLACK_CHANNEL_ID = "C048RQ3BX0B"

SERVER_VALUE = "localhost:9182"
INTERVAL_VALUE = "120s"

TIME_FROM = "now-5m"
TIME_TO = "now"
# ---------------------------------------------------

HEADERS = {
    "Authorization": f"Bearer {GRAFANA_API_TOKEN}",
    "Content-Type": "application/json"
}

def get_dashboard(uid):
    url = f"{GRAFANA_URL}/api/dashboards/uid/{uid}"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def fetch_panel_data(panel):
    datasource_uid = panel.get("datasource", {}).get("uid")
    queries = panel.get("targets", [])
    panel_title = panel.get("title", "Unknown Panel")

    panel_results = []

    for query in queries:
        expr = query.get("expr")
        if not expr:
            continue

        expr = expr.replace("$server", SERVER_VALUE)
        expr = expr.replace("$interval", INTERVAL_VALUE)

        api_url = f"{GRAFANA_URL}/api/ds/query"
        payload = {
            "queries": [
                {
                    "refId": query.get("refId", "A"),
                    "expr": expr,
                    "datasource": {"uid": datasource_uid},
                    "intervalMs": 120 * 1000,
                    "maxDataPoints": 1000,
                    "instant": True
                }
            ],
            "from": TIME_FROM,
            "to": TIME_TO
        }

        try:
            r = requests.post(api_url, headers=HEADERS, data=json.dumps(payload))
            r.raise_for_status()
            data = r.json()

            frames = data.get("results", {}).get(query.get("refId", "A"), {}).get("frames", [])
            last_value = None
            if frames and len(frames) > 0:
                values = frames[0].get("data", {}).get("values", [])
                if values and len(values) == 2:
                    metric_values = values[1]
                    if metric_values and len(metric_values) > 0:
                        last_value = metric_values[-1]

            panel_results.append({
                "panel": panel_title,
                "value": last_value if last_value is not None else "No data"
            })

        except Exception as e:
            panel_results.append({
                "panel": panel_title,
                "value": f"Error: {e}"
            })

    return panel_results

def post_to_slack(blocks):
    slack_url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel": SLACK_CHANNEL_ID,
        "blocks": blocks
    }
    resp = requests.post(slack_url, headers=headers, data=json.dumps(payload))
    resp.raise_for_status()
    return resp.json()

def build_slack_blocks(all_results):
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": f":bar_chart: *Windows Metrics from Grafana Dashboard*\n_Updated: {now_str}_"}},
        {"type": "divider"}
    ]

    # Group panels by keywords for better visuals
    categories = {
        "CPU": [],
        "Disk": [],
        "Network": [],
        "Services": [],
        "Other": []
    }

    for r in all_results:
        title_lower = r['panel'].lower()
        if "cpu" in title_lower:
            categories["CPU"].append(r)
        elif "disk" in title_lower or "hard" in title_lower:
            categories["Disk"].append(r)
        elif "network" in title_lower:
            categories["Network"].append(r)
        elif "service" in title_lower:
            categories["Services"].append(r)
        else:
            categories["Other"].append(r)

    emoji_map = {
        "CPU": ":computer:",
        "Disk": ":floppy_disk:",
        "Network": ":satellite:",
        "Services": ":gear:",
        "Other": ":bar_chart:"
    }

    for cat, items in categories.items():
        if not items:
            continue
        cat_text = f"{emoji_map.get(cat, ':bar_chart:')} *{cat} Metrics*"
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": cat_text}})
        for item in items:
            val = item['value']
            # Add simple status emoji
            if isinstance(val, (int, float)):
                status = "✅" if val != 0 else "⚠️"
            else:
                status = "❌"
            metric_text = f"*{item['panel']}*: `{val}` {status}"
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": metric_text}})
        blocks.append({"type": "divider"})

    # Footer
    blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": ":information_source: This message is auto-generated by Grafana bot"}]})

    return blocks

def main():
    try:
        dashboard_data = get_dashboard(DASHBOARD_UID)
        panels = dashboard_data.get("dashboard", {}).get("panels", [])
        print(f"✅ Found {len(panels)} panels in the dashboard.")

        all_results = []
        for panel in panels:
            results = fetch_panel_data(panel)
            all_results.extend(results)

        blocks = build_slack_blocks(all_results)
        slack_resp = post_to_slack(blocks)

        if slack_resp.get("ok"):
            print("✅ Posted metrics to Slack!")
        else:
            print(f"❌ Failed to post to Slack: {slack_resp}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
