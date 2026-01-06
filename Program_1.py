from pulp import *

# 1. Inisialisasi Model (Minimisasi Biaya)
model = LpProblem("Optimasi_Logistik_NML", LpMinimize)

# 2. Parameter Biaya & Jarak (Sesuai Sel B4, B5, B9, B10)
biaya_per_km = 2500
handling_per_unit = 1200000

jarak = {
    "Makassar_Priok": 1400,
    "Makassar_Perak": 900,
    "Balikpapan_Priok": 780,
    "Balikpapan_Perak": 400
}

# 3. Variabel Keputusan (Integer - Baris 18-21)
# x(rute)_(tipe_kontainer)
x18_20 = LpVariable("Makassar_Priok_20ft", lowBound=0, cat='Integer')
x18_40 = LpVariable("Makassar_Priok_40ft", lowBound=0, cat='Integer')
x19_20 = LpVariable("Makassar_Perak_20ft", lowBound=0, cat='Integer')
x19_40 = LpVariable("Makassar_Perak_40ft", lowBound=0, cat='Integer')
x20_20 = LpVariable("Balikpapan_Priok_20ft", lowBound=0, cat='Integer')
x20_40 = LpVariable("Balikpapan_Priok_40ft", lowBound=0, cat='Integer')
x21_20 = LpVariable("Balikpapan_Perak_20ft", lowBound=0, cat='Integer')
x21_40 = LpVariable("Balikpapan_Perak_40ft", lowBound=0, cat='Integer')

# 4. Fungsi Objektif (Sesuai Rumus Sel D26)
def hitung_biaya(qty_20, qty_40, dist):
    return (qty_20 + qty_40) * (dist * biaya_per_km + handling_per_unit)

model += (
    hitung_biaya(x18_20, x18_40, jarak["Makassar_Priok"]) +
    hitung_biaya(x19_20, x19_40, jarak["Makassar_Perak"]) +
    hitung_biaya(x20_20, x20_40, jarak["Balikpapan_Priok"]) +
    hitung_biaya(x21_20, x21_40, jarak["Balikpapan_Perak"])
), "Total_Biaya_Pengiriman"

# 5. Kendala (Constraints)
# Supply (Maksimal kapasitas pelabuhan asal - Baris 9-10)
model += (x18_20 + x18_40 + x19_20 + x19_40) <= 70, "Supply_Makassar"
model += (x20_20 + x20_40 + x21_20 + x21_40) <= 50, "Supply_Balikpapan"

# Demand (Minimal kebutuhan pelabuhan tujuan - Baris 11)
model += (x18_20 + x18_40 + x20_20 + x20_40) >= 60, "Demand_Priok"
model += (x19_20 + x19_40 + x21_20 + x21_40) >= 40, "Demand_Perak"

# 6. Eksekusi Solver
model.solve()

# 7. Output Hasil
print(f"Status: {LpStatus[model.status]}")
print(f"Total Biaya Minimum (Z): Rp {value(model.objective):,.0f}")
print("-" * 30)
for v in model.variables():
    if v.varValue > 0:
        print(f"{v.name}: {v.varValue} Unit")