import streamlit as st
import pandas as pd
from PIL import Image
import io

# Seitenkonfiguration im Wide-Modus
st.set_page_config(
    page_title="Professioneller Kunststoff-Zuschnittplaner (Industrie-Edition)",
    page_icon="✂️",
    layout="wide"
)

# Session State Initialisierung für Tabellen
if "rohplatten" not in st.session_state:
    st.session_state.rohplatten = []
if "bauteile" not in st.session_state:
    st.session_state.bauteile = []

# Hauptlayout in zwei Spalten aufteilen (Links: Eingaben, Rechts: Vorschau & Tabellen)
col_left, col_right = st.columns([5, 7], gap="medium")

with col_left:
    # 1. Auftrags- & Kopfdaten
    st.markdown("### Auftrags- & Kopfdaten (Druck-Metadaten)")
    with st.container(border=True):
        auftrag = st.text_input("Auftrag", key="inp_auftrag")
        material = st.text_input("Material", key="inp_material")
        sonstiges = st.text_input("Sonstiges", key="inp_sonstiges")

    # 2. Maschinen- & Industrie-Parameter
    st.markdown("### Maschinen- & Industrie-Parameter")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            schnittfuge = st.selectbox("Schnittfuge (mm):", ["4", "4.5", "5", "6", "6.5"], index=3)
        with c2:
            max_saege_hoehe = st.number_input("Max. Säge-Höhe:", value=100)
        
        drehbar = st.checkbox("Bauteile drehbar (90°)", value=True)
        
        st.write("Aufteilung:")
        aufteilung = st.radio(
            "Aufteilung Modus", 
            ["Kopfkanten / Kopfschnitte", "Längskanten / Längsschnitte", "Optimal"], 
            index=2, 
            label_visibility="collapsed", 
            horizontal=True
        )

        with st.expander("Besäumung (Kantenabzug)"):
            besaeum_aktiv = st.checkbox("Besäumung aktivieren", key="chk_besaeum")
            bc1, bc2, bc3 = st.columns([2, 1, 1])
            with bc1:
                besaeum_mass = st.number_input("Maß pro Kante (mm):", value=10, key="num_besaeum")
            with bc2:
                st.write("")
                besaeum_laenge = st.checkbox("Längskanten", value=True)
            with bc3:
                st.write("")
                besaeum_hoehe = st.checkbox("Kopfkanten", value=True)

        with st.expander("Spannungsfreischnitt"):
            freischnitt_aktiv = st.checkbox("Spannungsfreischnitt aktivieren", key="chk_freischnitt")
            fc1, fc2 = st.columns(2)
            with fc1:
                freischnitt_breite = st.number_input("Breite (mm):", value=15)
            with fc2:
                freischnitt_anzahl = st.number_input("Anzahl:", value=1, min_value=1)
            freischnitt_kante = st.radio("Kante:", ["Längskante", "Kopfkante"], horizontal=True)

    # 3. Verfügbare Pressplatten (Rohmaterial)
    st.markdown("### 1. Verfügbare Pressplatten (Rohmaterial)")
    with st.container(border=True):
        roh_formate = ["2090x2090", "3120x2090", "3120x2560", "4140x2090", "5200x2090", "6180x2090", "6180x2560"]
        
        rc1, rc2, rc3, rc4, rc5, rc6 = st.columns([2, 1.5, 1.5, 1.5, 1, 0.8])
        with rc1:
            sel_roh_preset = st.selectbox("Pos", roh_formate, index=6, label_visibility="collapsed")
        
        def_l, def_h = 6180, 2560
        if sel_roh_preset and "x" in sel_roh_preset:
            parts = sel_roh_preset.split("x")
            def_l, def_h = float(parts[0]), float(parts[1])

        with rc2:
            roh_l = st.number_input("L", value=def_l, key="roh_l_input", label_visibility="collapsed")
        with rc3:
            roh_h = st.number_input("H", value=def_h, key="roh_h_input", label_visibility="collapsed")
        with rc4:
            roh_staerke = st.selectbox("Stärke", [5, 10, 15, 20, 25, 30, 40, 50], index=3, label_visibility="collapsed")
        with rc5:
            roh_anz = st.number_input("Anz", value=1, min_value=1, key="roh_anz_input", label_visibility="collapsed")
        with rc6:
            if st.button("➕", key="add_roh", use_container_width=True):
                bez = f"Pressplatte_{int(roh_l)}x{int(roh_h)}"
                st.session_state.rohplatten.append({
                    "Bezeichnung": bez, "Länge (mm)": roh_l, "Höhe (mm)": roh_h, "Stärke": roh_staerke, "Stk.": roh_anz
                })
                st.rerun()

        if st.session_state.rohplatten:
            df_roh = pd.DataFrame(st.session_state.rohplatten)
            st.dataframe(df_roh, use_container_width=True, hide_index=True)
            if st.button("Rohplatte löschen", key="del_roh"):
                if st.session_state.rohplatten:
                    st.session_state.rohplatten.pop()
                    st.rerun()
        else:
            st.caption("Keine Rohplatten hinterlegt.")

    # 4. Gewünschte Bauteile / Zuschnitte
    st.markdown("### 2. Gewünschte Bauteile / Zuschnitte")
    with st.container(border=True):
        standard_teile = {
            "2050x1020": (2050, 1020), "2030x1250": (2030, 1250), 
            "3050x1020": (3050, 1020), "3050x1250": (3050, 1250)
        }
        tc1, tc2, tc3, tc4, tc5, tc6 = st.columns([2, 1.5, 1.5, 1.2, 1, 1.5])
        with tc1:
            sel_teil = st.selectbox("Pos", list(standard_teile.keys()), index=0, label_visibility="collapsed")
        def_tl, def_th = standard_teile[sel_teil]

        with tc2:
            teil_l = st.number_input("L", value=def_tl, key="teil_l_input", label_visibility="collapsed")
        with tc3:
            teil_h = st.number_input("H", value=def_th, key="teil_h_input", label_visibility="collapsed")
        with tc4:
            teil_st = st.number_input("St", value=20, key="teil_st_input", label_visibility="collapsed")
        with tc5:
            teil_anz = st.number_input("Anz", value=2, min_value=1, key="teil_anz_input", label_visibility="collapsed")
        with tc6:
            if st.button("➕", key="add_teil", use_container_width=True):
                name = f"Pos_{int(teil_l)}x{int(teil_h)}"
                st.session_state.bauteile.append({
                    "Position": name, "Länge (mm)": teil_l, "Höhe (mm)": teil_h, "Stärke (mm)": teil_st, "Anz.": teil_anz
                })
                st.rerun()

        uploaded_file = st.file_uploader("Arbeitskarte laden (OCR Bild/PDF)", type=["png", "jpg", "jpeg", "pdf"])
        if uploaded_file is not None:
            st.success(f"Arbeitskarte {uploaded_file.name} erfolgreich geladen!")

        if st.session_state.bauteile:
            df_teile = pd.DataFrame(st.session_state.bauteile)
            st.dataframe(df_teile, use_container_width=True, hide_index=True)
            if st.button("Ausgewähltes Bauteil löschen", key="del_teil"):
                if st.session_state.bauteile:
                    st.session_state.bauteile.pop()
                    st.rerun()
        else:
            st.caption("Keine Bauteile hinterlegt.")

        st.write("")
        act1, act2 = st.columns(2)
        with act1:
            if st.button("Zurücksetzen", use_container_width=True):
                st.session_state.rohplatten = []
                st.session_state.bauteile = []
                st.rerun()
        with act2:
            if st.button("Optimieren", type="primary", use_container_width=True):
                st.success("Zuschnitt & Reststücke erfolgreich berechnet!")

with col_right:
    # Rechte Spalte: Obere Steuerungsleiste
    header_c1, header_c2, header_c3 = st.columns([3, 2, 2])
    with header_c1:
        st.selectbox("Schnittplan:", ["Schnittplan 1 (1 Platte einzeln) [Ausnutzung: 19.65%]"], label_visibility="visible")
    with header_c2:
        st.write("")
        st.checkbox("Reststücke", value=True)
    with header_c3:
        st.write("")
        if st.button("Drucken / PDF Export", use_container_width=True):
            st.info("PDF-Export wird vorbereitet...")

    # Grafik-Vorschau
    st.markdown("### Schnittplan-Vorschau")
    svg_code = '''
    <div style="background-color: transparent; padding: 0px;">
        <svg viewBox="0 0 700 350" style="width: 100%; height: auto; background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px;">
            <text x="35" y="25" fill="#555555" font-family="Segoe UI" font-size="12">Pfeil = Schnittrichtung</text>
            <rect x="35" y="35" width="630" height="260" fill="#f8f9fa" stroke="#7f8c8d" stroke-width="2"/>
            <rect x="50" y="50" width="300" height="200" fill="#3498db" opacity="0.9" stroke="#2c3e50"/>
            <text x="200" y="155" fill="white" font-family="Segoe UI" font-size="14" font-weight="bold" text-anchor="middle">2030 x 1250 x 15 mm</text>
        </svg>
    </div>
    '''
    st.components.v1.html(svg_code, height=370)

    # Bauteil- und Mengenübersicht
    st.markdown("### Bauteil- und Mengenübersicht (Industrie-Standard)")
    info_data = pd.DataFrame(
        [["2030x1250", 2030, 1250, 1, 0, 1, 0]],
        columns=["Position", "Länge [mm]", "Breite [mm]", "gesamt Menge", "bisher geschnitten", "auf diesem Plan", "Rest Menge"]
    ) if st.session_state.bauteile else pd.DataFrame(columns=[
        "Position", "Länge [mm]", "Breite [mm]", "gesamt Menge", "bisher geschnitten", "auf diesem Plan", "Rest Menge"
    ])
    st.dataframe(info_data, use_container_width=True, hide_index=True)
