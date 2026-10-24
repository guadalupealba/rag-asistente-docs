import requests
import os
import json
import sys

api_key = "..."
url = "https://api.groq.com/openai/v1/models"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

try:
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()

    with open("json.json", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    print("JSON enregistré dans json.json")

except requests.exceptions.RequestException as e:
    print(f"Erreur API : {e}", file=sys.stderr)

except ValueError as e:
    print(f"Réponse JSON invalide : {e}", file=sys.stderr)
