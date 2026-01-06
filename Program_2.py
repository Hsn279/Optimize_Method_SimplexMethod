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
    st.header("⚖️ Berat Kontainer")
    w20 = st.slider("Berat 20ft (Ton)", 10, 25, 22)
    w40 = st.slider("Berat 40ft (Ton)", 20, 40, 28)

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
    # Jarak
    dist = {"mks_jk": 1400, "mks_sb": 900, "bpn_jk": 780, "bpn_sb": 400}
    
    # Model
    model = LpProblem("NML_Optimizer", LpMinimize)
    
    # Variabel (x18 sampai x21 sesuai baris Excel)
    x18_20 = LpVariable("Mks_Priok_20ft", 0, None, LpInteger)
    x18_40 = LpVariable("Mks_Priok_40ft", 0, None, LpInteger)
    x19_20 = LpVariable("Mks_Perak_20ft", 0, None, LpInteger)
    x19_40 = LpVariable("Mks_Perak_40ft", 0, None, LpInteger)
    x20_20 = LpVariable("Bpn_Priok_20ft", 0, None, LpInteger)
    x20_40 = LpVariable("Bpn_Priok_40ft", 0, None, LpInteger)
    x21_20 = LpVariable("Bpn_Perak_20ft", 0, None, LpInteger)
    x21_40 = LpVariable("Bpn_Perak_40ft", 0, None, LpInteger)

    # Fungsi Biaya
    def get_cost(q20, q40, d): return (q20 + q40) * (d * biaya_km + handling)
    
    model += (get_cost(x18_20, x18_40, dist["mks_jk"]) + get_cost(x19_20, x19_40, dist["mks_sb"]) +
              get_cost(x20_20, x20_40, dist["bpn_jk"]) + get_cost(x21_20, x21_40, dist["bpn_sb"]))

    # Batasan
    model += (x18_20 + x18_40 + x19_20 + x19_40) <= mks_sup
    model += (x20_20 + x20_40 + x21_20 + x21_40) <= bpn_sup
    model += (x18_20 + x18_40 + x20_20 + x20_40) >= priok_dem
    model += (x19_20 + x19_40 + x21_20 + x21_40) >= perak_dem

    model.solve()

    # Tampilkan Hasil
    st.success(f"### Total Biaya Minimum: Rp {value(model.objective):,.0f}")
    
    # Buat Tabel Hasil
    res = []
    for v in model.variables():
        if v.varValue > 0:
            berat = v.varValue * (w20 if "20ft" in v.name else w40)
            res.append({"Rute & Tipe": v.name.replace("_", " "), "Qty": int(v.varValue), "Total Berat": berat})
    
    st.table(pd.DataFrame(res))
