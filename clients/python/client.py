import requests

BASE = "http://localhost:8000/api/v1"

def resolve(text):
    return requests.post(f"{BASE}/resolve", json={"text": text}).json()