"""
Módulo de Motores de Búsqueda Integrados (Tarea 4 · Corte 2)
Alumno: Clemente Velasco Alhan · Matrícula: 233319
Materia: Minería de Datos · UPCh · Docente: Ramsés Alejandro Camas Nájera

Integra los motores desarrollados en las tareas anteriores del Corte 2 sobre el corpus de >= 50 documentos:
  - Motor 1 (Tarea 1 - Léxico): TF-IDF (Lab 2) y BM25 Okapi (Lab 3) con preprocesamiento spaCy.
  - Motor 2 (Tarea 2 - Semántico Denso): Bi-Encoder Sentence-BERT (paraphrase-multilingual-MiniLM-L12-v2).
  - Motor 3 (Tarea 3 - Híbrido y Reranking): Reciprocal Rank Fusion (RRF k=60, BM25 + SBERT) y
    Arquitectura de 2 Etapas con Cross-Encoder (mmarco-mMiniLMv2-L12-H384-v1).
"""

import json
import math
import re
import threading
import time
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import spacy
import torch
from sentence_transformers import CrossEncoder, SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CORPUS_PATH = DATA_DIR / "corpus_scraped.json"
PROCESADO_PATH = DATA_DIR / "corpus_procesado.json"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

RE_URL = re.compile(r"https?://\S+")
RE_HTML = re.compile(r"</?[a-zA-Z][^>]*>")
CONSERVAR = {"no", "nunca", "sin", "ni", "muy", "poco", "nada", "tampoco"}


def _qd(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def normalizar(t: str, quitar_acentos: bool = False) -> str:
    t = unicodedata.normalize("NFC", t.lower())
    t = RE_URL.sub(" ", t)
    t = RE_HTML.sub(" ", t)
    if quitar_acentos:
        t = _qd(t)
    return re.sub(r"\s+", " ", t).strip()


# Banco de Evaluación de 12 Consultas (4 Léxicas, 4 Semánticas, 4 Mixtas) sobre el Corpus de 60 Documentos
QRELS_CORPUS60: Dict[str, Dict[str, int]] = {
    # Consultas Léxicas (términos exactos, siglas, nombres propios)
    "UPCh": {"d31": 3},
    "canon del sumidero": {"d51": 3, "d14": 2, "d01": 1},
    "Aedes aegypti": {"d42": 3, "d41": 3, "d43": 2, "d44": 1},
    "presa chicoasen grijalva": {"d14": 3, "d12": 3, "d16": 2, "d51": 2},
    # Consultas Semánticas (sinónimos, paráfrasis, barrera léxica sin compartir lemas clave)
    "problemas de agua": {"d02": 3, "d18": 3, "d11": 3, "d19": 2, "d20": 2, "d17": 2},
    "temblor de tierra": {"d03": 3, "d04": 3},
    "enfermedades transmitidas por mosquitos": {"d41": 3, "d42": 3, "d43": 3, "d45": 3, "d44": 2, "d50": 2},
    "movimiento telurico en el mar": {"d03": 3, "d04": 2},
    # Consultas Mixtas (combinan vocabulario compartido e intención conceptual)
    "sequia y cultivos de maiz": {"d24": 3, "d06": 3, "d02": 3, "d25": 2},
    "exportacion de cafe y cacao": {"d21": 3, "d30": 3, "d22": 3, "d27": 3, "d26": 2, "d23": 2},
    "inteligencia artificial y robotica": {"d32": 3, "d35": 3, "d36": 3, "d31": 3, "d33": 2, "d34": 2},
    "turismo cultural en san cristobal": {"d52": 3, "d51": 2, "d30": 2, "d53": 2, "d57": 2},
}

TIPO_CONSULTA: Dict[str, str] = {
    "UPCh": "lexica",
    "canon del sumidero": "lexica",
    "Aedes aegypti": "lexica",
    "presa chicoasen grijalva": "lexica",
    "problemas de agua": "semantica",
    "temblor de tierra": "semantica",
    "enfermedades transmitidas por mosquitos": "semantica",
    "movimiento telurico en el mar": "semantica",
    "sequia y cultivos de maiz": "mixta",
    "exportacion de cafe y cacao": "mixta",
    "inteligencia artificial y robotica": "mixta",
    "turismo cultural en san cristobal": "mixta",
}


class SearchEngineHub:
    """
    Contenedor unificado y thread-safe de los motores de búsqueda del Corte 2:
      1. tfidf       : Motor Léxico TF-IDF (Tarea 1 · Lab 2)
      2. bm25        : Motor Léxico BM25 Okapi (Tarea 1 · Lab 3)
      3. sbert       : Motor Semántico Denso Bi-Encoder SBERT (Tarea 2 · Lab 5/6)
      4. rrf         : Motor Híbrido Reciprocal Rank Fusion BM25 + SBERT (Tarea 3 · Lab 7)
      5. rerank      : Motor Híbrido RRF + Cross-Encoder Reranking 2 Etapas (Tarea 3 · Lab 7)
    """

    def __init__(self, load_cross_encoder: bool = True):
        t_start = time.perf_counter()
        self.nlp = spacy.load("es_core_news_sm", disable=["ner", "parser"])
        self.mis_stopwords = set(self.nlp.Defaults.stop_words) - CONSERVAR
        self._nlp_lock = threading.Lock()

        if not CORPUS_PATH.exists():
            raise FileNotFoundError(
                f"No se encontró el corpus en {CORPUS_PATH}. Ejecuta primero scripts/scraper_corpus.py"
            )

        self.corpus: List[Dict[str, Any]] = json.loads(
            CORPUS_PATH.read_text(encoding="utf-8")
        )
        self.ids: List[str] = [d["id"] for d in self.corpus]
        self.doc_map: Dict[str, Dict[str, Any]] = {d["id"]: d for d in self.corpus}
        self.N = len(self.corpus)

        # Preprocesar o cargar tokens procesados
        self.tokens_map: Dict[str, List[str]] = {}
        self.texto_limpio_map: Dict[str, str] = {}
        self._preparar_corpus()

        # 1. Inicializar Motor Léxico TF-IDF (Tarea 1 - Lab 2)
        t0 = time.perf_counter()
        self.df = Counter(t for d in self.ids for t in set(self.tokens_map[d]))
        self.idf_tfidf = {t: math.log(self.N / self.df[t]) for t in self.df}
        self.indice_tfidf = {d: self._vec_tfidf(self.tokens_map[d]) for d in self.ids}
        self.normas_tfidf = {
            d: math.sqrt(sum(v * v for v in vec.values()))
            for d, vec in self.indice_tfidf.items()
        }
        self.time_init_tfidf_ms = (time.perf_counter() - t0) * 1000

        # 2. Inicializar Motor Léxico BM25 (Tarea 1 - Lab 3)
        t0 = time.perf_counter()
        self.k1 = 1.5
        self.b = 0.75
        self.avgdl = sum(len(self.tokens_map[d]) for d in self.ids) / self.N
        self.idf_bm25 = {
            t: math.log(1.0 + (self.N - self.df[t] + 0.5) / (self.df[t] + 0.5))
            for t in self.df
        }
        self.tfd = {d: Counter(self.tokens_map[d]) for d in self.ids}
        self.dl = {d: len(self.tokens_map[d]) for d in self.ids}
        # Índice invertido precalculado para BM25 (optimiza búsquedas concurrentes)
        self.bm25_postings: Dict[str, Dict[str, float]] = {}
        for t in self.df:
            postings = {}
            idf_val = self.idf_bm25[t]
            for d in self.ids:
                f = self.tfd[d].get(t, 0)
                if f > 0:
                    postings[d] = (
                        idf_val
                        * f
                        * (self.k1 + 1.0)
                        / (f + self.k1 * (1.0 - self.b + self.b * self.dl[d] / self.avgdl))
                    )
            self.bm25_postings[t] = postings
        self.time_init_bm25_ms = (time.perf_counter() - t0) * 1000

        # 3. Inicializar Motor Semántico Denso SBERT (Tarea 2 - Lab 5/6)
        t0 = time.perf_counter()
        self.bi_model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self.bi_encoder = SentenceTransformer(self.bi_model_name, device=DEVICE)
        textos_ordenados = [self.texto_limpio_map[d] for d in self.ids]
        self.doc_embeddings = self.bi_encoder.encode(
            textos_ordenados,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        self.emb_dim = int(self.doc_embeddings.shape[1])
        self.emb_doc = {d: self.doc_embeddings[i] for i, d in enumerate(self.ids)}
        self.time_init_sbert_ms = (time.perf_counter() - t0) * 1000

        # 4. Inicializar Cross-Encoder para Reranking (Tarea 3 - Lab 7)
        self.ce_model_name = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
        self.cross_encoder: Optional[CrossEncoder] = None
        self.time_init_ce_ms = 0.0
        if load_cross_encoder:
            t0 = time.perf_counter()
            self.cross_encoder = CrossEncoder(self.ce_model_name, device=DEVICE)
            self.time_init_ce_ms = (time.perf_counter() - t0) * 1000

        self.total_init_ms = (time.perf_counter() - t_start) * 1000

    def preprocesar(self, texto: str) -> List[str]:
        texto_norm = normalizar(texto, quitar_acentos=False)
        # make_doc solo tokeniza y asigna lemas en español con el pipeline ligero
        with self._nlp_lock:
            doc = self.nlp(texto_norm)
        out = []
        for tok in doc:
            if tok.is_punct or tok.is_space or tok.like_num or tok.is_stop:
                continue
            lema = _qd(tok.lemma_.lower())
            if lema in self.mis_stopwords or len(lema) <= 2:
                continue
            out.append(lema)
        return out

    def _preparar_corpus(self) -> None:
        procesado_list = []
        for d in self.corpus:
            doc_id = d["id"]
            full_text = f"{d['titulo']}. {d['texto']}"
            self.texto_limpio_map[doc_id] = normalizar(full_text, quitar_acentos=False)
            toks = self.preprocesar(full_text)
            self.tokens_map[doc_id] = toks
            procesado_list.append(
                {
                    "id": doc_id,
                    "titulo": d["titulo"],
                    "categoria": d["categoria"],
                    "num_palabras": d["num_palabras"],
                    "num_tokens": len(toks),
                    "tokens": toks,
                    "fuente_url": d["fuente_url"],
                }
            )
        PROCESADO_PATH.write_text(
            json.dumps(procesado_list, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _tf(self, toks: List[str]) -> Dict[str, float]:
        n = len(toks)
        return {t: f / n for t, f in Counter(toks).items()} if n else {}

    def _vec_tfidf(self, toks: List[str]) -> Dict[str, float]:
        return {
            t: w * self.idf_tfidf.get(t, 0.0) for t, w in self._tf(toks).items()
        }

    # --- CÁLCULO DE SCORES POR MOTOR ---

    def scores_tfidf(self, consulta: str, q_tokens: Optional[List[str]] = None) -> Dict[str, float]:
        toks = q_tokens if q_tokens is not None else self.preprocesar(consulta)
        vq = self._vec_tfidf(toks)
        nq = math.sqrt(sum(v * v for v in vq.values()))
        if nq == 0.0:
            return {d: 0.0 for d in self.ids}
        scores = {}
        set_vq = set(vq)
        for d in self.ids:
            vd = self.indice_tfidf[d]
            nd = self.normas_tfidf[d]
            comunes = set_vq & set(vd)
            if not comunes or nd == 0.0:
                scores[d] = 0.0
            else:
                num = sum(vq[t] * vd[t] for t in comunes)
                scores[d] = num / (nq * nd)
        return scores

    def scores_bm25(self, consulta: str, q_tokens: Optional[List[str]] = None) -> Dict[str, float]:
        toks = q_tokens if q_tokens is not None else self.preprocesar(consulta)
        scores = {d: 0.0 for d in self.ids}
        for t in toks:
            postings = self.bm25_postings.get(t)
            if postings:
                for d, val in postings.items():
                    scores[d] += val
        return scores

    def scores_sbert(self, consulta: str) -> Dict[str, float]:
        vq = self.bi_encoder.encode(
            [normalizar(consulta, quitar_acentos=False)],
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )[0]
        # Producto matricial vectorizado sobre los 60 documentos: (N, 384) @ (384,)
        sims = self.doc_embeddings @ vq
        return {d: float(sims[i]) for i, d in enumerate(self.ids)}

    @staticmethod
    def ranking(scores: Dict[str, float], solo_positivos: bool = False) -> List[str]:
        items = [
            (d, s) for d, s in scores.items() if s > 0.0 or not solo_positivos
        ]
        return [d for d, _ in sorted(items, key=lambda x: (-x[1], x[0]))]

    @staticmethod
    def minmax(scores: Dict[str, float]) -> Dict[str, float]:
        if not scores:
            return {}
        lo, hi = min(scores.values()), max(scores.values())
        return {
            d: (v - lo) / (hi - lo) if hi > lo else 0.0 for d, v in scores.items()
        }

    def scores_lineal(
        self,
        consulta: str,
        alpha: float = 0.4,
        normalizar_scores: bool = True,
        q_tokens: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        sb = self.scores_bm25(consulta, q_tokens=q_tokens)
        sd = self.scores_sbert(consulta)
        if normalizar_scores:
            sb, sd = self.minmax(sb), self.minmax(sd)
        return {d: alpha * sb[d] + (1.0 - alpha) * sd[d] for d in self.ids}

    def scores_rrf(
        self,
        consulta: str,
        k_rrf: int = 60,
        profundidad: int = 20,
        incluir_tfidf: bool = False,
        q_tokens: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        toks = q_tokens if q_tokens is not None else self.preprocesar(consulta)
        sb = self.scores_bm25(consulta, q_tokens=toks)
        sd = self.scores_sbert(consulta)
        r_bm25 = self.ranking(sb, solo_positivos=True)
        r_sbert = self.ranking(sd, solo_positivos=False)
        listas = [r_bm25, r_sbert]
        if incluir_tfidf:
            st = self.scores_tfidf(consulta, q_tokens=toks)
            r_tfidf = self.ranking(st, solo_positivos=True)
            listas.insert(0, r_tfidf)

        acc = Counter()
        for r in listas:
            for pos, doc_id in enumerate(r[:profundidad], start=1):
                acc[doc_id] += 1.0 / (k_rrf + pos)

        # Asegurar entrada para todos los documentos
        scores_final = {d: float(acc.get(d, 0.0)) for d in self.ids}
        return {
            "scores": scores_final,
            "bm25_scores": sb,
            "sbert_scores": sd,
            "bm25_rank": {d: i + 1 for i, d in enumerate(r_bm25)},
            "sbert_rank": {d: i + 1 for i, d in enumerate(r_sbert)},
        }

    def buscar_motor(
        self,
        consulta: str,
        motor: str = "rrf",
        top_k: int = 5,
        cand_rerank: int = 10,
    ) -> Dict[str, Any]:
        """
        Ejecuta la búsqueda en el motor especificado y devuelve los resultados enriquecidos
        junto con el tiempo exacto de latencia en milisegundos.
        Motores soportados:
          - 'tfidf'  : Motor 1A (Tarea 1 · Léxico TF-IDF)
          - 'bm25'   : Motor 1B (Tarea 1 · Léxico BM25 Okapi)
          - 'sbert'  : Motor 2  (Tarea 2 · Semántico Denso SBERT)
          - 'lineal' : Motor 3  (Tarea 3 · Híbrido Fusión Lineal min-max alpha=0.4)
          - 'rrf'    : Motor 3A (Tarea 3 · Híbrido RRF BM25 + SBERT, k=60)
          - 'rerank' : Motor 3B (Tarea 3 · Híbrido RRF + Cross-Encoder 2 Etapas)
        """
        t0 = time.perf_counter()
        motor = motor.lower().strip()
        q_tokens = []

        extra_meta: Dict[str, Dict[str, Any]] = {}

        if motor == "tfidf":
            q_tokens = self.preprocesar(consulta)
            scores = self.scores_tfidf(consulta, q_tokens=q_tokens)
            orden = self.ranking(scores, solo_positivos=True)
        elif motor == "bm25":
            q_tokens = self.preprocesar(consulta)
            scores = self.scores_bm25(consulta, q_tokens=q_tokens)
            orden = self.ranking(scores, solo_positivos=True)
        elif motor in ("sbert", "denso"):
            q_tokens = self.preprocesar(consulta)
            scores = self.scores_sbert(consulta)
            orden = self.ranking(scores, solo_positivos=False)
        elif motor == "lineal":
            q_tokens = self.preprocesar(consulta)
            scores = self.scores_lineal(consulta, alpha=0.4, normalizar_scores=True, q_tokens=q_tokens)
            orden = self.ranking(scores, solo_positivos=False)
        elif motor in ("rrf", "hibrido"):
            q_tokens = self.preprocesar(consulta)
            rrf_data = self.scores_rrf(consulta, k_rrf=60, profundidad=10, q_tokens=q_tokens)
            scores = rrf_data["scores"]
            orden = self.ranking(scores, solo_positivos=True)
            for d in orden[:top_k]:
                extra_meta[d] = {
                    "bm25_score": round(rrf_data["bm25_scores"].get(d, 0.0), 4),
                    "sbert_score": round(rrf_data["sbert_scores"].get(d, 0.0), 4),
                    "bm25_rank": rrf_data["bm25_rank"].get(d, None),
                    "sbert_rank": rrf_data["sbert_rank"].get(d, None),
                }
        elif motor in ("rerank", "cross-encoder"):
            q_tokens = self.preprocesar(consulta)
            rrf_data = self.scores_rrf(consulta, k_rrf=60, profundidad=10, q_tokens=q_tokens)
            cand_orden = self.ranking(rrf_data["scores"], solo_positivos=True)[:cand_rerank]
            if not cand_orden:
                cand_orden = self.ids[:cand_rerank]
            if self.cross_encoder is not None:
                pares = [(consulta, self.texto_limpio_map[d]) for d in cand_orden]
                ce_scores = self.cross_encoder.predict(pares, show_progress_bar=False)
                pares_ord = sorted(
                    zip(ce_scores, cand_orden), key=lambda x: (-float(x[0]), x[1])
                )
                orden = [d for _, d in pares_ord]
                scores = {d: float(s) for s, d in pares_ord}
            else:
                orden = cand_orden
                scores = rrf_data["scores"]
            for d in orden[:top_k]:
                extra_meta[d] = {
                    "rrf_score": round(rrf_data["scores"].get(d, 0.0), 5),
                    "bm25_score": round(rrf_data["bm25_scores"].get(d, 0.0), 4),
                    "sbert_score": round(rrf_data["sbert_scores"].get(d, 0.0), 4),
                    "bm25_rank": rrf_data["bm25_rank"].get(d, None),
                    "sbert_rank": rrf_data["sbert_rank"].get(d, None),
                }
        else:
            raise ValueError(f"Motor desconocido: {motor}")

        latencia_ms = (time.perf_counter() - t0) * 1000.0

        resultados = []
        for rank_idx, doc_id in enumerate(orden[:top_k], start=1):
            doc = self.doc_map[doc_id]
            item = {
                "rank": rank_idx,
                "id": doc_id,
                "titulo": doc["titulo"],
                "categoria": doc["categoria"],
                "score": round(float(scores.get(doc_id, 0.0)), 5),
                "texto": doc["texto"],
                "snippet": doc["texto"][:220] + ("..." if len(doc["texto"]) > 220 else ""),
                "num_palabras": doc["num_palabras"],
                "fuente_url": doc["fuente_url"],
                "tokens_coincidentes": sorted(
                    list(set(q_tokens) & set(self.tokens_map[doc_id]))
                ),
            }
            if doc_id in extra_meta:
                item["detalles_hibrido"] = extra_meta[doc_id]
            resultados.append(item)

        return {
            "motor": motor,
            "consulta": consulta,
            "tokens_consulta": q_tokens,
            "latencia_ms": round(latencia_ms, 3),
            "total_recuperados": len(orden),
            "resultados": resultados,
        }

    # --- EVALUACIÓN DE CALIDAD IR (nDCG@5, MRR, Recall@5) ---

    @staticmethod
    def ndcg_at_k(ranking_ids: List[str], q: str, k: int = 5) -> float:
        rel = QRELS_CORPUS60.get(q, {})
        if not rel:
            return 0.0
        dcg = sum(
            (2 ** rel.get(d, 0) - 1) / math.log2(i + 2)
            for i, d in enumerate(ranking_ids[:k])
        )
        ideal = sorted(rel.values(), reverse=True)[:k]
        idcg = sum((2**g - 1) / math.log2(i + 2) for i, g in enumerate(ideal))
        return dcg / idcg if idcg > 0 else 0.0

    @staticmethod
    def mrr_score(ranking_ids: List[str], q: str) -> float:
        rel = QRELS_CORPUS60.get(q, {})
        return next(
            (1.0 / (i + 1) for i, d in enumerate(ranking_ids) if rel.get(d, 0) > 0),
            0.0,
        )

    @staticmethod
    def recall_at_k(ranking_ids: List[str], q: str, k: int = 5) -> float:
        rel = {d for d, g in QRELS_CORPUS60.get(q, {}).items() if g > 0}
        if not rel:
            return 0.0
        return len(rel & set(ranking_ids[:k])) / len(rel)

    def evaluar_todos_los_motores(self, k: int = 5) -> Dict[str, Any]:
        motores_eval = [
            ("tfidf", "Motor 1A: TF-IDF (Tarea 1 - Léxico)"),
            ("bm25", "Motor 1B: BM25 Okapi (Tarea 1 - Léxico)"),
            ("sbert", "Motor 2: SBERT Denso (Tarea 2 - Semántico)"),
            ("lineal", "Motor 3 (Var): Híbrido Lineal min-max (α=0.4)"),
            ("rrf", "Motor 3A: Híbrido RRF BM25+SBERT (Tarea 3)"),
            ("rerank", "Motor 3B: Híbrido RRF + Cross-Encoder (Tarea 3)"),
        ]
        detalle_por_consulta = []
        resumen_motores = []

        for cod, nombre in motores_eval:
            ndcgs, mrrs, recalls = [], [], []
            por_tipo = {"lexica": [], "semantica": [], "mixta": []}
            latencias = []

            for q in QRELS_CORPUS60:
                res = self.buscar_motor(q, motor=cod, top_k=10)
                latencias.append(res["latencia_ms"])
                r_ids = [item["id"] for item in res["resultados"]]
                n_val = self.ndcg_at_k(r_ids, q, k=k)
                m_val = self.mrr_score(r_ids, q)
                rec_val = self.recall_at_k(r_ids, q, k=k)

                ndcgs.append(n_val)
                mrrs.append(m_val)
                recalls.append(rec_val)
                t_q = TIPO_CONSULTA[q]
                por_tipo[t_q].append(n_val)

                detalle_por_consulta.append(
                    {
                        "codigo_motor": cod,
                        "motor": nombre,
                        "consulta": q,
                        "tipo": t_q,
                        "ndcg_5": round(n_val, 4),
                        "mrr": round(m_val, 4),
                        "recall_5": round(rec_val, 4),
                        "latencia_ms": round(res["latencia_ms"], 3),
                        "top_5_ids": r_ids[:5],
                    }
                )

            resumen_motores.append(
                {
                    "codigo": cod,
                    "nombre": nombre,
                    "ndcg_5": round(float(np.mean(ndcgs)), 4),
                    "mrr": round(float(np.mean(mrrs)), 4),
                    "recall_5": round(float(np.mean(recalls)), 4),
                    "ndcg_lexica": round(float(np.mean(por_tipo["lexica"])), 4),
                    "ndcg_semantica": round(float(np.mean(por_tipo["semantica"])), 4),
                    "ndcg_mixta": round(float(np.mean(por_tipo["mixta"])), 4),
                    "latencia_media_ms": round(float(np.mean(latencias)), 3),
                }
            )

        return {
            "num_consultas": len(QRELS_CORPUS60),
            "num_documentos": self.N,
            "resumen": resumen_motores,
            "detalle": detalle_por_consulta,
        }
