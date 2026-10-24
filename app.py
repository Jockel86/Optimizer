import streamlit as st
import pandas as pd
from PIL import Image
import io

# Seitenkonfiguration im Wide-Modus für optimale Industrie-Ansicht
st.set_page_config(
    page_title="Professioneller Kunststoff-Zuschnittplaner",
    page_icon="✂️",
    layout="wide"
)

# Sitzungsspeicher (Session State) für Tabellen initialisieren
if "rohplatten" not in st.session_state:
    st.session_state.rohplatten = []
if "bauteile" not in st.session_state:
    st.session_state.bauteile = []

# Titel & Kopfzeile
st.title("Professioneller Kunststoff-Zuschnittplaner (Industrie-Edition)")

col_top1, col_top2, col_top3 = st.columns([2, 1, 1])
with col_top1:
    schnittplan_wahl = st.selectbox("Schnittplan", ["Schnittplan 1"], label_visibility="collapsed")
with col_top2:
    reststuecke_chk = st.checkbox("Reststücke anzeigen", value=True)
with col_top3:
    if st.button("Drucken / PDF Export", use_container_width=True):
        st.info("PDF-Export wird vorbereitet...")

# Hauptbereich in zwei Spalten aufteilen
col_left, col_right = st.columns([5, 7])

with col_left:
    # 1. Auftrags- & Kopfdaten
    with st.expander("Auftrags- & Kopfdaten (Druck-Metadaten)", expanded=True):
        auftrag = st.text_input("Auftrag")
        material = st.text_input("Material")
        sonstiges = st.text_input("Sonstiges")

    # 2. Maschinen- & Industrie-Parameter
    with st.expander("Maschinen- & Industrie-Parameter", expanded=True):
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            schnittfuge = st.selectbox("Schnittfuge (mm)", ["4", "4.5", "5", "6", "6.5"], index=3)
        with col_m2:
            max_saege_hoehe = st.number_input("Max. Säge-Höhe", value=100)
        
        drehbar = st.checkbox("Bauteile drehbar (90°)", value=True)
        
        st.write("Aufteilung:")
        aufteilung = st.radio(
            "Aufteilung Modus", 
            ["Kopfkanten / Kopfschnitte", "Längskanten / Längsschnitte", "Optimal"], 
            index=2, 
            label_visibility="collapsed", 
            horizontal=True
        )

        # Besäumung
        with st.expander("Besäumung (Kantenabzug)"):
            besaeum_aktiv = st.checkbox("Besäumung aktivieren")
            besaeum_mass = st.number_input("Maß pro Kante (mm)", value=10)
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                besaeum_laenge = st.checkbox("Längskanten", value=True)
            with col_b2:
                besaeum_hoehe = st.checkbox("Kopfkanten", value=True)

        # Spannungsfreischnitt
        with st.expander("Spannungsfreischnitt"):
            freischnitt_aktiv = st.checkbox("Spannungsfreischnitt aktivieren")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                freischnitt_breite = st.number_input("Breite (mm)", value=15)
            with col_f2:
                freischnitt_anzahl = st.number_input("Anzahl", value=1, min_value=1)
            freischnitt_kante = st.radio("Kante", ["Längskante", "Kopfkante"], horizontal=True)

    # 3. Verfügbare Pressplatten (Rohmaterial)
    with st.expander("1. Verfügbare Pressplatten (Rohmaterial)", expanded=True):
        roh_formate = ["2090x2090", "3120x2090", "3120x2560", "4140x2090", "5200x2090", "6180x2090", "6180x2560"]
        sel_format = st.selectbox("Pos / Format Vorlage", roh_formate, index=6)
        
        default_l, default_h = 6180, 2560
        if "x" in sel_format:
            parts = sel_format.split("x")
            default_l, default_h = float(parts[0]), float(parts[1])

        col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns([2, 2, 2, 2, 1])
        with col_r1:
            roh_l = st.number_input("L", value=default_l, key="roh_l_input")
        with col_r2:
            roh_h = st.number_input("H", value=default_h, key="roh_h_input")
        with col_r3:
            roh_staerke = st.selectbox("Stärke", [5, 10, 15, 20, 25, 30, 40, 50], index=3)
        with col_r4:
            roh_anz = st.number_input("Anz", value=1, min_value=1)
        with col_r5:
            st.write("") 
            if st.button("➕", key="add_roh", use_container_width=True):
                bez = f"Pressplatte_{int(roh_l)}x{int(roh_h)}"
                st.session_state.rohplatten.append({
                    "Bezeichnung": bez, "Länge": roh_l, "Höhe": roh_h, "Stärke": roh_staerke, "Stk.": roh_anz
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
    with st.expander("2. Gewünschte Bauteile / Zuschnitte", expanded=True):
        standard_teile = {
            "2050x1020": (2050, 1020), "2030x1250": (2030, 1250), 
            "3050x1020": (3050, 1020), "3050x1250": (3050, 1250)
        }
        sel_teil = st.selectbox("Pos Vorlage", list(standard_teile.keys()), index=0)
        def_tl, def_th = standard_teile[sel_teil]

        col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns([2, 2, 2, 2, 2])
        with col_t1:
            teil_l = st.number_input("L", value=def_tl, key="teil_l_input")
        with col_t2:
            teil_h = st.number_input("H", value=def_th, key="teil_h_input")
        with col_t3:
            teil_st = st.number_input("St", value=20, key="teil_st_input")
        with col_t4:
            teil_anz = st.number_input("Anz", value=2, min_value=1, key="teil_anz_input")
        with col_t5:
            uploaded_file = st.file_uploader("OCR Karte", type=["png", "jpg", "jpeg", "pdf"], label_visibility="collapsed")

        if st.button("Bauteil hinzufügen (➕)", use_container_width=True):
            name = f"Pos_{int(teil_l)}x{int(teil_h)}"
            st.session_state.bauteile.append({
                "Position": name, "Länge": teil_l, "Höhe": teil_h, "Stärke": teil_st, "Anz.": teil_anz
            })
            st.rerun()

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
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("Zurücksetzen", use_container_width=True):
                st.session_state.rohplatten = []
                st.session_state.bauteile = []
                st.rerun()
        with col_act2:
            if st.button("Optimieren", type="primary", use_container_width=True):
                st.success("Zuschnitt & Reststücke erfolgreich berechnet!")

with col_right:
    # Grafik-Vorschau
    st.subheader("Schnittplan-Vorschau")
    svg_code = '''
        <svg viewBox="0 0 700 350" style="width: 100%; height: auto; background-color: #f8f9fa; border: 1px solid #cbd5e1; border-radius: 8px;">
            <rect x="20" y="20" width="660" height="310" fill="#e2e8f0" stroke="#cbd5e1" stroke-width="2"/>
            <rect x="35" y="35" width="300" height="220" fill="#3b82f6" opacity="0.85" stroke="#1d4ed8"/>
            <text x="185" y="145" fill="white" font-size="14" font-weight="bold" text-anchor="middle">Seitenwand (2050x1020)</text>
            <rect x="355" y="35" width="220" height="150" fill="#10b981" opacity="0.85" stroke="#047857"/>
            <text x="465" y="115" fill="white" font-size="13" font-weight="bold" text-anchor="middle">Bodenplatte</text>
            <rect x="355" y="195" width="220" height="130" fill="#f59e0b" opacity="0.85" stroke="#d97706"/>
            <text x="465" y="265" fill="white" font-size="12" text-anchor="middle">Reststück (wiederverwendbar)</text>
        </svg>
    '''
    st.markdown(svg_code, unsafe_allow_html=True)

    # Bauteil- und Mengenübersicht
    st.subheader("Bauteil- und Mengenübersicht (Industrie-Standard)")
    info_data = pd.DataFrame(columns=[
        "Position", "Länge [mm]", "Breite [mm]", "gesamt Menge", 
        "bisher geschnitten", "auf diesem Plan", "Rest Menge"
    ])
    st.dataframe(info_data, use_container_width=True, hide_index=True)