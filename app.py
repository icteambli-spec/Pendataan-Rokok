import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io

# ==========================================
# 1. KONFIGURASI "CLOUD" LOKAL
# ==========================================
MASTER_DIR = "master pendataan cukai rokok 2025"
RESULT_DIR = "hasil_input_user"

for d in [MASTER_DIR, RESULT_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

st.set_page_config(page_title="Sistem Cukai 2025", layout="wide")

# ==========================================
# 2. MENU NAVIGASI
# ==========================================
st.sidebar.title("Navigasi Sistem")
menu = st.sidebar.radio("Pilih Akses:",["📝 Form Input User", "🔒 Menu Admin"])

# ==========================================
# 3. MENU ADMIN
# ==========================================
if menu == "🔒 Menu Admin":
    st.title("🔒 Halaman Administrator")
    password = st.text_input("Masukkan Password Admin:", type="password")
    
    if password == "icnbr034":
        st.success("Login Berhasil!")
        st.divider()
        
        # FITUR 1: UPLOAD MASTER
        st.subheader("📁 1. Upload Master File (Acuan Input User)")
        st.info("Upload format Excel Anda yang memuat PLU, DESC, KODE TOKO, dll.")
        file_master = st.file_uploader("Upload File Master Excel", type=["xlsx"])
        
        if file_master:
            master_path = os.path.join(MASTER_DIR, "master_data.xlsx")
            with open(master_path, "wb") as f:
                f.write(file_master.getbuffer())
            
            try:
                df_preview = pd.read_excel(master_path)
                st.success("✅ File Master berhasil di-upload dan terbaca oleh sistem!")
                st.write("Preview Master Data:")
                st.dataframe(df_preview.head(), use_container_width=True)
            except Exception as e:
                st.error(f"❌ Gagal membaca file Excel. Detail Error: {e}")
                
        st.divider()
        
        # FITUR 2: DOWNLOAD HASIL
        st.subheader("📥 2. Download Rekap Input User")
        all_files =[f for f in os.listdir(RESULT_DIR) if f.endswith('.csv')]
        
        if len(all_files) == 0:
            st.warning("Belum ada data yang disubmit oleh user.")
        else:
            st.write(f"Terdapat **{len(all_files)}** file hasil input dari berbagai toko.")
            if st.button("Download Semua Hasil (Jadikan 1 Excel)"):
                all_data =[]
                for file in all_files:
                    try:
                        df_temp = pd.read_csv(os.path.join(RESULT_DIR, file))
                        all_data.append(df_temp)
                    except:
                        continue
                    
                if all_data:
                    df_final = pd.concat(all_data, ignore_index=True)
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df_final.to_excel(writer, index=False, sheet_name='Rekap_Hasil')
                    
                    st.download_button(
                        label="📥 KLIK UNTUK DOWNLOAD REKAP EXCEL",
                        data=output.getvalue(),
                        file_name=f"Rekap_Sisa_Cukai_{datetime.now().strftime('%d%m%Y_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary"
                    )

    elif password != "":
        st.error("❌ Password Salah!")

# ==========================================
# 4. MENU USER (FORM INPUT DINAMIS)
# ==========================================
elif menu == "📝 Form Input User":
    st.title("📋 Pendataan QTY Sisa Cukai 2025")
    master_path = os.path.join(MASTER_DIR, "master_data.xlsx")
    
    if not os.path.exists(master_path):
        st.warning("⚠️ File Master belum di-upload. Sistem belum bisa digunakan. Silakan hubungi Admin.")
    else:
        try:
            # Membaca Data Master
            df_master = pd.read_excel(master_path)
            
            # Bersihkan nama kolom dari spasi
            df_master.columns = df_master.columns.astype(str).str.strip().str.upper()
            
            # Logika mengatasi 2 kolom "NAMA" di Excel
            if 'NAMA.1' in df_master.columns:
                df_master.rename(columns={'NAMA.1': 'NAMA TOKO'}, inplace=True)
            elif 'NAMA TOKO' not in df_master.columns and 'NAMA' in df_master.columns:
                df_master.rename(columns={'NAMA': 'NAMA TOKO'}, inplace=True)

            # === PERBAIKAN UTAMA: BERSIHKAN SPASI PADA ISI DATANYA ===
            # Menghapus spasi tersembunyi di awal/akhir teks dan mengubahnya jadi huruf besar
            df_master['KODE TOKO'] = df_master['KODE TOKO'].astype(str).str.strip().str.upper()
            df_master['NAMA TOKO'] = df_master['NAMA TOKO'].astype(str).str.strip()

            # Dictionary Toko
            df_toko = df_master[['KODE TOKO', 'NAMA TOKO']].drop_duplicates().dropna()
            dict_toko = dict(zip(df_toko['KODE TOKO'], df_toko['NAMA TOKO']))
            
            # List Produk
            df_produk = df_master[['PLU', 'DESC']].drop_duplicates().dropna()
            list_produk = df_produk.to_dict('records')
            
        except Exception as e:
            st.error(f"❌ Terjadi kesalahan membaca File Master. Detail Error: {e}")
            st.stop()
            
        # ==================== BAGIAN INPUT ====================
        col1, col2, col3 = st.columns(3)
        with col1:
            nama_user = st.text_input("NAMA KARYAWAN")
        with col2:
            nik_user = st.text_input("NIK")
        with col3:
            jabatan = st.selectbox("JABATAN",["", "COS", "SSL", "SJL", "SCB", "SCG"])
            
        st.divider()
        
        col_toko1, col_toko2 = st.columns([1, 2])
        with col_toko1:
            kode_toko = st.text_input("KODE TOKO", max_chars=4, help="Masukkan maksimal 4 digit").upper().strip()
            
        nama_toko = ""
        with col_toko2:
            if len(kode_toko) == 4:
                if kode_toko in dict_toko:
                    nama_toko = dict_toko[kode_toko]
                    st.success(f"NAMA TOKO: {nama_toko}")
                else:
                    st.error("❌ Kode Toko tidak ditemukan di Master Data!")
            elif len(kode_toko) > 0:
                st.warning("⏳ Ketik 4 digit kode toko untuk memunculkan nama toko...")
                
        # Jika toko valid
        if nama_toko != "":
            st.divider()
            st.info("💡 **INFO:** Jika fisik di toko tidak ada, isi kolom dengan angka **0 (nol)**")
            
            df_input = pd.DataFrame(list_produk)
            df_input["QTY SISA CUKAI 2025"] = None 
            
            edited_df = st.data_editor(
                df_input,
                disabled=["PLU", "DESC"],
                hide_index=True,
                use_container_width=True,
                column_config={
                    "QTY SISA CUKAI 2025": st.column_config.NumberColumn(
                        "QTY SISA CUKAI 2025",
                        help="Hanya bisa diisi angka",
                        min_value=0,
                        step=1
                    )
                }
            )
            
            # ==================== VALIDASI & SUBMIT ====================
            if st.button("💾 Simpan Pendataan", type="primary"):
                if not nama_user or not nik_user or jabatan == "":
                    st.error("⚠️ Lengkapi NAMA, NIK, dan JABATAN terlebih dahulu!")
                else:
                    if edited_df["QTY SISA CUKAI 2025"].isnull().any():
                        st.error("❌ ada kolom yang belum diisi")
                    else:
                        waktu_sekarang = datetime.now()
                        tanggal_submit = waktu_sekarang.strftime("%Y-%m-%d")
                        timestamp_lengkap = waktu_sekarang.strftime("%Y-%m-%d %H:%M:%S")
                        
                        final_data = edited_df.copy()
                        
                        # Susun kolom
                        final_data.insert(0, "KODE TOKO", kode_toko)
                        final_data.insert(0, "JABATAN", jabatan)
                        final_data.insert(0, "NIK", nik_user)
                        final_data.insert(0, "NAMA KARYAWAN", nama_user)
                        final_data.insert(4, "NAMA TOKO", nama_toko) 
                        
                        # Tambah timestamp
                        final_data["TIMESTAMP"] = timestamp_lengkap
                        
                        file_name = f"{kode_toko}_{tanggal_submit}.csv"
                        file_path = os.path.join(RESULT_DIR, file_name)
                        
                        if os.path.exists(file_path):
                            final_data.to_csv(file_path, mode='a', header=False, index=False)
                        else:
                            final_data.to_csv(file_path, index=False)
                            
                        st.success(f"✅ Data berhasil disimpan! (Tersubmit pukul {timestamp_lengkap})")
