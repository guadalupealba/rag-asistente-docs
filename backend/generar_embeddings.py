"""
Script para generar embeddings de los chunks de Stripe usando la API de Gemini,
y guardarlos en PostgreSQL (con la extensión pgvector).

Requisitos previos:
    - Haber corrido descargar_stripe_docs.py (genera data/chunks.json)
    - Tener un archivo .env en esta misma carpeta con:
        GEMINI_API_KEY=tu_clave
    - Tener PostgreSQL + pgvector corriendo (ver DECISIONS.md para el setup)

Uso:
    python generar_embeddings.py
"""

import json
import os

import psycopg2
from dotenv import load_dotenv
from google import genai
from google.genai.types import EmbedContentConfig

# Cargar variables de entorno desde .env
load_dotenv()

# --- Configuración ---
CHUNKS_PATH = os.path.join("data", "chunks.json")
MODELO_EMBEDDING = "gemini-embedding-001"
DIMENSIONES = 768  # Recortamos de 3072 a 768 para que sea más liviano y rápido

# Configuración de conexión a PostgreSQL (base local con pgvector, vía Conda)
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "rag_stripe",
    "user": "postgres",
    "password": "rag1234",
}


def cargar_chunks():
    """Carga los chunks generados por descargar_stripe_docs.py"""
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def crear_tabla(conn):
    """Crea la tabla de chunks con su columna de embedding (vector) si no existe."""
    with conn.cursor() as cur:
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS stripe_chunks (
                id TEXT PRIMARY KEY,
                texto TEXT NOT NULL,
                fuente TEXT NOT NULL,
                seccion TEXT,
                embedding vector({DIMENSIONES})
            );
        """)
    conn.commit()
    print("Tabla 'stripe_chunks' lista.")


def generar_embedding(cliente, texto):
    """Genera el embedding de un texto usando la API de Gemini."""
    resultado = cliente.models.embed_content(
        model=MODELO_EMBEDDING,
        contents=texto,
        config=EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=DIMENSIONES,
        ),
    )
    return resultado.embeddings[0].values


def guardar_chunk(conn, chunk, embedding):
    """Guarda (o actualiza) un chunk con su embedding en la base de datos."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO stripe_chunks (id, texto, fuente, seccion, embedding)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE
            SET texto = EXCLUDED.texto,
                fuente = EXCLUDED.fuente,
                seccion = EXCLUDED.seccion,
                embedding = EXCLUDED.embedding;
            """,
            (chunk["id"], chunk["texto"], chunk["fuente"], chunk["seccion"], embedding),
        )
    conn.commit()


def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No se encontró GEMINI_API_KEY. Revisá que el archivo .env "
            "esté en esta carpeta y tenga la clave configurada."
        )

    cliente = genai.Client(api_key=api_key)

    print("Cargando chunks...")
    chunks = cargar_chunks()
    print(f"Se cargaron {len(chunks)} chunks.")

    conn = psycopg2.connect(**DB_CONFIG)
    crear_tabla(conn)

    for i, chunk in enumerate(chunks, start=1):
        print(f"[{i}/{len(chunks)}] Generando embedding para: {chunk['id']}")
        embedding = generar_embedding(cliente, chunk["texto"])
        guardar_chunk(conn, chunk, embedding)

    conn.close()
    print("¡Listo! Todos los embeddings se generaron y guardaron en pgvector.")


if __name__ == "__main__":
    main()
