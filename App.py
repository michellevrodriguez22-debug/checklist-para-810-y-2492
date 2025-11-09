
import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak

# ------------------------------------------------------------------
# APP 810 + 2492 (tabla nutricional, declaraciones y sellos frontales)
# Con evidencia fotográfica por ítem NO CUMPLE y exporte a PDF
# ------------------------------------------------------------------
st.set_page_config(page_title="Checklist Etiquetado — Res. 810/2021 y 2492/2022", layout="wide")
st.title("Checklist de etiquetado nutricional — Resoluciones 810/2021 y 2492/2022 (Colombia)")

# ------------------------------------------------------------------
# SIDEBAR: Datos generales
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

# ------------------------------------------------------------------
# Definición ordenada de criterios (flujo de revisión)
# Abarca: Tabla nutricional, declaraciones, sellos frontales, aspectos gráficos y control.
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
         "Verificar si el alimento procesado/ultraprocesado supera los límites para azúcares libres, grasas saturadas, grasas trans o sodio; o si contiene edulcorantes (calóricos o no).",
         "Evaluar composición y decidir si requiere sellos.",
         "Res. 810/2021 art. 32 (mod. por 2492/2022)."),
        ("Límites de nutrientes críticos (criterios OPS)",
         "Azúcares libres ≥10% de energía total; grasas saturadas ≥10% de energía total; grasas trans ≥1% de energía total; sodio ≥1 mg/kcal o ≥300 mg/100 g (sólidos). Bebidas sin aporte energético: sodio ≥40 mg/100 mL.",
         "Comparar formulación vs. límites y aplicar sello si corresponde.",
         "Res. 810/2021 (Tabla de límites) mod. por Res. 2492/2022."),
        ("Sello 'Contiene edulcorante'",
         "Cuando el producto contenga edulcorantes, incluir sello de advertencia ('Contiene edulcorante, no recomendable en niños').",
         "Agregar sello correspondiente si contiene edulcorantes.",
         "Res. 2492/2022 (parámetros para edulcorantes)."),
        ("Forma, color y tipografía del sello",
         "Usar octágono negro con borde blanco, texto en mayúsculas de alto contraste ('EXCESO EN ...') según tipografía permitida.",
         "Ajustar forma, color y tipografía al estándar.",
         "Res. 2492/2022 (especificaciones gráficas)."),
        ("Ubicación y tamaño del sello (Tabla 17)",
         "Ubicar los sellos en el tercio superior de la cara principal de exhibición, sin obstrucciones. Dimensiones mínimas según el área principal del envase (Tabla 17).",
         "Reubicar/aumentar tamaño conforme a Tabla 17.",
         "Res. 810/2021 art. 32 y Tabla 17 (mod. 2492/2022)."),
        ("Excepciones a sellos",
         "Aplicar exenciones (p. ej., alimentos no procesados o mínimamente procesados, fórmulas infantiles, productos artesanales/típicos definidos, ciertos a granel, etc.).",
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
         "Contar con resultados de laboratorio (preferible acreditado) que soporten los valores declarados; ajustar frente a tolerancias.",
         "Solicitar/adjuntar certificado de análisis vigente.",
         "Res. 810/2021 art. 14."),
        ("Fichas técnicas y especificaciones de ingredientes",
         "Disponibilidad de fichas/especificaciones que respalden composición, aditivos, edulcorantes y contenido de nutrientes críticos.",
         "Mantener documentación de respaldo actualizada.",
         "Res. 810/2021 (soporte documental para declaraciones y sellos)."),
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

        # Para la "Tabla 17" se añade un recordatorio informativo de tamaños mínimos
        if titulo == "Ubicación y tamaño del sello (Tabla 17)":
            st.markdown("**Tabla 17 (resumen informativo):** dimensión mínima del octágono según área de la cara principal del envase. "
                        "Si el área es < 30 cm²: rotular envase secundario o incluir mecanismo de consulta (p. ej. QR); "
                        "≥30 a <35 cm²: 1,7 cm; ≥35 a <40: 1,8 cm; ≥40 a <50: 2,0 cm; ≥50 a <60: 2,2 cm; "
                        "≥60 a <80: 2,5 cm; ≥80 a <100: 2,8 cm; ≥100 a <125: 3,1 cm; ≥125 a <150: 3,4 cm; "
                        "≥150 a <200: 3,9 cm; ≥200 a <250: 4,4 cm; ≥250 a <300: 4,8 cm; >300 cm²: 15% del lado de la cara principal.")

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
    # Encabezado según confirmación del usuario (sin marcas comerciales)
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
