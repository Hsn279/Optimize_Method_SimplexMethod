import streamlit as st
from pulp import *
import pandas as pd

# Konfigurasi Tampilan
st.set_page_config(page_title="NML Logistics Dashboard", layout="wide")

st.title("🚢 Sistem Optimasi Logistik PT NML")
st.markdown("---")

# --- Bagian Input (Sidebar) ---
with st.sidebar:
    st.header("⚙️ Pengaturan Biaya")
    biaya_km = st.number_input("Biaya per KM (Rp)", value=2500)
    handling = st.number_input("Handling per Unit (Rp)", value=1200000)
    
    st.markdown("---")
    st.header("📦 Pilih Tipe Kontainer")
    # Pilihan Tipe Kontainer
    pakai_20ft = st.checkbox("Gunakan 20 ft", value=True)
    pakai_40ft = st.checkbox("Gunakan 40 ft", value=True)
    
    st.markdown("---")
    st.header("⚖️ Berat Kontainer")
    w20 = st.slider("Berat 20ft (Ton)", 10, 25, 22) if pakai_20ft else 0
    w40 = st.slider("Berat 40ft (Ton)", 20, 40, 28) if pakai_40ft else 0

# --- Bagian Data (Main Page) ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("📦 Supply (Kapasitas Asal)")
    mks_sup = st.number_input("Makassar", value=70)
    bpn_sup = st.number_input("Balikpapan", value=50)

with col2:
    st.subheader("📊 Demand (Kebutuhan Tujuan)")
    priok_dem = st.number_input("Tj. Priok", value=60)
    perak_dem = st.number_input("Tj. Perak", value=40)

# --- Logika Simplex ---
if st.button("🚀 Hitung Optimasi Sekarang"):
    if not pakai_20ft and not pakai_40ft:
        st.error("Silakan pilih minimal satu tipe kontainer (20ft atau 40ft) di sidebar!")
    else:
        dist = {"mks_jk": 1400, "mks_sb": 900, "bpn_jk": 780, "bpn_sb": 400}
        model = LpProblem("NML_Optimizer", LpMinimize)
        
        # Variabel Keputusan dengan Filter Pilihan
        # Kita buat variabel hanya jika tipe kontainer dipilih
        vars_dict = {}
        routes = [("Mks_Priok", "mks_jk"), ("Mks_Perak", "mks_sb"), 
                  ("Bpn_Priok", "bpn_jk"), ("Bpn_Perak", "bpn_sb")]
        
        total_cost = 0
        for r_name, r_key in routes:
            v20, v40 = 0, 0
            if pakai_20ft:
                v20 = LpVariable(f"{r_name}_20ft", 0, None, LpInteger)
                vars_dict[f"{r_name}_20ft"] = v20
                total_cost += v20 * (dist[r_key] * biaya_km + handling)
            if pakai_40ft:
                v40 = LpVariable(f"{r_name}_40ft", 0, None, LpInteger)
                vars_dict[f"{r_name}_40ft"] = v40
                total_cost += v40 * (dist[r_key] * biaya_km + handling)
        
        model += total_cost

        # Batasan (Constraints)
        # Supply Makassar
        model += (vars_dict.get("Mks_Priok_20ft", 0) + vars_dict.get("Mks_Priok_40ft", 0) + 
                  vars_dict.get("Mks_Perak_20ft", 0) + vars_dict.get("Mks_Perak_40ft", 0)) <= mks_sup
        # Supply Balikpapan
        model += (vars_dict.get("Bpn_Priok_20ft", 0) + vars_dict.get("Bpn_Priok_40ft", 0) + 
                  vars_dict.get("Bpn_Perak_20ft", 0) + vars_dict.get("Bpn_Perak_40ft", 0)) <= bpn_sup
        # Demand Priok
        model += (vars_dict.get("Mks_Priok_20ft", 0) + vars_dict.get("Mks_Priok_40ft", 0) + 
                  vars_dict.get("Bpn_Priok_20ft", 0) + vars_dict.get("Bpn_Priok_40ft", 0)) >= priok_dem
        # Demand Perak
        model += (vars_dict.get("Mks_Perak_20ft", 0) + vars_dict.get("Mks_Perak_40ft", 0) + 
                  vars_dict.get("Bpn_Perak_20ft", 0) + vars_dict.get("Bpn_Perak_40ft", 0)) >= perak_dem

        model.solve()

        if LpStatus[model.status] == 'Optimal':
            st.success(f"### Total Biaya Minimum: Rp {value(model.objective):,.0f}")
            
            res = []
            for name, var in vars_dict.items():
                if var.varValue > 0:
                    berat_unit = w20 if "20ft" in name else w40
                    res.append({
                        "Rute & Tipe": name.replace("_", " "),
                        "Jumlah Unit": int(var.varValue),
                        "Total Berat (Ton)": int(var.varValue * berat_unit)
                    })
            
            if res:
                st.table(pd.DataFrame(res))
            else:
                st.warning("Tidak ada pengiriman yang optimal dengan parameter tersebut.")
        else:
            st.error("Solusi tidak ditemukan. Coba tambah kapasitas Supply atau kurangi Demand.")
