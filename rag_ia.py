import json
import os
import psycopg2
from google import genai
from google.genai.types import EmbedContentConfig

# Configuración de rutas
ruta_memoria = "memoria/memoria_ia.json"
ruta_clave = ".secreto/claves_api.json"

# Lista de modelos disponibles (sin modificar la lista proporcionada por el usuario)
modelos_ia = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3-flash-preview"]
modelo_de_embedding = "gemini-embedding-001"
dimensiones_embedding = 768

# Configuración de conexión a PostgreSQL (con pgvector)
base_dato_config = {
    "host": "localhost",
    "port": 5433,
    "dbname": "rag_stripe",
    "user": "postgres",
    "password": "rag1234",
}

# Cargar la clave de la API
def obtener_clave_api():
    """
    Lee la clave de la API desde un archivo JSON.
    """
    with open(ruta_clave, 'r') as archivo:
        datos = json.load(archivo)
    return datos["claves_gemini"]

# Configurar el cliente de Gemini
cliente = genai.Client(api_key=obtener_clave_api())

# Cargar la memoria local de la IA 
def cargar_memoria():
    """
    Carga el historial de conversaciones desde el archivo JSON.
    """
    if not os.path.exists(ruta_memoria):
        return []
    with open(ruta_memoria, 'r', encoding='utf-8') as archivo:
        try:
            return json.load(archivo)
        except json.JSONDecodeError:
            return []

def guardar_memoria(historial):
    """
    Guarda el historial de conversaciones en el archivo JSON.
    """
    os.makedirs(os.path.dirname(ruta_memoria), exist_ok=True)
    with open(ruta_memoria, 'w', encoding='utf-8') as archivo:
        json.dump(historial, archivo, indent=4, ensure_ascii=False)

def generar_embedding_consulta(texto):
    """
    Genera el embedding para la consulta del usuario.
    """
    resultado = cliente.models.embed_content(
        model=modelo_de_embedding,
        contents=texto,
        config=EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=dimensiones_embedding,
        ),
    )
    return resultado.embeddings[0].values

def buscar_contexto_relevante(embedding, limite=3):
    """
    Busca los fragmentos más relevantes en PostgreSQL usando distancia coseno con pgvector.
    """
    try:
        conn = psycopg2.connect(**base_dato_config)
        with conn.cursor() as cur:
            # Usamos <=> para distancia coseno en pgvector
            cur.execute(
                """
                SELECT texto, fuente, seccion 
                FROM stripe_chunks 
                ORDER BY embedding <=> %s::vector 
                LIMIT %s;
                """,
                (embedding, limite),
            )
            resultados = cur.fetchall()
        conn.close()
        return resultados
    except Exception as e:
        print(f"Error al conectar o consultar PostgreSQL: {e}")
        return []

def generar_respuesta(pregunta):
    """
    Genera el embedding de la pregunta, recupera contexto relevante de PostgreSQL,
    construye el prompt final con RAG, y obtiene la respuesta de la IA.
    """
    # 1. Generar embedding y buscar contexto relevante
    print("Buscando información de soporte...")
    embedding = generar_embedding_consulta(pregunta)
    fragmentos = buscar_contexto_relevante(embedding)
    
    # 2. Construir el contexto para el prompt
    contexto = ""
    if fragmentos:
        contexto_lista = []
        for texto, fuente, seccion in fragmentos:
            ref = f"(Sección: {seccion})" if seccion else ""
            contexto_lista.append(f"- [{fuente}{ref}]: {texto}")
        contexto = "\n".join(contexto_lista)
    
    # 3. Crear el prompt final inyectando el contexto si existe
    if contexto:
        pregunta_con_contexto = (
            f"Utiliza la siguiente información de contexto para responder la pregunta del usuario de manera precisa.\n"
            f"Si no sabes la respuesta basada en el contexto, dilo claramente.\n\n"
            f"Contexto recuperado:\n{contexto}\n\n"
            f"Pregunta del usuario: {pregunta}"
        )
    else:
        pregunta_con_contexto = pregunta

    # 4. Cargar historial de conversación
    historial = cargar_memoria()

    # Preparar el historial para la API
    historial_api = []
    for m in historial:
        historial_api.append({
            "role": m["rol"],
            "parts": [{"text": m["contenido"]}]
        })

    # Agregar la nueva pregunta con el contexto inyectado al historial de la API
    historial_api.append({
        "role": "user",
        "parts": [{"text": pregunta_con_contexto}]
    })

    respuesta_final = None
    
    # Intentar con los modelos en orden
    for nombre_modelo in modelos_ia:
        try:
            respuesta = cliente.models.generate_content(
                model=nombre_modelo,
                contents=historial_api,
            )
            respuesta_final = respuesta.text
            break # Si funciona salimos del bucle
        except Exception as error:
            print(f"Error con el modelo {nombre_modelo}: {error}. Intentando con el siguiente...")
            continue

    if respuesta_final:
        # En el historial local guardamos la pregunta original (no la que tiene el contexto inyectado)
        historial.append({"rol": "user", "contenido": pregunta})
        historial.append({"rol": "model", "contenido": respuesta_final})
        guardar_memoria(historial)
        return respuesta_final
    else:
        return "Error: No se pudo generar una respuesta con ninguno de los modelos disponibles."

if __name__ == "__main__":
    print("="*10, "Iniciando conversación con la IA (RAG habilitado). Escribe 'salir' para terminar.", "="*10)

    while True:
        pregunta_usuario = input("\n¿Qué onda? ⌨️>: ")
        if pregunta_usuario.lower() == 'salir':
            print("¡Hasta luego!")
            break
        resultado = generar_respuesta(pregunta_usuario)
        print("Respuesta:")
        print(resultado)
