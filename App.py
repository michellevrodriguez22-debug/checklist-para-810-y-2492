
import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

# ------------------------------------------------------------------
# APP 810 + 2492 — con calculadora ajustada y guía visual estática
# ------------------------------------------------------------------
st.set_page_config(page_title="Checklist Etiquetado — 810/2021 y 2492/2022", layout="wide")
st.title("Checklist etiquetado nutricional — Resoluciones 810/2021 y 2492/2022 (Colombia)")

# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
st.sidebar.header("Datos de la verificación")
producto = st.sidebar.text_input("Nombre del producto")
categoria_producto = st.sidebar.selectbox("Tipo", ["Producto terminado", "Materia prima (uso industrial)", "Ambos"])
proveedor = st.sidebar.text_input("Proveedor / Fabricante")
responsable = st.sidebar.text_input("Responsable de la verificación")
invima_num = st.sidebar.text_input("Registro sanitario INVIMA (si aplica)")
invima_url = st.sidebar.text_input("URL consulta INVIMA (opcional)")
invima_estado_ok = st.sidebar.checkbox("Verificado en INVIMA como ACTIVO y coincidente", value=False)
nombre_pdf = st.sidebar.text_input("Nombre del PDF (sin .pdf)", f"informe_810_2492_{datetime.now().strftime('%Y%m%d')}")
filter_no = st.sidebar.checkbox("Mostrar solo 'No cumple'", value=False)

st.sidebar.caption("Esta app resume requisitos vigentes en 810/2021 y 2492/2022.")

# ------------------------------------------------------------------
# Criterios y flujo
# ------------------------------------------------------------------
CATEGORIAS = {
    "1. Identificación inicial y aplicabilidad": [
        ("Registro sanitario INVIMA visible y vigente",
         "Debe estar impreso en el empaque, legible e indeleble. Verificar en portal INVIMA que está ACTIVO y que nombre/titular/fabricante coinciden con lo impreso.",
         "Imprimir el número INVIMA en el envase y verificar vigencia y coincidencia en el portal.",
         "Control sanitario general; Res. 810/2021 art. 2 (aplicabilidad)."),

        ("Idioma español (información obligatoria)",
         "Toda la información obligatoria debe estar en español; en importados, adherir rótulo complementario con traducción completa.",
         "Agregar rótulo complementario en español cuando aplique.",
         "Res. 810/2021 art. 27.1.3"),

        ("Determinación de aplicabilidad (consumidor final vs uso industrial)",
         "Si es para consumidor final: debe tener tabla nutricional y evaluar sellos. Si es materia prima para uso industrial: se exceptúa de tabla/sellos, conservando trazabilidad.",
         "Clasificar correctamente el producto para aplicar requisitos.",
         "Res. 810/2021 art. 2; Res. 2492/2022 (modifica exenciones)."),
    ],

    "2. Tabla nutricional (estructura y formato)": [
        ("Presencia de la tabla nutricional",
         "Los alimentos destinados al consumidor final deben incluir tabla nutricional (con exenciones específicas: no envasados, mínimamente procesados, algunos a granel, etc.).",
         "Incluir la tabla cuando aplique (según destino y exenciones).",
         "Res. 810/2021 arts. 8–10."),

        ("Forma de presentación: por 100 g / 100 mL y por porción",
         "Declaración como mínimo por 100 g/100 mL y por porción; coherencia con el estado físico (sólido/líquido).",
         "Agregar ambos ejes (100 g/100 mL y por porción).",
         "Res. 810/2021 art. 12."),

        ("Número de porciones por envase",
         "Indicar el número de porciones por envase (salvo peso variable).",
         "Agregar número de porciones por envase.",
         "Res. 810/2021 art. 12 y par. 2 art. 2 (mod. 2492/2022)."),

        ("Nutrientes mínimos obligatorios",
         "Energía (kcal), grasa total, grasa saturada, grasa trans, carbohidratos, azúcares totales, proteínas y sodio (con unidades normativas).",
         "Asegurar declaración de todos los nutrientes mínimos.",
         "Res. 810/2021 arts. 8–10."),

        ("Micronutrientes (si se declaran)",
         "Cumplir umbrales permitidos y presentarlos en bloque separado por línea, sin inducir a error.",
         "Ajustar declaración y separación de micronutrientes.",
         "Res. 810/2021 art. 15 y 28.3."),

        ("Tolerancias analíticas",
         "La diferencia entre valores declarados y análisis no debe exceder ±20% (salvo excepciones).",
         "Verificar resultados y ajustar si excede tolerancias.",
         "Res. 810/2021 art. 14."),

        ("Formato, legibilidad y tipografía de la tabla",
         "Tipografía clara, contraste adecuado y disposición conforme a la resolución; evitar cortes o ilegibilidad.",
         "Ajustar formato/contraste y estructura.",
         "Res. 810/2021 art. 27."),
    ],

    "3. Declaraciones": [
        ("Declaraciones nutricionales ('fuente de', 'alto en')",
         "Solo si cumplen criterios de contenido y perfil de nutrientes (no deben exhibir sellos que las invaliden). Sustentar con %VD.",
         "Mantener solo las permitidas y sustentadas; retirar las que no cumplen.",
         "Res. 810/2021 art. 16 y 25.4 (mod. 2492/2022)."),

        ("Declaraciones de salud/funcionales",
         "Deben ser veraces, no engañosas y estar autorizadas por el MSPS cuando aplique. No atribuir propiedades medicinales.",
         "Usar solo declaraciones autorizadas y sustentadas.",
         "Res. 810/2021 art. 25."),

        ("Prohibición de declaraciones engañosas",
         "Evitar beneficios no sustentados o mensajes confusos sobre composición/efectos.",
         "Eliminar mensajes confusos o engañosos.",
         "Res. 810/2021 art. 25.5."),
    ],

    "4. Etiquetado frontal de advertencia (sellos)": [
        ("Determinación de aplicabilidad de sellos",
         "Determinar si requiere sellos por exceso en azúcares, grasas saturadas, grasas trans y sodio (diferenciando criterios de sólidos y líquidos).",
         "Evaluar formulación vs límites; documentar por qué aplica/no aplica sello(s).",
         "Res. 810/2021 art. 32 (mod. 2492/2022); criterios OPS."),

        ("Límites de nutrientes críticos (criterios OPS)",
         "Azúcares libres ≥10% kcal totales; grasas saturadas ≥10%; grasas trans ≥1%; sodio ≥1 mg/kcal o ≥300 mg/100 g (sólidos). En bebidas sin energía: sodio ≥40 mg/100 mL.",
         "Comparar composición vs límites.",
         "Res. 810/2021 (mod. 2492/2022)."),

        ("Sello 'Contiene edulcorante'",
         "Si contiene edulcorantes (calóricos o no), incluir el sello correspondiente ('Contiene edulcorante, no recomendable en niños').",
         "Agregar el sello si aplica.",
         "Res. 2492/2022."),

        ("Forma, color y tipografía del sello",
         "Octágono negro, borde blanco y texto en mayúsculas de alto contraste ('EXCESO EN ...').",
         "Ajustar forma, color y tipografía.",
         "Res. 2492/2022 (especificaciones gráficas)."),

        ("Ubicación y tamaño del sello (Tabla 17)",
         "Ubicar en el tercio superior de la cara principal (visible, sin obstrucciones). Tamaño mínimo del octágono según el área principal.",
         "Reubicar/aumentar tamaño según Tabla 17.",
         "Res. 810/2021 art. 32; Tabla 17 mod. 2492/2022."),

        ("Excepciones a sellos",
         "Aplicar exenciones previstas (no/minimamente procesados, fórmulas infantiles, artesanales/típicos definidos, ciertos a granel, etc.).",
         "Justificar la exención si corresponde.",
         "Res. 810/2021 art. 2 (mod. 2492/2022)."),
    ],

    "5. Requisitos gráficos generales": [
        ("Legibilidad y contraste del rótulo",
         "Información visible, indeleble y con contraste suficiente respecto del fondo. Evitar pliegues/cortes que oculten texto.",
         "Mejorar contraste/tamaño y asegurar indelebilidad.",
         "Res. 810/2021 art. 27."),
        ("Ubicación visible (cara principal de exhibición)",
         "Colocar elementos obligatorios en la cara de fácil lectura/visualización por el consumidor.",
         "Reubicar contenido si no es visible.",
         "Res. 810/2021 art. 27."),
    ],

    "6. Control y evidencia": [
        ("Certificado de análisis (soporte de la tabla)",
         "Resultados de laboratorio (preferible acreditado) que soporten valores declarados; ajustar frente a tolerancias.",
         "Solicitar/adjuntar certificado vigente.",
         "Res. 810/2021 art. 14."),
        ("Fichas técnicas y especificaciones de ingredientes",
          "Fichas que respalden composición, aditivos, edulcorantes y contenido de nutrientes críticos.",
          "Mantener documentación actualizada.",
          "Res. 810/2021 (soporte documental)."),
    ],
}

APLICA = {
    k: ("Producto terminado" if "uso industrial" not in k.lower() else "Materia prima")
    for k in [i[0] for c in CATEGORIAS.values() for i in c]
}
APLICA["Determinación de aplicabilidad (consumidor final vs uso industrial)"] = "Ambos"
APLICA["Legibilidad y contraste del rótulo"] = "Ambos"
APLICA["Ubicación visible (cara principal de exhibición)"] = "Ambos"
APLICA["Fichas técnicas y especificaciones de ingredientes"] = "Ambos"

# Estado y notas
if "status_810" not in st.session_state:
    st.session_state.status_810 = {i[0]: "none" for c in CATEGORIAS.values() for i in c}
if "note_810" not in st.session_state:
    st.session_state.note_810 = {i[0]: "" for c in CATEGORIAS.values() for i in c}
if "evidence_810" not in st.session_state:
    st.session_state.evidence_810 = {i[0]: [] for c in CATEGORIAS.values() for i in c}

st.header("Checklist según flujo de revisión (810/2021 y 2492/2022)")
st.markdown("Responde con ✅ Cumple / ❌ No cumple / ⚪ No aplica. Si marcas **No cumple**, puedes **adjuntar evidencia fotográfica**.")

# Métrica
def compute_metrics():
    yes = sum(1 for v in st.session_state.status_810.values() if v == "yes")
    no = sum(1 for v in st.session_state.status_810.values() if v == "no")
    answered = yes + no
    pct = round((yes / answered * 100), 1) if answered > 0 else 0.0
    return yes, no, answered, pct

yes_count = sum(1 for v in st.session_state.status_810.values() if v == "yes")
no_count  = sum(1 for v in st.session_state.status_810.values() if v == "no")
answered_count = yes_count + no_count
percent = round((yes_count / answered_count * 100), 1) if answered_count > 0 else 0.0
st.metric("Cumplimiento total (sobre ítems contestados)", f"{percent}%")

# Tabla 17
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

# Helpers
def energia_por_gramos(gr, kcal_por_g):
    if gr is None: return None
    try:
        return float(gr) * float(kcal_por_g)
    except:
        return None

def porcentaje_energia(kcal_nutriente, kcal_total):
    if kcal_nutriente is None or kcal_total is None or kcal_total == 0:
        return None
    return 100.0 * float(kcal_nutriente) / float(kcal_total)

# Render
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
        st.markdown(f"**Aplica a:** {APLICA.get(titulo, 'Producto terminado')}")

        # --- Calculadora de aplicabilidad de sellos (sin checkbox y con 'Calorías (kcal)') ----
        if titulo == "Determinación de aplicabilidad de sellos":
            with st.expander("Abrir calculadora de aplicabilidad de sellos"):
                col1, col2 = st.columns([0.6, 0.4])
                with col1:
                    estado_fisico = st.radio("Estado físico", ["Sólido / semisólido (por 100 g)", "Líquido (por 100 mL)"], index=0)
                    st.markdown("**Ingrese por 100 g / 100 mL:**")
                    kcal = st.number_input("Calorías (kcal)", min_value=0.0, value=200.0, step=1.0, key="kcal_input")
                    azuc_tot = st.number_input("Azúcares totales (g)", min_value=0.0, value=10.0, step=0.1, key="azu_tot_input")
                    grasa_sat = st.number_input("Grasa saturada (g)", min_value=0.0, value=2.0, step=0.1, key="sat_input")
                    grasa_trans = st.number_input("Grasa trans (g)", min_value=0.0, value=0.0, step=0.05, key="trans_input")
                    sodio_mg = st.number_input("Sodio (mg)", min_value=0.0, value=300.0, step=5.0, key="sod_input")
                    bebida_sin_energia = False
                    if "Líquido" in estado_fisico:
                        bebida_sin_energia = st.checkbox("¿Bebida sin aporte energético? (0 kcal por 100 mL)", value=False)

                with col2:
                    # Cálculos (azúcares totales -> 4 kcal/g)
                    kcal_azu_tot = energia_por_gramos(azuc_tot, 4.0)
                    pct_azu = porcentaje_energia(kcal_azu_tot, kcal)
                    kcal_sat = energia_por_gramos(grasa_sat, 9.0)
                    pct_sat = porcentaje_energia(kcal_sat, kcal)
                    kcal_trans = energia_por_gramos(grasa_trans, 9.0)
                    pct_trans = porcentaje_energia(kcal_trans, kcal)

                    criterio_sodio_a = (kcal > 0 and (sodio_mg / max(kcal, 1.0)) >= 1.0)  # mg/kcal >=1
                    if "Sólido" in estado_fisico:
                        criterio_sodio_b = (sodio_mg >= 300.0)
                    else:
                        if bebida_sin_energia:
                            criterio_sodio_b = (sodio_mg >= 40.0)
                        else:
                            criterio_sodio_b = (sodio_mg / max(kcal, 1.0)) >= 1.0

                    excede_azuc = (pct_azu is not None) and (pct_azu >= 10.0)
                    excede_sat = (pct_sat is not None) and (pct_sat >= 10.0)
                    excede_trans = (pct_trans is not None) and (pct_trans >= 1.0)
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

                    st.caption("Umbrales de referencia: azúcares libres ≥10% kcal; saturadas ≥10%; trans ≥1%; sodio ≥1 mg/kcal o ≥300 mg/100 g (sólidos) y 40 mg/100 mL en bebidas sin energía.")

        # --- Tabla 17: sin simulación, con cálculo y guía visual PNG ----
        if titulo == "Ubicación y tamaño del sello (Tabla 17)":
            st.markdown("> **Guía rápida:** Los sellos van en el **tercio superior** de la cara principal, visibles y sin obstrucciones. El **lado mínimo** del octágono depende del área de la cara (Tabla 17).")

            st.dataframe(df_tabla17, use_container_width=True)

            colA, colB = st.columns([0.55, 0.45])
            with colA:
                area_opcion = st.selectbox(
                    "Rango de área de la cara principal (cm²)",
                    options=[r[0] for r in TABLA_17 if r[0] != "< 30 cm²"],
                    key="area_tabla17_sel"
                )
                num_sellos = st.selectbox("Cantidad de sellos", options=[1,2,3,4], index=1, key="num_sellos_sel")
                espaciado_cm = st.number_input("Separación estimada entre sellos (cm)", min_value=0.0, value=0.2, step=0.1, key="esp_sel")

            with colB:
                ancho_cara_cm = None
                if area_opcion == "> 300 cm²":
                    ancho_cara_cm = st.number_input("Ancho de la cara principal (cm) para calcular el 15% del lado", min_value=1.0, value=10.0, step=0.5, key="ancho_cara_calc")

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
                st.success(f"**Resultado:** Lado mínimo del sello = {lado_cm} cm · Ancho total estimado para {num_sellos} sello(s) ≈ {ancho_total} cm.")

            st.image("guia_tercio_superior.png", caption="Referencia: 'Tercio superior — ubicación de los sellos'", use_column_width=True)

        # Estado
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

        est = st.session_state.status_810[titulo]
        if est == "yes":
            st.markdown("<div style='background:#e6ffed;padding:6px;border-radius:5px;'>✅ Cumple</div>", unsafe_allow_html=True)
        elif est == "no":
            st.markdown(f"<div style='background:#ffe6e6;padding:6px;border-radius:5px;'>❌ No cumple — {recomendacion}</div>", unsafe_allow_html=True)
        elif est == "na":
            st.markdown("<div style='background:#f2f2f2;padding:6px;border-radius:5px;'>⚪ No aplica</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background:#fff;padding:6px;border-radius:5px;'>Sin responder</div>", unsafe_allow_html=True)

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

        st.markdown("---")

# Resumen
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
    story.append(Paragraph("<b>Informe de verificación — Resoluciones 810/2021 y 2492/2022</b>", style_header))
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
