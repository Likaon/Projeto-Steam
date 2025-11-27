import os
import requests
import datetime as dt

from .parser import normalize_featured
from .schemas import validate_envelope

def now_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def fetch_featured():
    """
    Captura categorias em destaque da Steam.
    Retorna envelope validado e normalizado.
    """
    base = os.getenv("STEAM_API_BASE", "https://store.steampowered.com")
    url = f"{base}/api/featuredcategories"
    headers = {"User-Agent": "steam-data-pipeline/1.0"}
    r = requests.get(url, timeout=30, headers=headers)
    r.raise_for_status()
    payload = r.json()

    envelope = {
        "source": "steam",
        "endpoint": "featuredcategories",
        "captured_at": now_iso(),
        "data": normalize_featured(payload),
    }

    validate_envelope(envelope)
    return envelope


##if __name__ == "__main__":
##    result = fetch_featured()
##    print("Envelope capturado:")
##    print(result.keys())  # mostra as chaves principais
##    print("Source:", result["source"])
##    print("Endpoint:", result["endpoint"])
##    print("Captured_at:", result["captured_at"])
##    print("Data sample:", str(result["data"])[:200], "...")
