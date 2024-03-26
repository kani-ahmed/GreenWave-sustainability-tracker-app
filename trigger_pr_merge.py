# trigger_pr_merge.py

import requests
import time
import os
from dotenv import load_dotenv

# load_dotenv()

# Slack configurations
SLACK_CHANNEL_ID = os.getenv('SLACK_CHANNEL_ID')
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')

# GitHub configuration
GITHUB_REPO = "kenny-ahmedd/GreenWave-sustainability-tracker-app"
GITHUB_WORKFLOW_ID = "workflow_dispatch_merge.yml"
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# API endpoints
CONVERSATIONS_HISTORY_URL = "https://slack.com/api/conversations.history"
REACTIONS_GET_URL = "https://slack.com/api/reactions.get"
GITHUB_DISPATCH_URL = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{GITHUB_WORKFLOW_ID}/dispatches"

# Headers
slack_headers = {
    "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
    "Content-Type": "application/json"
}
github_headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


def find_latest_pr_opened_message(channel_id):
    params = {"channel": channel_id, "limit": 100}
    response = requests.get(CONVERSATIONS_HISTORY_URL, headers=slack_headers, params=params)
    if response.status_code == 200:
        messages = response.json().get("messages", [])
        for message in messages:
            if "text" in message and "Pull Request Opened" in message["text"]:
                return message
            if "attachments" in message:
                for attachment in message["attachments"]:
                    if "pretext" in attachment and "Pull Request Opened" in attachment["pretext"]:
                        return message
    else:
        print(f"Failed to retrieve messages. Status code: {response.status_code}")
    return None


def get_reaction_count(message_ts, channel_id):
    params = {"channel": channel_id, "timestamp": message_ts}
    response = requests.get(REACTIONS_GET_URL, headers=slack_headers, params=params)
    if response.status_code == 200:
        data = response.json()
        reactions = data.get('message', {}).get('reactions', [])
        for reaction in reactions:
            if reaction['name'] == '+1':
                return reaction['count']
    return 0


def trigger_github_workflow(pr_number):
    data = {
        "ref": "main",
        "inputs": {
            "prNumber": str(pr_number)
        }
    }
    response = requests.post(GITHUB_DISPATCH_URL, headers=github_headers, json=data)
    if response.status_code == 204:
        print("Successfully triggered the GitHub workflow.")
    else:
        print(f"Failed to trigger the GitHub workflow. Status: {response.status_code}, Response: {response.text}")


def continuously_check_reactions(threshold=1):
    while True:
        latest_pr_message = find_latest_pr_opened_message(SLACK_CHANNEL_ID)
        if latest_pr_message:
            message_id = latest_pr_message.get("ts")
            thumbs_up_count = get_reaction_count(message_id, SLACK_CHANNEL_ID)
            print(f"Thumbs-up reaction count: {thumbs_up_count}")
            if thumbs_up_count >= threshold:
                pr_number = extract_pr_number(latest_pr_message)
                if pr_number:
                    trigger_github_workflow(pr_number)
                    break
                else:
                    print("Failed to extract pull request number from the message.")
        else:
            print("No 'Pull Request Opened' message found in the channel.")
        time.sleep(10)


def extract_pr_number(message):
    if "attachments" in message:
        for attachment in message["attachments"]:
            if "title" in attachment and "Pull Request #" in attachment["title"]:
                return attachment["title"].split("#")[1]
    return None


if __name__ == "__main__":
    continuously_check_reactions()
