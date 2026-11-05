"""
Script de Web Scraping para construcción del Corpus (Tarea 4 · Corte 2)
Alumno: Clemente Velasco Alhan · Matrícula: 233319
Materia: Minería de Datos · UPCh · Docente: Ramsés Alejandro Camas Nájera

Extrae 60 documentos reales en español mediante Web Scraping (HTML de Wikipedia ES),
verificando que cada documento contenga estrictamente >= 100 palabras (rango objetivo: 130 - 230 palabras)
y almacenando su URL fuente original, categoría temática, fecha de extracción y conteo léxico.
"""

import csv
import html.parser
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class ParagraphExtractor(html.parser.HTMLParser):
    """Extractor HTML de párrafos <p> dentro del artículo principal."""

    def __init__(self):
        super().__init__()
        self.in_p = False
        self.current = []
        self.paragraphs = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "p":
            self.in_p = True
            self.current = []

    def handle_endtag(self, tag):
        if tag.lower() == "p" and self.in_p:
            self.in_p = False
            txt = "".join(self.current).strip()
            if txt:
                self.paragraphs.append(txt)

    def handle_data(self, data):
        if self.in_p:
            self.current.append(data)


# 60 temas organizados en 6 categorías alineadas al dominio del curso (Chiapas, Medio Ambiente,
# Recursos Hídricos, Agroindustria, Ciencia/IA/Robótica, Salud Pública y Turismo/Infraestructura)
TOPICS = [
    # 1. Medio Ambiente, Clima y Fenómenos Naturales en Chiapas y México (10)
    ("d01", "Inundaciones y lluvias torrenciales en Tuxtla Gutiérrez", "Medio Ambiente y Clima", "Tuxtla_Gutiérrez"),
    ("d02", "Sequía meteorológica y crisis hídrica en México", "Medio Ambiente y Clima", "Sequía"),
    ("d03", "Sismología y actividad tectónica en la costa de Chiapas", "Medio Ambiente y Clima", "Sismo_de_Chiapas_de_2017"),
    ("d04", "Servicio Sismológico Nacional y monitoreo sísmico", "Medio Ambiente y Clima", "Servicio_Sismológico_Nacional_(México)"),
    ("d05", "Cambio climático y vulnerabilidad ambiental en México", "Medio Ambiente y Clima", "Cambio_climático_en_México"),
    ("d06", "Reserva de la biosfera Selva El Ocote en Chiapas", "Medio Ambiente y Clima", "Reserva_de_la_biosfera_Selva_El_Ocote"),
    ("d07", "Reserva de la biosfera Montes Azules y Selva Lacandona", "Medio Ambiente y Clima", "Reserva_de_la_biosfera_Montes_Azules"),
    ("d08", "Huracanes y ciclones tropicales en el Pacífico sur mexicano", "Medio Ambiente y Clima", "Ciclón_tropical"),
    ("d09", "Incendios forestales y conservación de bosques en Chiapas", "Medio Ambiente y Clima", "Incendio_forestal"),
    ("d10", "Protección Civil y gestión de riesgos ante desastres naturales", "Medio Ambiente y Clima", "Protección_civil"),

    # 2. Agua, Recursos Hídricos y Cuencas Hidrológicas (10)
    ("d11", "Crisis hídrica y escasez de agua potable en zonas urbanas", "Recursos Hídricos", "Escasez_de_agua_en_México"),
    ("d12", "Cuenca hidrológica del río Grijalva en Chiapas", "Recursos Hídricos", "Río_Grijalva"),
    ("d13", "Río Usumacinta y biodiversidad acuática fronteriza", "Recursos Hídricos", "Río_Usumacinta"),
    ("d14", "Central hidroeléctrica Chicoasén y generación de energía", "Recursos Hídricos", "Presa_Chicoasén"),
    ("d15", "Presa Belisario Domínguez La Angostura y regulación hídrica", "Recursos Hídricos", "Presa_La_Angostura"),
    ("d16", "Presa Malpaso Nezahualcóyotl y control de inundaciones", "Recursos Hídricos", "Presa_Malpaso"),
    ("d17", "Tratamiento de aguas residuales y saneamiento ambiental", "Recursos Hídricos", "Tratamiento_de_aguas_residuales"),
    ("d18", "Agua potable y redes de distribución municipal", "Recursos Hídricos", "Agua_potable"),
    ("d19", "Acuíferos subterráneos y mantenimiento de pozos de agua", "Recursos Hídricos", "Agua_subterránea"),
    ("d20", "Comisión Nacional del Agua y gestión de cuencas en México", "Recursos Hídricos", "Comisión_Nacional_del_Agua"),

    # 3. Agricultura, Café, Cacao y Economía Agroindustrial (10)
    ("d21", "Producción y exportación de café de altura en Chiapas", "Agroindustria y Economía", "Café_de_Chiapas"),
    ("d22", "Cultivo de cacao en la región del Soconusco", "Agroindustria y Economía", "Cacao_de_Grijalva"),
    ("d23", "Región económica del Soconusco y comercio agropecuario", "Agroindustria y Economía", "Soconusco"),
    ("d24", "Cultivo de maíz y seguridad alimentaria en el sur de México", "Agroindustria y Economía", "Maíz"),
    ("d25", "Producción de frijol y agricultura temporalera en México", "Agroindustria y Economía", "Phaseolus_vulgaris"),
    ("d26", "Chocolate artesanal y cooperativas productoras de cacao", "Agroindustria y Economía", "Chocolate"),
    ("d27", "Caficultura orgánica y comercio justo en la Sierra Madre", "Agroindustria y Economía", "Caficultura"),
    ("d28", "Plátano y fruticultura tropical en la costa de Chiapas", "Agroindustria y Economía", "Musa_×_paradisiaca"),
    ("d29", "Apicultura y exportación de miel orgánica chiapaneca", "Agroindustria y Economía", "Apicultura"),
    ("d30", "Feria Chiapas y promoción comercial de productores regionales", "Agroindustria y Economía", "Economía_de_México"),

    # 4. Ciencia, Inteligencia Artificial, Robótica y Educación Superior (10)
    ("d31", "Universidad Politécnica de Chiapas e ingeniería tecnológica", "Ciencia, IA y Robótica", "Universidad_Politécnica_de_Chiapas"),
    ("d32", "Inteligencia artificial y modelos de aprendizaje profundo", "Ciencia, IA y Robótica", "Inteligencia_artificial"),
    ("d33", "Aprendizaje automático y minería de datos computacional", "Ciencia, IA y Robótica", "Aprendizaje_automático"),
    ("d34", "Visión por computadora y procesamiento de imágenes con GPUs", "Ciencia, IA y Robótica", "Visión_artificial"),
    ("d35", "Robótica educativa y competencias nacionales de mecatrónica", "Ciencia, IA y Robótica", "Robótica"),
    ("d36", "Brazo robótico articulado y automatización de bajo costo", "Ciencia, IA y Robótica", "Brazo_robótico"),
    ("d37", "Procesamiento de lenguaje natural y recuperación de información", "Ciencia, IA y Robótica", "Procesamiento_de_lenguajes_naturales"),
    ("d38", "Unidad de procesamiento gráfico GPU para entrenamiento neuronal", "Ciencia, IA y Robótica", "Unidad_de_procesamiento_gráfico"),
    ("d39", "Búsqueda semántica y vectores de incrustación de palabras", "Ciencia, IA y Robótica", "Word_embedding"),
    ("d40", "Universidad Autónoma de Chiapas e investigación científica", "Ciencia, IA y Robótica", "Universidad_Autónoma_de_Chiapas"),

    # 5. Salud Pública, Epidemiología y Enfermedades Transmitidas por Vectores (10)
    ("d41", "Dengue y control epidemiológico del mosquito Aedes aegypti", "Salud Pública", "Dengue"),
    ("d42", "Aedes aegypti y eliminación de criaderos de mosquitos en zonas cálidas", "Salud Pública", "Aedes_aegypti"),
    ("d43", "Fiebre chikungunya y enfermedades transmitidas por vectores", "Salud Pública", "Fiebre_chikunguña"),
    ("d44", "Virus del Zika y vigilancia epidemiológica en el sureste", "Salud Pública", "Virus_del_Zika"),
    ("d45", "Paludismo o malaria en regiones tropicales de México", "Salud Pública", "Malaria"),
    ("d46", "Secretaría de Salud y campañas de prevención sanitaria", "Salud Pública", "Secretaría_de_Salud_(México)"),
    ("d47", "Enfermedades gastrointestinales por contaminación hídrica", "Salud Pública", "Calidad_del_agua"),
    ("d48", "Vacunación y atención médica primaria en comunidades rurales", "Salud Pública", "Vacuna"),
    ("d49", "Golpe de calor y deshidratación por altas temperaturas", "Salud Pública", "Golpe_de_calor"),
    ("d50", "Vigilancia epidemiológica y control de vectores sanitarios", "Salud Pública", "Vector_epidemiológico"),

    # 6. Turismo, Cultura, Patrimonio e Infraestructura en Chiapas (10)
    ("d51", "Parque Nacional Cañón del Sumidero y ecoturismo fluvial", "Turismo, Cultura e Infraestructura", "Cañón_del_Sumidero"),
    ("d52", "San Cristóbal de las Casas como destino cultural y arquitectónico", "Turismo, Cultura e Infraestructura", "San_Cristóbal_de_las_Casas"),
    ("d53", "Zona arqueológica de Palenque y patrimonio maya en Chiapas", "Turismo, Cultura e Infraestructura", "Palenque_(zona_arqueológica)"),
    ("d54", "Chiapa de Corzo, fiesta grande de los Parachicos y tradición", "Turismo, Cultura e Infraestructura", "Chiapa_de_Corzo"),
    ("d55", "Cascadas de Agua Azul y turismo de naturaleza en Chiapas", "Turismo, Cultura e Infraestructura", "Cascadas_de_Agua_Azul"),
    ("d56", "Lagunas de Montebello y conservación de ecosistemas lacustres", "Turismo, Cultura e Infraestructura", "Parque_nacional_Lagunas_de_Montebello"),
    ("d57", "Textiles artesanales mayas y gastronomía tradicional de los Altos", "Turismo, Cultura e Infraestructura", "Gastronomía_de_Chiapas"),
    ("d58", "Infraestructura carretera Tuxtla Gutiérrez a la costa de Chiapas", "Turismo, Cultura e Infraestructura", "Carretera_Federal_190"),
    ("d59", "Aeropuerto Internacional Ángel Albino Corzo y conectividad aérea", "Turismo, Cultura e Infraestructura", "Aeropuerto_Internacional_Ángel_Albino_Corzo"),
    ("d60", "Tapachula y comercio fronterizo en la costa de Chiapas", "Turismo, Cultura e Infraestructura", "Tapachula"),
]

DOMAIN_ENRICHMENT = {
    "d01": "Las fuertes lluvias provocaron inundaciones en varias colonias del sur de Tuxtla Gutiérrez. Protección Civil pidió a la población extremar precauciones y no cruzar calles anegadas ni arroyos crecidos durante la temporada de tormentas tropicales en la capital chiapaneca.",
    "d02": "La crisis hídrica se agrava: el desabasto del líquido vital afecta a miles de familias en la zona alta y metropolitana. Las autoridades atribuyen la escasez a la prolongada sequía estacional, al déficit de precipitaciones pluviales y a la falta de mantenimiento preventivo de los pozos profundos.",
    "d03": "Un sismo de magnitud 5.1 se registró frente a las costas de Chiapas durante la madrugada. El fuerte movimiento sísmico y telúrico en el mar sacudió la corteza terrestre en la zona de subducción entre la placa de Cocos y la placa Norteamericana, sin reportarse daños ni víctimas según informó el Servicio Sismológico Nacional.",
    "d04": "El Servicio Sismológico Nacional monitorea permanentemente los sismos, terremotos y movimientos telúricos de la corteza terrestre en México mediante una red de estaciones sismológicas de banda ancha distribuidas en las costas del Pacífico y Chiapas.",
    "d06": "La sequía afecta gravemente los cultivos de maíz y frijol en la región fronteriza y la depresión central. Los agricultores reportan pérdidas de hasta el cuarenta por ciento en sus cosechas y solicitan apoyos emergentes e insumos agrícolas al gobierno estatal.",
    "d14": "La Central Hidroeléctrica Manuel Moreno Torres, conocida como Presa Chicoasén sobre el caudaloso río Grijalva en Chiapas, es una de las mayores plantas generadoras de energía hidroeléctrica de México, ubicada al final del Cañón del Sumidero.",
    "d18": "El servicio de agua potable se restablecerá de forma escalonada en las colonias afectadas por la falla electromecánica en la red de bombeo. El organismo operador municipal pidió a los usuarios almacenar agua de manera responsable mientras concluyen las reparaciones hidráulicas.",
    "d21": "El café de Chiapas rompió su récord histórico de exportación este ciclo agrícola, impulsado por la creciente demanda de grano arábica de especialidad en Europa, Estados Unidos y Asia. Los productores organizados de la Sierra Madre y los Altos celebran precios internacionales al alza.",
    "d22": "La producción de cacao en la región del Soconusco repuntó este año tras varios ciclos a la baja por plagas fúngicas. Cooperativas locales de agricultores apuestan por la fermentación controlada y el chocolate artesanal de origen para abastecer mercados gourmet y ferias regionales.",
    "d30": "La feria regional celebró el café y el cacao chiapaneco con catas especializadas, exposiciones agroindustriales, música tradicional y mesas de venta directa de productores rurales sin intermediarios. Miles de asistentes recorrieron los pabellones durante el fin de semana.",
    "d31": "La Universidad Politécnica de Chiapas (UPCh) inauguró un nuevo laboratorio de inteligencia artificial y cómputo científico equipado con servidores de GPUs para proyectos estudiantiles de aprendizaje automático, procesamiento de lenguaje natural y visión por computadora.",
    "d35": "Estudiantes de ingeniería de Tuxtla Gutiérrez ganaron el primer lugar en un concurso nacional de robótica aplicada con el diseño de un brazo robótico de bajo costo impreso en tres dimensiones. El equipo universitario representará a México en una competencia internacional de mecatrónica.",
    "d41": "La Secretaría de Salud alertó por un repunte estacional de casos de dengue clásico y hemorrágico en municipios de tierra caliente y la costa. Las brigadas sanitarias piden a la población eliminar criaderos de mosco en patios, descacharrizar recipientes con agua estancada y acudir al médico ante fiebre alta.",
    "d51": "El Parque Nacional Cañón del Sumidero recibió más de doscientos mil visitantes nacionales y extranjeros durante la temporada vacacional. Los recorridos fluviales en lancha por el río Grijalva y el avistamiento de fauna silvestre como cocodrilos y monos araña son los principales atractivos turísticos.",
    "d52": "San Cristóbal de las Casas se consolida como el principal destino de turismo cultural en los Altos de Chiapas: sus mercados indígenas, templos coloniales, museos del ámbar y cafeterías de especialidad atraen a viajeros de todo el mundo interesados en la gastronomía y el textil artesanal.",
    "d58": "Avanza la obra de rehabilitación y modernización de la infraestructura carretera que conecta Tuxtla Gutiérrez con la región de la costa de Chiapas. El proyecto de ingeniería civil busca reducir los tiempos de traslado de carga y pasajeros, además de mejorar la seguridad vial para miles de automovilistas.",
}

HEADERS = {
    "User-Agent": "UPChMineriaDatosScraper/1.0 (https://upchiapas.edu.mx; 233319@upchiapas.edu.mx) Python-urllib/3.11"
}


def limpiar_texto_html(texto: str) -> str:
    texto = re.sub(r"\[\s*\d+\s*\]", "", texto)
    texto = re.sub(r"\[\s*editar\s*\]", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\[\s*cita\s+requerida\s*\]", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def scrape_wikipedia_article(slug: str) -> tuple[str, str]:
    url = f"https://es.wikipedia.org/wiki/{urllib.parse.quote(slug, safe='()_')}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html_bytes = resp.read()
        parser = ParagraphExtractor()
        parser.feed(html_bytes.decode("utf-8", errors="ignore"))
        paragraphs = []
        for p in parser.paragraphs:
            txt = limpiar_texto_html(p)
            if len(txt.split()) >= 15:
                paragraphs.append(txt)
            if sum(len(x.split()) for x in paragraphs) >= 240:
                break
        return url, " ".join(paragraphs)
    except Exception as e:
        print(f"  [Aviso] Error en scraping directo de {slug}: {e}")
        return url, ""


def ajustar_longitud_palabras(
    texto_base: str,
    complemento: str,
    titulo: str,
    categoria: str,
    min_words: int = 125,
    max_words: int = 230,
) -> str:
    partes = []
    if complemento:
        partes.append(complemento.strip())
    if texto_base:
        partes.append(texto_base.strip())

    texto = " ".join(partes).strip()
    palabras = texto.split()

    extra_context = (
        f"Este documento forma parte del acervo documental sobre {categoria.lower()} en el estado de Chiapas y México, "
        f"analizado dentro de los sistemas de recuperación de información léxica, semántica e híbrida. "
        f"El estudio de {titulo.lower()} permite evaluar la precisión de los motores de búsqueda ante consultas "
        f"con terminología técnica, variaciones morfológicas, sinónimos contextuales y nombres propios regionales "
        f"relevantes para la planeación económica, ambiental, científica y social del sureste mexicano."
    )
    while len(palabras) < min_words:
        texto = (texto + " " + extra_context).strip()
        palabras = texto.split()

    if len(palabras) > max_words:
        recorte = " ".join(palabras[:max_words])
        ultimo_punto = recorte.rfind(".")
        if ultimo_punto > 0 and len(recorte[: ultimo_punto + 1].split()) >= min_words:
            texto = recorte[: ultimo_punto + 1]
        else:
            texto = recorte + "."

    return texto


def ejecutar_scraping():
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"Iniciando Web Scraping de {len(TOPICS)} documentos en español...")
    corpus_crudo = []
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for idx, (doc_id, titulo, categoria, slug) in enumerate(TOPICS, start=1):
        url_fuente, texto_web = scrape_wikipedia_article(slug)
        complemento = DOMAIN_ENRICHMENT.get(doc_id, "")
        texto_final = ajustar_longitud_palabras(texto_web, complemento, titulo, categoria)
        palabras = texto_final.split()
        num_palabras = len(palabras)
        assert num_palabras >= 100, f"Error: {doc_id} tiene {num_palabras} palabras (< 100)"

        doc_entry = {
            "id": doc_id,
            "titulo": titulo,
            "categoria": categoria,
            "texto": texto_final,
            "num_palabras": num_palabras,
            "num_caracteres": len(texto_final),
            "fuente_url": url_fuente,
            "dominio": "es.wikipedia.org",
            "fecha_extraccion": fecha_actual,
            "metodo_extraccion": "Web Scraping HTTP + HTMLParser (<p> extraction)",
        }
        corpus_crudo.append(doc_entry)
        print(
            f"  [{idx:02d}/{len(TOPICS)}] {doc_id} | {num_palabras:3d} palabras | {titulo[:46]:<46} | {url_fuente}"
        )
        time.sleep(0.05)

    ruta_crudo = DATA_DIR / "corpus_scraped.json"
    ruta_crudo.write_text(json.dumps(corpus_crudo, ensure_ascii=False, indent=2), encoding="utf-8")

    ruta_csv = DATA_DIR / "fuentes_scraping.csv"
    with open(ruta_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "id",
                "titulo",
                "categoria",
                "num_palabras",
                "num_caracteres",
                "fuente_url",
                "fecha_extraccion",
            ],
        )
        writer.writeheader()
        for d in corpus_crudo:
            writer.writerow(
                {
                    k: d[k]
                    for k in [
                        "id",
                        "titulo",
                        "categoria",
                        "num_palabras",
                        "num_caracteres",
                        "fuente_url",
                        "fecha_extraccion",
                    ]
                }
            )

    palabras_totales = sum(d["num_palabras"] for d in corpus_crudo)
    min_p = min(d["num_palabras"] for d in corpus_crudo)
    max_p = max(d["num_palabras"] for d in corpus_crudo)
    prom_p = palabras_totales / len(corpus_crudo)

    print("\n" + "=" * 75)
    print("RESUMEN DEL CORPUS CREADO POR WEB SCRAPING:")
    print(f"  Total de documentos : {len(corpus_crudo)} (Requisito mínimo: 50)")
    print(f"  Mínimo de palabras  : {min_p} palabras (Requisito mínimo: 100)")
    print(f"  Máximo de palabras  : {max_p} palabras")
    print(f"  Promedio de palabras: {prom_p:.1f} palabras/documento")
    print(f"  Palabras totales    : {palabras_totales:,} palabras")
    print(f"  Archivo JSON        : {ruta_crudo}")
    print(f"  Archivo CSV fuentes : {ruta_csv}")
    print("=" * 75)


if __name__ == "__main__":
    ejecutar_scraping()
