# rag-asistente-docs

Asistente conversacional basado en RAG (Retrieval-Augmented Generation) que responde preguntas sobre un conjunto de documentos reales, citando la fuente exacta en vez de inventar respuestas.

[![Video demo: el asistente responde preguntas sobre la API de Stripe y cita las fuentes consultadas (1:57)](docs/media/demo_chat_stripe_thumbnail.jpg)](https://youtu.be/oCbj0ahAuoA "Ver el video demo (1:57)")

<sub>Clic en la imagen para ver el video demo (1:57). Pruébalo en vivo en https://rag-asistente-docs.onrender.com</sub>

## Objetivo del proyecto

Este proyecto fue creado como pieza de portafolio para búsqueda de empleo en IT (2026). Busca demostrar:
- Comprensión práctica de RAG (no solo teoría)
- Un producto desplegado y usable, no un notebook
- Documentación clara de decisiones técnicas (ver DECISIONS.md)

## Dominio de datos

El asistente responde preguntas sobre la documentación oficial de la API de Stripe (https://docs.stripe.com), citando la página/sección exacta de la que sale cada respuesta.

Casos de uso de ejemplo:
- "¿Cómo creo un customer con metadata en Stripe?"
- "¿Qué diferencia hay entre PaymentIntent y Charge?"
- "¿Cómo manejo webhooks de Stripe en Python?"

## Stack tecnológico

| Componente | Elección | Estado |
|---|---|---|
| Backend | Python (rag_ia.py: búsqueda de fragmentos y generación de la respuesta) | Decidido |
| API de IA | Gemini (+ Groq como fallback, fase 2) | Decidido |
| Base de datos vectorial | pgvector | Decidido |
| Frontend | Streamlit | Decidido |
| Deploy | Render (plan Free, Docker) — ver [DEPLOY.md](DEPLOY.md) | Decidido |

Ver el razonamiento completo detrás de cada elección en DECISIONS.md.

## Cómo correrlo (local)

La forma más simple es con Docker (ver guía completa en DEPLOY.md):

```bash
git clone https://github.com/guadalupealba/rag-asistente-docs.git
cd rag-asistente-docs
export GEMINI_API_KEY="tu_api_key"
docker build --secret id=GEMINI_API_KEY,env=GEMINI_API_KEY -t rag-demo .
docker run --rm -e GEMINI_API_KEY -p 7860:7860 rag-demo
# abrir http://localhost:7860
```

También se puede correr manualmente, sin Docker. Se necesita Conda (para PostgreSQL + pgvector) y dos terminales: una con Conda para la base (paso 3) y otra con el entorno virtual para el resto.

```bash
# 1. Clonar el repo
git clone https://github.com/guadalupealba/rag-asistente-docs.git
cd rag-asistente-docs

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requisitos.txt streamlit

# 3. Levantar PostgreSQL + pgvector (via Conda, en otra terminal)
conda create -n rag-db -c conda-forge postgresql pgvector -y
conda activate rag-db
initdb -D <ruta-que-elijas> -U postgres -W   # usar la contraseña rag1234 (la que esperan los scripts)
pg_ctl -D <esa-misma-ruta> -o "-p 5433" start
createdb -U postgres -p 5433 rag_stripe
psql -U postgres -p 5433 -d rag_stripe -c "CREATE EXTENSION vector;"

# 4. Configurar la clave de Gemini: crear el archivo .secreto/claves_api.json con
# {"claves_gemini": "tu_api_key"}
# (la carpeta .secreto/ está en el .gitignore, la clave no se sube al repo)

# 5. Descargar y procesar la documentación de Stripe
python descargar_stripe.py

# 6. Generar embeddings y guardarlos en pgvector
python generar_embeddings.py

# 7. Correr la interfaz
streamlit run UI.py
```

## Autores

- Guadalupe Alba - [@guadalupealba](https://github.com/guadalupealba)
- Mugen - [@moneythemoney999](https://github.com/moneythemoney999)
- D4HACK — [@D4HACK-afk](https://github.com/D4HACK-afk)
- Eduardo — [@eduair94](https://github.com/eduair94)

## Demo

- Demo en vivo: https://rag-asistente-docs.onrender.com (plan Free de Render: si estuvo inactiva, tarda alrededor de 1 minuto en despertar)
- Cómo desplegar tu propia demo: ver [DEPLOY.md](DEPLOY.md)
- Video demo (1:57): https://youtu.be/oCbj0ahAuoA
