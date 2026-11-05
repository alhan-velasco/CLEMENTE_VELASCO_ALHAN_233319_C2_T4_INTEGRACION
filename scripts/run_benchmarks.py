"""
Script de Evaluación IR, Simulación de Carga de hasta 50 Usuarios Concurrentes (p50 y p95)
y Generación de Gráficas de Desempeño (Tarea 4 · Corte 2)
Alumno: Alhan Clemente Velasco · Matrícula: 233319
Materia: Minería de Datos · UPCh · Docente: Ramsés Alejandro Camas Nájera
"""

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.scraper_corpus import ejecutar_scraping
from backend.engines import QRELS_CORPUS60, SearchEngineHub

DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def simular_concurrencia_motores(hub: SearchEngineHub):
    """
    Simula 1, 5, 10, 25 y 50 usuarios concurrentes realizando peticiones simultáneas
    al sistema para cada motor de búsqueda. Calcula latencia p50, p95, p99, media y RPS.
    """
    niveles_usuarios = [1, 5, 10, 25, 50]
    motores = [
        ("tfidf", "TF-IDF (T1 Léxico)"),
        ("bm25", "BM25 Okapi (T1 Léxico)"),
        ("sbert", "SBERT Denso (T2 Semántico)"),
        ("rrf", "Híbrido RRF BM25+SBERT (T3)"),
        ("rerank", "Híbrido RRF + Cross-Encoder (T3)"),
    ]
    consultas = list(QRELS_CORPUS60.keys())

    # Calentamiento inicial de todos los motores
    print("\nCalentando motores de búsqueda antes del benchmark concurrente...")
    for cod, _ in motores:
        for q in consultas[:3]:
            hub.buscar_motor(q, motor=cod, top_k=5)

    resultados_concurrencia = {
        "niveles_usuarios": niveles_usuarios,
        "motores": {cod: {"nombre": nom, "niveles": {}} for cod, nom in motores},
        "tabla_50_usuarios": [],
    }

    for n_users in niveles_usuarios:
        print(f"\n--- Simulando {n_users} usuario(s) concurrente(s) ---")
        for cod, nom in motores:
            # Para obtener percentiles p50 y p95 estadísticamente sólidos:
            # Con 1 usuario: 24 peticiones secuenciales; con 5..50 usuarios: max(24, n_users * 2) peticiones concurrentes
            # (Para Cross-Encoder con 25 y 50 usuarios usamos n_users peticiones simultáneas exactas para medir la cola real de 50 usuarios)
            if cod == "rerank" and n_users >= 25:
                total_reqs = n_users
            else:
                total_reqs = max(24, n_users * 2)

            tareas_q = [consultas[i % len(consultas)] for i in range(total_reqs)]
            latencias_ms = []
            errores = 0

            def _user_request(q_text: str) -> float:
                t_start = time.perf_counter()
                hub.buscar_motor(q_text, motor=cod, top_k=5)
                return (time.perf_counter() - t_start) * 1000.0

            t_wall0 = time.perf_counter()
            with ThreadPoolExecutor(max_workers=n_users) as executor:
                futures = [executor.submit(_user_request, q_t) for q_t in tareas_q]
                for fut in as_completed(futures):
                    try:
                        latencias_ms.append(fut.result())
                    except Exception as exc:
                        errores += 1
                        print(f"Error en {cod}: {exc}")
            wall_time_s = time.perf_counter() - t_wall0

            arr = np.array(latencias_ms, dtype=float)
            p50 = float(np.percentile(arr, 50))
            p95 = float(np.percentile(arr, 95))
            p99 = float(np.percentile(arr, 99))
            media = float(np.mean(arr))
            std = float(np.std(arr))
            min_v = float(np.min(arr))
            max_v = float(np.max(arr))
            rps = float(total_reqs / wall_time_s) if wall_time_s > 0 else 0.0

            metricas_nivel = {
                "usuarios_concurrentes": n_users,
                "total_peticiones": total_reqs,
                "errores": errores,
                "p50_ms": round(p50, 3),
                "p95_ms": round(p95, 3),
                "p99_ms": round(p99, 3),
                "media_ms": round(media, 3),
                "std_ms": round(std, 3),
                "min_ms": round(min_v, 3),
                "max_ms": round(max_v, 3),
                "throughput_rps": round(rps, 2),
                "tiempo_lote_s": round(wall_time_s, 3),
            }
            resultados_concurrencia["motores"][cod]["niveles"][str(n_users)] = metricas_nivel
            print(
                f"  {nom:<34} | U={n_users:2d} | p50={p50:8.2f} ms | p95={p95:8.2f} ms | Media={media:8.2f} ms | RPS={rps:6.1f}"
            )

            if n_users == 50:
                resultados_concurrencia["tabla_50_usuarios"].append(
                    {
                        "codigo": cod,
                        "motor": nom,
                        "usuarios": 50,
                        "p50_ms": round(p50, 2),
                        "p95_ms": round(p95, 2),
                        "p99_ms": round(p99, 2),
                        "media_ms": round(media, 2),
                        "min_ms": round(min_v, 2),
                        "max_ms": round(max_v, 2),
                        "throughput_rps": round(rps, 2),
                    }
                )

    ruta_bench = DATA_DIR / "benchmark_results.json"
    ruta_bench.write_text(
        json.dumps(resultados_concurrencia, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nBenchmark concurrente guardado en: {ruta_bench}")
    return resultados_concurrencia


def generar_graficas(hub: SearchEngineHub, eval_res: dict, bench_res: dict):
    plt.rcParams["font.sans-serif"] = "DejaVu Sans"
    plt.rcParams["axes.edgecolor"] = "#CBD5E1"
    plt.rcParams["axes.linewidth"] = 0.8

    # 1. Gráfica de Calidad IR (nDCG@5 Global vs Semánticas vs Léxicas vs Mixtas)
    resumen = eval_res["resumen"]
    nombres = [r["nombre"].replace("Motor ", "M").split("(")[0].strip() for r in resumen]
    ndcg_global = [r["ndcg_5"] for r in resumen]
    ndcg_sem = [r["ndcg_semantica"] for r in resumen]
    mrr_vals = [r["mrr"] for r in resumen]
    rec_vals = [r["recall_5"] for r in resumen]

    fig, ax = plt.subplots(figsize=(9.5, 4.6), dpi=220)
    x = np.arange(len(nombres))
    w = 0.25
    b1 = ax.bar(x - w, ndcg_global, width=w, label="nDCG@5 Global (12 q)", color="#1C3257")
    b2 = ax.bar(x, ndcg_sem, width=w, label="nDCG@5 Semánticas (4 q)", color="#E08A6E")
    b3 = ax.bar(x + w, rec_vals, width=w, label="Recall@5 Global", color="#2B7A78")

    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h + 0.015,
                f"{h:.3f}",
                ha="center",
                va="bottom",
                fontsize=7.5,
                fontweight="bold",
                color="#1E293B",
            )

    ax.set_xticks(x)
    ax.set_xticklabels(nombres, rotation=15, ha="right", fontsize=8.5, fontweight="bold")
    ax.set_ylim(0, 1.14)
    ax.set_ylabel("Puntaje de Calidad IR (0.0 - 1.0)", fontsize=9.5, fontweight="bold")
    ax.set_title(
        "Desempeño de Calidad IR sobre Corpus de 60 Documentos (Web Scraping)",
        fontsize=11,
        fontweight="bold",
        color="#1C3257",
        pad=12,
    )
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(frameon=True, facecolor="#F8FAFC", fontsize=8.5, loc="lower right")
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "fig1_calidad_ndcg.png", dpi=220)
    plt.close(fig)

    # 2. Gráfica de Latencia p50 y p95 con 50 Usuarios Concurrentes (Escala Logarítmica y Lineal)
    t50 = bench_res["tabla_50_usuarios"]
    m_labels = [x["motor"].split("(")[0].strip() for x in t50]
    p50_vals = [x["p50_ms"] for x in t50]
    p95_vals = [x["p95_ms"] for x in t50]

    fig, ax = plt.subplots(figsize=(9.2, 4.5), dpi=220)
    x = np.arange(len(m_labels))
    w = 0.35
    bars_p50 = ax.bar(x - w / 2, p50_vals, width=w, label="Latencia p50 (Mediana)", color="#2563EB")
    bars_p95 = ax.bar(x + w / 2, p95_vals, width=w, label="Latencia p95 (Percentil 95)", color="#DC2626")

    ax.set_yscale("log")
    for bar in bars_p50:
        v = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            v * 1.15,
            f"{v:.1f} ms",
            ha="center",
            va="bottom",
            fontsize=7.5,
            fontweight="bold",
            color="#1E3A8A",
        )
    for bar in bars_p95:
        v = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            v * 1.15,
            f"{v:.1f} ms",
            ha="center",
            va="bottom",
            fontsize=7.5,
            fontweight="bold",
            color="#991B1B",
        )

    ax.set_xticks(x)
    ax.set_xticklabels(m_labels, rotation=12, ha="right", fontsize=8.5, fontweight="bold")
    ax.set_ylabel("Latencia en Milisegundos (escala log)", fontsize=9.5, fontweight="bold")
    ax.set_title(
        "Latencia p50 y p95 bajo Carga de 50 Usuarios Concurrentes",
        fontsize=11,
        fontweight="bold",
        color="#1C3257",
        pad=12,
    )
    ax.set_ylim(min(p50_vals) * 0.5, max(p95_vals) * 3.5)
    ax.grid(axis="y", which="both", linestyle="--", alpha=0.35)
    ax.legend(frameon=True, facecolor="#F8FAFC", fontsize=9)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "fig2_latencia_p50_p95_50users.png", dpi=220)
    plt.close(fig)

    # 3. Curvas de Escalabilidad de Concurrencia (1, 5, 10, 25, 50 usuarios concurrentes)
    niveles = bench_res["niveles_usuarios"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.3), dpi=220)
    colores_m = {
        "tfidf": "#64748B",
        "bm25": "#0D9488",
        "sbert": "#2563EB",
        "rrf": "#D97706",
        "rerank": "#DC2626",
    }
    marcadores = {"tfidf": "o", "bm25": "s", "sbert": "^", "rrf": "D", "rerank": "P"}

    for cod, info in bench_res["motores"].items():
        y_p50 = [info["niveles"][str(u)]["p50_ms"] for u in niveles]
        y_p95 = [info["niveles"][str(u)]["p95_ms"] for u in niveles]
        lbl = info["nombre"].split("(")[0].strip()
        ax1.plot(niveles, y_p50, marker=marcadores[cod], lw=2, color=colores_m[cod], label=lbl)
        ax2.plot(niveles, y_p95, marker=marcadores[cod], lw=2, color=colores_m[cod], label=lbl)

    ax1.set_yscale("log")
    ax1.set_title("Evolución de Latencia p50 (1 a 50 Usuarios)", fontsize=10, fontweight="bold", color="#1C3257")
    ax1.set_xlabel("Usuarios Concurrentes", fontsize=9)
    ax1.set_ylabel("Latencia p50 (ms, escala log)", fontsize=9)
    ax1.set_xticks(niveles)
    ax1.grid(True, which="both", linestyle="--", alpha=0.35)
    ax1.legend(fontsize=7.5)

    ax2.set_yscale("log")
    ax2.set_title("Evolución de Latencia p95 (1 a 50 Usuarios)", fontsize=10, fontweight="bold", color="#1C3257")
    ax2.set_xlabel("Usuarios Concurrentes", fontsize=9)
    ax2.set_ylabel("Latencia p95 (ms, escala log)", fontsize=9)
    ax2.set_xticks(niveles)
    ax2.grid(True, which="both", linestyle="--", alpha=0.35)
    ax2.legend(fontsize=7.5)

    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "fig3_escalabilidad_concurrencia.png", dpi=220)
    plt.close(fig)

    # 4. Distribución de longitud de palabras del Corpus de 60 documentos (Web Scraping)
    palabras_doc = [d["num_palabras"] for d in hub.corpus]
    categorias = {}
    for d in hub.corpus:
        categorias[d["categoria"]] = categorias.get(d["categoria"], 0) + 1

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 4.0), dpi=220)
    ax1.hist(palabras_doc, bins=12, color="#1C3257", edgecolor="white", alpha=0.9)
    ax1.axvline(100, color="#DC2626", linestyle="--", lw=1.8, label="Mínimo requerido (100 palabras)")
    ax1.axvline(np.mean(palabras_doc), color="#E08A6E", linestyle="-", lw=2, label=f"Media ({np.mean(palabras_doc):.1f} pal.)")
    ax1.set_title("Distribución de Palabras por Documento (N=60)", fontsize=9.8, fontweight="bold", color="#1C3257")
    ax1.set_xlabel("Número de Palabras", fontsize=8.8)
    ax1.set_ylabel("Frecuencia (Documentos)", fontsize=8.8)
    ax1.legend(fontsize=7.8)
    ax1.grid(axis="y", linestyle="--", alpha=0.35)

    cats_nombres = list(categorias.keys())
    cats_vals = list(categorias.values())
    y_pos = np.arange(len(cats_nombres))
    ax2.barh(y_pos, cats_vals, color="#2B7A78", height=0.6)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(cats_nombres, fontsize=8)
    ax2.set_xlabel("Documentos Extraídos por Web Scraping", fontsize=8.8)
    ax2.set_title("Balance Temático del Corpus (6 Categorías)", fontsize=9.8, fontweight="bold", color="#1C3257")
    ax2.set_xlim(0, max(cats_vals) + 3)
    for i, v in enumerate(cats_vals):
        ax2.text(v + 0.2, i, f"{v} docs", va="center", fontsize=8, fontweight="bold", color="#1E293B")
    ax2.grid(axis="x", linestyle="--", alpha=0.35)

    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "fig4_corpus_distribucion.png", dpi=220)
    plt.close(fig)

    # 5. Frontera Pareto Calidad (nDCG@5) vs Latencia p95 (50 usuarios)
    fig, ax = plt.subplots(figsize=(8.2, 4.3), dpi=220)
    map_eval = {r["codigo"]: r for r in eval_res["resumen"]}
    for item in t50:
        cod = item["codigo"]
        ev = map_eval[cod]
        x_lat = item["p95_ms"]
        y_qual = ev["ndcg_5"]
        ax.scatter(x_lat, y_qual, s=150, color=colores_m[cod], edgecolors="#1E293B", linewidth=1.2, zorder=5)
        ax.annotate(
            f"{item['motor'].split('(')[0].strip()}\n(p95={x_lat:.1f}ms, nDCG={y_qual:.3f})",
            (x_lat, y_qual),
            textcoords="offset points",
            xytext=(8, -6),
            fontsize=8,
            fontweight="bold",
            color="#1E293B",
        )

    ax.set_xscale("log")
    ax.set_xlabel("Latencia p95 con 50 Usuarios Concurrentes (ms, escala log)", fontsize=9.2, fontweight="bold")
    ax.set_ylabel("Calidad de Recuperación (nDCG@5 Global)", fontsize=9.2, fontweight="bold")
    ax.set_title("Criterio de Decisión: Trade-off Calidad (nDCG@5) vs. Latencia p95", fontsize=10.5, fontweight="bold", color="#1C3257")
    ax.set_ylim(0.55, 1.05)
    ax.grid(True, which="both", linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "fig5_tradeoff_calidad_latencia.png", dpi=220)
    plt.close(fig)
    print(f"Gráficas guardadas exitosamente en: {REPORTS_DIR}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if not (DATA_DIR / "corpus_scraped.json").exists():
        ejecutar_scraping()
    else:
        print("Corpus scrapeado ya existe, verificando integridad...")
        ejecutar_scraping()

    print("\nInicializando SearchEngineHub (TF-IDF, BM25, SBERT, RRF, Cross-Encoder)...")
    hub = SearchEngineHub(load_cross_encoder=True)
    print(f"Motores inicializados en {hub.total_init_ms:.1f} ms sobre {hub.N} documentos.")

    print("\nEjecutando evaluación de calidad IR (nDCG@5, MRR, Recall@5)...")
    eval_res = hub.evaluar_todos_los_motores(k=5)
    (DATA_DIR / "evaluation_results.json").write_text(
        json.dumps(eval_res, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for r in eval_res["resumen"]:
        print(
            f"  {r['nombre']:<48} | nDCG@5={r['ndcg_5']:.3f} | MRR={r['mrr']:.3f} | R@5={r['recall_5']:.3f} | Sem={r['ndcg_semantica']:.3f}"
        )

    ruta_bench = DATA_DIR / "benchmark_results.json"
    if ruta_bench.exists():
        print(f"\nCargando resultados de concurrencia (1..50 usuarios) desde {ruta_bench}...")
        bench_res = json.loads(ruta_bench.read_text(encoding="utf-8"))
    else:
        bench_res = simular_concurrencia_motores(hub)
    generar_graficas(hub, eval_res, bench_res)


if __name__ == "__main__":
    main()
