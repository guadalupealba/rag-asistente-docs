# rag-asistente-docs

Asistente conversacional basado en **RAG (Retrieval-Augmented Generation)** que responde preguntas sobre un conjunto de documentos reales, citando la fuente exacta en vez de inventar respuestas.

## 🎯 Objetivo del proyecto

Este proyecto fue creado como pieza de portafolio para búsqueda de empleo en IT (2026). Busca demostrar:
- Comprensión práctica de RAG (no solo teoría)
- Un producto desplegado y usable, no un notebook
- Documentación clara de decisiones técnicas ([ver DECISIONS.md](./DECISIONS.md))

## 📄 Dominio de datos

_Pendiente de definir: sobre qué documentos va a responder el asistente (ej. documentación de una API pública, reglamento de una institución, etc.)_

## 🛠️ Stack tecnológico

| Componente | Elección | Estado |
|---|---|---|
| Backend | Python (FastAPI) | ✅ Decidido |
| API de IA | [Groq](https://console.groq.com/) | ✅ Decidido |
| Base de datos vectorial | pgvector / ChromaDB | ⏳ Pendiente |
| Frontend | — | ⏳ Pendiente |
| Deploy | Railway / Render | ⏳ Pendiente |

Ver el razonamiento completo detrás de cada elección en [DECISIONS.md](./DECISIONS.md).
 ## 🚀 Cómo correrlo (local)

\`\`\`bash
# 1. Clonar el repo
git clone https://github.com/guadalupealba/rag-asistente-docs.git
cd rag-asistente-docs

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Instalar dependencias del backend
cd backend
pip install -r requirements.txt
pip install requests google-genai psycopg2-binary python-dotenv

# 4. Configurar variables de entorno
cp .env.example .env
# Completar .env con tu GEMINI_API_KEY real

# 5. Levantar PostgreSQL + pgvector (vía Conda)
conda create -n rag-db -c conda-forge postgresql pgvector -y
conda activate rag-db
initdb -D <ruta-que-elijas> -U postgres -W
pg_ctl -D <esa-misma-ruta> -o "-p 5433" start
createdb -U postgres -p 5433 rag_stripe
psql -U postgres -p 5433 -d rag_stripe -c "CREATE EXTENSION vector;"

# 6. Descargar y procesar la documentación de Stripe
python descargar_stripe_docs.py

# 7. Generar embeddings y guardarlos en pgvector
python generar_embeddings.py

# 8. Probar que la búsqueda funciona
python probar_busqueda.py "como creo un customer con metadata"

# 9. Correr el servidor
uvicorn main:app --reload
\`\`\`



## 👥 Autores

- [Tu nombre] — [tu GitHub]
- [Nombre del compa] — [GitHub del compa]

## 📹 Demo

_Pendiente: link al video demo de 2 minutos_
