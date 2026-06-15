"""
Scraper de recetas de refinería de No Man's Sky
Fuente: https://nomansskyrecipes.com/refining
Genera: data/recipes.json

Estructura de la tabla HTML:
  col0=Input1 | col1=Input2 | col2=Input3 | col3=Output | col4=Operación | col5=Tiempo
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import os

URL = "https://nomansskyrecipes.com/refining"
OUTPUT = os.path.join(os.path.dirname(__file__), "data", "recipes.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
}

def extract_code(src):
    """Extrae el código del material desde la URL del icono."""
    if not src:
        return None
    match = re.search(r'/images/items/([^.]+)\.(?:png|webp)', src)
    return match.group(1) if match else None

def parse_cell(td):
    """Extrae {name, code, qty} de una celda de material. Devuelve None si vacía."""
    a = td.find("a")
    if not a:
        return None

    # Nombre: span oculto con clase "d-none sort"
    name_span = td.find("span", class_="d-none")
    name = name_span.get_text(strip=True) if name_span else (a.get("alt") or "")

    # Cantidad: span con clase "amount"
    qty_span = td.find("span", class_="amount")
    try:
        qty = int(qty_span.get_text(strip=True)) if qty_span else 1
    except ValueError:
        qty = 1

    # Código: desde el src del img
    img = td.find("img")
    code = extract_code(img["src"]) if img and img.get("src") else None

    return {"name": name, "code": code, "qty": qty}

def refinery_type(n):
    return {1: "pequeña", 2: "mediana", 3: "grande"}.get(n, "desconocida")

def scrape():
    print(f"Descargando {URL} ...")
    resp = requests.get(URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table")
    if not table:
        raise RuntimeError("No se encontró ninguna tabla en la página")

    rows = table.find_all("tr")
    print(f"Filas encontradas: {len(rows)}")

    recipes = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 5:
            continue  # encabezado u otras filas sin datos

        # Inputs: col 0, 1, 2
        inputs = [parse_cell(cells[i]) for i in range(3)]
        inputs = [m for m in inputs if m]  # eliminar celdas vacías

        # Output: col 3
        output = parse_cell(cells[3])

        if not inputs or not output:
            continue

        operation = cells[4].get_text(strip=True) if len(cells) > 4 else ""
        duration  = cells[5].get_text(strip=True) if len(cells) > 5 else ""

        recipes.append({
            "operation": operation,
            "inputs": inputs,
            "output": output,
            "time": duration,
            "refinery_type": refinery_type(len(inputs))
        })

    print(f"Recetas extraídas: {len(recipes)}")

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)

    print(f"Guardado en: {OUTPUT}")
    return recipes

if __name__ == "__main__":
    recipes = scrape()

    from collections import Counter
    counts = Counter(r["refinery_type"] for r in recipes)
    print("\nRecetas por tipo de refinería:")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")

    codes = set()
    for r in recipes:
        for inp in r["inputs"]:
            if inp.get("code"):
                codes.add(inp["code"])
        if r["output"] and r["output"].get("code"):
            codes.add(r["output"]["code"])
    print(f"\nCódigos únicos de iconos: {len(codes)}")
