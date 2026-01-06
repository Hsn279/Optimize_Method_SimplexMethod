import streamlit as st
from pulp import *
import pandas as pd
import pydeck as pdk

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="NML Logistics System", layout="wide", page_icon="🚢")

# 2. DATA PELABUHAN
pelabuhan_data = [
    {"name": "Makassar", "lat": -5.1476, "lon": 119.4327, "type": "Domestik"},
    {"name": "Balikpapan", "lat": -1.2654, "lon": 116.8312, "type": "Domestik"},
    {"name": "Priok", "lat": -6.1033, "lon": 106.8821, "type": "Domestik"},
    {"name": "Perak", "lat": -7.2015, "lon": 112.7375, "type": "Domestik"},
    {"name": "Singapore", "lat": 1.2902, "lon": 103.8519, "type": "Internasional"},
    {"name": "Shanghai", "lat": 31.2304, "lon": 121.4737, "type": "Internasional"}
]
coords = {p["name"]: {"lat": p["lat"], "lon": p["lon"]} for p in pelabuhan_data}
coords_data = [{"name": p["name"], "lat": p["lat"], "lon": p["lon"]} for p in pelabuhan_data if p["type"] == "Domestik"]

# 3. SIDEBAR CONFIGURATION
with st.sidebar:
    st.header("📍 Konfigurasi Rute")
    tipe_rute = st.multiselect("Pilih Cakupan Wilayah", ["Domestik", "Internasional"], default=["Domestik"])
    
    if "Internasional" in tipe_rute:
        st.error("### ⚠️ SYSTEM FAILURE (404)")
        st.stop()
    
    st.markdown("---")
    st.header("📦 Jenis Kontainer")
    mode_kontainer = st.radio("Pilih Mode Kontainer:", ["Semua (20ft & 40ft)", "Hanya 20ft", "Hanya 40ft"])
    
    filtered_ports = [p["name"] for p in pelabuhan_data if p["type"] == "Domestik"]
    pilihan_asal = st.multiselect("Asal (Supply)", filtered_ports, default=["Makassar", "Balikpapan"])
    pilihan_tujuan = st.multiselect("Tujuan (Demand)", filtered_ports, default=["Priok", "Perak"])
    
    st.markdown("---")
    st.header("⚙️ Parameter Biaya Terpisah")
    
    # Inisialisasi default agar tidak error
    biaya_km_20, handling_20 = 0, 0
    biaya_km_40, handling_40 = 0, 0

    if mode_kontainer in ["Semua (20ft & 40ft)", "Hanya 20ft"]:
        st.subheader("🔵 Biaya Kontainer 20ft")
        biaya_km_20 = st.number_input("Biaya/KM (20ft)", value=2500, key="km20")
        handling_20 = st.number_input("Handling (20ft)", value=1200000, key="h20")
    
    if mode_kontainer in ["Semua (20ft & 40ft)", "Hanya 40ft"]:
        st.subheader("🟢 Biaya Kontainer 40ft")
        biaya_km_40 = st.number_input("Biaya/KM (40ft)", value=4500, key="km40")
        handling_40 = st.number_input("Handling (40ft)", value=2100000, key="h40")

# 4. KONTEN UTAMA
st.title("🚢 Optimasi Logistik PT NML")

col1, col2 = st.columns(2)
with col1:
    st.subheader("📦 Stok (Supply)")
    supply_20, supply_40 = {}, {}
    for asal in pilihan_asal:
        st.markdown(f"**{asal}**")
        if mode_kontainer in ["Semua (20ft & 40ft)", "Hanya 20ft"]:
            supply_20[asal] = st.number_input(f"Stok 20ft {asal}", value=150, key=f"s20_{asal}")
        if mode_kontainer in ["Semua (20ft & 40ft)", "Hanya 40ft"]:
            supply_40[asal] = st.number_input(f"Stok 40ft {asal}", value=150, key=f"s40_{asal}")

with col2:
    st.subheader("📊 Kebutuhan (Demand)")
    demand_20, demand_40 = {}, {}
    def_vals = {"Makassar": 75, "Balikpapan": 60, "Priok": 150, "Perak": 100}
    for tujuan in pilihan_tujuan:
        st.markdown(f"**{tujuan}**")
        total_def = def_vals.get(tujuan, 50)
        if mode_kontainer in ["Semua (20ft & 40ft)", "Hanya 20ft"]:
            demand_20[tujuan] = st.number_input(f"Butuh 20ft {tujuan}", value=int(total_def * 0.6), key=f"d20_{tujuan}")
        if mode_kontainer in ["Semua (20ft & 40ft)", "Hanya 40ft"]:
            demand_40[tujuan] = st.number_input(f"Butuh 40ft {tujuan}", value=int(total_def * 0.4), key=f"d40_{tujuan}")

# 5. LOGIKA OPTIMASI
if st.button("🚀 Jalankan Optimasi"):
    dist_map = {
        ("Makassar", "Priok"): 1400, ("Makassar", "Perak"): 900, ("Makassar", "Balikpapan"): 550,
        ("Balikpapan", "Priok"): 780, ("Balikpapan", "Perak"): 400, ("Balikpapan", "Makassar"): 550,
        ("Priok", "Perak"): 800, ("Priok", "Makassar"): 1400, ("Priok", "Balikpapan"): 780,
        ("Perak", "Priok"): 800, ("Perak", "Makassar"): 900, ("Perak", "Balikpapan"): 400
    }

    model = LpProblem("NML_Split_Cost_Optimizer", LpMinimize)
    v = {}
    
    # Menyimpan koefisien biaya untuk rekap akhir
    cost_dict = {}

    for a in pilihan_asal:
        for t in pilihan_tujuan:
            if a != t:
                jarak = dist_map.get((a, t), 1000)
                if mode_kontainer in ["Semua (20ft & 40ft)", "Hanya 20ft"]:
                    v[f"{a}_{t}_20"] = LpVariable(f"{a}_{t}_20", 0, None, LpInteger)
                    cost_20 = jarak * biaya_km_20 + handling_20
                    cost_dict[f"{a}_{t}_20"] = cost_20
                
                if mode_kontainer in ["Semua (20ft & 40ft)", "Hanya 40ft"]:
                    v[f"{a}_{t}_40"] = LpVariable(f"{a}_{t}_40", 0, None, LpInteger)
                    cost_40 = jarak * biaya_km_40 + handling_40
                    cost_dict[f"{a}_{t}_40"] = cost_40

    if v:
        model += lpSum([v[k] * cost_dict[k] for k in v])
        
        # Constraints Supply & Demand
        for a in pilihan_asal:
            if mode_kontainer in ["Semua (20ft & 40ft)", "Hanya 20ft"]:
                model += lpSum([v[k] for k in v if k.startswith(f"{a}_") and "_20" in k]) <= supply_20[a]
            if mode_kontainer in ["Semua (20ft & 40ft)", "Hanya 40ft"]:
                model += lpSum([v[k] for k in v if k.startswith(f"{a}_") and "_40" in k]) <= supply_40[a]
        
        for t in pilihan_tujuan:
            if mode_kontainer in ["Semua (20ft & 40ft)", "Hanya 20ft"]:
                model += lpSum([v[k] for k in v if f"_{t}_20" in k]) >= demand_20[t]
            if mode_kontainer in ["Semua (20ft & 40ft)", "Hanya 40ft"]:
                model += lpSum([v[k] for k in v if f"_{t}_40" in k]) >= demand_40[t]

        model.solve()

        if LpStatus[model.status] == 'Optimal':
            # HITUNG REKAP BIAYA TERPISAH
            total_cost_20 = sum([var.varValue * cost_dict[k] for k, var in v.items() if "_20" in k])
            total_cost_40 = sum([var.varValue * cost_dict[k] for k, var in v.items() if "_40" in k])
            total_all = value(model.objective)

            # TAMPILAN RINGKASAN BIAYA
            st.subheader("💰 Ringkasan Biaya Terpisah")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Biaya 20ft", f"Rp {total_cost_20:,.0f}")
            c2.metric("Total Biaya 40ft", f"Rp {total_cost_40:,.0f}")
            c3.metric("Total Keseluruhan", f"Rp {total_all:,.0f}", delta=f"Mode: {mode_kontainer}", delta_color="off")
            
            # VISUALISASI DAN TABEL
            res_list = []
            arc_data = []
            for k, var in v.items():
                if var.varValue > 0:
                    a, t, tipe = k.split("_")
                    jarak_km = dist_map.get((a, t), 0)
                    res_list.append({
                        "Asal": a, "Tujuan": t, "Tipe": f"{tipe}ft", 
                        "Jarak": f"{jarak_km} KM", "Jumlah": int(var.varValue),
                        "Subtotal Biaya": f"Rp {var.varValue * cost_dict[k]:,.0f}"
                    })
                    arc_data.append({
                        "source": [coords[a]["lon"], coords[a]["lat"]],
                        "target": [coords[t]["lon"], coords[t]["lat"]],
                        "color": [0, 255, 100] if tipe == "20" else [0, 150, 255],
                        "qty": int(var.varValue), "type": tipe
                    })

            st.pydeck_chart(pdk.Deck(
                initial_view_state=pdk.ViewState(latitude=-3.5, longitude=115.0, zoom=4.2, pitch=45),
                layers=[
                    pdk.Layer("ArcLayer", data=arc_data, get_source_position="source", get_target_position="target",
                              get_source_color="color", get_target_color="color", get_width="qty * 0.3", pickable=True),
                    pdk.Layer("TextLayer", data=pd.DataFrame(coords_data), get_position="[lon, lat]", get_text="name", get_size=18)
                ]
            ))
            st.write("### 📋 Rincian Pengiriman dan Biaya")
            st.table(pd.DataFrame(res_list))
        else:
            st.error("Solusi tidak ditemukan.")

