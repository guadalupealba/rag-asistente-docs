"""
Script para descargar la especificación OpenAPI de Stripe y convertirla
en chunks de texto listos para generar embeddings.

Uso:
    python descargar_stripe_docs.py
"""

import json
import os
import requests

# URL oficial de la especificación de Stripe (mantenida por Stripe en GitHub)
STRIPE_SPEC_URL = "https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json"

# Carpeta donde se van a guardar los datos descargados y procesados
DATA_DIR = "data"
RAW_SPEC_PATH = os.path.join(DATA_DIR, "stripe_spec3.json")
CHUNKS_OUTPUT_PATH = os.path.join(DATA_DIR, "chunks.json")

# Palabras clave para filtrar solo los endpoints que nos interesan.
# Se buscan estas palabras dentro de la ruta (path) de cada endpoint.
KEYWORDS_FILTRO = [
    "payment_intent",
    "charge",
    "customer",
    "webhook_endpoint",
]


def descargar_spec():
    """Descarga el archivo spec3.json de Stripe si no está ya descargado."""
    os.makedirs(DATA_DIR, exist_ok=True)

    if os.path.exists(RAW_SPEC_PATH):
        print(f"El archivo ya existe en {RAW_SPEC_PATH}, no se vuelve a descargar.")
        return

    print("Descargando especificación de Stripe (puede tardar un momento, pesa ~7 MB)...")
    response = requests.get(STRIPE_SPEC_URL)
    response.raise_for_status()

    with open(RAW_SPEC_PATH, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"Descarga completa. Guardado en {RAW_SPEC_PATH}")


def endpoint_es_relevante(path):
    """Chequea si la ruta del endpoint contiene alguna palabra clave de interés."""
    path_lower = path.lower()
    return any(keyword in path_lower for keyword in KEYWORDS_FILTRO)


def construir_texto_chunk(path, metodo, operacion):
    """
    Arma el texto de un chunk a partir de un endpoint de la especificación.
    Incluye: método HTTP, ruta, resumen, descripción y parámetros principales.
    """
    partes = [f"Endpoint: {metodo.upper()} {path}"]

    summary = operacion.get("summary", "")
    if summary:
        partes.append(f"Resumen: {summary}")

    description = operacion.get("description", "")
    if description:
        partes.append(f"Descripción: {description}")

    # Parámetros del endpoint (si los tiene)
    parametros = operacion.get("parameters", [])
    if parametros:
        nombres_parametros = [p.get("name", "") for p in parametros if p.get("name")]
        if nombres_parametros:
            partes.append(f"Parámetros: {', '.join(nombres_parametros)}")

    return "\n".join(partes)


def procesar_spec():
    """Lee el spec descargado, filtra los endpoints relevantes y arma los chunks."""
    print("Leyendo y procesando la especificación...")

    with open(RAW_SPEC_PATH, "r", encoding="utf-8") as f:
        spec = json.load(f)

    paths = spec.get("paths", {})
    chunks = []

    for path, metodos in paths.items():
        if not endpoint_es_relevante(path):
            continue

        for metodo, operacion in metodos.items():
            # Nos aseguramos de que sea un método HTTP válido (get, post, delete, etc.)
            if metodo.lower() not in ["get", "post", "put", "delete", "patch"]:
                continue

            texto = construir_texto_chunk(path, metodo, operacion)

            chunk = {
                "id": f"{metodo.upper()}_{path}",
                "texto": texto,
                "fuente": f"Stripe API docs: {metodo.upper()} {path}",
                "seccion": clasificar_seccion(path),
            }
            chunks.append(chunk)

    print(f"Se generaron {len(chunks)} chunks.")

    with open(CHUNKS_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"Chunks guardados en {CHUNKS_OUTPUT_PATH}")


def clasificar_seccion(path):
    """Clasifica el endpoint en una sección general, útil para filtros después."""
    path_lower = path.lower()
    if "payment_intent" in path_lower or "charge" in path_lower:
        return "Payments"
    if "customer" in path_lower:
        return "Customers"
    if "webhook" in path_lower:
        return "Webhooks"
    return "Otro"


if __name__ == "__main__":
    descargar_spec()
    procesar_spec()
