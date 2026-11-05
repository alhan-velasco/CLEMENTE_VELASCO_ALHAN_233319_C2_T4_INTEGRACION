# CLEMENTE_VELASCO_ALHAN_233319_C2_T4_INTEGRACION

**Universidad Politécnica de Chiapas (UPCh) · Ingeniería en Software · 9° Cuatrimestre**  
**Materia:** Minería de Datos  
**Docente:** Ramsés Alejandro Camas Nájera  
**Alumno:** Clemente Velasco Alhan  
**Matrícula:** 233319  
**Corte 2 · Tarea 4:** Integración Fullstack de Motores de Búsqueda, Creación de Corpus mediante Web Scraping y Benchmark de Concurrencia (Hasta 50 Usuarios Concurrentes)

---

## 1. Descripción del Proyecto

Este repositorio implementa una plataforma **Fullstack (Backend FastAPI + Frontend Web Interactivo)** que integra y compara en tiempo real los **3 motores de búsqueda** desarrollados a lo largo de las tareas del Corte 2 sobre un **nuevo corpus de 60 documentos en español (todos con $\ge 100$ palabras verificadas)** extraído de forma automatizada mediante **Web Scraping**:

1. **Motor 1 (Tarea 1 — Búsqueda Léxica):**
   - **Motor 1A (`TF-IDF`, Lab 2):** Frecuencia relativa $TF(t,d)$, $IDF(t) = \ln(N/df_t)$ y similitud coseno dispersa con filtrado `solo_positivos=True`.
   - **Motor 1B (`BM25 Okapi`, Lab 3):** Saturación de frecuencia ($k_1 = 1.5$) y normalización por longitud ($b = 0.75$) sobre índice invertido precalculado con lematización en español vía `spaCy` (`es_core_news_sm`).
2. **Motor 2 (Tarea 2 — Búsqueda Semántica Densa con Embeddings):**
   - **Bi-Encoder `Sentence-BERT` (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, Lab 5 y Lab 6):** Codificación neuronal multilingüe en vectores densos de 384 dimensiones normalizados ($L_2=1$) y recuperación por similitud coseno (producto punto matricial).
3. **Motor 3 (Tarea 3 — Búsqueda Híbrida y Reranking de Dos Etapas):**
   - **Motor 3A (`Híbrido RRF`, Lab 7):** Fusión de rankings entre `BM25` y `SBERT Denso` mediante **Reciprocal Rank Fusion** ($\mathrm{RRF}(d) = \sum \frac{1}{60 + \mathrm{rank}_i(d)}$) y variante de **Fusión Lineal con normalización min-max** ($\alpha = 0.4$).
   - **Motor 3B (`Híbrido RRF + Cross-Encoder Reranking`, Lab 7):** Arquitectura de embudo en dos etapas donde la Etapa 1 (`RRF BM25 + SBERT`) recupera el Top-10 de candidatos de alto *recall* y la Etapa 2 los reordena con atención cruzada token a token mediante `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`.

---

## 2. Estructura del Repositorio

```text
CLEMENTE_VELASCO_ALHAN_233319_C2_T4_INTEGRACION/
├── backend/
│   ├── __init__.py
│   ├── engines.py               # Implementación de TF-IDF, BM25, SBERT, RRF, Cross-Encoder y Qrels
│   └── main.py                  # Servidor API REST FastAPI + Servidor de Frontend y Benchmark en vivo
├── frontend/
│   └── index.html               # Aplicación Web Fullstack (Buscador lado a lado, p50/p95, Corpus)
├── scripts/
│   ├── scraper_corpus.py        # Script de Web Scraping (60 artículos >= 100 palabras + URLs fuente)
│   ├── run_benchmarks.py        # Evaluación IR (nDCG@5, MRR, R@5) y Simulación de 1 a 50 usuarios
│   └── generate_report_pdf.py   # Generador del reporte técnico en PDF con gráficas y tablas
├── data/
│   ├── corpus_scraped.json      # Corpus crudo de 60 documentos (>= 125 palabras c/u) con URLs
│   ├── corpus_procesado.json    # Corpus lematizado con spaCy (se genera solo al iniciar el backend, no se sube a Git)
│   ├── fuentes_scraping.csv     # Catálogo auditable de las 60 fuentes de Web Scraping
│   ├── evaluation_results.json  # Resultados de calidad IR (nDCG@5, MRR, Recall@5)
│   └── benchmark_results.json   # Resultados de latencia p50, p95, p99 y RPS (1 a 50 usuarios)
├── reports/
│   ├── fig1_calidad_ndcg.png
│   ├── fig2_latencia_p50_p95_50users.png
│   ├── fig3_escalabilidad_concurrencia.png
│   ├── fig4_corpus_distribucion.png
│   └── fig5_tradeoff_calidad_latencia.png
├── CLEMENTE_VELASCO_ALHAN_233319_C2_T4_INTEGRACION.pdf  # Reporte Técnico Final en PDF
├── AI_USAGE.md                  # Declaración de uso de Inteligencia Artificial
├── requirements.txt             # Dependencias del sistema
└── README.md
```

---

## 3. Instalación y Ejecución del Sistema Fullstack

### 3.1. Instalar dependencias
```bash
pip install -r requirements.txt
python -m spacy download es_core_news_sm
```

### 3.2. Ejecutar Web Scraping del Corpus y Benchmarks (1 a 50 usuarios concurrentes)
```bash
python scripts/run_benchmarks.py
```

### 3.3. Iniciar el Servidor Fullstack (Backend FastAPI + Frontend Web)
Desde la carpeta `CLEMENTE_VELASCO_ALHAN_233319_C2_T4_INTEGRACION`:
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
Abrir en el navegador: **`http://127.0.0.1:8000`** o **`http://localhost:8000`**
- Documentación interactiva Swagger/OpenAPI del Backend: **`http://127.0.0.1:8000/docs`**
