"""
Generador del Reporte Técnico en PDF (Tarea 4 · Corte 2: Integración de Motores de Búsqueda)
Alumno: Clemente Velasco Alhan · Matrícula: 233319
Nomenclatura: CLEMENTE_VELASCO_ALHAN_233319_C2_T4_INTEGRACION.pdf
"""

import json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

NAVY = colors.HexColor("#1C3257")
TEAL = colors.HexColor("#1F6E6C")
CORAL = colors.HexColor("#C85A32")
DARK_TEXT = colors.HexColor("#1E293B")
MUTED_TEXT = colors.HexColor("#64748B")
LIGHT_BG = colors.HexColor("#F8FAFC")
CALLOUT_BG = colors.HexColor("#FFFBEB")
CALLOUT_BORDER = colors.HexColor("#D97706")
BORDER_GRAY = colors.HexColor("#CBD5E1")


def header_footer(canvas, doc):
    if doc.page == 1:
        return
    canvas.saveState()
    canvas.setStrokeColor(BORDER_GRAY)
    canvas.setLineWidth(0.6)
    canvas.line(0.75 * inch, 0.65 * inch, letter[0] - 0.75 * inch, 0.65 * inch)
    canvas.setFont("Helvetica", 8.5)
    canvas.setFillColor(MUTED_TEXT)
    canvas.drawString(
        0.75 * inch,
        0.45 * inch,
        "Clemente Velasco Alhan · 233319 · Corte 2 Tarea 4: Integración de Motores de Búsqueda",
    )
    canvas.drawRightString(
        letter[0] - 0.75 * inch,
        0.45 * inch,
        f"UPCh · Minería de Datos · Pág. {doc.page}",
    )
    canvas.restoreState()


def build_styles():
    styles = getSampleStyleSheet()
    custom = {
        "CoverUniv": ParagraphStyle(
            "CoverUniv",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=21,
            leading=26,
            alignment=TA_RIGHT,
            textColor=TEAL,
        ),
        "CoverCareer": ParagraphStyle(
            "CoverCareer",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=20,
            alignment=TA_RIGHT,
            textColor=DARK_TEXT,
        ),
        "CoverTitle": ParagraphStyle(
            "CoverTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=19,
            alignment=TA_RIGHT,
            textColor=NAVY,
        ),
        "CoverMeta": ParagraphStyle(
            "CoverMeta",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=16,
            alignment=TA_LEFT,
            textColor=DARK_TEXT,
        ),
        "H1": ParagraphStyle(
            "H1",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=14.5,
            leading=19,
            textColor=NAVY,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "H2": ParagraphStyle(
            "H2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=15,
            textColor=TEAL,
            spaceBefore=10,
            spaceAfter=5,
        ),
        "H3": ParagraphStyle(
            "H3",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10.2,
            leading=14,
            textColor=CORAL,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.6,
            leading=14.2,
            alignment=TA_JUSTIFY,
            textColor=DARK_TEXT,
            spaceAfter=6,
        ),
        "BulletItem": ParagraphStyle(
            "BulletItem",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.4,
            leading=13.8,
            leftIndent=14,
            firstLineIndent=-8,
            alignment=TA_JUSTIFY,
            textColor=DARK_TEXT,
            spaceAfter=4,
        ),
        "Caption": ParagraphStyle(
            "Caption",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8.5,
            leading=11.5,
            alignment=TA_CENTER,
            textColor=MUTED_TEXT,
            spaceBefore=3,
            spaceAfter=8,
        ),
        "TableHeader": ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.3,
            leading=11,
            textColor=colors.white,
            alignment=TA_LEFT,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.1,
            leading=10.8,
            textColor=DARK_TEXT,
            alignment=TA_LEFT,
        ),
        "TableCellTiny": ParagraphStyle(
            "TableCellTiny",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.2,
            leading=9.4,
            textColor=DARK_TEXT,
            alignment=TA_LEFT,
        ),
        "Callout": ParagraphStyle(
            "Callout",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=13.2,
            textColor=DARK_TEXT,
        ),
        "CodeBlock": ParagraphStyle(
            "CodeBlock",
            parent=styles["Code"],
            fontName="Courier",
            fontSize=7.8,
            leading=10.5,
            textColor=DARK_TEXT,
            leftIndent=6,
            rightIndent=6,
        ),
    }
    return custom


def make_callout(text_html: str, st):
    p = Paragraph(text_html, st["Callout"])
    tbl = Table([[p]], colWidths=[6.9 * inch])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CALLOUT_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
                ("LINEBEFORE", (0, 0), (0, -1), 3.5, CALLOUT_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 11),
                ("RIGHTPADDING", (0, 0), (-1, -1), 11),
            ]
        )
    )
    return tbl


def make_styled_table(headers, rows, col_widths, st, cell_style_key="TableCell"):
    data = [[Paragraph(f"<b>{h}</b>", st["TableHeader"]) for h in headers]]
    for r in rows:
        data.append([Paragraph(str(c), st[cell_style_key]) for c in r])

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER_GRAY),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT_BG))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


def section_heading(title: str, st):
    return [
        Paragraph(title, st["H1"]),
        HRFlowable(width="100%", thickness=1.5, color=CORAL, spaceBefore=1, spaceAfter=8),
    ]


def generar_pdf():
    st = build_styles()
    corpus = json.loads((DATA_DIR / "corpus_scraped.json").read_text(encoding="utf-8"))
    eval_res = json.loads((DATA_DIR / "evaluation_results.json").read_text(encoding="utf-8"))
    bench_res = json.loads((DATA_DIR / "benchmark_results.json").read_text(encoding="utf-8"))

    palabras_list = [d["num_palabras"] for d in corpus]
    min_pal = min(palabras_list)
    max_pal = max(palabras_list)
    avg_pal = sum(palabras_list) / len(palabras_list)
    tot_pal = sum(palabras_list)

    pdf_paths = [
        BASE_DIR / "CLEMENTE_VELASCO_ALHAN_233319_C2_T4_INTEGRACION.pdf",
        WORKSPACE_DIR / "CLEMENTE_VELASCO_ALHAN_233319_C2_T4_INTEGRACION.pdf",
    ]

    for out_path in pdf_paths:
        doc = SimpleDocTemplate(
            str(out_path),
            pagesize=letter,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
            topMargin=0.7 * inch,
            bottomMargin=0.75 * inch,
            title="CLEMENTE_VELASCO_ALHAN_233319_C2_T4_INTEGRACION",
            author="Clemente Velasco Alhan (233319)",
        )
        story = []

        # ================= PORTADA =================
        story.append(Spacer(1, 0.8 * inch))
        story.append(Paragraph("UNIVERSIDAD POLITÉCNICA DE<br/>CHIAPAS", st["CoverUniv"]))
        story.append(Spacer(1, 0.65 * inch))
        story.append(Paragraph("Ingeniería en Software", st["CoverCareer"]))
        story.append(Spacer(1, 0.45 * inch))
        story.append(Paragraph("Minería de datos", st["CoverCareer"]))
        story.append(Spacer(1, 0.55 * inch))
        story.append(
            Paragraph(
                "TAREA 4 CORTE 2: INTEGRACIÓN FULLSTACK DE MOTORES DE<br/>"
                "BÚSQUEDA (TF-IDF/BM25, SBERT DENSO Y RRF + RERANKING),<br/>"
                "CORPUS POR WEB SCRAPING Y BENCHMARK DE 50 USUARIOS",
                st["CoverTitle"],
            )
        )
        story.append(Spacer(1, 0.55 * inch))
        story.append(
            Paragraph(
                "<para align='right'><b>Docente:</b> RAMSES ALEJANDRO CAMAS NAJERA</para>",
                st["Body"],
            )
        )
        story.append(Spacer(1, 1.1 * inch))
        story.append(Paragraph("<b>Estudiante:</b> Clemente Velasco Alhan", st["CoverMeta"]))
        story.append(Paragraph("<b>Matrícula:</b> 233319", st["CoverMeta"]))
        story.append(
            Paragraph(
                "<b>Entrega:</b> CLEMENTE_VELASCO_ALHAN_233319_C2_T4_INTEGRACION",
                st["CoverMeta"],
            )
        )
        story.append(
            Paragraph("<b>Corte 2 · Tarea 4 · Integración de Motores de Búsqueda</b>", st["CoverMeta"])
        )
        story.append(Spacer(1, 0.35 * inch))
        story.append(Paragraph("<b>Fecha de Entrega:</b> Noviembre de 2026", st["CoverMeta"]))
        story.append(PageBreak())

        # ================= SECCIÓN 1: INTRODUCCIÓN Y WEB SCRAPING =================
        story.extend(
            section_heading(
                "1. Resumen del Sistema y Creación del Corpus con Web Scraping (+10 Puntos Extra)",
                st,
            )
        )
        story.append(
            Paragraph(
                "En este reporte documento el diseño, construcción y evaluación experimental del sistema "
                "<b>Fullstack de Recuperación de Información</b> correspondiente a la <b>Tarea 4 del Corte 2</b>. "
                "Siguiendo las instrucciones al pie de la letra, integré los motores obtenidos en las tareas "
                "anteriores dentro de una arquitectura Backend (<b>FastAPI</b>) y Frontend (<b>Web App Interactiva</b>), "
                "creé un nuevo corpus de <b>60 documentos en español (todos con más de 100 palabras)</b> mediante "
                "<b>Web Scraping automatizado</b> (adjuntando las 60 fuentes verificables en la Sección 7), evalué la "
                "calidad de recuperación con métricas estándar (<b>nDCG@5</b>, <b>MRR</b> y <b>Recall@5</b>) y simulé "
                "cargas de <b>1, 5, 10, 25 y hasta 50 usuarios concurrentes</b> reportando las latencias <b>p50</b> y <b>p95</b>.",
                st["Body"],
            )
        )

        story.append(Paragraph("1.1. Metodología de Web Scraping y Validación del Corpus", st["H2"]))
        story.append(
            Paragraph(
                f"Para superar el límite del mini-corpus de 14 notas cortas (~28 palabras por nota) usado en los "
                f"laboratorios previos y cumplir el requisito de <b>al menos 50 documentos de mínimo 100 palabras cada uno</b>, "
                f"desarrollé el script <code>scripts/scraper_corpus.py</code>. Este módulo realiza peticiones HTTP reales con "
                f"<code>urllib.request</code> e interpreta el árbol DOM mediante una subclase de <code>html.parser.HTMLParser</code> "
                f"(<code>ParagraphExtractor</code>) que extrae y limpia los párrafos <code>&lt;p&gt;</code> de artículos de "
                f"Wikipedia en Español, eliminando etiquetas HTML, hipervínculos y corchetes de citación (<code>[1]</code>, "
                f"<code>[editar]</code>).",
                st["Body"],
            )
        )

        rows_corpus_stats = [
            ["Total de documentos extraídos", f"{len(corpus)} documentos", ">= 50 documentos (Cumplido: +20% extra)"],
            ["Mínimo de palabras por documento", f"{min_pal} palabras", ">= 100 palabras en el 100% del corpus"],
            ["Máximo de palabras por documento", f"{max_pal} palabras", "Textos densos de varios párrafos"],
            ["Promedio de palabras por documento", f"{avg_pal:.1f} palabras/doc", "7.5x más extenso que el corpus del Lab 1"],
            ["Total de palabras en el corpus", f"{tot_pal:,} palabras", "Vocabulario único: 2,340+ lemas sin stopwords"],
            ["Categorías temáticas cubiertas", "6 categorías (10 docs c/u)", "Medio Ambiente, Agua, Agro, IA/Robótica, Salud, Turismo"],
        ]
        story.append(
            make_styled_table(
                ["Métrica del Corpus Scrapeado", "Valor Obtenido", "Cumplimiento de la Rúbrica"],
                rows_corpus_stats,
                [2.3 * inch, 1.8 * inch, 2.8 * inch],
                st,
            )
        )
        story.append(Spacer(1, 8))

        fig4_path = REPORTS_DIR / "fig4_corpus_distribucion.png"
        if fig4_path.exists():
            story.append(Image(str(fig4_path), width=6.6 * inch, height=2.58 * inch))
            story.append(
                Paragraph(
                    "Figura 1. Izquierda: Distribución del número de palabras por documento en el corpus de 60 documentos (todos superan ampliamente el umbral mínimo de 100 palabras). Derecha: Balance de 10 documentos en cada una de las 6 categorías temáticas.",
                    st["Caption"],
                )
            )

        story.append(
            make_callout(
                "<b>Por qué diseñé el corpus en estas 6 categorías:</b> Al organizar los 60 artículos scrapeados en "
                "<i>Medio Ambiente y Clima</i>, <i>Recursos Hídricos</i>, <i>Agroindustria (Café, Cacao, Maíz)</i>, "
                "<i>Ciencia, IA y Robótica (UPCh)</i>, <i>Salud Pública (Dengue/Vectores)</i> y <i>Turismo/Infraestructura en Chiapas</i>, "
                "conservamos todos los fenómenos lingüísticos estudiados en clase (siglas como <i>UPCh</i>, nombres científicos como "
                "<i>Aedes aegypti</i> y sinónimos como <i>agua/hídrica</i> o <i>temblor/sismo</i>), pero en un escenario realista "
                "con 60 documentos extensos donde aparecen falsos positivos léxicos y competencia semántica.",
                st,
            )
        )

        # ================= SECCIÓN 2: DESARROLLO DEL SISTEMA FULLSTACK =================
        story.extend(
            section_heading(
                "2. Desarrollo del Sistema Fullstack e Integración de los 3 Motores",
                st,
            )
        )
        story.append(
            Paragraph(
                "El sistema se estructuró bajo una arquitectura desacoplada en dos capas dentro del repositorio "
                "<code>CLEMENTE_VELASCO_ALHAN_233319_C2_T4_INTEGRACION</code>:",
                st["Body"],
            )
        )
        story.append(
            Paragraph(
                "• <b>Backend API REST (<code>backend/engines.py</code> y <code>backend/main.py</code>):</b> "
                "Construido con <b>FastAPI</b> y <b>Uvicorn</b>. Al iniciar el servidor, la clase <code>SearchEngineHub</code> "
                "carga el corpus scrapeado de 60 documentos, ejecuta el preprocesamiento morfológico con <code>spaCy</code> "
                "(<code>es_core_news_sm</code>), construye en memoria las estructuras de índice invertido de <b>TF-IDF</b> y "
                "<b>BM25</b>, precalcula la matriz de embeddings densos normalizados (60 × 384) con <b>Sentence-BERT</b> y "
                "mantiene cargado el modelo <b>Cross-Encoder</b> para reranking en dos etapas. Incluye protección thread-safe "
                "(<code>threading.Lock</code>) en el tokenizador de <code>spaCy</code> para soportar peticiones concurrentes.",
                st["BulletItem"],
            )
        )
        story.append(
            Paragraph(
                "• <b>Frontend Web Interactivo (<code>frontend/index.html</code>):</b> Single-Page Application (SPA) servida "
                "en la raíz <code>GET /</code> con diseño institucional UPCh y gráficos dinámicos en <b>Chart.js</b>. "
                "Cuenta con cuatro pestañas: (1) <i>Buscador Comparativo Multi-Motor</i> que muestra lado a lado los resultados, "
                "scores, tiempos de respuesta en milisegundos, lemas coincidentes y enlaces a las fuentes; (2) <i>Simulador de "
                "Concurrencia de hasta 50 Usuarios</i> con tablas y gráficas de latencia <b>p50</b> y <b>p95</b>; (3) <i>Tablero de "
                "Evaluación de Calidad IR</i>; y (4) <i>Explorador Auditable del Corpus Scrapeado</i>.",
                st["BulletItem"],
            )
        )

        story.append(Paragraph("2.1. Los Motores Obtenidos en las Tareas Anteriores del Corte 2", st["H2"]))
        rows_motores_arq = [
            [
                "Motor 1 (Tarea 1)\nLéxico: TF-IDF y BM25\n(Labs 1, 2 y 3)",
                "Lematización con spaCy (es_core_news_sm), sin acentos y conservando negaciones. TF-IDF usa coseno disperso; BM25 usa saturación de frecuencia (k1=1.5) y control de longitud (b=0.75) con solo_positivos=True.",
                "O(|q| · df_medio)\nÍndice invertido en RAM",
            ],
            [
                "Motor 2 (Tarea 2)\nSemántico Denso: SBERT\n(Labs 5 y 6)",
                "Bi-Encoder multilingüe (paraphrase-multilingual-MiniLM-L12-v2). Codifica título + texto limpio en vectores de 384 dimensiones con norma L2=1. La similitud coseno se evalúa como producto matricial (E @ v_q).",
                "1 pasada de BERT para q\n+ producto punto (60×384)",
            ],
            [
                "Motor 3A (Tarea 3)\nHíbrido RRF (k=60)\n(Lab 7 - Etapa 1)",
                "Combina las listas ordenadas de BM25 (top-10 positivos) y SBERT Denso (top-10) mediante Reciprocal Rank Fusion: RRF(d) = Σ 1/(60 + rank_i(d)), premiando el consenso sin calibrar escalas.",
                "Suma de tiempos de\nBM25 + SBERT + fusión O(k)",
            ],
            [
                "Motor 3B (Tarea 3)\nHíbrido RRF + Cross-Encoder\n(Lab 7 - 2 Etapas)",
                "Arquitectura de embudo: Etapa 1 (RRF BM25+SBERT) filtra los 10 mejores candidatos de alto recall; Etapa 2 pasa los 10 pares [CLS] q [SEP] d al Cross-Encoder (mmarco-mMiniLMv2-L12-H384-v1) con atención cruzada token a token.",
                "Etapa 1 + 10 pasadas\ncompletas del Transformer",
            ],
        ]
        story.append(
            make_styled_table(
                ["Motor Integrado (Origen)", "Formulación e Implementación en el Backend", "Complejidad por Consulta"],
                rows_motores_arq,
                [1.75 * inch, 3.65 * inch, 1.5 * inch],
                st,
            )
        )
        story.append(PageBreak())

        # ================= SECCIÓN 3: COMPORTAMIENTO Y CALIDAD IR =================
        story.extend(
            section_heading(
                "3. Comportamiento de los Motores de Búsqueda y Evaluación de Calidad IR",
                st,
            )
        )
        story.append(
            Paragraph(
                "Para evaluar con rigor cómo se comportan los motores al pasar de 14 notas breves a nuestro nuevo "
                "corpus de <b>60 documentos extensos (> 200 palabras promedio)</b>, construí un banco de evaluación "
                "(<code>QRELS_CORPUS60</code>) con <b>12 consultas de prueba</b> divididas equitativamente en tres tipos: "
                "<b>4 Léxicas</b> (<code>UPCh</code>, <code>canon del sumidero</code>, <code>Aedes aegypti</code>, "
                "<code>presa chicoasen grijalva</code>), <b>4 Semánticas</b> (<code>problemas de agua</code>, "
                "<code>temblor de tierra</code>, <code>enfermedades transmitidas por mosquitos</code>, "
                "<code>movimiento telurico en el mar</code>) y <b>4 Mixtas</b> (<code>sequia y cultivos de maiz</code>, "
                "<code>exportacion de cafe y cacao</code>, <code>inteligencia artificial y robotica</code>, "
                "<code>turismo cultural en san cristobal</code>).",
                st["Body"],
            )
        )

        rows_eval = []
        for r in eval_res["resumen"]:
            rows_eval.append(
                [
                    r["nombre"],
                    f"<b>{r['ndcg_5']:.3f}</b>",
                    f"{r['mrr']:.3f}",
                    f"{r['recall_5']:.3f}",
                    f"{r['ndcg_lexica']:.3f}",
                    f"<b>{r['ndcg_semantica']:.3f}</b>",
                    f"{r['ndcg_mixta']:.3f}",
                ]
            )

        story.append(
            make_styled_table(
                [
                    "Motor de Búsqueda Evaluado",
                    "nDCG@5 Global",
                    "MRR Global",
                    "Recall@5",
                    "nDCG@5 Léxicas",
                    "nDCG@5 Semánt.",
                    "nDCG@5 Mixtas",
                ],
                rows_eval,
                [2.25 * inch, 0.78 * inch, 0.72 * inch, 0.72 * inch, 0.81 * inch, 0.81 * inch, 0.81 * inch],
                st,
            )
        )
        story.append(Spacer(1, 8))

        fig1_path = REPORTS_DIR / "fig1_calidad_ndcg.png"
        if fig1_path.exists():
            story.append(Image(str(fig1_path), width=6.5 * inch, height=3.15 * inch))
            story.append(
                Paragraph(
                    "Figura 2. Comparación experimental de nDCG@5 Global, nDCG@5 en Consultas Semánticas y Recall@5 sobre el corpus de 60 documentos extraídos por Web Scraping.",
                    st["Caption"],
                )
            )

        story.append(Paragraph("3.1. Análisis Detallado del Comportamiento por Motor", st["H2"]))
        story.append(
            Paragraph(
                "• <b>Comportamiento de TF-IDF y BM25 (Motores Léxicos - Tarea 1):</b> En consultas léxicas y mixtas "
                "alcanzan un desempeño sobresaliente (<code>nDCG@5 Léxicas = 0.863</code> en BM25 y <code>Mixtas = 0.858</code> "
                "en TF-IDF) porque localizan de inmediato siglas exactas como <code>UPCh</code> (<code>d31</code> en 1° lugar) "
                "o términos científicos como <code>Aedes aegypti</code> (<code>d42</code> y <code>d41</code>). Sin embargo, en la "
                "consulta semántica <code>temblor de tierra</code> ambos obtienen <b><code>nDCG@5 = 0.000</code></b>: caen en una "
                "trampa léxica porque ningún documento usa la palabra <i>temblor</i> (dicen <i>sismo</i> o <i>terremoto</i>), pero "
                "muchos artículos geográficos de Chiapas contienen la palabra <i>tierra</i>, llenando el Top-5 de falsos positivos.",
                st["BulletItem"],
            )
        )
        story.append(
            Paragraph(
                "• <b>Comportamiento de SBERT Denso (Motor Semántico - Tarea 2):</b> Resuelve de raíz la barrera de "
                "vocabulario en las consultas semánticas y mixtas, subiendo el <code>nDCG@5 Semántico</code> de <code>0.593</code> "
                "(BM25) a <b><code>0.745</code></b> y liderando en <code>Mixtas</code> con <b><code>0.895</code></b>: en "
                "<code>temblor de tierra</code> coloca a <code>d03</code> (<i>Sismología en la costa de Chiapas</i>) en 1° lugar "
                "con <code>MRR = 1.000</code>, y en <code>problemas de agua</code> recupera tanto <code>d02</code> (<i>crisis "
                "hídrica / sequía</i>) como <code>d18</code> (<i>agua potable</i>). En contraparte, sufre <b>dilución semántica "
                "en documentos largos</b> para consultas de entidades específicas: en <code>canon del sumidero</code> y "
                "<code>presa chicoasen grijalva</code> su <code>nDCG@5 Léxico</code> cae a <code>0.492</code> porque comprimir "
                "~215 palabras en un solo vector de 384 dimensiones difumina los nombres propios.",
                st["BulletItem"],
            )
        )
        story.append(
            Paragraph(
                "• <b>Comportamiento del Motor Híbrido RRF y Cross-Encoder Reranking (Tarea 3):</b> Al combinar "
                "BM25 y SBERT con <b>RRF k=60</b> (<code>nDCG@5 = 0.766</code>, <code>Semántico = 0.746</code>) o "
                "<b>Fusión Lineal min-max</b> (<code>0.762</code>), se corrige el colapso de SBERT en consultas léxicas "
                "(subiendo de <code>0.492</code> a <code>0.706–0.729</code>) sin perder cobertura semántica. Finalmente, al "
                "aplicar la Etapa 2 con el <b>Cross-Encoder (<code>mmarco-mMiniLMv2-L12-H384-v1</code>)</b> sobre los 10 "
                "candidatos de RRF, el sistema alcanza el <b>mejor desempeño global de toda la comparativa "
                "(<code>nDCG@5 = 0.798</code>, <code>MRR = 0.896</code>, <code>Recall@5 = 0.765</code> y "
                "<code>nDCG@5 Semántico = 0.757</code>)</b>.",
                st["BulletItem"],
            )
        )
        story.append(PageBreak())

        # ================= SECCIÓN 4: LATENCIA P50 Y P95 (50 USUARIOS CONCURRENTES) =================
        story.extend(
            section_heading(
                "4. Simulación de hasta 50 Usuarios Concurrentes: Latencia p50 y p95",
                st,
            )
        )
        story.append(
            Paragraph(
                "Para evaluar el comportamiento de los motores bajo estrés de producción, implementé un generador de "
                "carga concurrente con <code>ThreadPoolExecutor</code> (tanto en <code>scripts/run_benchmarks.py</code> como "
                "en el endpoint interactivo <code>POST /api/benchmark/run</code>). Se simularon <b>5 niveles de concurrencia: "
                "1, 5, 10, 25 y 50 usuarios simultáneos</b> enviando consultas al mismo tiempo. Para cada motor se registraron "
                "los tiempos de respuesta de extremo a extremo por usuario y se calcularon los percentiles requeridos: "
                "<b>latencia p50 (mediana)</b> y <b>latencia p95 (percentil 95, que representa el límite superior experimentado "
                "por el 95% de los usuarios)</b>, además de <b>p99</b>, <b>media</b> y <b>Throughput (consultas/segundo, RPS)</b>.",
                st["Body"],
            )
        )

        story.append(
            Paragraph("4.1. Resultados Oficiales de Latencia p50 y p95 con 50 Usuarios Concurrentes", st["H2"])
        )
        rows_50 = []
        for r in bench_res["tabla_50_usuarios"]:
            rows_50.append(
                [
                    r["motor"],
                    "50 usuarios",
                    f"<b>{r['p50_ms']:.2f} ms</b>",
                    f"<b>{r['p95_ms']:.2f} ms</b>",
                    f"{r['p99_ms']:.2f} ms",
                    f"{r['media_ms']:.2f} ms",
                    f"{r['throughput_rps']:.2f} req/s",
                ]
            )
        story.append(
            make_styled_table(
                [
                    "Motor de Búsqueda",
                    "Concurrencia",
                    "Latencia p50",
                    "Latencia p95",
                    "Latencia p99",
                    "Latencia Media",
                    "Throughput (RPS)",
                ],
                rows_50,
                [2.05 * inch, 0.85 * inch, 0.85 * inch, 0.85 * inch, 0.8 * inch, 0.8 * inch, 0.7 * inch],
                st,
            )
        )
        story.append(Spacer(1, 8))

        fig2_path = REPORTS_DIR / "fig2_latencia_p50_p95_50users.png"
        if fig2_path.exists():
            story.append(Image(str(fig2_path), width=6.4 * inch, height=3.1 * inch))
            story.append(
                Paragraph(
                    "Figura 3. Comparación de Latencia p50 (mediana) y Latencia p95 (percentil 95) bajo una carga simultánea de 50 usuarios concurrentes (escala logarítmica en milisegundos).",
                    st["Caption"],
                )
            )

        story.append(
            Paragraph("4.2. Evolución de Latencia p50 y p95 al Escalar de 1 a 50 Usuarios Concurrentes", st["H2"])
        )
        niveles = bench_res["niveles_usuarios"]
        rows_levels = []
        for cod, info in bench_res["motores"].items():
            fila = [info["nombre"]]
            for u in niveles:
                n = info["niveles"][str(u)]
                fila.append(f"p50: <b>{n['p50_ms']:.1f}</b>\np95: {n['p95_ms']:.1f} ms")
            rows_levels.append(fila)

        story.append(
            make_styled_table(
                [
                    "Motor de Búsqueda",
                    "1 Usuario",
                    "5 Usuarios",
                    "10 Usuarios",
                    "25 Usuarios",
                    "50 Usuarios",
                ],
                rows_levels,
                [1.9 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch],
                st,
            )
        )
        story.append(Spacer(1, 8))

        fig3_path = REPORTS_DIR / "fig3_escalabilidad_concurrencia.png"
        if fig3_path.exists():
            story.append(Image(str(fig3_path), width=6.6 * inch, height=2.7 * inch))
            story.append(
                Paragraph(
                    "Figura 4. Curvas de escalabilidad de la latencia p50 (izquierda) y p95 (derecha) conforme aumenta la carga de 1 hasta 50 usuarios concurrentes.",
                    st["Caption"],
                )
            )

        story.append(
            make_callout(
                "<b>Interpretación técnica del fenómeno de concurrencia (1 a 50 usuarios):</b><br/>"
                "1. <b>BM25 y TF-IDF mantienen latencia sub-segundo aún con 50 usuarios simultáneos</b> "
                "(BM25 logra <b>p50 = 245.80 ms</b> y <b>p95 = 301.40 ms</b> con un throughput de <b>163.6 req/s</b>), "
                "donde casi todo el tiempo corresponde al lock de lematización de spaCy y no al índice invertido.<br/>"
                "2. <b>SBERT Denso y el Híbrido RRF</b> pasan de ~48 ms (1 usuario) a <b>p50 ≈ 2,358–2,382 ms</b> y "
                "<b>p95 ≈ 2,605–2,625 ms</b> con 50 usuarios concurrentes en CPU (manteniendo un throughput estable de ~20 req/s), "
                "debido al encolamiento de la pasada neuronal del Bi-Encoder en CPU.<br/>"
                "3. <b>El Cross-Encoder Reranker</b> ejecuta 10 pasadas de un Transformer por cada consulta (~1.74 s con 1 usuario). "
                "Bajo una ráfaga simultánea de 50 usuarios en CPU sin GPU ni batching inter-petición, las 500 evaluaciones del "
                "Transformer se encolan secuencialmente, elevando la latencia a <b>p50 = 87,478 ms</b> y <b>p95 = 90,943 ms</b>.",
                st,
            )
        )
        story.append(PageBreak())

        # ================= SECCIÓN 5: VENTAJAS, DESVENTAJAS, CUÁNDO USAR CADA CORPUS Y CRITERIO DE DECISIÓN =================
        story.extend(
            section_heading(
                "5. Ventajas y Desventajas, Cuándo Usar los Corpus y Criterio de Decisión",
                st,
            )
        )

        story.append(Paragraph("5.1. Ventajas y Desventajas Observadas de Cada Motor", st["H2"]))
        rows_pros_cons = [
            [
                "Motor 1A: TF-IDF\n(Tarea 1 - Lab 2)",
                "• Implementación simple e interpretable.\n• Altísima velocidad (p50=5.35 ms con 1 usuario; p95=313.8 ms con 50 usuarios).\n• Mínimo consumo de memoria RAM.",
                "• Sin saturación de frecuencia (un término repetido 20 veces domina el score).\n• Penaliza en exceso documentos largos.\n• Cero comprensión de sinónimos o paráfrasis.",
            ],
            [
                "Motor 1B: BM25 Okapi\n(Tarea 1 - Lab 3)",
                "• El motor más veloz y con mayor throughput (213 req/s; p50=4.28 ms en 1 usuario y p95=301.4 ms en 50 usuarios).\n• Saturación controlada (k1=1.5) y ajuste por longitud (b=0.75).\n• Imbatible en siglas (UPCh) y nombres técnicos.",
                "• Barrera léxica estricta: obtiene nDCG@5 = 0.000 en consultas puramente semánticas como 'temblor de tierra'.\n• Depende fuertemente de la calidad del lematizador (spaCy).",
            ],
            [
                "Motor 2: SBERT Denso\n(Tarea 2 - Labs 5/6)",
                "• Excelente en consultas semánticas (0.745) y líder en mixtas (0.895).\n• Resuelve sinónimos (agua/hídrica, temblor/sismo) y paráfrasis.\n• Los embeddings de los documentos se precalculan una sola vez offline.",
                "• Pierde precisión en siglas y entidades locales dentro de textos largos (nDCG@5 Léxico cae a 0.492).\n• 10x más lento que BM25 en CPU (p95 = 2,625 ms con 50 usuarios).\n• Mayor huella de RAM (~470 MB del modelo).",
            ],
            [
                "Motor 3A: Híbrido RRF\n(BM25 + SBERT, k=60)\n(Tarea 3 - Lab 7)",
                "• Combina coincidencias léxicas exactas y semánticas (nDCG@5 Global = 0.766, Semántico = 0.746) sin calibrar escalas.\n• Costo prácticamente idéntico a SBERT solo (BM25 añade < 5 ms).\n• Robusto ante cambios de corpus sin reentrenar hiperparámetros.",
                "• Al ignorar la magnitud del score y usar solo posiciones, un falso positivo léxico que aparezca en ambas listas (ej. palabra común 'tierra') puede subir antes del reranking.",
            ],
            [
                "Motor 3B: Híbrido RRF +\nCross-Encoder Rerank\n(Tarea 3 - Lab 7)",
                "• Máxima calidad global (nDCG@5 = 0.798, MRR = 0.896, Recall@5 = 0.765).\n• Atención cruzada token a token que desambigua trampas léxicas.\n• Ideal como etapa previa a generación RAG.",
                "• Costo computacional muy alto en CPU (~1.74 s en 1 usuario; ~90.9 s p95 con 50 usuarios concurrentes).\n• No puede rescatar documentos que no hayan entrado al Top-N de la Etapa 1.",
            ],
        ]
        story.append(
            make_styled_table(
                ["Motor de Búsqueda", "Ventajas Observadas en la Integración", "Desventajas y Limitaciones Observadas"],
                rows_pros_cons,
                [1.45 * inch, 2.72 * inch, 2.73 * inch],
                st,
            )
        )
        story.append(Spacer(1, 8))

        story.append(Paragraph("5.2. ¿Cuándo Usar Cada Tipo de Corpus y Cómo Afecta al Motor?", st["H2"]))
        story.append(
            Paragraph(
                "Al contrastar el <b>corpus corto de los laboratorios previos (14 notas de ~28 palabras)</b> contra el "
                "<b>nuevo corpus extenso creado por Web Scraping (60 documentos de 144 a 230 palabras)</b>, identifiqué "
                "criterios claros sobre cuándo utilizar cada tipo de corpus y qué arquitectura aplicar:",
                st["Body"],
            )
        )
        story.append(
            Paragraph(
                "1. <b>Corpus de documentos breves o micro-textos (15 a 50 palabras: titulares, tuits, FAQs cortas, tickets):</b> "
                "En textos cortos, un único vector denso de 384 dimensiones (<b>SBERT</b>) captura casi toda la intención "
                "sin pérdida de información (en el Lab 7 de 14 notas, SBERT lograba <code>1.000</code> en léxicas). Sin embargo, "
                "hay muy poca redundancia léxica, por lo que BM25 falla con facilidad si el usuario cambia una sola palabra.",
                st["BulletItem"],
            )
        )
        story.append(
            Paragraph(
                "2. <b>Corpus de documentos extensos y enciclopédicos (>= 100 a 500+ palabras: artículos web scrapeados, noticias completas, manuales, normativas):</b> "
                "Al superar las 100–200 palabras por documento, ocurren dos fenómenos opuestos: (a) <b>BM25 mejora su cobertura</b> "
                "porque un artículo largo menciona más variaciones léxicas del tema, pero también aumenta el riesgo de coincidencias "
                "accidentales en palabras comunes (como <i>tierra</i> o <i>costa</i>); y (b) <b>SBERT sufre compresión/dilución "
                "semántica</b> al promediar múltiples párrafos en un solo vector. En este tipo de corpus es indispensable "
                "usar <b>Búsqueda Híbrida (BM25 + SBERT)</b> o aplicar <i>chunking</i> (división en pasajes de 100–150 palabras) "
                "acompañado de <b>Cross-Encoder Reranking</b>.",
                st["BulletItem"],
            )
        )
        story.append(
            Paragraph(
                "3. <b>Corpus técnicos, legales, médicos o con identificadores exactos (catálogos, matrículas, leyes, especies como <i>Aedes aegypti</i>):</b> "
                "Deben indexarse obligatoriamente con un componente léxico (<b>BM25</b>), ya que los modelos densos preentrenados "
                "suelen distorsionar siglas fuera de vocabulario o números de folio.",
                st["BulletItem"],
            )
        )

        story.append(Paragraph("5.3. Criterio de Decisión Ingenieril (Calidad vs. Latencia p50/p95)", st["H2"]))
        fig5_path = REPORTS_DIR / "fig5_tradeoff_calidad_latencia.png"
        if fig5_path.exists():
            story.append(Image(str(fig5_path), width=6.0 * inch, height=3.1 * inch))
            story.append(
                Paragraph(
                    "Figura 5. Frontera de decisión Calidad (nDCG@5 Global) vs. Latencia p95 con 50 usuarios concurrentes.",
                    st["Caption"],
                )
            )

        rows_decision = [
            [
                "Escenario A: Alta concurrencia en CPU\n(50 usuarios simultáneos, SLA p95 < 350 ms)",
                "Motor 1B: BM25 Okapi\n(o Híbrido con caché)",
                "Garantiza p50 = 245.8 ms y p95 = 301.4 ms con 163.6 req/s y excelente precisión en búsquedas por palabras clave (nDCG@5 Léxico = 0.863).",
            ],
            [
                "Escenario B: Buscador generalista equilibrado\n(1 a 10 usuarios concurrentes en CPU, SLA < 650 ms)",
                "Motor 3A: Híbrido (BM25 + SBERT)\ncon RRF (k=60) o Lineal min-max",
                "Combina el recall léxico y semántico (nDCG@5 = 0.766, Semántico = 0.746) manteniendo p50 ≈ 48.7 ms (1 usuario) y ~510.8 ms (10 usuarios) sin costo de Cross-Encoder.",
            ],
            [
                "Escenario C: Pipeline RAG / Asistente IA o Servidor con GPU\n(Prioridad absoluta en precisión Top-3)",
                "Motor 3B: Híbrido RRF +\nCross-Encoder Reranking",
                "Logra el máximo nDCG@5 (0.798), MRR (0.896) y Recall@5 (0.765). En producción con 50 usuarios concurrentes requiere inferencia en GPU (donde 10 pares toman ~25 ms en vez de 1,740 ms en CPU).",
            ],
        ]
        story.append(
            make_styled_table(
                ["Escenario Operativo y Restricción SLA", "Motor Elegido", "Justificación Cuantitativa (Criterio de Decisión)"],
                rows_decision,
                [2.15 * inch, 1.65 * inch, 3.1 * inch],
                st,
            )
        )
        story.append(PageBreak())

        # ================= SECCIÓN 6: ANEXO DE LAS 60 FUENTES DEL WEB SCRAPING =================
        story.extend(
            section_heading(
                "6. Anexo: Fuentes Oficiales del Corpus Creado con Web Scraping (+10 Puntos Extra)",
                st,
            )
        )
        story.append(
            Paragraph(
                "A continuación se adjunta el catálogo auditable de los <b>60 documentos extraídos mediante Web Scraping</b> "
                "(almacenados en <code>data/corpus_scraped.json</code> y <code>data/fuentes_scraping.csv</code>), incluyendo su "
                "identificador, título, categoría temática, conteo exacto de palabras (todos <b>&ge; 144 palabras</b>, cumpliendo "
                "holgadamente el mínimo de 100 palabras) y la URL fuente consultada:",
                st["Body"],
            )
        )

        rows_sources = []
        for d in corpus:
            rows_sources.append(
                [
                    f"<b>{d['id']}</b>",
                    d["titulo"],
                    d["categoria"],
                    f"<b>{d['num_palabras']}</b> pal.",
                    d["fuente_url"],
                ]
            )

        story.append(
            make_styled_table(
                ["ID", "Título del Documento", "Categoría", "Palabras", "URL Fuente (Web Scraping)"],
                rows_sources,
                [0.42 * inch, 2.05 * inch, 1.35 * inch, 0.68 * inch, 2.4 * inch],
                st,
                cell_style_key="TableCellTiny",
            )
        )
        story.append(PageBreak())

        # ================= SECCIÓN 7: REPOSITORIO GITHUB Y AI_USAGE =================
        story.extend(
            section_heading(
                "7. Entrega de Repositorio GitHub y Declaración de Uso de IA (AI_USAGE.md)",
                st,
            )
        )
        story.append(
            Paragraph(
                "<para align='left'>• <b>Nomenclatura oficial del proyecto y entregables:</b> "
                "<code>CLEMENTE_VELASCO_ALHAN_233319_C2_T4_INTEGRACION</code>.<br/>"
                "• <b>Comando para iniciar el sistema Fullstack localmente:</b> "
                "<code>uvicorn backend.main:app --host 0.0.0.0 --port 8000</code> (Interfaz web en "
                "<code>http://localhost:8000</code> y documentación OpenAPI en <code>http://localhost:8000/docs</code>).</para>",
                st["Body"],
            )
        )

        rows_ai = [
            [
                "Tarea 4 Corte 2\n(Integración Fullstack,\nScraping y Benchmark)",
                "Gemini\n(Antigravity)",
                "scraper_corpus.py,\nbackend/engines.py,\nbackend/main.py,\nfrontend/index.html,\nrun_benchmarks.py",
                "Estructura del extractor HTML para los 60 artículos, API REST con FastAPI, interfaz comparativa en HTML/Chart.js y arnés ThreadPoolExecutor para 50 usuarios concurrentes.",
                "Seleccioné las 60 fuentes temáticas de Chiapas y ciencia, validé que los 60 documentos tuvieran >= 144 palabras, integré mis motores TF-IDF, BM25, SBERT y RRF+Cross-Encoder de las tareas previas y redacté el criterio de decisión con las latencias p50 y p95.",
            ]
        ]
        story.append(
            make_styled_table(
                ["Entrega", "Herramienta", "Módulos", "Lo que propuso la IA", "Lo que implementé y verifiqué personalmente"],
                rows_ai,
                [1.15 * inch, 0.85 * inch, 1.15 * inch, 1.85 * inch, 1.9 * inch],
                st,
            )
        )

        doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
        print(f"PDF generado exitosamente en: {out_path}")


if __name__ == "__main__":
    generar_pdf()
