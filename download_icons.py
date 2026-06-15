"""
Descarga todos los iconos PNG de materiales desde nomansskyrecipes.com
Requiere que data/recipes.json ya exista (ejecutar scraper.py primero)
Guarda los iconos en: icons/{CODE}.png
"""

import requests
import json
import os
import time

RECIPES_FILE = os.path.join(os.path.dirname(__file__), "data", "recipes.json")
ICONS_DIR = os.path.join(os.path.dirname(__file__), "icons")
BASE_URL = "https://nomansskyrecipes.com/images/items/{code}.png"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
}

def collect_codes(recipes):
    codes = {}  # code -> name (para referencia)
    for r in recipes:
        for inp in r["inputs"]:
            if inp.get("code"):
                codes[inp["code"]] = inp["name"]
        if r["output"] and r["output"].get("code"):
            codes[r["output"]["code"]] = r["output"]["name"]
    return codes

def download_icons():
    with open(RECIPES_FILE, encoding="utf-8") as f:
        recipes = json.load(f)

    codes = collect_codes(recipes)
    print(f"Códigos únicos a descargar: {len(codes)}")

    os.makedirs(ICONS_DIR, exist_ok=True)

    downloaded = 0
    skipped = 0
    failed = []

    for code, name in sorted(codes.items()):
        dest = os.path.join(ICONS_DIR, f"{code}.png")
        if os.path.exists(dest):
            skipped += 1
            continue

        url = BASE_URL.format(code=code)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200 and resp.content:
                with open(dest, "wb") as f:
                    f.write(resp.content)
                downloaded += 1
                print(f"  OK {code} ({name})")
            else:
                failed.append((code, name, resp.status_code))
                print(f"  FAIL {code} ({name}) HTTP {resp.status_code}")
        except Exception as e:
            failed.append((code, name, str(e)))
            print(f"  ERR {code} ({name}) {e}")

        time.sleep(0.1)  # pausa cortés entre peticiones

    print(f"\nDescargados: {downloaded}  |  Ya existían: {skipped}  |  Fallidos: {len(failed)}")
    if failed:
        print("Fallidos:")
        for code, name, reason in failed:
            print(f"  {code} ({name}): {reason}")

if __name__ == "__main__":
    download_icons()
