%%writefile app.py
import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# 1. SETTING HALAMAN
st.set_page_config(page_title="Dashboard Gempa RI Live", layout="wide", page_icon="🌋")
st_autorefresh(interval=600000, key="datarefresh")

# 2. FUNGSI AMBIL DATA TERPADU
@st.cache_data(ttl=600)
def get_combined_data():
    try:
        # Sumber 1: M > 5.0
        res5 = requests.get("https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json").json()
        df5 = pd.DataFrame(res5['Infogempa']['gempa'])
        df5['Kategori'] = "M > 5.0"
        
        # Sumber 2: Dirasakan
        resD = requests.get("https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.json").json()
        dfD = pd.DataFrame(resD['Infogempa']['gempa'])
        dfD['Kategori'] = "Dirasakan"
        
        # Gabungkan
        df = pd.concat([df5, dfD], ignore_index=True)
        
        # --- PEMBERSIHAN DATA YANG AMAN ---
        # Pisahkan Koordinat
        coords = df['Coordinates'].str.split(',', expand=True)
        df['Lat'] = pd.to_numeric(coords[0], errors='coerce')
        df['Lon'] = pd.to_numeric(coords[1], errors='coerce')
        
        # Konversi Magnitudo
        df['Magnitude'] = pd.to_numeric(df['Magnitude'], errors='coerce')
        
        # Konversi Kedalaman (Menghilangkan ' km' dengan aman)
        df['Kedalaman'] = df['Kedalaman'].astype(str).str.replace(' km', '').str.replace('km', '').str.strip()
        df['Kedalaman'] = pd.to_numeric(df['Kedalaman'], errors='coerce')
        
        # Hapus data yang gagal dikonversi
        df = df.dropna(subset=['Magnitude', 'Kedalaman', 'Lat', 'Lon'])
        
        return df.drop_duplicates(subset=['DateTime', 'Coordinates'])
    except Exception as e:
        st.error(f"Gagal mengambil data dari API BMKG: {e}")
        return pd.DataFrame()

df_all = get_combined_data()

# 3. SIDEBAR
st.sidebar.title("🎮 Kontrol Panel")
kategori = st.sidebar.multiselect("Pilih Kategori", ["M > 5.0", "Dirasakan"], default=["M > 5.0", "Dirasakan"])

# Cek apakah df_all kosong sebelum slider dibuat
if not df_all.empty:
    min_mag_val = float(df_all['Magnitude'].min())
    max_mag_val = float(df_all['Magnitude'].max())
    min_mag = st.sidebar.slider("Minimal Magnitudo", min_mag_val, max_mag_val, 4.0, step=0.1)

    # 4. FILTERING
    df_filtered = df_all[(df_all['Magnitude'] >= min_mag) & (df_all['Kategori'].isin(kategori))].copy()

    # 5. TAMPILAN UTAMA
    st.title("🛰️ Sistem Monitoring Seismik Nasional")
    
    if not df_filtered.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Gempa Terkuat", f"{df_filtered['Magnitude'].max()} M")
        m2.metric("Rerata Kedalaman", f"{int(df_filtered['Kedalaman'].mean())} km")
        m3.metric("Total Kejadian", len(df_filtered))

        st.divider()
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.subheader("📍 Peta Sebaran Spasial")
            fig_map = px.scatter_mapbox(df_filtered, lat="Lat", lon="Lon", color="Magnitude", 
                                        size="Magnitude", hover_name="Wilayah", 
                                        color_continuous_scale='Reds', zoom=3.5,
                                        mapbox_style="carto-darkmatter", height=500)
            st.plotly_chart(fig_map, use_container_width=True)

        with c2:
            st.subheader("📉 Korelasi Mag vs Kedalaman")
            fig_corr = px.scatter(df_filtered, x="Magnitude", y="Kedalaman", 
                                 color="Kategori", size="Magnitude",
                                 hover_name="Wilayah",
                                 template="plotly_dark")
            fig_corr.update_yaxes(autorange="reversed") # Agar kedalaman 0 di atas
            st.plotly_chart(fig_corr, use_container_width=True)

        # Insight Otomatis
        st.info("💡 **Insight Analisis Otomatis:**")
        dangkal = df_filtered[df_filtered['Kedalaman'] <= 50]
        persen = (len(dangkal)/len(df_filtered)*100)
        if persen > 50:
            st.warning(f"**Waspada:** {persen:.1f}% gempa adalah **Gempa Dangkal**. Risiko kerusakan infrastruktur lebih tinggi.")
        else:
            st.success(f"Dominasi gempa menengah-dalam ({100-persen:.1f}%).")
    else:
        st.warning("Data tidak ditemukan untuk filter tersebut.")
else:
    st.error("Koneksi ke BMKG terputus atau data tidak tersedia.")
