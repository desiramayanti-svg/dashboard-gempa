import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh # Perlu install streamlit-autorefresh

# 1. SETTING HALAMAN & AUTO REFRESH
st.set_page_config(page_title="Dashboard Gempa RI Live", layout="wide", page_icon="🌋")

# Update otomatis setiap 10 menit (600.000 milidetik)
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
        
        df = pd.concat([df5, dfD], ignore_index=True)
        df[['Lat', 'Lon']] = df['Coordinates'].str.split(',', expand=True).astype(float)
        df['Magnitude'] = df['Magnitude'].astype(float)
        df['Kedalaman'] = df['Kedalaman'].str.replace(' km', '').astype(int)
        return df.drop_duplicates(subset=['DateTime', 'Coordinates'])
    except:
        return pd.DataFrame() # Jika API Down

df_all = get_combined_data()

# 3. SIDEBAR
st.sidebar.title("🎮 Kontrol Panel")
st.sidebar.info("Dashboard ini melakukan refresh otomatis setiap 10 menit.")
min_mag = st.sidebar.slider("Filter Minimal Magnitudo", 3.0, 9.0, 4.5, step=0.1)
kategori = st.sidebar.multiselect("Kategori Data", ["M > 5.0", "Dirasakan"], default=["M > 5.0", "Dirasakan"])

# Filtering
df_filtered = df_all[(df_all['Magnitude'] >= min_mag) & (df_all['Kategori'].isin(kategori))]

# 4. HEADER
st.title("🛰️ Sistem Monitoring Seismik Nasional (Real-Time)")
st.markdown(f"Status Data: **Aktif** | Total Kejadian Terdeteksi: **{len(df_filtered)}**")

# 5. LAYOUT UTAMA
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.subheader("📍 Visualisasi Spasial")
    fig = px.scatter_mapbox(df_filtered, lat="Lat", lon="Lon", color="Kedalaman", 
                            size="Magnitude", hover_name="Wilayah", 
                            color_continuous_scale='RdYlGn_r', zoom=3.8,
                            mapbox_style="carto-darkmatter", height=500)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 Statistik")
    st.metric("Gempa Terkuat", f"{df_filtered['Magnitude'].max()} M")
    st.metric("Rerata Kedalaman", f"{int(df_filtered['Kedalaman'].mean())} km")

with col3:
    st.subheader("📋 Log Terakhir")
    st.write(df_filtered[['Tanggal', 'Magnitude', 'Wilayah']].head(10))

# 6. MODUL INTERPRETASI OTOMATIS
st.divider()
st.subheader("🧠 Automated Data Insight")
gempa_dangkal = df_filtered[df_filtered['Kedalaman'] <= 50]
persen = (len(gempa_dangkal)/len(df_filtered)*100) if len(df_filtered)>0 else 0

if persen > 50:
    st.warning(f"**ANALISIS:** Terdeteksi dominasi gempa dangkal ({persen:.1f}%). Wilayah titik merah pada peta memerlukan perhatian ekstra pada ketahanan bangunan.")
else:
    st.success("**ANALISIS:** Distribusi gempa didominasi kedalaman menengah-dalam. Risiko kerusakan langsung pada bangunan cenderung lebih rendah.")

st.caption("Pusat Data Seismik Nasional - Dikembangkan untuk Penelitian Mitigasi Bencana")
