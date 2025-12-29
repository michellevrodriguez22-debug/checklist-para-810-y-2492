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
# SIDEBAR: Datos generales
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
st.sidebar.caption("Guía práctica para verificación de etiquetado nutricional, declaraciones y sellos frontales según Res. 810/2021 modificada por Res. 2492/2022.")
st.sidebar.caption("Guía práctica para verificación de etiquetado nutricional, declaraciones y sellos frontales (Res. 810/2021, mod. 2492/2022).")

# ------------------------------------------------------------------
# Definición ordenada de criterios (flujo de revisión)
# Abarca: Tabla nutricional, declaraciones, sellos frontales, aspectos gráficos y control.
# ------------------------------------------------------------------
CATEGORIAS = {
    "1. Principios generales de etiquetado nutricional": [
        ("No inducir a error o confusión",
         "Verificar que el etiquetado nutricional y cualquier información asociada no atribuyan propiedades que no posea, ni induzcan a error sobre composición, cantidad o beneficios.",
         "Res. 810/2021, Art. 5."),
        ("Tabla nutricional obligatoria (aplicabilidad)",
         "Que la tabla nutricional esté diseñada y presentada conforme al área disponible del envase, utilizando el formato permitido vertical, simplificado, lineal o tabular, y que cumpla con los requisitos de legibilidad y estructura establecidos por la norma.",
         "Res. 810/2021, Art. 6."),
    ],
    "2. Estructura y contenido de la tabla nutricional": [
        ("Unidades de medida (estructura general)",
         "Que la información se declare por 100 g o 100 mL y por porción (según estado físico), incluyendo número de porciones por envase",
         "Res. 810/2021, Art. 7 y 8."),
        ("Nutrientes obligatorios declarados",
         "La tabla nutricional debe incluir los macronutrientes obligatorios: Calorías, grasas totales, grasas saturadas, grasas trans, carbohidratos totales, azúcares totales, proteínas y sodio. Micronutrientes obligatorios: Vitamina A, Vitamina D, Hierro, Calcio y Zinc (Una forma de declararlos tambien es incluirlos en el apartado inferior de 'No es fuente significativa de'.",
         "Res. 810/2021, Art. 8.1.1"),
        ("Unidades específicas por nutriente",
         "Que las unidades declaradas correspondan a lo exigido por la norma: Calorías en kcal y/o kJ; Grasas totales, grasas saturadas, carbohidratos totales, fibra dietaria, azúcares totales, azúcares añadidos y proteina en g; Grasas trans y Sodio en mg; En el caso de micronutrientes: ; Vitamina A en µg ER; Vitamina A en µg; Calcio, Hierro, Vitamina C, Zinc y otros micronutrientes en mg.",
         "Res. 810/2021, Art. 8"),
        ("Formato y tipografía",
         "Que la tabla emplee tipografía Arial o Helvetica, en negro sobre fondo contrastante, sin negrillas ni cursivas, con tamaño ≥ 8 pt para envases con área principal hasta 100 cm² y proporcionalmente mayor para envases más grandes; conservar márgenes y proporciones sin imágenes ni logotipos dentro del recuadro.",
         "Res. 810/2021, Art. 9.1, 9.2 y 9.5"),
         ("Declaración de porciones",
         "Que la porción indicada en la tabla nutricional esté declarada en unidades del Sistema Internacional, acompañada de una medida casera común, y que el número de porciones por envase coincida con el contenido neto del producto. Ejemplo: si el envase contiene 150 g y la porción es 30 g, el número de porciones debe ser 5; esta porción puede expresarse como 1 onza (oz), donde 1 onza de peso equivale a 28 g.",
         "Res. 810/2021, Art. 12."),
        ("Verificación de calorías declaradas (±20% tolerancia)",
         "Comprobar que las calorías declaradas coinciden con las calculadas por macronutrientes (4 kcal/g CHO, 4 kcal/g proteínas, 9 kcal/g grasas). 💡 Use la herramienta a continuación para comprobarlo.",
         "Res. 810/2021, Art. 17 (Tolerancias)."),
        ("Consistencia con análisis bromatológico (±20%)",
         "Verificar que los valores declarados en la tabla nutricional coinciden con el análisis bromatológico dentro de ±20%; usar resultados de laboratorio acreditado/certificado.",
         "Res. 810/2021, Art. 17 (Tolerancias)."),
    ],
    "3. Sellos frontales de advertencia": [
        ("Determinación de aplicabilidad de sellos",
         "Evaluar si corresponde ‘EXCESO EN’ (azúcares, grasas saturadas, grasas trans, sodio) o ‘CONTIENE EDULCORANTE’. 💡 Use la herramienta a continuación para determinar la aplicabilidad de sellos.",
         "Res. 810/2021, Art. 25 y tabla 3, modificado por Res. 2492/2022."),
        ("Sello ‘Contiene edulcorante’",
         "Si se declara que el producto contiene edulcorantes (calóricos o no), debe incluirse el sello ‘Contiene edulcorantes’.",
         "Res. 2492/2022 (modifica Art. 27 Res. 810/2021)."),
        ("Ubicación, distribución y tamaño de sellos (Tabla 17)",
        "Que los sellos frontales de advertencia estén ubicados en el tercio superior de la cara principal de exhibición del empaque. En envases planos, los sellos deben colocarse en el tercio superior derecho, alineados horizontalmente y sin superposición. En envases cilíndricos, deben ubicarse en el tercio superior central, manteniendo la alineación horizontal y una lectura clara desde el frente. Para verificar el tamaño del sello, se debe hacer uso de la herramienta incluida en la aplicación.",
        "Res. 810/2021, Art. 27; modificado por Res. 2492/2022."),
    ],
}

# Mapa de aplicabilidad sugerida
APLICA = {
    # 1
    "Registro sanitario INVIMA visible y vigente": "Producto terminado",
    "Idioma español (información obligatoria)": "Ambos",
    "Determinación de aplicabilidad (consumidor final vs. uso industrial)": "Ambos",
    # 2
    "Presencia de la tabla nutricional": "Producto terminado",
    "Forma de presentación: por 100 g / 100 mL y por porción": "Producto terminado",
    "Número de porciones por envase": "Producto terminado",
    "Nutrientes obligatorios mínimos": "Producto terminado",
    "Micronutrientes (cuando se declaren)": "Producto terminado",
    "Tolerancias analíticas": "Producto terminado",
    "Formato, legibilidad y tipografía de la tabla": "Producto terminado",
    # 3
    "Declaraciones nutricionales (p. ej., 'fuente de', 'alto en')": "Producto terminado",
    "Declaraciones de salud / funcionales": "Producto terminado",
    "Prohibición de declaraciones engañosas": "Producto terminado",
    # 4
    "Determinación de aplicabilidad de sellos": "Producto terminado",
    "Límites de nutrientes críticos (criterios OPS)": "Producto terminado",
    "Sello 'Contiene edulcorante'": "Producto terminado",
    "Forma, color y tipografía del sello": "Producto terminado",
    "Ubicación y tamaño del sello (Tabla 17)": "Producto terminado",
    "Excepciones a sellos": "Producto terminado",
    # 5
    "Legibilidad y contraste del rótulo": "Ambos",
    "Ubicación visible (cara principal de exhibición)": "Ambos",
    # 6
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
        titulo, que_verificar, referencia = item

        estado = st.session_state.status_810.get(titulo, "none")
        if filter_no and estado != "no":
            continue

        st.markdown(f"### {titulo}")
        st.markdown(f"**Qué verificar:** {que_verificar}")
        st.markdown(f"**Referencia:** {referencia}")
        st.markdown(f"**Aplica a:** {APLICA.get(titulo, 'Ambos')}")

        # Para la "Tabla 17" se añade un recordatorio informativo de tamaños mínimos
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
            st.markdown("**Tabla 17 (resumen informativo):** dimensión mínima del octágono según área de la cara principal del envase. "
                        "Si el área es < 30 cm²: rotular envase secundario o incluir mecanismo de consulta (p. ej. QR); "
                        "≥30 a <35 cm²: 1,7 cm; ≥35 a <40: 1,8 cm; ≥40 a <50: 2,0 cm; ≥50 a <60: 2,2 cm; "
                        "≥60 a <80: 2,5 cm; ≥80 a <100: 2,8 cm; ≥100 a <125: 3,1 cm; ≥125 a <150: 3,4 cm; "
                        "≥150 a <200: 3,9 cm; ≥200 a <250: 4,4 cm; ≥250 a <300: 4,8 cm; >300 cm²: 15% del lado de la cara principal.")

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
            st.markdown("<div style='background:#ffe6e6;padding:6px;border-radius:5px;'>❌ No cumple</div>", unsafe_allow_html=True)
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
    for titulo, que_verificar, referencia in items:
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
            "Referencia": referencia,
            "Observación": st.session_state.note_810.get(titulo, ""),
        })
df = pd.DataFrame(rows, columns=["Ítem", "Estado", "Referencia", "Observación"])

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
    # Encabezado según confirmación del usuario (sin marcas comerciales)
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
    data = [["Ítem", "Estado", "Referencia", "Observación"]]
    for _, r in df.iterrows():
        obs = r["Observación"] or "-"
        if obs != "-":
            obs = split_observation_text(obs, chunk=100)
        data.append([
            Paragraph(str(r["Ítem"]),          style_cell),
            Paragraph(str(r["Estado"]),        style_cell),
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

    # Evidencia fotográfica (solo ítems No cumple con imágenes)
    evidencias_total = sum(len(v) for v in st.session_state.evidence_810.values())
    no_cumple_items = [k for k,v in st.session_state.status_810.items() if v == "no" and len(st.session_state.evidence_810.get(k,[]))>0]
    if evidencias_total > 0 and len(no_cumple_items)>0:
        story.append(PageBreak())
        story.append(Paragraph("<b>Evidencia fotográfica de incumplimientos</b>", style_header))
        story.append(Spacer(1, 3*mm))

        max_img_width = 120*mm
        for titulo in no_cumple_items:
            story.append(Spacer(1, 2*mm))
            story.append(Paragraph(f"<b>Ítem:</b> {titulo}", style_header))
            ev_list = st.session_state.evidence_810.get(titulo, [])
            for ev in ev_list:
                img_buf = BytesIO(ev["bytes"])
                try:
                    img = RLImage(img_buf)
                    iw, ih = img.drawWidth, img.drawHeight
                    scale = max_img_width / iw if iw > 0 else 1.0
                    img.drawWidth = max_img_width
                    img.drawHeight = ih * scale
                    story.append(img)
                except Exception:
                    story.append(Paragraph("(No se pudo renderizar la imagen adjunta)", style_cell))
                if ev["caption"]:
                    story.append(Paragraph(ev["caption"], style_cell))
                story.append(Spacer(1, 3*mm))

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
