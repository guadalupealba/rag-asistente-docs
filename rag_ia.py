import json
import os
import psycopg2
from google import genai
from google.genai.types import EmbedContentConfig
from groq import Groq

# Configuración de rutas
ruta_memoria = "memoria/memoria_ia.json"
ruta_clave = ".secreto/claves_api.json"

# Listas de modelos disponibles para cada proveedor
modelos_gemini = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3-flash-preview"]
modelos_groq = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]

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

# Cargar las claves de la API o solicitarlas interactivamente
def obtener_claves_api():
	"""
	Lee las claves de la API (Gemini y Groq) desde un archivo JSON o las solicita interactivamente si no existen.
	"""
	datos = {}
	if os.path.isfile(ruta_clave):
		with open(ruta_clave, "r", encoding="utf-8") as archivo:
			try:
				datos = json.load(archivo)
			except json.JSONDecodeError:
				datos = {}

	# Verificar o pedir clave de Gemini
	clave_gemini = datos.get("claves_gemini", "")
	if not clave_gemini or clave_gemini == "<tu clave API aquí>" or clave_gemini == "<tu clave API hier>":
		print(f"\n[!] No se encontró o está sin configurar la clave de Gemini en {ruta_clave}")
		clave_gemini = input("Por favor, ingresa tu clave API de Gemini: ").strip()
		datos["claves_gemini"] = clave_gemini

	# Verificar o pedir clave de Groq
	clave_groq = datos.get("claves_groq", "")
	if not clave_groq or clave_groq == "<tu clave API aquí>" or clave_groq == "<tu clave API hier>":
		print(f"\n[!] No se encontró o está sin configurar la clave de Groq en {ruta_clave}")
		clave_groq = input("Por favor, ingresa tu clave API de Groq: ").strip()
		datos["claves_groq"] = clave_groq

	# Guardar ambas claves actualizadas
	os.makedirs(os.path.dirname(ruta_clave), exist_ok=True)
	with open(ruta_clave, "w", encoding="utf-8") as archivo:
		json.dump(datos, archivo, indent=4, ensure_ascii=False)

	return clave_gemini, clave_groq

# Inicializar clientes
clave_gem, clave_grq = obtener_claves_api()
cliente_gemini = genai.Client(api_key=clave_gem)
cliente_groq = Groq(api_key=clave_grq)

def verificar_y_actualizar_clave_gemini(error):
	"""
	Verifica si un error de Gemini corresponde a una clave API inválida.
	"""
	error_str = str(error)
	es_error_api_key = (
		"API_KEY_INVALID" in error_str.upper() or
		("400" in error_str and "INVALID_ARGUMENT" in error_str.upper() and "API_KEY" in error_str.upper()) or
		hasattr(error, "status_code") and getattr(error, "status_code", None) == 400 and "API_KEY_INVALID" in error_str or
		"403" in error_str or "401" in error_str
	)
	
	if es_error_api_key:
		print("\n(⁠ ͡⁠°⁠ ͜⁠ʖ⁠ ͡⁠°⁠) La clave API de Gemini actual no es válida.")
		nueva_clave = input("Por favor, ingresa una nueva clave API de Gemini válida: ").strip()
		
		with open(ruta_clave, "r", encoding="utf-8") as archivo:
			datos = json.load(archivo)
		datos["claves_gemini"] = nueva_clave
		with open(ruta_clave, "w", encoding="utf-8") as archivo:
			json.dump(datos, archivo, indent=4, ensure_ascii=False)
		
		global cliente_gemini
		cliente_gemini = genai.Client(api_key=nueva_clave)
		print("Clave de Gemini actualizada correctamente.")
		return True
	return False

def verificar_y_actualizar_clave_groq(error):
	"""
	Verifica si un error de Groq corresponde a una clave API inválida.
	"""
	error_str = str(error)
	es_error_api_key = (
		"API_KEY_INVALID" in error_str.upper() or
		"401" in error_str or "UNAUTHORIZED" in error_str.upper() or "INVALID_API_KEY" in error_str.upper()
	)
	
	if es_error_api_key:
		print("\n(⁠ ͡⁠°⁠ ͜⁠ʖ⁠ ͡⁠°⁠) La clave API de Groq actual no es válida.")
		nueva_clave = input("Por favor, ingresa una nueva clave API de Groq válida: ").strip()
		
		with open(ruta_clave, "r", encoding="utf-8") as archivo:
			json.load(archivo)
		datos["claves_groq"] = nueva_clave
		with open(ruta_clave, "w", encoding="utf-8") as archivo:
			json.dump(datos, archivo, indent=4, ensure_ascii=False)
		
		global cliente_groq
		cliente_groq = Groq(api_key=nueva_clave)
		print("Clave de Groq actualizada correctamente.")
		return True
	return False

# Cargar la memoria local de la IA 
def cargar_memoria():
	"""
	Carga el historial de conversaciones desde el archivo JSON.
	"""
	if not os.path.isfile(ruta_memoria):
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
	Genera el embedding para la consulta del usuario usando Gemini.
	"""
	try:
		resultado = cliente_gemini.models.embed_content(
			model=modelo_de_embedding,
			contents=texto,
			config=EmbedContentConfig(
				task_type="RETRIEVAL_QUERY",
				output_dimensionality=dimensiones_embedding,
				),
			)
		return resultado.embeddings[0].values
	except Exception as error:
		if verificar_y_actualizar_clave_gemini(error):
			return generar_embedding_consulta(texto)
		raise error

def buscar_contexto_relevante(embedding, limite=3):
	"""
	Busca los fragmentos más relevantes en PostgreSQL usando distancia coseno con pgvector.
	"""
	try:
		conexion = psycopg2.connect(**base_dato_config)
		with conexion.cursor() as cur:
			embedding_pg = "[" + ",".join(map(str, embedding)) + "]"
			cur.execute(
			"""
			SELECT texto, fuente, seccion 
			FROM stripe_chunks 
			ORDER BY embedding <=> %s::vector 
			LIMIT %s;
			""",
			(embedding_pg, limite)
			)
			resultados = cur.fetchall()
			conexion.close()
		return resultados
	except Exception as e:
		print(f"Error al conectar o consultar PostgreSQL: {e}")
		return []

def generar_respuesta(datos_entrada):
	"""
	Genera respuesta usando RAG y el proveedor de IA especificado (Gemini o Groq).
	Recibe un diccionario con estructura: {"pregunta": {"texto": "...", "historial": [...], "modelo_de_ia": {"tipo": "gemini|groq", "modelo": "..."}}}
	Devuelve un diccionario estructurado con respuesta, fuentes, modelo de IA y posibles errores.
	"""
	global cliente_gemini, cliente_groq
	datos_pregunta = datos_entrada.get("pregunta", {})
	pregunta = datos_pregunta.get("texto", "")
	historial_externo = datos_pregunta.get("historial", [])
	config_modelo = datos_pregunta.get("modelo_de_ia", {})
	
	tipo_ia = config_modelo.get("tipo", "gemini").lower()
	modelo_solicitado = config_modelo.get("modelo")

	# 1. Generar embedding y buscar contexto relevante
	print("Buscando información de soporte...")
	try:
		embedding = generar_embedding_consulta(pregunta)
	except Exception as error:
		if verificar_y_actualizar_clave_gemini(error):
			embedding = generar_embedding_consulta(pregunta)
		else:
			raise error

	fragmentos = buscar_contexto_relevante(embedding)

	# 2. Construir el contexto para el prompt
	contexto = ""
	fuentes_utilizadas = []
	contexto_lista = []
	if fragmentos:
		for texto, fuente, seccion in fragmentos:
			referencia = f"(Sección: {seccion})" if seccion else ""
			contexto_lista.append(f"- [{fuente}{referencia}]: {texto}")
			if fuente not in fuentes_utilizadas:
				fuentes_utilizadas.append(fuente)
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

	# 4. Procesar según el proveedor (Gemini o Groq)
	respuesta_final = None
	modelo_usado = 0

	if tipo_ia == "groq":
		lista_de_modelos = [modelo_solicitado] if modelo_solicitado else modelos_groq
		
		# Groq espera el historial en formato [{"role": "user", "content": "..."}, ...]
		historial_groq = []
		for mensaje in historial_externo:
			rol = "assistant" if mensaje["rol"] == "model" else mensaje["rol"]
			historial_groq.append({
				"role": rol,
				"content": mensaje["contenido"]
			})
		historial_groq.append({"role": "user", "content": pregunta_con_contexto})

		for nombre_modelo in lista_de_modelos:
			modelo_usado = nombre_modelo
			try:
				completion = cliente_groq.chat.completions.create(
					model=nombre_modelo,
					messages=historial_groq,
				)
				respuesta_final = completion.choices[0].message.content
				break
			except Exception as error:
				error_str = str(error)
				if verificar_y_actualizar_clave_groq(error):
					return generar_respuesta(datos_entrada)

				if "404" in error_str or "NOT_FOUND" in error_str.upper():
					return {
						"respuesta": {
							"texto": 0,
							"fuentes": 0,
							"modelo_de_ia": {
								"tipo": "groq",
								"modelo": nombre_modelo
							},
							"errores": {
								"MODELO_INEXISTANTE": f"El modelo {nombre_modelo} no existe."
							}
						}
					}

				if "429" in error_str or "RATE_LIMIT" in error_str.upper():
					if nombre_modelo == lista_de_modelos[-1]:
						return {
							"respuesta": {
								"texto": 0,
								"fuentes": 0,
								"modelo_de_ia": {
									"tipo": "groq",
									"modelo": nombre_modelo
								},
								"errores": {
									"TOKENS_ALCANZADO": "Has alcanzado el límite de tokens (rate limit) de Groq."
								}
							}
						}
					continue

				print(f"Error con Groq ({nombre_modelo}): {error}. Intentando con el siguiente...")
				continue

	else:  # Por defecto Gemini
		historial_api = []
		for mensaje in historial_externo:
			historial_api.append({
				"role": mensaje["rol"],
				"parts": [{"text": mensaje["contenido"]}]
			})
		historial_api.append({
			"role": "user",
			"parts": [{"text": pregunta_con_contexto}]
		})

		lista_de_modelos = [modelo_solicitado] if modelo_solicitado else modelos_gemini

		for nombre_modelo in lista_de_modelos:
			modelo_usado = nombre_modelo
			try:
				respuesta = cliente_gemini.models.generate_content(
					model=nombre_modelo,
					contents=historial_api,
				)
				respuesta_final = respuesta.text
				break
			except Exception as error:
				error_str = str(error)
				
				if verificar_y_actualizar_clave_gemini(error):
					return generar_respuesta(datos_entrada)

				if "404" in error_str or "NOT_FOUND" in error_str.upper():
					return {
						"respuesta": {
							"texto": 0,
							"fuentes": 0,
							"modelo_de_ia": {
								"tipo": "gemini",
								"modelo": nombre_modelo
							},
							"errores": {
								"MODELO_INEXISTANTE": f"El modelo {nombre_modelo} no existe."
							}
						}
					}
				
				if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str.upper():
					print(f"Límite de tokens alcanzado con {nombre_modelo}. Intentando con el siguiente...")
					if nombre_modelo == lista_de_modelos[-1]:
						return {
							"respuesta": {
								"texto": 0,
								"fuentes": 0,
								"modelo_de_ia": {
									"tipo": "gemini",
									"modelo": nombre_modelo
								},
								"errores": {
									"TOKENS_ALCANZADO": "Has alcanzado el límite de tokens de este modelo. Inténtalo de nuevo más tarde o utiliza otro modelo."
								}
							}
						}
					continue
				
				print(f"Error con Gemini ({nombre_modelo}): {error}. Intentando con el siguiente...")
				continue

	if respuesta_final:
		# Guardamos en la memoria local el mensaje original (sin contexto)
		historial_guardar = historial_externo + [{"rol": "user", "contenido": pregunta}, {"rol": "model", "contenido": respuesta_final}]
		guardar_memoria(historial_guardar)
		
		diccionario_fuentes = {str(i + 1): fuente for i, fuente in enumerate(fuentes_utilizadas)} if fuentes_utilizadas else 0
		return {
			"respuesta": {
				"texto": respuesta_final,
				"fuentes": diccionario_fuentes,
				"modelo_de_ia": {
					"tipo": tipo_ia,
					"modelo": modelo_usado
				}
			}
		}
	else:
		return {
			"respuesta": {
				"texto": 0,
				"fuentes": 0,
				"modelo_de_ia": {
					"tipo": tipo_ia,
					"modelo": modelo_usado
				},
				"errores": {
					"modelo_error": "No se pudo generar una respuesta con ninguno de los modelos disponibles."
				}
			}
		}

if __name__ == "__main__":
	print("="*10, "Iniciando conversación con la IA multi-proveedor (RAG habilitado). Escribe '.salir' para terminar.", "="*10)

	while True:
		pregunta_usuario = input("\n¿Qué onda? ⌨️>: ")
		if pregunta_usuario.lower() == '.salir':
			print('⁠(⁠ ⁠ ⁠•⁠ ⁠‿⁠ ⁠•⁠ ⁠ ⁠)' *20)
			break
		
		# Preguntar opcionalmente el proveedor en el CLI de prueba
		proveedor = input("Proveedor [gemini/groq] (por defecto gemini): ").strip().lower()
		if not proveedor:
			proveedor = "gemini"

		historial_actual = cargar_memoria()
		datos_paquete = {
			"pregunta": {
				"texto": pregunta_usuario,
				"historial": historial_actual,
				"modelo_de_ia": {
					"tipo": proveedor
				}
			}
		}
		
		resultado = generar_respuesta(datos_paquete)

		if "errores" in resultado["respuesta"]:
			print("Error:", json.dumps(resultado["respuesta"]["errores"], indent=4, ensure_ascii=False))
		else:
			print("✦Respuesta:", resultado["respuesta"]["texto"])
			print("🌐Fuentes:", resultado["respuesta"]["fuentes"])
			print("🤖Modelo:", resultado["respuesta"]["modelo_de_ia"])
