import streamlit as st
import pandas as pd
import base64
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image as RLPlatypusImage

# ------------------------------------------------------------
# CONFIGURACIÓN INICIAL
# ------------------------------------------------------------
st.set_page_config(page_title="Checklist de Etiquetado Nutricional — 810/2021 y 2492/2022", layout="wide")
st.title("Checklist de Etiquetado Nutricional — Resoluciones 810/2021 y 2492/2022 (Colombia)")

# Introducción (extendida)
st.markdown(
    "> Este checklist se basa en las **Resoluciones 810 de 2021** y **2492 de 2022**, "
    "que establecen los requisitos técnicos para el **etiquetado nutricional** y el **etiquetado frontal de advertencia** "
    "en alimentos y bebidas envasadas destinados al consumo humano en Colombia."
)

# ------------------------------------------------------------
# SIDEBAR: Datos de la verificación
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# TABLA 17 — referencia (informativa en pantalla)
# ------------------------------------------------------------
TABLA_17 = [
    ("< 30 cm²", "Rotular en envase secundario o incluir codigo QR o página para consultar"),
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

# ------------------------------------------------------------
# CHECKLIST — 810/2021 y 2492/2022 (orden completo)
# ------------------------------------------------------------
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

APLICA = {k: "Producto terminado" for cat in CATEGORIAS.values() for (k,_,_) in cat}

# ------------------------------------------------------------
# ESTADO, NOTAS Y EVIDENCIA (persistente con base64)
# ------------------------------------------------------------
if "status_810" not in st.session_state:
    st.session_state.status_810 = {i[0]: "none" for c in CATEGORIAS.values() for i in c}
if "note_810" not in st.session_state:
    st.session_state.note_810 = {i[0]: "" for c in CATEGORIAS.values() for i in c}
if "evidence_810" not in st.session_state:
    st.session_state.evidence_810 = {i[0]: [] for c in CATEGORIAS.values() for i in c}

def split_observation_text(text: str, chunk: int = 100) -> str:
    if not text:
        return ""
    s = str(text)
    if len(s) <= chunk:
        return s
    parts = [s[i:i+chunk] for i in range(0, len(s), chunk)]
    return "\\n".join(parts)

# ------------------------------------------------------------
# RENDER DEL CHECKLIST (con herramientas integradas por ítem)
# ------------------------------------------------------------
st.header("Checklist")
st.markdown("Responde con ✅ Cumple / ❌ No cumple / ⚪ No aplica. Si marcas **No cumple**, podrás **adjuntar evidencia**.")

for categoria, items in CATEGORIAS.items():
    st.subheader(categoria)
    for (titulo, que_verificar, referencia) in items:
        estado = st.session_state.status_810.get(titulo, "none")
        if solo_no and estado != "no":
            continue

        st.markdown(f"### {titulo}")
        st.markdown(f"**Qué verificar:** {que_verificar}")
        st.markdown(f"**Referencia normativa:** {referencia}")
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
            st.markdown("<div style='background:#ffe6e6;padding:6px;border-radius:5px;'>❌ No cumple</div>", unsafe_allow_html=True)
        elif estado == "na":
            st.markdown("<div style='background:#f2f2f2;padding:6px;border-radius:5px;'>⚪ No aplica</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background:#fff;padding:6px;border-radius:5px;'>Sin responder</div>", unsafe_allow_html=True)

        # Herramientas integradas (cuadros azul #e6f0ff)
        if titulo == "Verificación de calorías declaradas (±20% tolerancia)":
            st.markdown("<div style='background:#e6f0ff;padding:10px;border-radius:8px;'><b>Herramienta:</b> Verifique el valor energético declarado vs calculado.</div>", unsafe_allow_html=True)
            colA  = st.columns(2)
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
        
        if titulo == "Determinación de aplicabilidad de sellos":
            st.markdown(
                "<div style='background:#e6f0ff;padding:10px;border-radius:8px;'>"
                "<b>Herramienta:</b> Determinación de aplicabilidad de sellos según Res. 810/2021 Art. 25 y Tabla 3 "
                "(modificada por Res. 2492/2022)."
                "</div>",
                unsafe_allow_html=True
            )

            col1, col2 = st.columns(2)

            # -------------------------------
            # ENTRADAS
            # -------------------------------
            with col1:
                base = st.radio(
                    "Base de evaluación",
                    ["Por 100 g", "Por 100 mL"],
                    index=0,
                    key="base_sellos"
                )

                kcal_totales = st.number_input(
                    "Calorías totales (kcal)",
                    min_value=0.0,
                    step=1.0,
                    key="sellos_kcal"
                )

                azucares_para_sellos_g = st.number_input(
                    "Azúcares para evaluación de sellos (g)",
                    help=(
                        "Corresponde a los AZÚCARES LIBRES según Res. 3803 de 2016: "
                        "azúcares añadidos + azúcares provenientes de jugos, concentrados o purés. "
                        "No usar azúcares totales si el producto contiene fruta entera o lactosa natural."
                    ),
                    min_value=0.0,
                    step=0.1,
                    key="sellos_azucares_libres"
                )

                grasas_saturadas = st.number_input(
                    "Grasas saturadas (g)",
                    min_value=0.0,
                    step=0.1,
                    key="sellos_sat"
                )

                grasas_trans_mg = st.number_input(
                    "Grasas trans (mg)",
                    min_value=0.0,
                    step=0.01,
                    key="sellos_trans"
                )

                sodio_mg = st.number_input(
                    "Sodio (mg)",
                    min_value=0.0,
                    step=1.0,
                    key="sellos_sodio"
                )

                contiene_edulcorante = st.checkbox(
                    "¿Contiene edulcorantes (calóricos o no calóricos)?",
                    key="sellos_edulcorante"
                )

                bebida_sin_calorias = st.checkbox(
                    "¿Es bebida sin aporte energético?",
                    key="bebida_sin_kcal"
                )

            # -------------------------------
            # CÁLCULOS SEGÚN RES. 810 / 2492
            # -------------------------------
            # Conversión de mg a g para grasas trans
            grasas_trans_g = grasas_trans_mg / 1000  # mg → g
            
            # Azúcares
            pct_azucar = (azucares_para_sellos_g * 4 / kcal_totales * 100) if kcal_totales > 0 else 0

            # Grasas saturadas
            pct_sat = (grasas_saturadas * 9 / kcal_totales * 100) if kcal_totales > 0 else 0

            # Grasas trans
            pct_trans = (grasas_trans_g * 9 / kcal_totales * 100) if kcal_totales > 0 else 0

            # Sodio – cálculo 1 (relación sodio/kcal)
            rel_sodio_kcal = (sodio_mg / kcal_totales) if kcal_totales > 0 else 0

            # -------------------------------
            # RESULTADO
            # -------------------------------
            with col2:
                st.markdown("### Resultado normativo (Res. 810/2021 – Res. 2492/2022)")

                aplica_sellos = []

                # AZÚCARES
                if pct_azucar >= 10:
                    aplica_sellos.append(f"❗ EXCESO EN AZÚCARES ({pct_azucar:.1f}% kcal)")

                # GRASAS SATURADAS
                if pct_sat >= 10:
                    aplica_sellos.append(f"❗ EXCESO EN GRASAS SATURADAS ({pct_sat:.1f}% kcal)")

                # GRASAS TRANS
                if pct_trans >= 1:
                    aplica_sellos.append(f"❗ EXCESO EN GRASAS TRANS ({pct_trans:.1f}% kcal)")

                # SODIO
                sodio_exceso = False

                if not bebida_sin_calorias and rel_sodio_kcal >= 1:
                    sodio_exceso = True

                if not bebida_sin_calorias and sodio_mg >= 300:
                    sodio_exceso = True

                if bebida_sin_calorias and sodio_mg >= 40:
                    sodio_exceso = True

                if sodio_exceso:
                    aplica_sellos.append("❗ EXCESO EN SODIO")

                # EDULCORANTE
                if contiene_edulcorante:
                    aplica_sellos.append("⚠️ CONTIENE EDULCORANTE")

                if aplica_sellos:
                    st.error("Aplican los siguientes sellos:")
                    for s in aplica_sellos:
                        st.write(f"- {s}")
                else:
                    st.success("✅ No aplica ningún sello frontal de advertencia")

            # -------------------------------
            # OBSERVACIÓN
            # -------------------------------
            nota = st.text_area(
                "Observación (opcional)",
                value=st.session_state.note_810.get(titulo, ""),
                key=f"{titulo}_nota"
            )
            st.session_state.note_810[titulo] = nota

        st.markdown("---")

if titulo == "Ubicación y tamaño de sellos (Tabla 17)":

    st.markdown("<div style='background:#e6f0ff;padding:10px;border-radius:8px;'><b>Herramienta:</b> Verificación de tamaño y ubicación de sellos según Tabla 17.</div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='background:#e6f0ff;padding:10px;border-radius:8px;'>"
        "<b>Herramienta:</b> Verificación de tamaño y ubicación de sellos según Tabla 17."
        "</div>",
        unsafe_allow_html=True
    )

    # -------------------------------
    # ENTRADAS (CON KEY 🔑)
    # ENTRADAS
    # -------------------------------
    area_cara_cm2 = st.number_input(
        "Área de la cara principal (cm²)",
        min_value=0.0,
        step=1.0,
        key="area_cara"
    )

    ancho_cara_cm = st.number_input(
        "Ancho de la cara principal (cm)",
        min_value=0.0,
        step=0.1,
        key="ancho_cara"
    )

    num_sellos = st.number_input(
        "Cantidad de sellos en la cara principal",
        min_value=1,
        step=1,
        key="num_sellos"
    )

    lado_real_cm = st.number_input(
        "Tamaño del sello en el arte (cm)",
        min_value=0.0,
        step=0.1,
        key="lado_sello"
    )

    espaciado_cm = st.number_input(
        "Espaciado entre sellos (cm)",
        min_value=0.0,
        step=0.1,
        key="espaciado_sellos"
    )

    # -------------------------------
    # TABLA 17 → LADO BASE
    # TABLA 17 → LADO BASE (SOLO PARA 1 SELLO)
    # -------------------------------
    lado_base = None

    if area_cara_cm2 < 30:
        st.warning("Área < 30 cm² → rotular en envase secundario o QR.")
    elif area_cara_cm2 < 35:
        lado_base = 1.7
    elif area_cara_cm2 < 40:
        lado_base = 1.8
    elif area_cara_cm2 < 50:
        lado_base = 2.0
    elif area_cara_cm2 < 60:
        lado_base = 2.2
    elif area_cara_cm2 < 80:
        lado_base = 2.5
    elif area_cara_cm2 < 100:
        lado_base = 2.8
    elif area_cara_cm2 < 125:
        lado_base = 3.1
    elif area_cara_cm2 < 150:
        lado_base = 3.4
    elif area_cara_cm2 < 200:
        lado_base = 3.9
    elif area_cara_cm2 < 250:
        lado_base = 4.4
    elif area_cara_cm2 < 300:
        lado_base = 4.8
    else:
        lado_base = 0.15 * ancho_cara_cm
        st.info("Área > 300 cm² → lado = 15% del ancho.")

    # -------------------------------
    # VERIFICACIÓN
    # -------------------------------
    if lado_base is not None:

        st.markdown("---")
        st.write(f"**Lado mínimo requerido:** {lado_base:.2f} cm")
        st.write(f"**Cantidad de sellos detectada:** {num_sellos}")

        # 🔹 UN SELLO
        # 🔹 UN SELLO → TABLA 17
        if num_sellos == 1:

            st.write(f"**Lado mínimo requerido (Tabla 17):** {lado_base:.2f} cm")
            st.write(f"**Tamaño real del sello:** {lado_real_cm:.2f} cm")

            if lado_real_cm >= lado_base:
                st.success("✅ CUMPLE (1 sello — Tabla 17)")
            else:
                st.error("❌ NO CUMPLE (tamaño insuficiente)")
                st.error("❌ NO CUMPLE: tamaño insuficiente según Tabla 17")

        # 🔹 DOS O MÁS SELLOS
        # 🔹 DOS O MÁS SELLOS → 30% DEL ANCHO (TU LÓGICA)
        else:
            ancho_real_total = num_sellos * lado_real_cm + (num_sellos - 1) * espaciado_cm
            ancho_max_total = 0.30 * ancho_cara_cm
            lado_minimo_por_sello = ancho_max_total

            st.write(f"• Tamaño de cada sello: {lado_real_cm:.2f} cm")
            st.write(f"• Ancho total ocupado: {ancho_real_total:.2f} cm")
            st.write(f"• Límite 30%: {ancho_max_total:.2f} cm")

            if lado_real_cm >= lado_base and ancho_real_total <= ancho_max_total:
                st.success("✅ CUMPLE (múltiples sellos + 30%)")
            elif lado_real_cm < lado_base:
                st.error("❌ NO CUMPLE: tamaño individual insuficiente")
            if lado_real_cm >= lado_minimo_por_sello:
                st.success("✅ CUMPLE (múltiples sellos — criterio 30%)")
            else:
                st.error("❌ NO CUMPLE: excede el 30% permitido")
                st.error(
                    "❌ NO CUMPLE: tamaño individual insuficiente. "
                    f"Cada sello debe medir al menos {lado_minimo_por_sello:.2f} cm."
                )


        nota = st.text_area("Observación (opcional)", value=st.session_state.note_810.get(titulo, ""), key=f"{titulo}_nota")
        st.session_state.note_810[titulo] = nota

        if st.session_state.status_810[titulo] == "no":
            st.markdown("**Adjunta evidencia (JPG/PNG):**")
            files = st.file_uploader("Subir imágenes", type=["jpg","jpeg","png"], accept_multiple_files=True, key=f"upl_{titulo}")
            if files:
                caption = st.text_input("Descripción breve para estas imágenes (opcional)", key=f"cap_{titulo}")
                if st.button("Agregar evidencia", key=f"btn_add_{titulo}"):
                    for f in files:
                        st.session_state.evidence_810[titulo].append({
                            "name": f.name,
                            "base64": base64.b64encode(f.read()).decode("utf-8"),
                            "caption": caption or ""
                        })
                    st.success(f"Se agregaron {len(files)} imagen(es) a: {titulo}")
            ev_list = st.session_state.evidence_810.get(titulo, [])
            if ev_list:
                st.markdown("**Evidencia acumulada:**")
                cols = st.columns(4)
                for idx, ev in enumerate(ev_list):
                    img_bytes = base64.b64decode(ev["base64"])
                    with cols[idx % 4]:
                        st.image(img_bytes, caption=ev["caption"] or ev["name"], use_column_width=True)

        st.markdown("---")

# ------------------------------------------------------------
# MÉTRICAS
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# PDF (A4 horizontal) — incluye referencias y evidencias (página nueva)
# ------------------------------------------------------------
def split_observation_text_pdf(text: str, chunk: int = 100) -> str:
    if not text:
        return ""
    s = str(text)
    if len(s) <= chunk:
        return s
    parts = [s[i:i+chunk] for i in range(0, len(s), chunk)]
    return "\\n".join(parts)

def generar_pdf():
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
    story.append(Spacer(1, 3*mm))
    intro_pdf = (
        "Este checklist se basa exclusivamente en las Resoluciones 810 de 2021 y 2492 de 2022, "
        "que establecen los requisitos técnicos para el etiquetado nutricional y frontal de advertencia en alimentos "
        "y bebidas envasadas destinados al consumo humano en Colombia."
    )
    story.append(Paragraph(intro_pdf, style_header))
    story.append(Spacer(1, 5*mm))

    yes_c = sum(1 for v in st.session_state.status_810.values() if v == "yes")
    no_c = sum(1 for v in st.session_state.status_810.values() if v == "no")
    ans_c = yes_c + no_c
    pct = round((yes_c / ans_c * 100), 1) if ans_c > 0 else 0.0
    story.append(Paragraph(f"<b>Cumplimiento (sobre ítems contestados):</b> {pct}%", style_header))
    story.append(Spacer(1, 4*mm))

    # Tabla principal (Ítem, Estado, Observación, Referencia)
    data = [["Ítem", "Estado", "Observación", "Referencia"]]
    for items in CATEGORIAS.values():
        for (titulo, _, referencia) in items:
            estado_val = st.session_state.status_810.get(titulo, "none")
            estado_humano = (
                "Cumple" if estado_val == "yes"
                else "No cumple" if estado_val == "no"
                else "No aplica" if estado_val == "na"
                else "Sin responder"
            )
            obs = st.session_state.note_810.get(titulo, "") or "-"
            if obs != "-":
                obs = split_observation_text_pdf(obs, chunk=100)
            data.append([
                Paragraph(str(titulo),          style_cell),
                Paragraph(str(estado_humano),   style_cell),
                Paragraph(obs,                  style_cell),
                Paragraph(str(referencia),      style_cell),
            ])

    col_widths = [100*mm, 25*mm, 85*mm, 55*mm]
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

    # Página nueva para evidencias — FIX definitivo: BytesIO directo en RLPlatypusImage
    any_ev = any(len(v) > 0 for v in st.session_state.evidence_810.values())
    if any_ev:
        story.append(PageBreak())
        story.append(Paragraph("<b>Evidencia fotográfica</b>", style_header))
        story.append(Spacer(1, 3*mm))

        for titulo, ev_list in st.session_state.evidence_810.items():
            if not ev_list:
                continue
            story.append(Paragraph(f"<b>Ítem:</b> {titulo}", style_header))
            story.append(Paragraph("<b>Evidencia de incumplimiento:</b>", style_header))
            story.append(Spacer(1, 2*mm))
            for idx, ev in enumerate(ev_list):
                try:
                    img_bytes = base64.b64decode(ev["base64"])
                    # 👇 FIX: pasar BytesIO(img_bytes) directo a Image (no usar ImageReader)
                    story.append(RLPlatypusImage(BytesIO(img_bytes), width=85*mm, height=55*mm))
                    if ev.get("caption"):
                        story.append(Paragraph(ev["caption"], style_cell))
                    story.append(Spacer(1, 3*mm))
                except Exception as e:
                    story.append(Paragraph(f"<i>⚠️ Error al cargar imagen {ev.get('name', '')}: {e}</i>", style_cell))
            story.append(Spacer(1, 5*mm))

    doc.build(story)
    buf.seek(0)
    return buf

# ------------------------------------------------------------
# EXPORTAR PDF
# ------------------------------------------------------------
st.subheader("Generar informe PDF (A4 horizontal)")
if st.button("Generar PDF"):
    pdf_buffer = generar_pdf()
    file_name = (nombre_pdf.strip() or f"informe_810_2492_{datetime.now().strftime('%Y%m%d')}") + ".pdf"
    st.download_button("Descargar PDF", data=pdf_buffer, file_name=file_name, mime="application/pdf")
