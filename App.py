
import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak
)
import tempfile
import os

# ------------------------------------------------------------------------------------
# CONFIGURACIÓN INICIAL
# ------------------------------------------------------------------------------------
st.set_page_config(page_title="Checklist Etiquetado — 810/2021 y 2492/2022", layout="wide")
st.title("Checklist de Etiquetado Nutricional — Resoluciones 810/2021 y 2492/2022 (Colombia)")

# ------------------------------------------------------------------------------------
# SIDEBAR: Datos generales
# ------------------------------------------------------------------------------------
st.sidebar.header("Datos de la verificación")
producto = st.sidebar.text_input("Nombre del producto")
proveedor = st.sidebar.text_input("Proveedor / Fabricante")
responsable = st.sidebar.text_input("Responsable de la verificación")
categoria_producto = st.sidebar.selectbox("Tipo de producto", ["Producto terminado", "Materia prima (uso industrial)", "Ambos"])
invima_registro = st.sidebar.text_input("Registro sanitario INVIMA (si aplica)")
invima_estado_activo = st.sidebar.checkbox("Verificado en portal INVIMA como ACTIVO y coincidente", value=False)
invima_url = st.sidebar.text_input("URL de consulta INVIMA (opcional)")
nombre_pdf = st.sidebar.text_input("Nombre del PDF (sin .pdf)", f"informe_810_2492_{datetime.now().strftime('%Y%m%d')}")
solo_no = st.sidebar.checkbox("Mostrar solo 'No cumple'", value=False)

# ------------------------------------------------------------------------------------
# TABLA 17: referencia para tamaño del sello
# ------------------------------------------------------------------------------------
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
df_tabla17 = pd.DataFrame(TABLA_17, columns=["Área de la cara principal", "Lado mínimo del sello (cm)"])

# ------------------------------------------------------------------------------------
# FLUJO SIMPLIFICADO DE CHECKLIST (810/2021 y 2492/2022)
# ------------------------------------------------------------------------------------
CATEGORIAS = {
    "1. Verificación inicial (producto y registro sanitario)": [
        ("Registro sanitario INVIMA visible y vigente",
         "Debe estar impreso en el empaque (producto terminado), legible e indeleble. Confirmar en portal INVIMA que el registro se encuentra ACTIVO y que el nombre del producto, titular y fabricante coinciden con lo impreso.",
         "Imprimir el número INVIMA en el envase y verificar vigencia/coincidencia en el portal."),
        ("Nombre del producto coincide con INVIMA",
         "Verificar que el nombre del alimento coincida exactamente con el declarado en el registro sanitario INVIMA y refleje la verdadera naturaleza del producto (no usar solo marca).",
         "Alinear la denominación impresa con la denominación registrada en INVIMA."),
        ("Fabricante/Importador y país de origen declarados",
         "Declarar razón social y dirección del fabricante/importador, y país de origen cuando corresponda.",
         "Completar nombre/dirección del fabricante/importador y país de origen."),
    ],
    "2. Elementos generales del rótulo": [
        ("Nombre del alimento (coincidente con registro)",
         "El nombre del alimento debe reflejar la verdadera naturaleza y coincidir con el del registro sanitario INVIMA.",
         "Ajustar la denominación para coincidir con registro y naturaleza del producto."),
        ("Lista de ingredientes en orden decreciente",
         "Listar todos los ingredientes en orden decreciente de peso al momento de fabricación, del de mayor presencia al de menor.",
         "Reordenar y completar la lista de ingredientes de mayor a menor presencia."),
        ("Declaración de alérgenos (si aplica)",
         "Incluir advertencia de alérgenos cuando corresponda (p. ej., gluten, leche, soya, huevo, maní, etc.).",
         "Agregar la declaración específica de alérgenos presentes."),
        ("Contenido neto y unidades SI",
         "Declarar el contenido neto utilizando unidades del SI (g, kg, mL, L), en la cara visible para el consumidor, con legibilidad adecuada.",
         "Corregir formato/unidades y visibilidad del contenido neto."),
        ("Legibilidad y contraste",
         "Garantizar que la información sea visible, indeleble y con contraste suficiente respecto del fondo; evitar pliegues o cortes que oculten el texto.",
         "Mejorar contraste, tamaño de fuente o disposición para legibilidad."),
        ("Idioma (traducción en importados)",
         "Toda la información obligatoria debe estar en español. En productos importados, adherir rótulo complementario con traducción completa al español.",
         "Agregar rótulo complementario en español cuando aplique."),
    ],
    "3. Información nutricional obligatoria": [
        ("Presencia de la tabla nutricional",
         "Incluya tabla nutricional cuando el producto se destine al consumidor final (exenciones específicas pueden aplicar).",
         "Agregar la tabla nutricional conforme a aplicabilidad."),
        ("Unidades y forma de presentación",
         "Declarar por 100 g/100 mL y por porción (coherente con estado físico).",
         "Agregar o corregir las unidades y las columnas requeridas."),
        ("Porciones por envase",
         "Indicar claramente el número de porciones por envase (salvo peso variable).",
         "Agregar el dato de porciones por envase."),
        ("Formato y coherencia",
         "Usar tipografía clara y disposición conforme a la resolución; evitar cortes o ilegibilidad.",
         "Ajustar formato y coherencia de la tabla."),
    ],
    "4. Declaraciones y sellos": [
        ("Declaraciones nutricionales/funcionales permitidas",
         "Usar solo declaraciones permitidas y sustentadas; no atribuir propiedades medicinales. No deben contradecir sellos de advertencia.",
         "Eliminar o ajustar declaraciones no sustentadas o no permitidas."),
        ("Determinación de aplicabilidad de sellos (810/2492)",
         "Verificar si corresponde 'EXCESO EN' (azúcares, grasas saturadas, grasas trans, sodio) y/o 'CONTIENE EDULCORANTE'.",
         "Aplicar los sellos cuando se excedan límites o cuando existan edulcorantes."),
        ("Ubicación y tamaño de sellos (Tabla 17)",
         "Los sellos deben ubicarse en el tercio superior de la cara principal y su tamaño debe cumplir con Tabla 17.",
         "Reubicar o ajustar tamaño de los sellos para cumplir con Tabla 17."),
    ],
}

APLICA = {
    "Registro sanitario INVIMA visible y vigente": "Producto terminado",
    "Nombre del producto coincide con INVIMA": "Producto terminado",
    "Fabricante/Importador y país de origen declarados": "Ambos",
    "Nombre del alimento (coincidente con registro)": "Producto terminado",
    "Lista de ingredientes en orden decreciente": "Producto terminado",
    "Declaración de alérgenos (si aplica)": "Producto terminado",
    "Contenido neto y unidades SI": "Producto terminado",
    "Legibilidad y contraste": "Ambos",
    "Idioma (traducción en importados)": "Ambos",
    "Presencia de la tabla nutricional": "Producto terminado",
    "Unidades y forma de presentación": "Producto terminado",
    "Porciones por envase": "Producto terminado",
    "Formato y coherencia": "Producto terminado",
    "Declaraciones nutricionales/funcionales permitidas": "Producto terminado",
    "Determinación de aplicabilidad de sellos (810/2492)": "Producto terminado",
    "Ubicación y tamaño de sellos (Tabla 17)": "Producto terminado",
}

# ------------------------------------------------------------------------------------
# ESTADO, NOTAS Y EVIDENCIA
# ------------------------------------------------------------------------------------
if "status_810" not in st.session_state:
    st.session_state.status_810 = {i[0]: "none" for c in CATEGORIAS.values() for i in c}
if "note_810" not in st.session_state:
    st.session_state.note_810 = {i[0]: "" for c in CATEGORIAS.values() for i in c}
if "evidence_810" not in st.session_state:
    st.session_state.evidence_810 = {i[0]: [] for c in CATEGORIAS.values() for i in c}

# ------------------------------------------------------------------------------------
# UTILIDADES
# ------------------------------------------------------------------------------------
def energia_por_gramos(gr, kcal_por_g):
    try:
        gr = float(gr)
        return gr * float(kcal_por_g)
    except:
        return None

def porcentaje_energia(kcal_nutriente, kcal_total):
    try:
        if kcal_total is None or kcal_total == 0:
            return None
        return 100.0 * float(kcal_nutriente) / float(kcal_total)
    except:
        return None

def split_observation_text(text: str, chunk: int = 100) -> str:
    if not text:
        return ""
    s = str(text)
    if len(s) <= chunk:
        return s
    parts = [s[i:i+chunk] for i in range(0, len(s), chunk)]
    return "\\n".join(parts)

# ------------------------------------------------------------------------------------
# RENDER DEL CHECKLIST CON FLUJO
# ------------------------------------------------------------------------------------
st.header("Checklist por etapas")
st.markdown("Responde con ✅ Cumple / ❌ No cumple / ⚪ No aplica. Si marcas **No cumple**, podrás **adjuntar evidencia**.")

for categoria, items in CATEGORIAS.items():
    st.subheader(categoria)
    for titulo, que_verificar, recomendacion in items:
        estado = st.session_state.status_810.get(titulo, "none")
        if solo_no and estado != "no":
            continue

        st.markdown(f"### {titulo}")
        st.markdown(f"**Qué verificar:** {que_verificar}")
        st.markdown(f"**Aplica a:** {APLICA.get(titulo, 'Producto terminado')}")

        # Botonera de estado
        c1, c2, c3, _ = st.columns([0.12, 0.12, 0.12, 0.64])
        with c1:
            if st.button("✅ Cumple", key=f"{titulo}_yes"):
                st.session_state.status_810[titulo] = "yes"
        with c2:
            if st.button("❌ No cumple", key=f"{titulo}_no"):
                st.session_state.status_810[titulo] = "no"
        with c3:
            if st.button("⚪ No aplica", key=f"{titulo}_na"):
                st.session_state.status_810[titulo] = "na"

        # Estado visual
        estado = st.session_state.status_810[titulo]
        if estado == "yes":
            st.markdown("<div style='background:#e6ffed;padding:6px;border-radius:5px;'>✅ Cumple</div>", unsafe_allow_html=True)
        elif estado == "no":
            st.markdown(f"<div style='background:#ffe6e6;padding:6px;border-radius:5px;'>❌ No cumple — {recomendacion}</div>", unsafe_allow_html=True)
        elif estado == "na":
            st.markdown("<div style='background:#f2f2f2;padding:6px;border-radius:5px;'>⚪ No aplica</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background:#fff;padding:6px;border-radius:5px;'>Sin responder</div>", unsafe_allow_html=True)

        # Observación
        nota = st.text_area("Observación (opcional)", value=st.session_state.note_810.get(titulo, ""), key=f"{titulo}_nota")
        st.session_state.note_810[titulo] = nota

        # Evidencia
        if st.session_state.status_810[titulo] == "no":
            st.markdown("**Adjunta evidencia (JPG/PNG):**")
            files = st.file_uploader("Subir imágenes", type=["jpg","jpeg","png"], accept_multiple_files=True, key=f"upl_{titulo}")
            if files:
                caption = st.text_input("Descripción breve para estas imágenes (opcional)", key=f"cap_{titulo}")
                if st.button("Agregar evidencia", key=f"btn_add_{titulo}"):
                    for f in files:
                        st.session_state.evidence_810[titulo].append({
                            "name": f.name,
                            "bytes": f.read(),
                            "caption": caption or ""
                        })
                    st.success(f"Se agregaron {len(files)} imagen(es) a: {titulo}")
            ev_list = st.session_state.evidence_810.get(titulo, [])
            if ev_list:
                st.markdown("**Evidencia acumulada:**")
                cols = st.columns(4)
                for idx, ev in enumerate(ev_list):
                    with cols[idx % 4]:
                        st.image(ev["bytes"], caption=ev["caption"] or ev["name"], use_column_width=True)

        st.markdown("---")

# ------------------------------------------------------------------------------------
# MÉTRICAS DE CUMPLIMIENTO
# ------------------------------------------------------------------------------------
yes_count = sum(1 for v in st.session_state.status_810.values() if v == "yes")
no_count = sum(1 for v in st.session_state.status_810.values() if v == "no")
answered_count = yes_count + no_count
percent = round((yes_count / answered_count * 100), 1) if answered_count > 0 else 0.0
st.metric("Cumplimiento total (sobre ítems contestados)", f"{percent}%")
st.write(
    f"CUMPLE: {yes_count} — NO CUMPLE: {no_count} — "
    f"NO APLICA: {sum(1 for v in st.session_state.status_810.values() if v == 'na')} — "
    f"SIN RESPONDER: {sum(1 for v in st.session_state.status_810.values() if v == 'none')}"
)

# ------------------------------------------------------------------------------------
# CALCULADORA — Verificación de calorías declaradas (±20% fijo)
# ------------------------------------------------------------------------------------
st.header("Calculadora: Verificación de calorías declaradas (±20% tolerancia)")
with st.expander("Abrir calculadora de calorías declaradas vs calculadas"):
    colA, colB = st.columns(2)
    with colA:
        base = st.radio("Base de declaración", ["Por 100 g", "Por 100 mL"], index=0, key="base_cal")
        carb_g = st.number_input("Carbohidratos (g)", min_value=0.0, value=20.0, step=0.1, key="c_cal_carb")
        prot_g = st.number_input("Proteínas (g)", min_value=0.0, value=5.0, step=0.1, key="c_cal_prot")
        grasa_g = st.number_input("Grasas (g)", min_value=0.0, value=7.0, step=0.1, key="c_cal_grasa")
        kcal_decl = st.number_input("Calorías declaradas (kcal)", min_value=0.0, value=200.0, step=1.0, key="c_cal_decl")
    with colB:
        kcal_calc = 4.0 * carb_g + 4.0 * prot_g + 9.0 * grasa_g
        diff_abs = abs(kcal_calc - kcal_decl)
        diff_pct = (diff_abs / kcal_decl * 100.0) if kcal_decl > 0 else None
        st.write(f"**Calorías calculadas:** {kcal_calc:.1f} kcal")
        if diff_pct is not None:
            st.write(f"**Diferencia:** {diff_abs:.1f} kcal ({diff_pct:.1f}%)")
            if diff_pct <= 20.0:
                st.success("✅ Consistente: dentro de ±20% de tolerancia (Res. 810/2021 art. 14).")
            else:
                st.error("⚠️ Inconsistente: excede ±20% de tolerancia (Res. 810/2021 art. 14).")
        else:
            st.info("Ingrese calorías declaradas para evaluar la diferencia.")

# ------------------------------------------------------------------------------------
# CALCULADORA — Determinación de aplicabilidad de sellos (810/2492)
# ------------------------------------------------------------------------------------
st.header("Calculadora: Aplicabilidad de sellos de advertencia (810/2021 y 2492/2022)")
with st.expander("Abrir calculadora de sellos"):
    col1, col2 = st.columns([0.6, 0.4])
    with col1:
        estado_fisico = st.radio("Estado físico", ["Sólido / semisólido (por 100 g)", "Líquido (por 100 mL)"], index=0, key="sello_fisico")
        kcal = st.number_input("Calorías (kcal)", min_value=0.0, value=200.0, step=1.0, key="sello_kcal")
        azuc_tot = st.number_input("Azúcares totales (g)", min_value=0.0, value=10.0, step=0.1, key="sello_azu")
        grasa_sat = st.number_input("Grasa saturada (g)", min_value=0.0, value=2.0, step=0.1, key="sello_sat")
        grasa_trans = st.number_input("Grasa trans (g)", min_value=0.0, value=0.0, step=0.05, key="sello_trans")
        sodio_mg = st.number_input("Sodio (mg)", min_value=0.0, value=300.0, step=5.0, key="sello_sod")
        bebida_sin_energia = False
        if "Líquido" in estado_fisico:
            bebida_sin_energia = st.checkbox("¿Bebida sin aporte energético? (0 kcal por 100 mL)", value=False, key="sello_bebida0")

    with col2:
        kcal_azu_tot = 4.0 * azuc_tot
        pct_azu = 100.0 * kcal_azu_tot / kcal if kcal > 0 else 0.0
        pct_sat = 100.0 * (9.0 * grasa_sat) / kcal if kcal > 0 else 0.0
        pct_trans = 100.0 * (9.0 * grasa_trans) / kcal if kcal > 0 else 0.0

        criterio_sodio_a = (kcal > 0 and (sodio_mg / max(kcal, 1.0)) >= 1.0)  # mg/kcal >=1
        if "Sólido" in estado_fisico:
            criterio_sodio_b = (sodio_mg >= 300.0)
        else:
            if bebida_sin_energia:
                criterio_sodio_b = (sodio_mg >= 40.0)
            else:
                criterio_sodio_b = (sodio_mg / max(kcal, 1.0)) >= 1.0

        excede_azuc = pct_azu >= 10.0
        excede_sat = pct_sat >= 10.0
        excede_trans = pct_trans >= 1.0
        excede_sodio = criterio_sodio_a or criterio_sodio_b

        sellos = []
        if excede_azuc: sellos.append("EXCESO EN AZÚCARES")
        if excede_sat: sellos.append("EXCESO EN GRASAS SATURADAS")
        if excede_trans: sellos.append("EXCESO EN GRASAS TRANS")
        if excede_sodio: sellos.append("EXCESO EN SODIO")

        if len(sellos) == 0:
            st.success("✅ No requiere sellos según los límites ingresados.")
        else:
            st.error("⚠️ Debe llevar sello(s): " + ", ".join(sellos))

        st.caption("Umbrales: azúcares ≥10% kcal; saturadas ≥10%; trans ≥1%; sodio ≥1 mg/kcal o ≥300 mg/100 g (sólidos) y ≥40 mg/100 mL (bebidas sin energía).")

# ------------------------------------------------------------------------------------
# UBICACIÓN Y TAMAÑO (TABLA 17) — Sin imágenes, solo cálculo
# ------------------------------------------------------------------------------------
st.header("Ubicación y tamaño del sello (Tabla 17)")
st.markdown("• Ubicar en el **tercio superior** de la cara principal de exhibición, visible y sin obstrucciones. "
            "• El **lado mínimo** del octágono depende del área de la cara principal (Tabla 17).")
st.dataframe(df_tabla17, use_container_width=True)

colA, colB = st.columns([0.55, 0.45])
with colA:
    area_sel = st.selectbox("Rango de área de la cara principal (cm²)", options=[r[0] for r in TABLA_17 if r[0] != "< 30 cm²"], key="t17_area")
    num_sellos = st.selectbox("Cantidad de sellos", options=[1,2,3,4], index=1, key="t17_n")
    espaciado_cm = st.number_input("Separación estimada entre sellos (cm)", min_value=0.0, value=0.2, step=0.1, key="t17_sep")
with colB:
    ancho_cara_cm = None
    if area_sel == "> 300 cm²":
        ancho_cara_cm = st.number_input("Ancho de la cara principal (cm) para calcular 15% del lado", min_value=1.0, value=10.0, step=0.5, key="t17_ancho")

def get_lado_sello(area_key: str, ancho_cara=None):
    if area_key == "> 300 cm²":
        if ancho_cara is None:
            return None
        return round(0.15 * float(ancho_cara), 2)
    for k, v in TABLA_17:
        if k == area_key:
            return v
    return None

lado_cm = get_lado_sello(area_sel, ancho_cara_cm)
if lado_cm is None:
    st.warning("Para el rango seleccionado, ingresa el **ancho de la cara principal (cm)** para calcular el 15% del lado del sello.")
else:
    ancho_total = round(num_sellos * lado_cm + (num_sellos - 1) * espaciado_cm, 2)
    st.success(f"**Resultado:** Lado mínimo del sello = {lado_cm} cm · Ancho total estimado ({num_sellos} sello(s)) ≈ {ancho_total} cm.")

# ------------------------------------------------------------------------------------
# RESUMEN Y EXPORTACIÓN A PDF (A4 horizontal con portada)
# ------------------------------------------------------------------------------------
st.header("Exportar informe")
# Armar DataFrame final
rows = []
for items in CATEGORIAS.values():
    for (titulo, _, recomendacion) in items:
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
            "Observación": st.session_state.note_810.get(titulo, "")
        })
df = pd.DataFrame(rows, columns=["Ítem", "Estado", "Recomendación", "Observación"])

def generar_pdf(df: pd.DataFrame):
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=8*mm, rightMargin=8*mm,
        topMargin=8*mm, bottomMargin=8*mm
    )
    styles = getSampleStyleSheet()
    style_header = ParagraphStyle("header", parent=styles["Normal"], fontSize=9, leading=11)
    style_cell   = ParagraphStyle("cell",   parent=styles["Normal"], fontSize=8, leading=10)

    story = []

    # Portada (encabezado)
    fecha_str = datetime.now().strftime("%Y-%m-%d")
    inv_str = invima_registro or "-"
    inv_estado = "ACTIVO y coincidente" if invima_estado_activo else "No verificado / No activo / No coincide"
    portada = (
        f"<b>Informe de verificación — Resoluciones 810/2021 y 2492/2022</b><br/>"
        f"<b>Fecha:</b> {fecha_str} &nbsp;&nbsp; "
        f"<b>Producto:</b> {producto or '-'} &nbsp;&nbsp; "
        f"<b>Proveedor:</b> {proveedor or '-'} &nbsp;&nbsp; "
        f"<b>Responsable:</b> {responsable or '-'} &nbsp;&nbsp; "
        f"<b>Tipo:</b> {categoria_producto or '-'}<br/>"
        f"<b>Registro INVIMA:</b> {inv_str} &nbsp;&nbsp; <b>Estado en portal:</b> {inv_estado}"
    )
    if invima_url.strip():
        portada += f" &nbsp;&nbsp; <b>Consulta:</b> {invima_url}"
    story.append(Paragraph(portada, style_header))
    story.append(Spacer(1, 5*mm))

    # Métrica
    yes_c = sum(1 for v in st.session_state.status_810.values() if v == "yes")
    no_c = sum(1 for v in st.session_state.status_810.values() if v == "no")
    ans_c = yes_c + no_c
    pct = round((yes_c / ans_c * 100), 1) if ans_c > 0 else 0.0
    story.append(Paragraph(f"<b>Cumplimiento (sobre ítems contestados):</b> {pct}%", style_header))
    story.append(Spacer(1, 4*mm))

    # Tabla
    data = [["Ítem", "Estado", "Recomendación", "Observación"]]
    for _, r in df.iterrows():
        obs = r["Observación"] or "-"
        if obs != "-":
            obs = split_observation_text(obs, chunk=100)
        data.append([
            Paragraph(str(r["Ítem"]),          style_cell),
            Paragraph(str(r["Estado"]),        style_cell),
            Paragraph(str(r["Recomendación"]), style_cell),
            Paragraph(obs,                     style_cell),
        ])

    col_widths = [80*mm, 25*mm, 110*mm, 50*mm]
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f2f2f2")),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,0), 9),
        ("GRID",       (0,0), (-1,-1), 0.25, colors.grey),
        ("VALIGN",     (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",(0,0), (-1,-1), 3),
        ("RIGHTPADDING",(0,0), (-1,-1), 3),
    ]))
    story.append(tbl)

    # Evidencia fotográfica (si existe)
    any_ev = any(len(v)>0 for v in st.session_state.evidence_810.values())
    if any_ev:
        story.append(PageBreak())
        story.append(Paragraph("<b>Evidencia fotográfica</b>", style_header))
        story.append(Spacer(1, 3*mm))

        # Guardar imágenes temporales para ReportLab
        with tempfile.TemporaryDirectory() as tmpdir:
            for titulo, ev_list in st.session_state.evidence_810.items():
                if not ev_list:
                    continue
                story.append(Paragraph(f"<b>Ítem:</b> {titulo}", style_header))
                story.append(Spacer(1, 2*mm))
                # Mostrar hasta 4 por fila aprox (dependiendo de tamaño)
                row_imgs = []
                for idx, ev in enumerate(ev_list):
                    img_path = os.path.join(tmpdir, f"ev_{hash(titulo)}_{idx}.png")
                    with open(img_path, "wb") as f:
                        f.write(ev["bytes"])
                    # Insertar imagen con ancho fijo para mosaico
                    img = RLImage(img_path, width=85*mm, height=55*mm)  # tamaño razonable
                    story.append(img)
                    if ev.get("caption"):
                        story.append(Paragraph(ev["caption"], style_cell))
                    story.append(Spacer(1, 3*mm))
                story.append(Spacer(1, 5*mm))

    doc.build(story)
    buf.seek(0)
    return buf

st.subheader("Generar informe PDF (A4 horizontal)")
if st.button("Generar PDF"):
    pdf_buffer = generar_pdf(df)
    file_name = (nombre_pdf.strip() or f"informe_810_2492_{datetime.now().strftime('%Y%m%d')}") + ".pdf"
    st.download_button("Descargar PDF", data=pdf_buffer, file_name=file_name, mime="application/pdf")
