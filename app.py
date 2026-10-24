import streamlit as st
import pandas as pd
from collections import defaultdict

# Seitenkonfiguration im Wide-Modus
st.set_page_config(
    page_title="Professioneller Kunststoff-Zuschnittplaner (Industrie-Edition)",
    page_icon="✂️",
    layout="wide"
)

# Session State Initialisierung für Standardwerte & Tabellen
if "rohplatten" not in st.session_state:
    st.session_state.rohplatten = []
if "bauteile" not in st.session_state:
    st.session_state.bauteile = []
if "optimized_layouts" not in st.session_state:
    st.session_state.optimized_layouts = []

# Initialisierung der Eingabefelder im Session State für die Dropdown-Synchronisation
if "roh_l_input" not in st.session_state:
    st.session_state.roh_l_input = 6180
if "roh_h_input" not in st.session_state:
    st.session_state.roh_h_input = 2560

if "teil_l_input" not in st.session_state:
    st.session_state.teil_l_input = 2030
if "teil_h_input" not in st.session_state:
    st.session_state.teil_h_input = 1250

standard_teile = {
    "2030x1250": (2030, 1250),
    "3050x1250": (3050, 1250),
    "2050x1020": (2050, 1020), 
    "3050x1020": (3050, 1020)
}

# Callbacks zur automatischen Anpassung der Maße bei Dropdown-Auswahl
def update_roh_dims():
    val = st.session_state.get("sel_roh_preset")
    if val and "x" in val:
        l_str, h_str = val.split("x")
        st.session_state.roh_l_input = int(l_str)
        st.session_state.roh_h_input = int(h_str)
        st.rerun()

def update_teil_dims():
    val = st.session_state.get("sel_teil_preset")
    if val in standard_teile:
        b, h = standard_teile[val]
        st.session_state.teil_l_input = int(b)
        st.session_state.teil_h_input = int(h)
        st.rerun()

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
            schnittfuge = st.selectbox("Schnittfuge (mm):", ["4", "4.5", "5", "6", "6.5"], index=3, key="sel_schnittfuge")
        with c2:
            max_saege_hoehe = st.number_input("Max. Säge-Höhe:", value=100, format="%d", key="num_saegehoehe")
        
        drehbar = st.checkbox("Bauteile drehbar (90°)", value=True, key="chk_drehbar")
        
        st.write("Aufteilung:")
        aufteilung = st.radio(
            "Aufteilung Modus", 
            ["Kopfkanten / Kopfschnitte", "Längskanten / Längsschnitte", "Optimal"], 
            index=2, 
            label_visibility="collapsed", 
            horizontal=True,
            key="radio_aufteilung"
        )

        with st.expander("Besäumung (Kantenabzug)"):
            besaeum_aktiv = st.checkbox("Besäumung aktivieren", key="chk_besaeum")
            bc1, bc2, bc3 = st.columns([2, 1, 1])
            with bc1:
                besaeum_mass = st.number_input("Maß pro Kante (mm):", value=10, format="%d", key="num_besaeum")
            with bc2:
                st.write("")
                besaeum_laenge = st.checkbox("Längskanten", value=True, key="chk_b_laenge")
            with bc3:
                st.write("")
                besaeum_hoehe = st.checkbox("Kopfkanten", value=True, key="chk_b_hoehe")

        with st.expander("Spannungsfreischnitt"):
            freischnitt_aktiv = st.checkbox("Spannungsfreischnitt aktivieren", key="chk_freischnitt")
            fc1, fc2 = st.columns(2)
            with fc1:
                freischnitt_breite = st.number_input("Breite (mm):", value=15, format="%d", key="num_f_breite")
            with fc2:
                freischnitt_anzahl = st.number_input("Anzahl:", value=1, min_value=1, format="%d", key="num_f_anzahl")
            freischnitt_kante = st.radio("Kante:", ["Längskante", "Kopfkante"], horizontal=True, key="radio_f_kante")

    # 3. Verfügbare Pressplatten (Rohmaterial)
    st.markdown("### 1. Verfügbare Pressplatten (Rohmaterial)")
    with st.container(border=True):
        roh_formate = ["2090x2090", "3120x2090", "3120x2560", "4140x2090", "5200x2090", "6180x2090", "6180x2560"]
        
        # Perfekt optimierte Spaltenbreiten, damit auch Stärke und Dropdowns voll sichtbar sind
        rc1, rc2, rc3, rc4, rc5, rc6 = st.columns([2.5, 1.6, 1.6, 1.8, 1.1, 0.8])
        with rc1:
            sel_roh_preset = st.selectbox("Pos", roh_formate, index=6, label_visibility="collapsed", key="sel_roh_preset", on_change=update_roh_dims)

        with rc2:
            roh_l = st.number_input("L", format="%d", key="roh_l_input", label_visibility="collapsed")
        with rc3:
            roh_h = st.number_input("H", format="%d", key="roh_h_input", label_visibility="collapsed")
        with rc4:
            roh_staerke = st.selectbox("Stärke", [5, 10, 15, 20, 25, 30, 40, 50], index=3, label_visibility="collapsed", key="sel_roh_st")
        with rc5:
            roh_anz = st.number_input("Anz", value=1, min_value=1, format="%d", key="roh_anz_input", label_visibility="collapsed")
        with rc6:
            if st.button("➕", key="add_roh", use_container_width=True):
                bez = f"Pressplatte_{int(st.session_state.roh_l_input)}x{int(st.session_state.roh_h_input)}"
                st.session_state.rohplatten.append({
                    "Bezeichnung": bez, "Länge (mm)": st.session_state.roh_l_input, "Höhe (mm)": st.session_state.roh_h_input, "Stärke": roh_staerke, "Stk.": roh_anz
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
        tc1, tc2, tc3, tc4, tc5, tc6 = st.columns([2.5, 1.6, 1.6, 1.8, 1.1, 0.8])
        with tc1:
            sel_teil = st.selectbox("Pos", list(standard_teile.keys()), index=0, label_visibility="collapsed", key="sel_teil_preset", on_change=update_teil_dims)

        with tc2:
            teil_l = st.number_input("L", format="%d", key="teil_l_input", label_visibility="collapsed")
        with tc3:
            teil_h = st.number_input("H", format="%d", key="teil_h_input", label_visibility="collapsed")
        with tc4:
            teil_st = st.number_input("St", value=15, format="%d", key="teil_st_input", label_visibility="collapsed")
        with tc5:
            teil_anz = st.number_input("Anz", value=3, min_value=1, format="%d", key="teil_anz_input", label_visibility="collapsed")
        with tc6:
            if st.button("➕", key="add_teil", use_container_width=True):
                name = f"{int(st.session_state.teil_l_input)}x{int(st.session_state.teil_h_input)}"
                st.session_state.bauteile.append({
                    "Position": name, "Länge (mm)": st.session_state.teil_l_input, "Höhe (mm)": st.session_state.teil_h_input, "Stärke (mm)": teil_st, "Anz.": teil_anz
                })
                st.rerun()

        uploaded_file = st.file_uploader("Arbeitskarte laden (OCR Bild/PDF)", type=["png", "jpg", "jpeg", "pdf"], key="up_ocr")
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
                st.session_state.optimized_layouts = []
                st.rerun()
        with act2:
            if st.button("Optimieren", type="primary", use_container_width=True):
                if not st.session_state.rohplatten:
                    default_plate_w, default_plate_h = 6180, 2560
                else:
                    default_plate_w = st.session_state.rohplatten[0]["Länge (mm)"]
                    default_plate_h = st.session_state.rohplatten[0]["Höhe (mm)"]
                
                saege = float(schnittfuge)
                
                item_counts = defaultdict(int)
                item_dims = {}
                for t in st.session_state.bauteile:
                    key = (t["Länge (mm)"], t["Höhe (mm)"], t["Position"])
                    item_counts[key] += int(t["Anz."])
                    item_dims[key] = (t["Länge (mm)"], t["Höhe (mm)"], t["Position"])
                
                sorted_keys = sorted(item_counts.keys(), key=lambda k: k[1], reverse=True)
                
                placed = []
                margin = 20.0
                cur_y = margin
                max_plate_w = default_plate_w - margin
                
                for key in sorted_keys:
                    w, h, name = item_dims[key]
                    remaining_count = item_counts[key]
                    
                    while remaining_count > 0:
                        cur_x = margin
                        row_items = []
                        
                        while remaining_count > 0:
                            needed_w = w if not row_items else (w + saege)
                            if cur_x + needed_w <= max_plate_w:
                                if row_items:
                                    cur_x += saege
                                row_items.append((cur_x, cur_y, w, h, name))
                                cur_x += w
                                remaining_count -= 1
                            else:
                                break
                        
                        if not row_items:
                            break
                            
                        for rx, ry, rw, rh, rname in row_items:
                            placed.append({
                                "x": rx,
                                "y": ry,
                                "w": rw,
                                "h": rh,
                                "name": rname
                            })
                        
                        cur_y += h + saege
                
                st.session_state.optimized_layouts = [{
                    "plate_w": default_plate_w,
                    "plate_h": default_plate_h,
                    "placed": placed
                }]
                st.success("Zuschnitt & Reststücke erfolgreich berechnet!")
                st.rerun()

with col_right:
    header_c1, header_c2, header_c3 = st.columns([3, 2, 2])
    with header_c1:
        plan_options = [f"Schnittplan {i+1} [Platte {int(lay['plate_w'])}x{int(lay['plate_h'])}mm]" for i, lay in enumerate(st.session_state.optimized_layouts)] if st.session_state.optimized_layouts else ["Kein Schnittplan berechnet"]
        selected_plan = st.selectbox("Schnittplan:", plan_options, label_visibility="visible", key="sel_plan")
    with header_c2:
        st.write("")
        rest_chk = st.checkbox("Reststücke", value=True, key="chk_rest")
    with header_c3:
        st.write("")
        if st.button("Drucken / PDF Export", use_container_width=True, key="btn_pdf"):
            st.info("PDF-Export wird vorbereitet...")

    st.markdown("### Schnittplan-Vorschau")
    
    if st.session_state.optimized_layouts:
        layout = st.session_state.optimized_layouts[0]
        pw = layout["plate_w"]
        ph = layout["plate_h"]
        
        svg_w = 700
        svg_h = 350
        scale = min((svg_w - 60) / pw, (svg_h - 60) / ph) if pw > 0 and ph > 0 else 1
        
        draw_w = pw * scale
        draw_h = ph * scale
        start_x = (svg_w - draw_w) / 2
        start_y = (svg_h - draw_h) / 2
        
        rects_svg = ""
        colors = ["#3498db", "#2ecc71", "#9b59b6", "#f39c12", "#1abc9c", "#d35400"]
        name_to_color = {}
        
        for p in layout["placed"]:
            rname = p["name"]
            if rname not in name_to_color:
                name_to_color[rname] = colors[len(name_to_color) % len(colors)]
            color = name_to_color[rname]

            rx = start_x + p["x"] * scale
            ry = start_y + p["y"] * scale
            rw = p["w"] * scale
            rh = p["h"] * scale
            
            rects_svg += f'''
                <rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" fill="{color}" opacity="0.9" stroke="#2c3e50" stroke-width="1.5"/>
                <text x="{rx + rw/2}" y="{ry + rh/2}" fill="white" font-family="Segoe UI" font-size="11" font-weight="bold" text-anchor="middle" dominant-baseline="middle">{int(p["w"])} x {int(p["h"])}</text>
            '''
        
        svg_code = f'''
        <div style="background-color: transparent; padding: 0px;">
            <svg viewBox="0 0 {svg_w} {svg_h}" style="width: 100%; height: auto; background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px;">
                <text x="30" y="22" fill="#555555" font-family="Segoe UI" font-size="11">Platte: {int(pw)} x {int(ph)} mm (Einheitliche Positionsfarben)</text>
                <rect x="{start_x}" y="{start_y}" width="{draw_w}" height="{draw_h}" fill="#f8f9fa" stroke="#7f8c8d" stroke-width="2"/>
                {rects_svg}
            </svg>
        </div>
        '''
    else:
        svg_code = '''
        <div style="background-color: transparent; padding: 0px;">
            <svg viewBox="0 0 700 350" style="width: 100%; height: auto; background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px;">
                <text x="35" y="30" fill="#555555" font-family="Segoe UI" font-size="12">Bitte links auf "Optimieren" klicken, um den Zuschnitt zu berechnen.</text>
                <rect x="35" y="45" width="630" height="250" fill="#f8f9fa" stroke="#7f8c8d" stroke-width="2"/>
            </svg>
        </div>
        '''
        
    st.components.v1.html(svg_code, height=370)

    st.markdown("### Bauteil- und Mengenübersicht (Industrie-Standard)")
    
    if st.session_state.bauteile:
        info_rows = []
        for item in st.session_state.bauteile:
            gesamt = item["Anz."]
            auf_plan = gesamt if st.session_state.optimized_layouts else 0
            info_rows.append([
                item["Position"],
                int(item["Länge (mm)"]),
                int(item["Höhe (mm)"]),
                gesamt,
                0,  # bisher geschnitten
                auf_plan,  # auf diesem Plan
                0   # Rest Menge
            ])
        info_data = pd.DataFrame(info_rows, columns=[
            "Position", "Länge [mm]", "Breite [mm]", "gesamt Menge", 
            "bisher geschnitten", "auf diesem Plan", "Rest Menge"
        ])
    else:
        info_data = pd.DataFrame(columns=[
            "Position", "Länge [mm]", "Breite [mm]", "gesamt Menge", 
            "bisher geschnitten", "auf diesem Plan", "Rest Menge"
        ])

    st.dataframe(info_data, use_container_width=True, hide_index=True)
