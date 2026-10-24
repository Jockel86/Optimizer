import streamlit as st
import pandas as pd
import math
from collections import defaultdict
from fpdf import FPDF
import io

# Seitenkonfiguration im Wide-Modus
st.set_page_config(
    page_title="Professioneller Kunststoff-Zuschnittplaner (Industrie-Edition)",
    page_icon="✂️",
    layout="wide"
)

# Benutzerdefiniertes CSS für perfekte Button-Ausrichtung und Lesbarkeit
st.markdown("""
<style>
    .add-btn-col {
        padding-top: 28px;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialisierung für Standardwerte & Tabellen
if "rohplatten" not in st.session_state:
    st.session_state.rohplatten = []
if "bauteile" not in st.session_state:
    st.session_state.bauteile = []
if "optimized_layouts" not in st.session_state:
    st.session_state.optimized_layouts = []

# Initialisierung der Eingabefelder im Session State für die Synchronisation
if "roh_l_input" not in st.session_state:
    st.session_state.roh_l_input = 4140
if "roh_h_input" not in st.session_state:
    st.session_state.roh_h_input = 2090
if "sel_roh_st" not in st.session_state:
    st.session_state.sel_roh_st = 20

if "teil_l_input" not in st.session_state:
    st.session_state.teil_l_input = 2050
if "teil_h_input" not in st.session_state:
    st.session_state.teil_h_input = 1020
if "teil_st_input" not in st.session_state:
    st.session_state.teil_st_input = 20

standard_teile = {
    "2050x1020": (2050, 1020),
    "3050x1020": (3050, 1020),
    "2030x1250": (2030, 1250),
    "3050x1250": (3050, 1250)
}

# Callbacks zur automatischen Anpassung der Maße und Stärken
def update_roh_dims():
    val = st.session_state.get("sel_roh_preset")
    if val and "x" in val:
        l_str, h_str = val.split("x")
        st.session_state.roh_l_input = int(l_str)
        st.session_state.roh_h_input = int(h_str)
        st.rerun()

def update_roh_thickness():
    st.session_state.teil_st_input = int(st.session_state.sel_roh_st)
    st.rerun()

def update_teil_dims():
    val = st.session_state.get("sel_teil_preset")
    if val in standard_teile:
        b, h = standard_teile[val]
        st.session_state.teil_l_input = int(b)
        st.session_state.teil_h_input = int(h)
        st.rerun()

# PDF-Generierungsfunktion für alle Schnittpläne eines Auftrags
def generate_pdf_report(auftrag, material, sonstiges, layouts, bauteile, show_rest, besaeum_info):
    pdf = FPDF()
    
    # Für jeden Schnittplan eine eigene Seite generieren
    for idx, layout in enumerate(layouts):
        pdf.add_page()
        pdf.set_font('helvetica', 'B', 16)
        
        # Titel
        pdf.cell(0, 10, 'Zuschnittplan - Industrie-Edition', 0, 1, 'C')
        pdf.ln(2)
        
        # Kopfdaten / Metadaten
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(0, 5, 'Auftrags- & Kopfdaten:', 0, 1)
        pdf.set_font('helvetica', '', 9)
        pdf.cell(0, 4, f'Auftrag: {auftrag or "-"} | Material: {material or "-"} | Sonstiges: {sonstiges or "-"}', 0, 1)
        pdf.ln(3)
        
        pdf.set_font('helvetica', 'B', 11)
        pdf.cell(0, 6, f'Plan-Details: {layout["title"]} (Auslastung: {layout["utilization"]}%)', 0, 1)
        pdf.set_font('helvetica', '', 10)
        pdf.cell(0, 5, f'Pressplatten-Format: {int(layout["plate_w"])} x {int(layout["plate_h"])} mm', 0, 1)
        if besaeum_info["aktiv"]:
            pdf.cell(0, 5, f'Besäumung (V/H/K1/K2): {besaeum_info["l_vorn"]}/{besaeum_info["l_hinten"]}/{besaeum_info["k_vorn"]}/{besaeum_info["k_hinten"]} mm', 0, 1)
        pdf.ln(3)
        
        # Grafische Vorschau im PDF zeichnen
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(0, 6, 'Schnittplan-Vorschau:', 0, 1)
        
        pw = layout["plate_w"]
        ph = layout["plate_h"]
        
        max_box_w = 170.0
        max_box_h = 75.0
        scale = min(max_box_w / pw, max_box_h / ph) if pw > 0 and ph > 0 else 1
        
        draw_w = pw * scale
        draw_h = ph * scale
        start_x = (210 - draw_w) / 2
        start_y = pdf.get_y()
        
        pdf.set_fill_color(248, 249, 250)
        pdf.set_draw_color(127, 140, 141)
        pdf.rect(start_x, start_y, draw_w, draw_h, 'DF')
        
        # Besäumungs-Rahmen im PDF (falls aktiv)
        if besaeum_info["aktiv"]:
            bx = start_x + besaeum_info["l_vorn"] * scale
            by = start_y + besaeum_info["k_vorn"] * scale
            bw = draw_w - (besaeum_info["l_vorn"] + besaeum_info["l_hinten"]) * scale
            bh = draw_h - (besaeum_info["k_vorn"] + besaeum_info["k_hinten"]) * scale
            pdf.set_draw_color(200, 50, 50)
            pdf.set_line_width(0.3)
            pdf.rect(bx, by, bw, bh)
            pdf.set_draw_color(127, 140, 141)
            pdf.set_line_width(0.2)

        # Reststücke im PDF zeichnen, falls aktiviert
        if show_rest and "offcuts" in layout:
            for o in layout["offcuts"]:
                ox = start_x + o["x"] * scale
                oy = start_y + o["y"] * scale
                ow = o["w"] * scale
                oh = o["h"] * scale
                
                if o["to_scrap"]:
                    pdf.set_fill_color(203, 213, 225)
                    pdf.set_draw_color(100, 116, 139)
                    pdf.rect(ox, oy, ow, oh, 'DF')
                else:
                    pdf.set_fill_color(226, 232, 240)
                    pdf.set_draw_color(148, 163, 184)
                    pdf.rect(ox, oy, ow, oh, 'DF')
                    if ow > 15 and oh > 8:
                        pdf.set_font('helvetica', '', 7)
                        pdf.set_text_color(100, 116, 139)
                        pdf.set_xy(ox, oy + (oh / 2) - 3)
                        pdf.cell(ow, 6, f'{int(o["w"])}x{int(o["h"])}', 0, 0, 'C')
                        pdf.set_text_color(0, 0, 0)

        colors_rgb = [
            (52, 152, 219),
            (46, 204, 113),
            (155, 89, 182),
            (243, 156, 18),
            (26, 188, 156),
            (211, 84, 0)
        ]
        name_to_color_idx = {}
        
        for p in layout["placed"]:
            rname = p["name"]
            if rname not in name_to_color_idx:
                name_to_color_idx[rname] = len(name_to_color_idx) % len(colors_rgb)
            col = colors_rgb[name_to_color_idx[rname]]
            
            rx = start_x + p["x"] * scale
            ry = start_y + p["y"] * scale
            rw = p["w"] * scale
            rh = p["h"] * scale
            
            pdf.set_fill_color(col[0], col[1], col[2])
            pdf.set_draw_color(44, 62, 80)
            pdf.rect(rx, ry, rw, rh, 'DF')
            
            if rw > 10 and rh > 6:
                pdf_font_size = 8
                if rw < 25 or rh < 12:
                    pdf_font_size = 6
                pdf.set_font('helvetica', 'B', pdf_font_size)
                pdf.set_text_color(255, 255, 255)
                pdf.set_xy(rx, ry + (rh / 2) - 3)
                pdf.cell(rw, 6, f'{int(p["w"])}x{int(p["h"])}', 0, 0, 'C')
                pdf.set_text_color(0, 0, 0)
                
    # Abschließend eine gemeinsame Bauteil- und Mengenübersicht-Seite anhängen
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 10, 'Bauteil- und Mengenübersicht (Gesamtauftrag)', 0, 1, 'L')
    pdf.ln(3)
    
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(70, 7, 'Position', 1, 0, 'C', True)
    pdf.cell(35, 7, 'Länge [mm]', 1, 0, 'C', True)
    pdf.cell(35, 7, 'Breite [mm]', 1, 0, 'C', True)
    pdf.cell(30, 7, 'Menge', 1, 1, 'C', True)
    
    pdf.set_font('helvetica', '', 10)
    for item in bauteile:
        pdf.cell(70, 6, str(item["Position"]), 1)
        pdf.cell(35, 6, str(int(item["Länge (mm)"])), 1, 0, 'C')
        pdf.cell(35, 6, str(int(item["Höhe (mm)"])), 1, 0, 'C')
        pdf.cell(30, 6, str(item["Anz."]), 1, 1, 'C')
        
    return bytes(pdf.output())

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
        
        st.write("Aufteilung / Strategie:")
        aufteilung = st.radio(
            "Aufteilung Modus", 
            ["Längsschnitte bevorzugen", "Kopfschnitte bevorzugen", "Optimal"], 
            index=2, 
            label_visibility="collapsed", 
            horizontal=False,
            key="radio_aufteilung"
        )

        with st.expander("Besäumung (Kantenabzug)"):
            besaeum_aktiv = st.checkbox("Besäumung aktivieren", key="chk_besaeum")
            if besaeum_aktiv:
                bc1, bc2 = st.columns(2)
                with bc1:
                    besaeum_l_vorn = st.number_input("Vordere Längsseite (mm):", value=10, format="%d", key="num_b_l_vorn")
                    besaeum_l_hinten = st.number_input("Hintere Längsseite (mm):", value=10, format="%d", key="num_b_l_hinten")
                with bc2:
                    besaeum_k_vorn = st.number_input("Vordere Kopfseite (mm):", value=10, format="%d", key="num_b_k_vorn")
                    besaeum_k_hinten = st.number_input("Hintere Kopfseite (mm):", value=10, format="%d", key="num_b_k_hinten")

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
        
        rc1, rc2, rc3, rc4, rc5, rc6 = st.columns([2.2, 1.3, 1.3, 1.5, 0.8, 2.3])
        with rc1:
            sel_roh_preset = st.selectbox("Pos", roh_formate, index=3, label_visibility="collapsed", key="sel_roh_preset", on_change=update_roh_dims)

        with rc2:
            roh_l = st.number_input("L", format="%d", key="roh_l_input", label_visibility="collapsed")
        with rc3:
            roh_h = st.number_input("H", format="%d", key="roh_h_input", label_visibility="collapsed")
        with rc4:
            roh_staerke = st.selectbox("Stärke", [5, 10, 15, 20, 25, 30, 40, 50], index=3, label_visibility="collapsed", key="sel_roh_st", on_change=update_roh_thickness)
        with rc5:
            roh_anz = st.number_input("Anz", value=1, min_value=1, format="%d", key="roh_anz_input", label_visibility="collapsed")
        with rc6:
            st.markdown('<div class="add-btn-col">', unsafe_allow_html=True)
            if st.button("➕ Hinzufügen", key="add_roh", use_container_width=True, type="secondary"):
                bez = f"Pressplatte_{int(st.session_state.roh_l_input)}x{int(st.session_state.roh_h_input)}"
                st.session_state.rohplatten.append({
                    "Bezeichnung": bez, "Länge (mm)": st.session_state.roh_l_input, "Höhe (mm)": st.session_state.roh_h_input, "Stärke": st.session_state.sel_roh_st, "Stk.": roh_anz
                })
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.rohplatten:
            df_roh = pd.DataFrame(st.session_state.rohplatten)
            st.dataframe(df_roh, use_container_width=True, hide_index=True)
            if st.button("Rohplatte löschen", key="del_roh"):
                if st.session_state.rohplatten:
                    st.session_state.rohplatten.pop()
                    st.rerun()
        else:
            st.caption("Noch keine Rohplatten hinterlegt.")

    # 4. Gewünschte Bauteile / Zuschnitte
    st.markdown("### 2. Gewünschte Bauteile / Zuschnitte")
    with st.container(border=True):
        tc1, tc2, tc3, tc4, tc5, tc6 = st.columns([2.2, 1.3, 1.3, 1.5, 0.8, 2.3])
        with tc1:
            sel_teil = st.selectbox("Pos", list(standard_teile.keys()), index=0, label_visibility="collapsed", key="sel_teil_preset", on_change=update_teil_dims)

        with tc2:
            teil_l = st.number_input("L", format="%d", key="teil_l_input", label_visibility="collapsed")
        with tc3:
            teil_h = st.number_input("H", format="%d", key="teil_h_input", label_visibility="collapsed")
        with tc4:
            teil_st = st.number_input("St", format="%d", key="teil_st_input", label_visibility="collapsed")
        with tc5:
            teil_anz = st.number_input("Anz", value=1, min_value=1, format="%d", key="teil_anz_input", label_visibility="collapsed")
        with tc6:
            st.markdown('<div class="add-btn-col">', unsafe_allow_html=True)
            if st.button("➕ Hinzufügen", key="add_teil", use_container_width=True, type="secondary"):
                name = f"{int(st.session_state.teil_l_input)}x{int(st.session_state.teil_h_input)}"
                st.session_state.bauteile.append({
                    "Position": name, "Länge (mm)": st.session_state.teil_l_input, "Höhe (mm)": st.session_state.teil_h_input, "Stärke (mm)": st.session_state.teil_st_input, "Anz.": teil_anz
                })
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

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
            st.caption("Noch keine Bauteile hinterlegt.")

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
                    default_plate_w, default_plate_h = 4140, 2090
                else:
                    default_plate_w = st.session_state.rohplatten[0]["Länge (mm)"]
                    default_plate_h = st.session_state.rohplatten[0]["Höhe (mm)"]
                
                saege = float(schnittfuge)
                strategie = st.session_state.get("radio_aufteilung", "Optimal")
                
                # Besäumungswerte auslesen
                besaeum_aktiv = st.session_state.get("chk_besaeum", False)
                if besaeum_aktiv:
                    m_l = float(st.session_state.get("num_b_l_vorn", 10))
                    m_r = float(st.session_state.get("num_b_l_hinten", 10))
                    m_t = float(st.session_state.get("num_b_k_vorn", 10))
                    m_b = float(st.session_state.get("num_b_k_hinten", 10))
                else:
                    m_l, m_r, m_t, m_b = 5.0, 5.0, 5.0, 5.0

                max_w_row = default_plate_w - m_r
                max_h_plate = default_plate_h - m_b

                # Multi-Platten-Packer
                def pack_all_items(items_to_pack, title_prefix, variant_type_key):
                    current_items = list(items_to_pack)
                    plate_idx = 1
                    generated_layouts = []
                    
                    plate_total_area = default_plate_w * default_plate_h

                    while current_items and plate_idx <= 20:
                        placed_items = []
                        offcuts = []
                        cur_y = m_t
                        max_plate_w = default_plate_w - m_r
                        max_plate_h = default_plate_h - m_b
                        
                        remaining_on_plate = list(current_items)
                        remaining_on_plate.sort(key=lambda x: (x["h"], x["w"]), reverse=True)
                        
                        plate_placed = []
                        next_remaining = []
                        
                        while remaining_on_plate and cur_y < max_plate_h:
                            row_item = remaining_on_plate.pop(0)
                            row_h = row_item["h"]
                            
                            if cur_y + row_h > max_plate_h:
                                next_remaining.append(row_item)
                                next_remaining.extend(remaining_on_plate)
                                break
                                
                            cur_x = m_l
                            row_items = [{
                                "x": cur_x,
                                "y": cur_y,
                                "w": row_item["w"],
                                "h": row_h,
                                "name": row_item["name"]
                            }]
                            cur_x += row_item["w"]
                            
                            i = 0
                            while i < len(remaining_on_plate):
                                item = remaining_on_plate[i]
                                needed_w = item["w"] + saege
                                if item["h"] <= row_h and cur_x + needed_w <= max_plate_w:
                                    cur_x += saege
                                    row_items.append({
                                        "x": cur_x,
                                        "y": cur_y,
                                        "w": item["w"],
                                        "h": item["h"],
                                        "name": item["name"]
                                    })
                                    cur_x += item["w"]
                                    remaining_on_plate.pop(i)
                                else:
                                    i += 1
                                    
                            # Interne Restflächen unter kürzeren Teilen in derselben Zeile prüfen
                            for rit in row_items:
                                if rit["h"] < row_h:
                                    sub_w = rit["w"]
                                    sub_h = row_h - rit["h"]
                                    if sub_w > 20 and sub_h > 20:
                                        is_valid_rest = (sub_w >= 500 and sub_h >= 2000) or (sub_h >= 500 and sub_w >= 2000)
                                        offcuts.append({
                                            "x": rit["x"],
                                            "y": rit["y"] + rit["h"],
                                            "w": sub_w,
                                            "h": sub_h,
                                            "to_scrap": not is_valid_rest
                                        })

                            plate_placed.extend(row_items)
                            
                            row_end_x = row_items[-1]["x"] + row_items[-1]["w"]
                            right_offcut_w = max_plate_w - row_end_x
                            if right_offcut_w > 20:
                                is_valid_rest = (right_offcut_w >= 500 and row_h >= 2000) or (row_h >= 500 and right_offcut_w >= 2000)
                                offcuts.append({
                                    "x": row_end_x,
                                    "y": cur_y,
                                    "w": right_offcut_w,
                                    "h": row_h,
                                    "to_scrap": not is_valid_rest
                                })
                                
                            cur_y += row_h + saege
                            
                        next_remaining.extend(remaining_on_plate)
                        
                        if plate_placed:
                            max_used_y = max(p["y"] + p["h"] for p in plate_placed)
                            bottom_offcut_h = max_plate_h - max_used_y
                            if bottom_offcut_h > 20:
                                offcut_w = max_plate_w - m_l
                                is_valid_rest = (offcut_w >= 500 and bottom_offcut_h >= 2000) or (bottom_offcut_h >= 500 and offcut_w >= 2000)
                                offcuts.append({
                                    "x": m_l,
                                    "y": max_used_y,
                                    "w": offcut_w,
                                    "h": bottom_offcut_h,
                                    "to_scrap": not is_valid_rest
                                })
                            
                            placed_area = sum(p["w"] * p["h"] for p in plate_placed)
                            utilization = round((placed_area / plate_total_area) * 100, 1)

                            generated_layouts.append({
                                "title": f"{title_prefix} - Platte {plate_idx}",
                                "variant_type": variant_type_key,
                                "utilization": utilization,
                                "plate_w": default_plate_w,
                                "plate_h": default_plate_h,
                                "placed": plate_placed,
                                "offcuts": offcuts
                            })
                            current_items = next_remaining
                            plate_idx += 1
                        else:
                            break
                            
                    return generated_layouts if not current_items else []

                layouts = []

                # Bauteile in Listen aufteilen
                items_normal = []
                items_rotated = []
                valid_rot = True

                for t in st.session_state.bauteile:
                    for _ in range(int(t["Anz."])):
                        items_normal.append({"w": t["Länge (mm)"], "h": t["Höhe (mm)"], "name": t["Position"]})
                    
                    rw, rh = t["Höhe (mm)"], t["Länge (mm)"]
                    if rw > max_w_row or rh > max_h_plate:
                        valid_rot = False
                    for _ in range(int(t["Anz."])):
                        items_rotated.append({"w": rw, "h": rh, "name": t["Position"]})

                # Je nach gewählter Strategie berechnen
                if strategie == "Längsschnitte bevorzugen":
                    norm_layouts = pack_all_items(items_normal, "Schnittplan (Längsschnitte)", "Laengsschnitte")
                    if norm_layouts:
                        layouts.extend(norm_layouts)
                elif strategie == "Kopfschnitte bevorzugen":
                    if valid_rot:
                        rot_layouts = pack_all_items(items_rotated, "Schnittplan (Kopfschnitte)", "Kopfschnitte")
                        if rot_layouts:
                            layouts.extend(rot_layouts)
                else:  # "Optimal"
                    norm_layouts = pack_all_items(items_normal, "Schnittplan (Standard)", "Standard")
                    if norm_layouts:
                        layouts.extend(norm_layouts)
                    if valid_rot:
                        rot_layouts = pack_all_items(items_rotated, "Schnittplan (90° Gedreht)", "Rotated")
                        if rot_layouts:
                            layouts.extend(rot_layouts)

                if layouts:
                    st.session_state.optimized_layouts = layouts
                    st.success(f"{len(layouts)} Schnittpläne erfolgreich berechnet!")
                else:
                    st.error("Bauteile überschreiten die maximalen Pressplatten-Abmessungen!")
                st.rerun()

with col_right:
    # 3 Spalten Layout: Dropdown (voll lesbar), Reststücke-Checkbox und PDF-Download
    header_c1, header_c2, header_c3 = st.columns([6.0, 2.0, 2.0])
    selected_index = 0
    with header_c1:
        if st.session_state.optimized_layouts:
            plan_options = [f"{lay['title']} — Auslastung: {lay['utilization']}%" for lay in st.session_state.optimized_layouts]
            selected_plan_title = st.selectbox("Schnittplan-Variante wählen:", plan_options, label_visibility="visible", key="sel_plan_variant")
            selected_index = plan_options.index(selected_plan_title)
        else:
            st.selectbox("Schnittplan:", ["Kein Schnittplan berechnet"], label_visibility="visible", key="sel_plan")
            
    with header_c2:
        st.write("")
        rest_chk = st.checkbox("Reststücke", value=True, key="chk_rest")

    with header_c3:
        st.write("")
        if st.session_state.optimized_layouts:
            current_layouts_list = st.session_state.optimized_layouts
            
            besaeum_info = {
                "aktiv": st.session_state.get("chk_besaeum", False),
                "l_vorn": int(st.session_state.get("num_b_l_vorn", 10)),
                "l_hinten": int(st.session_state.get("num_b_l_hinten", 10)),
                "k_vorn": int(st.session_state.get("num_b_k_vorn", 10)),
                "k_hinten": int(st.session_state.get("num_b_k_hinten", 10))
            }
            
            pdf_bytes = generate_pdf_report(
                st.session_state.get("inp_auftrag", ""),
                st.session_state.get("inp_material", ""),
                st.session_state.get("inp_sonstiges", ""),
                current_layouts_list,
                st.session_state.bauteile,
                rest_chk,
                besaeum_info
            )
            st.download_button(
                label="📥 PDF herunterladen",
                data=pdf_bytes,
                file_name="Zuschnittplan.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="btn_download_pdf"
            )
        else:
            st.button("Drucken / PDF Export", disabled=True, use_container_width=True, key="btn_pdf_disabled")

    st.markdown("### Schnittplan-Vorschau")
    
    if st.session_state.optimized_layouts:
        layout = st.session_state.optimized_layouts[selected_index]
        pw = layout["plate_w"]
        ph = layout["plate_h"]
        
        svg_w = 700
        svg_h = 350
        scale = min((svg_w - 40) / pw, (svg_h - 40) / ph) if pw > 0 and ph > 0 else 1
        
        draw_w = pw * scale
        draw_h = ph * scale
        start_x = (svg_w - draw_w) / 2
        start_y = (svg_h - draw_h) / 2
        
        rects_svg = f'''
        <defs>
            <pattern id="scrap_hatch" width="12" height="12" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
                <line x1="0" y1="0" x2="0" y2="12" stroke="#94a3b8" stroke-width="2.5" />
            </pattern>
        </defs>
        '''
        
        if st.session_state.get("chk_besaeum", False):
            bv_l = st.session_state.get("num_b_l_vorn", 10) * scale
            bv_r = st.session_state.get("num_b_l_hinten", 10) * scale
            bk_v = st.session_state.get("num_b_k_vorn", 10) * scale
            bk_h = st.session_state.get("num_b_k_hinten", 10) * scale
            
            bx = start_x + bv_l
            by = start_y + bk_v
            bw = draw_w - (bv_l + bv_r)
            bh = draw_h - (bk_v + bk_h)
            rects_svg += f'''
                <rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="none" stroke="#e74c3c" stroke-width="1.5" stroke-dasharray="6"/>
            '''

        if rest_chk and "offcuts" in layout:
            for o in layout["offcuts"]:
                ox = start_x + o["x"] * scale
                oy = start_y + o["y"] * scale
                ow = o["w"] * scale
                oh = o["h"] * scale
                
                if o["to_scrap"]:
                    rects_svg += f'''
                        <rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" fill="url(#scrap_hatch)" opacity="0.9" stroke="#64748b" stroke-width="1.5"/>
                    '''
                else:
                    rects_svg += f'''
                        <rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" fill="#e2e8f0" opacity="0.7" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4"/>
                        <text x="{ox + ow/2}" y="{oy + oh/2}" fill="#64748b" font-family="Segoe UI" font-size="10" font-weight="bold" text-anchor="middle" dominant-baseline="middle">{int(o["w"])} x {int(o["h"])}</text>
                    '''

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
            
            font_size = 11
            if rw < 60 or rh < 25:
                font_size = 8
            if rw < 40 or rh < 18:
                font_size = 6

            rects_svg += f'''
                <rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" fill="{color}" opacity="0.9" stroke="#2c3e50" stroke-width="1.5"/>
            '''
            if rw > 10 and rh > 6:
                rects_svg += f'''
                    <text x="{rx + rw/2}" y="{ry + rh/2}" fill="white" font-family="Segoe UI" font-size="{font_size}" font-weight="bold" text-anchor="middle" dominant-baseline="middle">{int(p["w"])} x {int(p["h"])}</text>
                '''
        
        svg_code = f'''
        <div style="background-color: transparent; padding: 0px;">
            <svg viewBox="0 0 {svg_w} {svg_h}" style="width: 100%; height: auto; background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px;">
                <text x="20" y="20" fill="#555555" font-family="Segoe UI" font-size="11">Platte: {int(pw)} x {int(ph)} mm ({layout['title']} — Auslastung: {layout['utilization']}%)</text>
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
