# Decisiones técnicas del proyecto

Este documento registra las decisiones técnicas tomadas durante el desarrollo, el porqué de cada una, y los problemas que fuimos encontrando. Es parte clave del portafolio: muestra el proceso de pensamiento, no solo el resultado final.

---

## 1. ¿Por qué Python?

Uno de los integrantes viene de Java, pero se eligió Python porque:
- Es el estándar de facto para proyectos de IA/RAG
- Tiene el ecosistema más maduro de librerías (LangChain, LlamaIndex, embeddings, etc.)
- Facilita la colaboración en equipo sobre un stack más estandarizado en la industria de IA

## 2. ¿Por qué Gemini API (+ Groq como fallback)?

Alternativas evaluadas:
- **Groq** — se consideró primero por su velocidad de inferencia
- **Gemini API**  — elegida como proveedor principal
- Ollama (local) — gratis y sin límites, pero más lento y requiere buena RAM

Motivo del cambio: se evaluó Groq inicialmente por su velocidad, pero se decidió pasar a Gemini por consistencia de conocimiento dentro del equipo (uno de los integrantes ya tenía experiencia previa con esta API) y para reducir la fricción de arranque conjunto del proyecto.

**Decisión de equipo:** en vez de elegir uno solo, se decidió usar **ambos proveedores**:
- **Fase 1 (arranque):** implementar el flujo completo del RAG usando solo Gemini, para tener algo funcional rápido
- **Fase 2 (mejora):** agregar Groq como fallback automático (si Gemini falla por rate limit o error, el sistema cae a Groq) y/o como comparador de respuestas en la interfaz

Esto permite documentar una evolución real del proyecto y demuestra manejo de resiliencia entre proveedores de IA, algo valorado en sistemas de producción.

## 3. Base de datos vectorial

Motivo de la elección: se optó por pgvector (extensión de PostgreSQL) por razones técnicas concretas:
- **Menos infraestructura**: no requiere un servicio de base de datos separado; los embeddings viven en el mismo PostgreSQL donde se guardan los demás datos del proyecto
- **Consistencia transaccional**: los chunks de texto, sus embeddings y su metadata (ej. de qué sección de la doc de Stripe provienen) se guardan en la misma transacción, evitando desincronización entre datos relacionales y vectoriales
- **Búsquedas híbridas**: permite combinar filtros SQL tradicionales (ej. `WHERE seccion = 'Payments'`) con búsqueda por similitud vectorial en una sola query


## 4. Estrategia de chunking (troceo de documentos)

_Pendiente de definir:_
- Tamaño de chunk (`CHUNK_SIZE`)
- Overlap entre chunks (`CHUNK_OVERLAP`)
- Estrategia (por párrafos, por tokens, semántico, etc.)

## 5. Frontend

_Pendiente de decidir._

## 6. Deploy

_Pendiente. Candidatos: Railway, Render._

## 7. Problemas encontrados

_Ir completando acá a medida que surjan bugs, limitaciones o decisiones de último momento que valga la pena documentar (ej. rate limits de la API, problemas de precisión en las respuestas, tiempos de indexado, etc.)_
