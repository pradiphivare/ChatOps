import requests
import json

# ------------------ Slack Config ------------------
SLACK_BOT_TOKEN = "xoxb-4283369281543-9540607100839-XpjkvPoumQDyS2E6mcBHHCot"
SLACK_CHANNEL_ID = "C048RQ3BX0B"
# ---------------------------------------------------

def post_to_slack(message):
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel": SLACK_CHANNEL_ID,
        "text": message
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        data = response.json()
        print(data)
        if data.get("ok"):
            print("✅ Slack test successful!")
        else:
            print("❌ Slack test failed:", data)
    except Exception as e:
        print("❌ Error posting to Slack:", e)

if __name__ == "__main__":
    post_to_slack(":white_check_mark: Slack bot test successful! :tada:")
