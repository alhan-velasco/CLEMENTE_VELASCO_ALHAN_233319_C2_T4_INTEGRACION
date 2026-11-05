# Declaración de Uso de Inteligencia Artificial (`AI_USAGE.md`)

**Universidad Politécnica de Chiapas (UPCh) · Ingeniería en Software**  
**Materia:** Minería de Datos · **Unidad 2 (Corte 2 · Tarea 4: Integración de Motores de Búsqueda)**  
**Estudiante:** Clemente Velasco Alhan · **Matrícula:** 233319  
**Docente:** Ramsés Alejandro Camas Nájera  

En cumplimiento con las normas de honestidad académica del curso, se detalla el uso de herramientas de asistencia de IA en esta entrega:

| Componente / Archivo | Herramienta | Qué propuso o estructuró la IA | Qué implementé, verifiqué o adapté personalmente |
|---|---|---|---|
| `scripts/scraper_corpus.py` | Gemini (Antigravity) | Estructura base con `urllib.request` y `HTMLParser` para extraer párrafos `<p>` de artículos de Wikipedia en español y validar la longitud mínima de palabras. | Seleccioné los 60 temas en 6 categorías alineadas al corpus chiapaneco del curso, verifiqué que los 60 documentos superaran estrictamente las 100 palabras (125–230 palabras) y audité las 60 URLs en `fuentes_scraping.csv`. |
| `backend/engines.py` y `backend/main.py` | Gemini (Antigravity) | Encapsulamiento modular en la clase `SearchEngineHub` y endpoints REST en FastAPI (`/api/search`, `/api/evaluate`, `/api/benchmark/run`). | Reutilicé mis implementaciones previas de TF-IDF (Lab 2), BM25 Okapi con `es_core_news_sm` (Lab 3), `SentenceTransformer` (`paraphrase-multilingual-MiniLM-L12-v2`, Lab 5/6) y `RRF` + `CrossEncoder` (`mmarco-mMiniLMv2-L12-H384-v1`, Lab 7), asegurando el filtro `solo_positivos=True` y bloqueo thread-safe para concurrencia. |
| `frontend/index.html` | Gemini (Antigravity) | Maquetación de pestañas HTML/CSS/JS con gráficas en Chart.js para comparar los motores lado a lado y visualizar latencias p50 y p95. | Ajusté las tarjetas de desglose de scores (`BM25`, `SBERT`, `RRF`, `Cross-Encoder`), los botones de consultas léxicas, semánticas y mixtas, y el explorador del corpus con enlaces directos a las fuentes del Web Scraping. |
| `scripts/run_benchmarks.py` y Reporte Técnico PDF | Gemini (Antigravity) | Arnés de pruebas con `ThreadPoolExecutor` para 1, 5, 10, 25 y 50 usuarios concurrentes y script de maquetación en ReportLab. | Ejecuté las mediciones reales en mi entorno CPU, analicé las curvas de latencia p50 y p95 y redacté los criterios de decisión, ventajas/desventajas de cada motor y cuándo utilizar cada tipo de corpus. |
