import requests
import os
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
API_KEY_PATH = ROOT_DIR / "API_keys" / "Inworld_API_key.txt"
OUTPUT_PATH = ROOT_DIR / "Documentation" / "Inworld TTS" / "voices.txt"

def fetch_voices():
    if not API_KEY_PATH.exists():
        print(f"API key file not found: {API_KEY_PATH}")
        return

    api_key = API_KEY_PATH.read_text(encoding='utf-8').strip()
    if not api_key:
        print("API key is empty.")
        return

    url = "https://api.inworld.ai/voices/v1/voices?languages=EN_US"
    headers = {
        "Authorization": f"Basic {api_key}"
    }

    print("Fetching voices from Inworld API...")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch voices: {response.status_code} - {response.text}")
        return

    data = response.json()
    voices = data.get("voices", [])

    if not voices:
        print("No voices found in response.")
        return

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for voice in voices:
            voice_id = voice.get("voiceId", "")
            description = voice.get("description", "").strip()
            # If description is empty, fallback to displayName + tags
            if not description:
                display_name = voice.get("displayName", "")
                tags = voice.get("tags", [])
                description = display_name
                if tags:
                    description += f" ({', '.join(tags)})"
            
            # Normalize description to a single line
            description = description.replace("\n", " ").replace("\r", "")
            
            if voice_id:
                f.write(f"{voice_id} -- {description}\n")

    print(f"Successfully saved {len(voices)} voices to {OUTPUT_PATH}")

if __name__ == "__main__":
    fetch_voices()
