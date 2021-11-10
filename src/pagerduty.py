import requests
import json
import os

pagerduty_url = 'https://events.pagerduty.com/generic/2010-04-15/create_event.json'


def notify_pagerduty(message, event_type, incident_key, queue_size=None):
    payload = {
        "service_key": os.environ['SERVICE_KEY'],
        "event_type": event_type,
        "incident_key": incident_key,
        "description": message,
        "details": {
            "Queue size": queue_size
        }
    }

    r = requests.post(pagerduty_url, data=json.dumps(payload))
    return r.json()


