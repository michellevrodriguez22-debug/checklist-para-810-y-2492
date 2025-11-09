
import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak

# Visualizaciones
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon

# ------------------------------------------------------------------
# APP 810 + 2492 (tabla nutricional, declaraciones y sellos frontales)
# Con evidencia fotográfica por ítem NO CUMPLE y exporte a PDF
# + Módulos interactivos para sellos: (1) Aplicabilidad y (2) Tamaño/posición (Tabla 17)
# ------------------------------------------------------------------
st.set_page_config(page_title="Checklist Etiquetado — Res. 810/2021 y 2492/2022", layout="wide")
st.title("Checklist de etiquetado nutricional — Resoluciones 810/2021 y 2492/2022 (Colombia)")

# ------------------------------------------------------------------
# SIDEBAR: Datos de la verificación
# ------------------------------------------------------------------
st.sidebar.header("Datos de la verificación")
producto = st.sidebar.text_input("Nombre del producto")
categoria_producto = st.sidebar.selectbox("Tipo", ["Producto terminado", "Materia prima (para uso industrial)", "Ambos"])
proveedor = st.sidebar.text_input("Proveedor / Fabricante")
responsable = st.sidebar.text_input("Responsable de la verificación")
invima_num = st.sidebar.text_input("Registro sanitario INVIMA (si aplica a producto terminado)")
invima_url = st.sidebar.text_input("URL consulta INVIMA (opcional)")
invima_estado_ok = st.sidebar.checkbox("Verificación en INVIMA realizada y ACTIVO (coincide nombre/empresa)", value=False)
nombre_pdf = st.sidebar.text_input("Nombre del PDF (sin .pdf)", f"informe_810_2492_{datetime.now().strftime('%Y%m%d')}")
filter_no = st.sidebar.checkbox("Mostrar solo 'No cumple'", value=False)

st.sidebar.markdown("---")
st.sidebar.caption("Guía práctica para verificación de etiquetado nutricional, declaraciones y sellos frontales (Res. 810/2021, mod. 2492/2022).")

# ------------------------------------------------------------------
# Definición ordenada de criterios (flujo de revisión)
# ------------------------------------------------------------------
CATEGORIAS = {
    "1. Identificación inicial y aplicabilidad": [
        ("Registro sanitario INVIMA visible y vigente",
         "Verificar que el número INVIMA esté impreso en el empaque (producto terminado), legible/indeleble. Confirmar en portal INVIMA que el registro está ACTIVO y que el nombre del producto, titular y fabricante coinciden con lo impreso.",
         "Asegurar impresión del INVIMA en el envase y coherencia con la consulta oficial (estado ACTIVO).",
         "Control sanitario general; Res. 810/2021 art. 2 (definiciones de aplicabilidad); buenas prácticas de rotulado."),
        ("Idioma español (información obligatoria)",
         "Toda la información obligatoria debe estar en español; en importados, usar rótulo complementario adherido con la traducción completa.",
         "Incluir rótulo complementario en español cuando aplique.",
         "Res. 810/2021 art. 27.1.3"),
        ("Determinación de aplicabilidad (consumidor final vs. uso industrial)",
         "Confirmar si el producto se destina al consumidor final (requiere tabla nutricional y evaluación de sellos) o si es materia prima para uso industrial (exceptuado de tabla/sellos, pero debe cumplir trazabilidad).",
         "Clasificar correctamente el producto para aplicar los requisitos pertinentes.",
         "Res. 810/2021 art. 2; Res. 2492/2022 (modifica definiciones y exenciones)."),
    ],

    "2. Tabla nutricional obligatoria (estructura y formato)": [
        ("Presencia de la tabla nutricional",
         "Confirmar presencia de la tabla nutricional en alimentos destinados al consumidor final (excepciones: productos no envasados, mínimamente procesados, algunos a granel, etc.).",
         "Incluir la tabla nutricional cuando aplique (según destino y exenciones).",
         "Res. 810/2021 arts. 8, 9 y 10 (obligatoriedad y estructura)."),
        ("Forma de presentación: por 100 g / 100 mL y por porción",
         "La información debe declararse como mínimo por 100 g/100 mL y por porción; coherencia con estado físico (sólido/líquido).",
         "Incluir ambos ejes (100 g/100 mL y por porción).",
         "Res. 810/2021 art. 12."),
        ("Número de porciones por envase",
         "Declarar el número de porciones por envase (salvo productos de peso variable).",
         "Agregar número de porciones por envase si aplica.",
         "Res. 810/2021 art. 12 y par. 2 art. 2 (mod. 2492/2022)."),
        ("Nutrientes obligatorios mínimos",
         "Declarar al menos: energía (kcal), grasa total, grasa saturada, grasa trans, carbohidratos totales, azúcares totales, proteínas y sodio (con unidades normativas).",
         "Asegurar la inclusión de todos los nutrientes mínimos obligatorios.",
         "Res. 810/2021 art. 8-10 (y tablas asociadas)."),
        ("Micronutrientes (cuando se declaren)",
         "Si se declaran vitaminas/minerales, cumplir umbrales mínimos/máximos permitidos; presentar en bloque separado por línea, sin inducir a error.",
         "Ajustar la sección de micronutrientes a límites y formato establecidos.",
         "Res. 810/2021 art. 15 y 28.3."),
        ("Tolerancias analíticas",
         "La diferencia entre valores declarados y resultados analíticos no debe exceder ±20% (salvo excepciones).",
         "Verificar resultados de laboratorio y ajustar declaraciones si exceden tolerancias.",
         "Res. 810/2021 art. 14."),
        ("Formato, legibilidad y tipografía de la tabla",
         "Usar tipografía clara, contraste adecuado, líneas y disposición según lineamientos de la resolución; evitar que el texto quede cortado o ilegible.",
         "Ajustar tipografía/contraste y estructura de la tabla para legibilidad.",
         "Res. 810/2021 art. 27 (parámetros gráficos para la tabla)."),
    ],

    "3. Declaraciones nutricionales y de salud": [
        ("Declaraciones nutricionales (p. ej., 'fuente de', 'alto en')",
         "Solo pueden usarse si el producto cumple los criterios mínimos de contenido y el perfil de nutrientes (no debe exhibir sellos de advertencia que invaliden la declaración). Sustentar cuantitativamente (p. ej., %VD).",
         "Mantener solo declaraciones permitidas y sustentadas; retirar si no cumplen.",
         "Res. 810/2021 art. 16 y 25.4 (modificada por 2492/2022)."),
        ("Declaraciones de salud / funcionales",
         "Deben ser veraces, no engañosas y estar autorizadas por el MSPS cuando aplique. No atribuir propiedades medicinales (prevenir, tratar, curar enfermedades).",
         "Usar únicamente declaraciones autorizadas y con soporte científico.",
         "Res. 810/2021 art. 25."),
        ("Prohibición de declaraciones engañosas",
         "Evitar equivalencias simplistas o beneficios no sustentados. No utilizar mensajes que confundan sobre composición o efectos del producto.",
         "Eliminar declaraciones confusas o engañosas.",
         "Res. 810/2021 art. 25.5."),
    ],

    "4. Etiquetado frontal de advertencia (sellos negros)": [
        ("Determinación de aplicabilidad de sellos",
         "Determinar si el producto requiere sellos con base en límites de azúcares libres, grasas saturadas, grasas trans y sodio, diferenciando criterios para sólidos y líquidos.",
         "Evaluar composición vs límites; documentar el porqué SI/NO aplica sello(s).",
         "Res. 810/2021 art. 32 (mod. 2492/2022) y criterios OPS."),
        ("Límites de nutrientes críticos (criterios OPS)",
         "Azúcares libres ≥10% energía total; grasas saturadas ≥10% energía total; grasas trans ≥1% energía total; sodio ≥1 mg/kcal o ≥300 mg/100 g (sólidos). En bebidas sin aporte energético: sodio ≥40 mg/100 mL.",
         "Comparar formulación vs límites y aplicar sello si corresponde.",
         "Res. 810/2021 (Tabla de límites) mod. 2492/2022."),
        ("Sello 'Contiene edulcorante'",
         "Cuando el producto contenga edulcorantes, incluir sello de advertencia ('Contiene edulcorante, no recomendable en niños').",
         "Agregar sello correspondiente si contiene edulcorantes.",
         "Res. 2492/2022 (parámetros para edulcorantes)."),
        ("Forma, color y tipografía del sello",
         "Usar octágono negro con borde blanco, texto en mayúsculas de alto contraste ('EXCESO EN ...') según tipografía permitida.",
         "Ajustar forma, color y tipografía al estándar.",
         "Res. 2492/2022 (especificaciones gráficas)."),
        ("Ubicación y tamaño del sello (Tabla 17)",
         "Ubicar sellos en tercio superior de la cara principal, sin obstrucciones. Dimensionar según área (Tabla 17).",
         "Reubicar/aumentar tamaño conforme a Tabla 17.",
         "Res. 810/2021 art. 32 y Tabla 17 (mod. 2492/2022)."),
        ("Excepciones a sellos",
         "Aplicar exenciones (alimentos no/minimamente procesados, fórmulas infantiles, productos artesanales/típicos definidos, ciertos a granel, etc.).",
         "Documentar y justificar exención cuando corresponda.",
         "Res. 810/2021 art. 2 (definiciones y exenciones) mod. 2492/2022."),
    ],

    "5. Requisitos gráficos y de legibilidad (generales)": [
        ("Legibilidad y contraste del rótulo",
         "Información clara, visible, indeleble y con contraste suficiente respecto del fondo. Evitar pliegues/cortes que oculten el texto.",
         "Mejorar contraste/tamaño y asegurar indelebilidad.",
         "Res. 810/2021 art. 27 (parámetros gráficos)."),
        ("Ubicación visible (cara principal de exhibición)",
         "Elementos obligatorios en la cara de fácil lectura/visualización por el consumidor.",
         "Reubicar contenido para visibilidad adecuada.",
         "Res. 810/2021 art. 27 y definiciones de 'cara principal'."),
    ],

    "6. Control y evidencia documental": [
        ("Certificado de análisis (soporte de la tabla)",
         "Resultados de laboratorio (preferible acreditado) que soporten valores declarados; ajustar frente a tolerancias.",
         "Solicitar/adjuntar certificado de análisis vigente.",
         "Res. 810/2021 art. 14."),
        ("Fichas técnicas y especificaciones de ingredientes",
          "Fichas/especificaciones que respalden composición, aditivos, edulcorantes y contenido de nutrientes críticos.",
          "Mantener documentación de respaldo actualizada.",
          "Res. 810/2021 (soporte documental para declaraciones y sellos)."),
    ],
}

# Mapa de aplicabilidad sugerida
APLICA = {
    "Registro sanitario INVIMA visible y vigente": "Producto terminado",
    "Idioma español (información obligatoria)": "Ambos",
    "Determinación de aplicabilidad (consumidor final vs. uso industrial)": "Ambos",
    "Presencia de la tabla nutricional": "Producto terminado",
    "Forma de presentación: por 100 g / 100 mL y por porción": "Producto terminado",
    "Número de porciones por envase": "Producto terminado",
    "Nutrientes obligatorios mínimos": "Producto terminado",
    "Micronutrientes (cuando se declaren)": "Producto terminado",
    "Tolerancias analíticas": "Producto terminado",
    "Formato, legibilidad y tipografía de la tabla": "Producto terminado",
    "Declaraciones nutricionales (p. ej., 'fuente de', 'alto en')": "Producto terminado",
    "Declaraciones de salud / funcionales": "Producto terminado",
    "Prohibición de declaraciones engañosas": "Producto terminado",
    "Determinación de aplicabilidad de sellos": "Producto terminado",
    "Límites de nutrientes críticos (criterios OPS)": "Producto terminado",
    "Sello 'Contiene edulcorante'": "Producto terminado",
    "Forma, color y tipografía del sello": "Producto terminado",
    "Ubicación y tamaño del sello (Tabla 17)": "Producto terminado",
    "Excepciones a sellos": "Producto terminado",
    "Legibilidad y contraste del rótulo": "Ambos",
    "Ubicación visible (cara principal de exhibición)": "Ambos",
    "Certificado de análisis (soporte de la tabla)": "Producto terminado",
    "Fichas técnicas y especificaciones de ingredientes": "Ambos",
}

# ------------------------------------------------------------------
# Estado, notas y evidencia en sesión
# ------------------------------------------------------------------
if "status_810" not in st.session_state:
    st.session_state.status_810 = {i[0]: "none" for c in CATEGORIAS.values() for i in c}
if "note_810" not in st.session_state:
    st.session_state.note_810 = {i[0]: "" for c in CATEGORIAS.values() for i in c}
if "evidence_810" not in st.session_state:
    st.session_state.evidence_810 = {i[0]: [] for c in CATEGORIAS.values() for i in c}

st.header("Checklist según flujo de revisión (810/2021 y 2492/2022)")
st.markdown("Responde con ✅ Cumple / ❌ No cumple / ⚪ No aplica. Cuando marques **No cumple**, podrás **adjuntar evidencia fotográfica**.")

# Métrica rápida
def compute_metrics():
    yes = sum(1 for v in st.session_state.status_810.values() if v == "yes")
    no = sum(1 for v in st.session_state.status_810.values() if v == "no")
    answered = yes + no
    pct = round((yes / answered * 100), 1) if answered > 0 else 0.0
    return yes, no, answered, pct

yes_count, no_count, answered_count, percent = compute_metrics()
st.metric("Cumplimiento total (sobre ítems contestados)", f"{percent}%")

# Tabla 17 referencia (área -> tamaño cm)
TABLA_17 = [
    ("< 30 cm²", None),
    ("≥30 a <35 cm²", 1.7),
    ("≥35 a <40 cm²", 1.8),
    ("≥40 a <50 cm²", 2.0),
    ("≥50 a <60 cm²", 2.2),
    ("≥60 a <80 cm²", 2.5),
    ("≥80 a <100 cm²", 2.8),
    ("≥100 a <125 cm²", 3.1),
    ("≥125 a <150 cm²", 3.4),
    ("≥150 a <200 cm²", 3.9),
    ("≥200 a <250 cm²", 4.4),
    ("≥250 a <300 cm²", 4.8),
    ("> 300 cm²", "15% del lado de la cara principal"),
]
df_tabla17 = pd.DataFrame(TABLA_17, columns=["Área principal de la cara", "Lado mínimo del sello (cm)"])

# -------------------------
# Herramientas auxiliares
# -------------------------
def energia_por_gramos(gr, kcal_por_g):
    if gr is None: return None
    try:
        return float(gr) * float(kcal_por_g)
    except: return None

def porcentaje_energia(kcal_nutriente, kcal_total):
    if kcal_nutriente is None or kcal_total is None or kcal_total == 0:
        return None
    return 100.0 * float(kcal_nutriente) / float(kcal_total)

def draw_octagon(ax, center_x, center_y, side_len, fc='black', ec='white', lw=1.5):
    # Aproximación de octágono regular dentro de un cuadro de lado "side_len"
    s = side_len
    margin = s * 0.15  # recorte para esquinas
    pts = [
        (center_x - s/2 + margin, center_y + s/2),
        (center_x + s/2 - margin, center_y + s/2),
        (center_x + s/2, center_y + s/2 - margin),
        (center_x + s/2, center_y - s/2 + margin),
        (center_x + s/2 - margin, center_y - s/2),
        (center_x - s/2 + margin, center_y - s/2),
        (center_x - s/2, center_y - s/2 + margin),
        (center_x - s/2, center_y + s/2 - margin),
    ]
    poly = Polygon(pts, closed=True, facecolor=fc, edgecolor=ec, linewidth=lw)
    ax.add_patch(poly)

# -------------------------
# Render del checklist
# -------------------------
for categoria, items in CATEGORIAS.items():
    st.subheader(categoria)
    for item in items:
        titulo, que_verificar, recomendacion, referencia = item

        estado = st.session_state.status_810.get(titulo, "none")
        if filter_no and estado != "no":
            continue

        st.markdown(f"### {titulo}")
        st.markdown(f"**Qué verificar:** {que_verificar}")
        st.markdown(f"**Referencia:** {referencia}")
        st.markdown(f"**Aplica a:** {APLICA.get(titulo, 'Ambos')}")

        # =========================
        # 4.1 Determinación de aplicabilidad de sellos — MÓDULO DINÁMICO
        # =========================
        if titulo == "Determinación de aplicabilidad de sellos":
            with st.expander("Abrir calculadora de aplicabilidad de sellos"):
                col1, col2 = st.columns([0.55, 0.45])
                with col1:
                    estado_fisico = st.radio("Estado físico del producto", ["Sólido / semisólido (por 100 g)", "Líquido (por 100 mL)"], index=0)
                    st.markdown("**Ingrese por 100 g / 100 mL:**")
                    kcal = st.number_input("Energía (kcal)", min_value=0.0, value=200.0, step=1.0, key="kcal_input")
                    azuc_tot = st.number_input("Azúcares totales (g)", min_value=0.0, value=10.0, step=0.1, key="azu_tot_input")
                    usar_libres = st.checkbox("Tengo % de energía proveniente de **azúcares libres**")
                    if usar_libres:
                        pct_azu_libres = st.number_input("% energía de azúcares **libres**", min_value=0.0, max_value=100.0, value=0.0, step=0.1, key="pct_libres")
                    grasa_sat = st.number_input("Grasa saturada (g)", min_value=0.0, value=2.0, step=0.1, key="sat_input")
                    grasa_trans = st.number_input("Grasa trans (g)", min_value=0.0, value=0.0, step=0.05, key="trans_input")
                    sodio_mg = st.number_input("Sodio (mg)", min_value=0.0, value=300.0, step=5.0, key="sod_input")
                    bebida_sin_energia = False
                    if "Líquido" in estado_fisico:
                        bebida_sin_energia = st.checkbox("¿Bebida sin aporte energético? (0 kcal por 100 mL)", value=False)

                with col2:
                    # Cálculos
                    # Azúcares libres (umbral 10% de energía total)
                    if usar_libres:
                        pct_azu = pct_azu_libres
                    else:
                        # Aproximación si no se cuenta con libres: usar azúcares totales * 4 kcal/g
                        kcal_azu_tot = energia_por_gramos(azuc_tot, 4.0)
                        pct_azu = porcentaje_energia(kcal_azu_tot, kcal)

                    # Grasa saturada (10%)
                    kcal_sat = energia_por_gramos(grasa_sat, 9.0)
                    pct_sat = porcentaje_energia(kcal_sat, kcal)

                    # Grasa trans (1%)
                    kcal_trans = energia_por_gramos(grasa_trans, 9.0)
                    pct_trans = porcentaje_energia(kcal_trans, kcal)

                    # Sodio (dos criterios)
                    criterio_sodio_a = (kcal > 0 and (sodio_mg / max(kcal, 1.0)) >= 1.0)  # mg/kcal >=1
                    if "Sólido" in estado_fisico:
                        criterio_sodio_b = (sodio_mg >= 300.0)
                    else:
                        # líquidos: si es bebida sin energía, usar 40 mg/100 mL
                        if bebida_sin_energia:
                            criterio_sodio_b = (sodio_mg >= 40.0)
                        else:
                            criterio_sodio_b = (sodio_mg / max(kcal, 1.0)) >= 1.0  # aplica por mg/kcal también

                    excede_azuc = (pct_azu is not None) and (pct_azu >= 10.0)
                    excede_sat = (pct_sat is not None) and (pct_sat >= 10.0)
                    excede_trans = (pct_trans is not None) and (pct_trans >= 1.0)
                    excede_sodio = criterio_sodio_a or criterio_sodio_b

                    sellos = []
                    if excede_azuc: sellos.append("EXCESO EN AZÚCARES")
                    if excede_sat: sellos.append("EXCESO EN GRASAS SATURADAS")
                    if excede_trans: sellos.append("EXCESO EN GRASAS TRANS")
                    if excede_sodio: sellos.append("EXCESO EN SODIO")

                    # Resultado textual
                    if len(sellos) == 0:
                        st.success("✅ No requiere sellos según los límites ingresados.")
                    else:
                        st.error("⚠️ Debe llevar sello(s): " + ", ".join(sellos))

                    # Gráfico simple (una sola figura)
                    fig, ax = plt.subplots(figsize=(5.5, 2.8))
                    labels = ["Azúcares (%)", "Sat. (%)", "Trans (%)", "Sodio (criterio)"]
                    valores = [
                        pct_azu if pct_azu is not None else 0.0,
                        pct_sat if pct_sat is not None else 0.0,
                        pct_trans if pct_trans is not None else 0.0,
                        100.0 if excede_sodio else 0.0  # binario para sodio
                    ]
                    umbrales = [10.0, 10.0, 1.0, 100.0]  # referencia visual (sodio binario)
                    x = range(len(labels))
                    ax.bar(x, valores)
                    for i, (v, u) in enumerate(zip(valores, umbrales)):
                        ax.text(i, v + 1, f"{v:.1f}" if i != 3 else ("✓" if excede_sodio else "0"), ha="center", va="bottom", fontsize=8)
                        ax.axhline(u, linestyle="--")
                    ax.set_xticks(list(x), labels, rotation=0)
                    ax.set_ylim(0, max(110, max(valores)+10))
                    ax.set_ylabel("Porcentaje de energía (%)")
                    ax.set_title("Evaluación frente a umbrales (10%/1% y criterio sodio)")
                    st.pyplot(fig)

                    st.caption("Nota: Si no se cuenta con **azúcares libres**, se aproxima con azúcares totales × 4 kcal/g. Para bebidas **sin energía**, el criterio de sodio es 40 mg/100 mL.")

        # =========================
        # 4.5 Ubicación y tamaño del sello (Tabla 17) — MÓDULO VISUAL
        # =========================
        if titulo == "Ubicación y tamaño del sello (Tabla 17)":
            with st.expander("Abrir referencia visual (Tabla 17) y disposición de varios sellos"):
                st.dataframe(df_tabla17, use_container_width=True)

                colA, colB, colC = st.columns([0.36, 0.32, 0.32])
                with colA:
                    area_opcion = st.selectbox(
                        "Rango de área de la cara principal",
                        options=[r[0] for r in TABLA_17 if r[0] != "< 30 cm²"],
                        key="area_tabla17_sel"
                    )
                    tipo_sello = st.selectbox("Tipo de sello", options=[
                        "EXCESO EN AZÚCARES",
                        "EXCESO EN GRASAS SATURADAS",
                        "EXCESO EN GRASAS TRANS",
                        "EXCESO EN SODIO",
                        "CONTIENTE EDULCORANTE"
                    ], index=0, key="tipo_sello_sel")

                with colB:
                    num_sellos = st.selectbox("Cantidad de sellos", options=[1,2,3,4], index=1, key="num_sellos_sel")
                    espaciado_cm = st.number_input("Separación entre sellos (cm)", min_value=0.0, value=0.2, step=0.1, key="esp_sel")

                with colC:
                    ancho_cara_cm = None
                    if area_opcion == "> 300 cm²":
                        ancho_cara_cm = st.number_input("Ancho cara principal (cm) para 15%", min_value=1.0, value=10.0, step=0.5, key="ancho_cara_calc")

                # Determinar tamaño del sello (cm)
                def get_sello_cm(area_key: str, ancho_cara=None):
                    if area_key == "> 300 cm²":
                        if ancho_cara is None:
                            return None
                        return round(0.15 * float(ancho_cara), 2)
                    for k, v in TABLA_17:
                        if k == area_key:
                            return v
                    return None

                lado_cm = get_sello_cm(area_opcion, ancho_cara_cm)

                if lado_cm is None:
                    st.warning("Para el rango seleccionado, ingresa el **ancho de la cara principal (cm)** para calcular el 15% del lado del sello.")
                else:
                    ancho_total = round(num_sellos * lado_cm + (num_sellos - 1) * espaciado_cm, 2)
                    st.markdown(f"**Resultado:** Lado del sello = **{lado_cm} cm** · Ancho total del conjunto ({num_sellos}) ≈ **{ancho_total} cm** (separación: {espaciado_cm} cm).")
                    st.success("✅ Cumple con el tamaño mínimo de acuerdo con Tabla 17.")

                    # --------- Visualización (fondo blanco simplificado) ----------
                    # Escala proporcional: 1 cm = 20 unidades gráficas (arbitrario para pantalla)
                    scale = 20.0
                    envase_w_cm = max(ancho_total + 2.0, 10.0)  # ancho mínimo de envase para vista
                    envase_h_cm = envase_w_cm * 1.6              # proporción visual
                    tercio_y = envase_h_cm * (2.0/3.0)

                    fig, ax = plt.subplots(figsize=(7, 5))
                    # Cara principal (gris claro)
                    ax.add_patch(Rectangle((0, 0), envase_w_cm*scale, envase_h_cm*scale, facecolor="#EEEEEE", edgecolor="#BBBBBB"))
                    # Línea de referencia del tercio superior
                    ax.axhline(tercio_y*scale, linestyle="--")

                    # Dibujar sellos (octágonos) centrados horizontalmente en el tercio superior
                    total_w_px = ancho_total * scale
                    start_x = (envase_w_cm*scale - total_w_px) / 2.0 + (lado_cm*scale)/2.0
                    y_center = tercio_y*scale + (lado_cm*scale)/2.5  # un poco por encima de la línea
                    for i in range(num_sellos):
                        cx = start_x + i * (lado_cm*scale + espaciado_cm*scale)
                        draw_octagon(ax, cx, y_center, lado_cm*scale, fc="black", ec="white", lw=2.0)
                        # Texto del sello
                        ax.text(cx, y_center, tipo_sello, ha="center", va="center", color="white", fontsize=8, wrap=True)

                    ax.set_xlim(0, envase_w_cm*scale)
                    ax.set_ylim(0, envase_h_cm*scale)
                    ax.set_aspect('equal')
                    ax.axis('off')
                    st.pyplot(fig)

        # ----------------------- Botonera de estado -----------------------
        c1, c2, c3, _ = st.columns([0.12, 0.12, 0.12, 0.64])
        with c1:
            if st.button("✅ Cumple", key=f"{titulo}_yes_810"):
                st.session_state.status_810[titulo] = "yes"
        with c2:
            if st.button("❌ No cumple", key=f"{titulo}_no_810"):
                st.session_state.status_810[titulo] = "no"
        with c3:
            if st.button("⚪ No aplica", key=f"{titulo}_na_810"):
                st.session_state.status_810[titulo] = "na"

        # Visualización del estado
        estado = st.session_state.status_810[titulo]
        if estado == "yes":
            st.markdown("<div style='background:#e6ffed;padding:6px;border-radius:5px;'>✅ Cumple</div>", unsafe_allow_html=True)
        elif estado == "no":
            st.markdown(f"<div style='background:#ffe6e6;padding:6px;border-radius:5px;'>❌ No cumple — {recomendacion}</div>", unsafe_allow_html=True)
        elif estado == "na":
            st.markdown("<div style='background:#f2f2f2;padding:6px;border-radius:5px;'>⚪ No aplica</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background:#fff;padding:6px;border-radius:5px;'>Sin responder</div>", unsafe_allow_html=True)

        # Observación libre
        nota = st.text_area("Observación (opcional)", value=st.session_state.note_810.get(titulo, ""), key=f"{titulo}_nota_810")
        st.session_state.note_810[titulo] = nota

        # Evidencia fotográfica cuando NO CUMPLE
        if st.session_state.status_810[titulo] == "no":
            st.markdown("**Adjunta evidencia fotográfica del incumplimiento:**")
            files = st.file_uploader("Subir imágenes (JPG/PNG) — puedes cargar varias", type=["jpg","jpeg","png"], accept_multiple_files=True, key=f"uploader_{titulo}_810")
            if files:
                caption = st.text_input("Descripción breve para estas imágenes (opcional)", key=f"caption_{titulo}_810")
                if st.button("Agregar evidencia", key=f"add_ev_{titulo}_810"):
                    for f in files:
                        st.session_state.evidence_810[titulo].append({
                            "name": f.name,
                            "bytes": f.read(),
                            "caption": caption or ""
                        })
                    st.success(f"Se agregaron {len(files)} imagen(es) a la evidencia de: {titulo}")

            ev_list = st.session_state.evidence_810.get(titulo, [])
            if ev_list:
                st.markdown("**Evidencia acumulada:**")
                cols = st.columns(4)
                for idx, ev in enumerate(ev_list):
                    with cols[idx % 4]:
                        st.image(ev["bytes"], caption=ev["caption"] or ev["name"], use_column_width=True)
                        if st.button("Eliminar esta imagen", key=f"del_{titulo}_{idx}_810"):
                            st.session_state.evidence_810[titulo].pop(idx)
                            st.experimental_rerun()

        st.markdown("---")

# ------------------------------------------------------------------
# Resumen y exportación
# ------------------------------------------------------------------
rows = []
for items in CATEGORIAS.values():
    for titulo, que_verificar, recomendacion, referencia in items:
        estado_val = st.session_state.status_810.get(titulo, "none")
        estado_humano = (
            "Cumple" if estado_val == "yes"
            else "No cumple" if estado_val == "no"
            else "No aplica" if estado_val == "na"
            else "Sin responder"
        )
        rows.append({
            "Ítem": titulo,
            "Estado": estado_humano,
            "Recomendación": recomendacion,
            "Referencia": referencia,
            "Observación": st.session_state.note_810.get(titulo, ""),
        })
df = pd.DataFrame(rows, columns=["Ítem", "Estado", "Recomendación", "Referencia", "Observación"])

st.subheader("Resumen rápido")
st.write(
    f"CUMPLE: {sum(1 for v in st.session_state.status_810.values() if v == 'yes')} — "
    f"NO CUMPLE: {sum(1 for v in st.session_state.status_810.values() if v == 'no')} — "
    f"NO APLICA: {sum(1 for v in st.session_state.status_810.values() if v == 'na')} — "
    f"SIN RESPONDER: {sum(1 for v in st.session_state.status_810.values() if v == 'none')}"
)

def split_observation_text(text: str, chunk: int = 100) -> str:
    if not text:
        return ""
    s = str(text)
    if len(s) <= chunk:
        return s
    parts = [s[i:i+chunk] for i in range(0, len(s), chunk)]
    return "\\n".join(parts)

def generar_pdf(df: pd.DataFrame, producto: str, proveedor: str, responsable: str,
                categoria_producto: str, invima_num: str, invima_url: str,
                invima_estado_ok: bool, porcentaje: float, nombre_archivo: str) -> BytesIO:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=8*mm, rightMargin=8*mm,
        topMargin=8*mm, bottomMargin=8*mm
    )
    styles = getSampleStyleSheet()
    style_header = ParagraphStyle("header", parent=styles["Normal"], fontSize=8, leading=10)
    style_cell   = ParagraphStyle("cell",   parent=styles["Normal"], fontSize=7.5, leading=9)

    story = []
    # Encabezado
    story.append(Paragraph("<b>Informe de verificación de etiquetado nutricional — Resoluciones 810/2021 y 2492/2022</b>", style_header))
    story.append(Spacer(1, 3*mm))
    fecha_str = datetime.now().strftime("%Y-%m-%d")
    invima_str = invima_num or "-"
    invima_estado_str = "ACTIVO y coincidente" if invima_estado_ok else "No verificado / No activo / No coincide"
    meta = (
        f"<b>Fecha:</b> {fecha_str} &nbsp;&nbsp; "
        f"<b>Producto:</b> {producto or '-'} &nbsp;&nbsp; "
        f"<b>Tipo:</b> {categoria_producto or '-'} &nbsp;&nbsp; "
        f"<b>Proveedor:</b> {proveedor or '-'} &nbsp;&nbsp; "
        f"<b>Responsable:</b> {responsable or '-'}<br/>"
        f"<b>Registro INVIMA:</b> {invima_str} &nbsp;&nbsp; "
        f"<b>Estado en portal:</b> {invima_estado_str}"
    )
    if invima_url.strip():
        meta += f" &nbsp;&nbsp; <b>Consulta:</b> {invima_url}"
    story.append(Paragraph(meta, style_header))
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph(f"<b>Cumplimiento (sobre ítems contestados):</b> {porcentaje}%", style_header))
    story.append(Spacer(1, 5*mm))

    # Tabla principal
    data = [["Ítem", "Estado", "Recomendación", "Referencia", "Observación"]]
    for _, r in df.iterrows():
        obs = r["Observación"] or "-"
        if obs != "-":
            obs = split_observation_text(obs, chunk=100)
        data.append([
            Paragraph(str(r["Ítem"]),          style_cell),
            Paragraph(str(r["Estado"]),        style_cell),
            Paragraph(str(r["Recomendación"]), style_cell),
            Paragraph(str(r["Referencia"]),    style_cell),
            Paragraph(obs,                     style_cell),
        ])

    col_widths = [70*mm, 25*mm, 100*mm, 45*mm, 40*mm]
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f2f2f2")),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,0), 8),
        ("GRID",       (0,0), (-1,-1), 0.25, colors.grey),
        ("VALIGN",     (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",(0,0), (-1,-1), 3),
        ("RIGHTPADDING",(0,0), (-1,-1), 3),
    ]))
    story.append(tbl)

    # No añadimos visualizaciones al PDF (solo interfaz)
    doc.build(story)
    buf.seek(0)
    return buf

st.subheader("Generar informe PDF (A4 horizontal)")
if st.button("Generar PDF"):
    yes_count = sum(1 for v in st.session_state.status_810.values() if v == "yes")
    no_count = sum(1 for v in st.session_state.status_810.values() if v == "no")
    answered_count = yes_count + no_count
    percent = round((yes_count / answered_count * 100), 1) if answered_count > 0 else 0.0

    pdf_buffer = generar_pdf(
        df, producto, proveedor, responsable, categoria_producto,
        invima_num, invima_url, invima_estado_ok, percent, nombre_pdf
    )
    file_name = (nombre_pdf.strip() or f"informe_810_2492_{datetime.now().strftime('%Y%m%d')}") + ".pdf"
    st.download_button("Descargar PDF", data=pdf_buffer, file_name=file_name, mime="application/pdf")
