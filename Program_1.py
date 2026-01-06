from pulp import *

def get_num(prompt):
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("❌ Masukkan angka yang valid!")

def run_manual_route_solver():
    print("="*60)
    print("      NML LOGISTICS - MANUAL ROUTE SELECTION MODE")
    print("="*60)

    # 1. INPUT BIAYA (PER UKURAN)
    print("\n[1] PENGATURAN BIAYA")
    km20 = get_num("Biaya/KM 20ft: ")
    km40 = get_num("Biaya/KM 40ft: ")
    h20 = get_num("Handling 20ft: ")
    h40 = get_num("Handling 40ft: ")

    # 2. INPUT STOK (SUPPLY PER UKURAN)
    print("\n[2] STOK TERSEDIA (SUPPLY)")
    s_mks_20 = get_num("Stok Makassar 20ft: ")
    s_mks_40 = get_num("Stok Makassar 40ft: ")
    s_bpn_20 = get_num("Stok Balikpapan 20ft: ")
    s_bpn_40 = get_num("Stok Balikpapan 40ft: ")

    # 3. PILIHAN RUTE MANUAL
    print("\n[3] AKTIVASI RUTE (Ketik 'y' untuk Aktif, 'n' untuk Tutup)")
    all_routes = {
        "MKS_PRIOK": {"dist": 1400, "active": False},
        "MKS_PERAK": {"dist": 900,  "active": False},
        "BPN_PRIOK": {"dist": 780,  "active": False},
        "BPN_PERAK": {"dist": 400,  "active": False}
    }

    for r in all_routes:
        choice = input(f"Aktifkan Rute {r.replace('_',' -> ')}? (y/n): ").lower()
        if choice == 'y':
            all_routes[r]["active"] = True

    # 4. INPUT KEBUTUHAN (DEMAND PER UKURAN)
    print("\n[4] TARGET KEBUTUHAN (DEMAND)")
    d_priok_20 = get_num("Kebutuhan Priok 20ft: ")
    d_priok_40 = get_num("Kebutuhan Priok 40ft: ")
    d_perak_20 = get_num("Kebutuhan Perak 20ft: ")
    d_perak_40 = get_num("Kebutuhan Perak 40ft: ")

    # --- VALIDASI DASAR ---
    if (d_priok_20 + d_perak_20) > (s_mks_20 + s_bpn_20) or \
       (d_priok_40 + d_perak_40) > (s_mks_40 + s_bpn_40):
        print("\n❌ ERROR: Total Demand melebihi Total Supply per ukuran!")
        return

    # 5. MODELING
    model = LpProblem("NML_Manual_Route", LpMinimize)
    
    # Variabel: Hanya dibuat jika rute aktif
    v20 = {r: LpVariable(f"V20_{r}", 0, None, LpInteger) for r in all_routes if all_routes[r]["active"]}
    v40 = {r: LpVariable(f"V40_{r}", 0, None, LpInteger) for r in all_routes if all_routes[r]["active"]}

    if not v20:
        print("❌ Tidak ada rute yang diaktifkan!")
        return

    # OBJEKTIF
    model += (
        lpSum([v20[r] * (all_routes[r]["dist"] * km20 + h20) for r in v20]) +
        lpSum([v40[r] * (all_routes[r]["dist"] * km40 + h40) for r in v40])
    )

    # CONSTRAINTS SUPPLY
    model += lpSum([v20[r] for r in v20 if "MKS" in r]) <= s_mks_20
    model += lpSum([v40[r] for r in v40 if "MKS" in r]) <= s_mks_40
    model += lpSum([v20[r] for r in v20 if "BPN" in r]) <= s_bpn_20
    model += lpSum([v40[r] for r in v40 if "BPN" in r]) <= s_bpn_40

    # CONSTRAINTS DEMAND (EQUAL)
    model += lpSum([v20[r] for r in v20 if "PRIOK" in r]) == d_priok_20
    model += lpSum([v40[r] for r in v40 if "PRIOK" in r]) == d_priok_40
    model += lpSum([v20[r] for r in v20 if "PERAK" in r]) == d_perak_20
    model += lpSum([v40[r] for r in v40 if "PERAK" in r]) == d_perak_40

    # 6. SOLVE
    model.solve(PULP_CBC_CMD(msg=0))

    # 7. HASIL
    if LpStatus[model.status] == 'Optimal':
        print("\n" + "🏁 HASIL OPTIMASI RUTE MANUAL".center(55))
        print("="*55)
        print(f"BIAYA TOTAL MINIMUM: Rp {value(model.objective):,.0f}")
        print("-" * 55)
        print(f"{'RUTE TERPILIH':<25} | {'20ft':<8} | {'40ft':<8}")
        for r in all_routes:
            if all_routes[r]["active"]:
                val20 = int(v20[r].varValue)
                val40 = int(v40[r].varValue)
                if val20 > 0 or val40 > 0:
                    print(f"{r.replace('_',' -> '):<25} | {val20:<8} | {val40:<8}")
        print("="*55)
    else:
        print("\n❌ STATUS: Tidak Terjangkau (Infeasible).")
        print("Penyebab: Rute aktif tidak cukup untuk memenuhi target demand.")

if __name__ == "__main__":
    run_manual_route_solver()
