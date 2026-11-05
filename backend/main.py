"""
Backend Fullstack con FastAPI para Integración de Motores de Búsqueda (Tarea 4 · Corte 2)
Alumno: Clemente Velasco Alhan · Matrícula: 233319
Materia: Minería de Datos · UPCh · Docente: Ramsés Alejandro Camas Nájera
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.engines import QRELS_CORPUS60, TIPO_CONSULTA, SearchEngineHub

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FRONTEND_DIR = BASE_DIR / "frontend"
BENCHMARK_JSON = DATA_DIR / "benchmark_results.json"
EVAL_JSON = DATA_DIR / "evaluation_results.json"

app = FastAPI(
    title="UPCh Minería de Datos · Sistema Fullstack de Motores de Búsqueda (C2_T4)",
    description=(
        "Integración Fullstack de los 3 Motores de Búsqueda del Corte 2 "
        "(Motor 1: Léxico TF-IDF/BM25, Motor 2: Semántico Denso SBERT, "
        "Motor 3: Híbrido RRF + Cross-Encoder Reranking) sobre un corpus de "
        "60 documentos (>= 100 palabras c/u) obtenidos mediante Web Scraping."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

hub: Optional[SearchEngineHub] = None


def get_hub() -> SearchEngineHub:
    global hub
    if hub is None:
        hub = SearchEngineHub(load_cross_encoder=True)
    return hub


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Consulta de búsqueda en texto libre")
    engine: str = Field(
        default="compare3",
        description="Motor a ejecutar: 'tfidf', 'bm25', 'sbert', 'rrf', 'rerank', 'compare3' o 'all'",
    )
    top_k: int = Field(default=5, ge=1, le=20)


class LiveBenchmarkRequest(BaseModel):
    concurrent_users: int = Field(default=50, ge=1, le=50)
    queries_per_user: int = Field(default=2, ge=1, le=5)
    engines: List[str] = Field(
        default=["tfidf", "bm25", "sbert", "rrf", "rerank"]
    )


@app.on_event("startup")
def startup_event():
    get_hub()


@app.get("/api/health")
def health_check():
    h = get_hub()
    return {
        "status": "ok",
        "student": "Clemente Velasco Alhan",
        "matricula": "233319",
        "course": "Minería de Datos · Corte 2 · Tarea 4",
        "corpus_size": h.N,
        "vocab_size": len(h.df),
        "embedding_dim": h.emb_dim,
        "init_times_ms": {
            "tfidf": round(h.time_init_tfidf_ms, 2),
            "bm25": round(h.time_init_bm25_ms, 2),
            "sbert": round(h.time_init_sbert_ms, 2),
            "cross_encoder": round(h.time_init_ce_ms, 2),
            "total": round(h.total_init_ms, 2),
        },
    }


@app.get("/api/corpus")
def obtener_corpus(categoria: Optional[str] = Query(default=None)):
    h = get_hub()
    docs = h.corpus
    if categoria and categoria.lower() != "todas":
        docs = [d for d in docs if d["categoria"].lower() == categoria.lower()]

    palabras = [d["num_palabras"] for d in h.corpus]
    categorias_conteo = {}
    for d in h.corpus:
        categorias_conteo[d["categoria"]] = categorias_conteo.get(d["categoria"], 0) + 1

    return {
        "estadisticas": {
            "total_documentos": h.N,
            "min_palabras": int(min(palabras)),
            "max_palabras": int(max(palabras)),
            "promedio_palabras": round(float(np.mean(palabras)), 1),
            "mediana_palabras": round(float(np.median(palabras)), 1),
            "total_palabras": int(sum(palabras)),
            "vocabulario_unico_lemas": len(h.df),
            "promedio_tokens_lemas": round(float(h.avgdl), 1),
            "categorias": categorias_conteo,
        },
        "documentos": docs,
    }


@app.post("/api/search")
def buscar_endpoint(req: SearchRequest):
    h = get_hub()
    q = req.query.strip()
    if not q:
        raise HTTPException(status_code=400, detail="La consulta no puede estar vacía")

    modo = req.engine.lower().strip()
    t0_global = time.perf_counter()

    if modo == "compare3":
        # Los 3 motores principales de las tareas anteriores (T1: BM25, T2: SBERT Denso, T3: Híbrido RRF + Rerank)
        # más TF-IDF y RRF puro para análisis completo
        motores_lista = ["tfidf", "bm25", "sbert", "rrf", "rerank"]
        comparacion = {}
        for m in motores_lista:
            comparacion[m] = h.buscar_motor(q, motor=m, top_k=req.top_k)
        return {
            "modo": "comparacion_multiple",
            "consulta": q,
            "tokens_consulta": comparacion["bm25"]["tokens_consulta"],
            "tiempo_total_ms": round((time.perf_counter() - t0_global) * 1000.0, 3),
            "motores": comparacion,
        }
    elif modo == "all":
        motores_lista = ["tfidf", "bm25", "sbert", "lineal", "rrf", "rerank"]
        comparacion = {}
        for m in motores_lista:
            comparacion[m] = h.buscar_motor(q, motor=m, top_k=req.top_k)
        return {
            "modo": "comparacion_multiple",
            "consulta": q,
            "tokens_consulta": comparacion["bm25"]["tokens_consulta"],
            "tiempo_total_ms": round((time.perf_counter() - t0_global) * 1000.0, 3),
            "motores": comparacion,
        }
    else:
        res = h.buscar_motor(q, motor=modo, top_k=req.top_k)
        return {
            "modo": "individual",
            "consulta": q,
            "tokens_consulta": res["tokens_consulta"],
            "tiempo_total_ms": res["latencia_ms"],
            "motores": {modo: res},
        }


@app.get("/api/evaluate")
def evaluar_calidad():
    if EVAL_JSON.exists():
        return json.loads(EVAL_JSON.read_text(encoding="utf-8"))
    h = get_hub()
    res = h.evaluar_todos_los_motores(k=5)
    EVAL_JSON.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    return res


@app.get("/api/benchmark")
def obtener_benchmark():
    if BENCHMARK_JSON.exists():
        return json.loads(BENCHMARK_JSON.read_text(encoding="utf-8"))
    raise HTTPException(
        status_code=404,
        detail="Resultados de benchmark aún no generados. Ejecuta POST /api/benchmark/run o scripts/run_benchmarks.py",
    )


@app.post("/api/benchmark/run")
def ejecutar_benchmark_en_vivo(req: LiveBenchmarkRequest):
    """
    Simula N usuarios concurrentes (hasta 50 usuarios simultáneos) ejecutando consultas
    contra cada motor de búsqueda y calcula latencias p50, p95, p99, media y RPS.
    """
    h = get_hub()
    consultas_lista = list(QRELS_CORPUS60.keys())
    resultados_vivo = {}

    for motor in req.engines:
        # Calentamiento
        h.buscar_motor(consultas_lista[0], motor=motor, top_k=5)

        total_requests = req.concurrent_users * req.queries_per_user
        tareas_q = [
            consultas_lista[i % len(consultas_lista)] for i in range(total_requests)
        ]

        latencias_usuario_ms = []

        def _worker(q_str: str) -> float:
            t_req0 = time.perf_counter()
            h.buscar_motor(q_str, motor=motor, top_k=5)
            return (time.perf_counter() - t_req0) * 1000.0

        t_wall0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=req.concurrent_users) as pool:
            futs = [pool.submit(_worker, q_item) for q_item in tareas_q]
            for f in as_completed(futs):
                latencias_usuario_ms.append(f.result())
        wall_sec = time.perf_counter() - t_wall0

        arr = np.array(latencias_usuario_ms, dtype=float)
        resultados_vivo[motor] = {
            "motor": motor,
            "usuarios_concurrentes": req.concurrent_users,
            "total_peticiones": total_requests,
            "p50_ms": round(float(np.percentile(arr, 50)), 3),
            "p95_ms": round(float(np.percentile(arr, 95)), 3),
            "p99_ms": round(float(np.percentile(arr, 99)), 3),
            "media_ms": round(float(np.mean(arr)), 3),
            "std_ms": round(float(np.std(arr)), 3),
            "min_ms": round(float(np.min(arr)), 3),
            "max_ms": round(float(np.max(arr)), 3),
            "throughput_rps": round(float(total_requests / wall_sec), 2) if wall_sec > 0 else 0.0,
            "tiempo_total_s": round(float(wall_sec), 3),
        }

    return {
        "usuarios_concurrentes": req.concurrent_users,
        "peticiones_por_usuario": req.queries_per_user,
        "total_peticiones_por_motor": req.concurrent_users * req.queries_per_user,
        "resultados": resultados_vivo,
    }


# Servir archivos estáticos e interfaz Frontend
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Sistema Fullstack de Motores de Búsqueda - UPCh</h1>")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)

