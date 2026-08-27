import pandas as pd
import plotly.express as px
import streamlit as st

import db
import style
import auth

st.set_page_config(page_title="Raya Houses | Statistik Wilayah", page_icon="🗺️", layout="wide")
db.init_db()
style.inject()
style.header("Statistik Wilayah & Tipe Properti", "Wilayah terpopuler, tipe paling dicari, dan tipe paling laku.")
auth.sidebar_user_box()

user = auth.require_login(allowed_roles=["Admin", "Manager", "Agent", "Marketing"])

listings = db.list_listings()
df = pd.DataFrame(listings)

if df.empty:
    st.info("Belum ada data listing.")
    st.stop()

# ---------------------------------------------------------------------------
# Statistik Wilayah
# ---------------------------------------------------------------------------
st.subheader("🗺️ Statistik per Wilayah (Kota)")
by_city = df.groupby("city").agg(
    total_listing=("id", "count"),
    terjual=("status", lambda s: (s == "Terjual").sum()),
    harga_rata2=("price", "mean"),
    total_dilihat=("views", "sum"),
).reset_index().sort_values("total_listing", ascending=False)

col1, col2 = st.columns(2)
with col1:
    fig = px.bar(by_city, x="city", y="total_listing", title="Jumlah Listing per Kota",
                 color_discrete_sequence=["#F2A93B"])
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig2 = px.bar(by_city.sort_values("harga_rata2", ascending=False), x="city", y="harga_rata2",
                  title="Rata-rata Harga per Kota", color_discrete_sequence=["#C9821A"])
    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig2, use_container_width=True)

display_city = by_city.copy()
display_city["harga_rata2"] = display_city["harga_rata2"].apply(style.format_rupiah)
st.dataframe(display_city.rename(columns={
    "city": "Kota", "total_listing": "Total Listing", "terjual": "Terjual",
    "harga_rata2": "Rata-rata Harga", "total_dilihat": "Total Dilihat",
}), use_container_width=True, hide_index=True)

top_city = by_city.iloc[0]
st.success(f"📍 Wilayah paling aktif: **{top_city['city']}** dengan {int(top_city['total_listing'])} listing.")

st.markdown("---")

# ---------------------------------------------------------------------------
# Jenis properti: paling dicari (views), paling laku (terjual), terbanyak (listing)
# ---------------------------------------------------------------------------
st.subheader("🏷️ Analisis Tipe Properti")
by_type = df.groupby("type").agg(
    total_listing=("id", "count"),
    terjual=("status", lambda s: (s == "Terjual").sum()),
    total_views=("views", "sum"),
).reset_index()

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**📦 Tipe Terbanyak (Total Listing)**")
    t1 = by_type.sort_values("total_listing", ascending=False)
    fig3 = px.bar(t1, x="type", y="total_listing", color_discrete_sequence=["#F2A93B"])
    fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=320)
    st.plotly_chart(fig3, use_container_width=True)
    st.caption(f"🥇 Terbanyak: **{t1.iloc[0]['type']}** ({int(t1.iloc[0]['total_listing'])} listing)")

with c2:
    st.markdown("**👁️ Tipe Paling Dicari (Total Views)**")
    t2 = by_type.sort_values("total_views", ascending=False)
    fig4 = px.bar(t2, x="type", y="total_views", color_discrete_sequence=["#78D6FF"])
    fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=320)
    st.plotly_chart(fig4, use_container_width=True)
    st.caption(f"🥇 Paling dicari: **{t2.iloc[0]['type']}** ({int(t2.iloc[0]['total_views'])} dilihat)")

with c3:
    st.markdown("**✅ Tipe Paling Laku (Terjual)**")
    t3 = by_type.sort_values("terjual", ascending=False)
    fig5 = px.bar(t3, x="type", y="terjual", color_discrete_sequence=["#7CFC8B"])
    fig5.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=320)
    st.plotly_chart(fig5, use_container_width=True)
    st.caption(f"🥇 Paling laku: **{t3.iloc[0]['type']}** ({int(t3.iloc[0]['terjual'])} unit terjual)")

st.markdown("---")
st.markdown("### 🔎 Tipe Properti Terpopuler per Wilayah")
pivot = df.groupby(["city", "type"]).size().reset_index(name="jumlah")
top_per_city = pivot.loc[pivot.groupby("city")["jumlah"].idxmax()].sort_values("jumlah", ascending=False)
st.dataframe(top_per_city.rename(columns={
    "city": "Kota", "type": "Tipe Terpopuler", "jumlah": "Jumlah Listing"
}), use_container_width=True, hide_index=True)
