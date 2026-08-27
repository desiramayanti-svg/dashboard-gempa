import pandas as pd
import plotly.express as px
import streamlit as st

import db
import style
import auth

st.set_page_config(page_title="Raya Houses | Statistik Penjualan", page_icon="📈", layout="wide")
db.init_db()
style.inject()
style.header("Statistik Penjualan", "Analisis performa penjualan properti & agent.")
auth.sidebar_user_box()

user = auth.require_login(allowed_roles=["Admin", "Manager", "Agent"])

listings = db.list_listings()
df = pd.DataFrame(listings)

if df.empty:
    st.info("Belum ada data listing.")
    st.stop()

if user["role"] == "Agent":
    df = df[df["agent_id"] == user["staff_id"]]
    st.caption(f"Menampilkan statistik untuk listing Anda sendiri: **{user['staff_name']}**")

terjual = df[df["status"] == "Terjual"].copy()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Listing", len(df))
c2.metric("Terjual", len(terjual))
c3.metric("Total Nilai Terjual", style.format_rupiah(terjual["price"].sum()))
conv_rate = (len(terjual) / len(df) * 100) if len(df) else 0
c4.metric("Tingkat Konversi", f"{conv_rate:.1f}%")

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Status Listing")
    status_count = df["status"].value_counts().reset_index()
    status_count.columns = ["status", "jumlah"]
    fig = px.pie(status_count, names="status", values="jumlah", hole=0.45,
                 color_discrete_sequence=px.colors.sequential.Oranges_r)
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Tren Penjualan Bulanan")
    if not terjual.empty:
        terjual["sold_date"] = pd.to_datetime(terjual["sold_date"])
        terjual["bulan"] = terjual["sold_date"].dt.to_period("M").astype(str)
        monthly = terjual.groupby("bulan").agg(jumlah=("id", "count"), nilai=("price", "sum")).reset_index()
        fig2 = px.bar(monthly, x="bulan", y="jumlah", title="Jumlah Unit Terjual per Bulan",
                      color_discrete_sequence=["#F2A93B"])
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Belum ada listing terjual.")

st.markdown("---")

if user["role"] != "Agent":
    st.subheader("🏆 Peringkat Agent Berdasarkan Penjualan")
    rank = terjual.groupby("agent_name").agg(unit_terjual=("id", "count"), total_nilai=("price", "sum")).reset_index()
    rank = rank.sort_values("total_nilai", ascending=False)
    if not rank.empty:
        fig3 = px.bar(rank, x="agent_name", y="total_nilai", text="unit_terjual",
                      title="Total Nilai Penjualan per Agent (label = jumlah unit)",
                      color_discrete_sequence=["#F2A93B"])
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig3, use_container_width=True)
        rank_display = rank.copy()
        rank_display["total_nilai"] = rank_display["total_nilai"].apply(style.format_rupiah)
        st.dataframe(rank_display.rename(columns={
            "agent_name": "Agent", "unit_terjual": "Unit Terjual", "total_nilai": "Total Nilai"
        }), use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada penjualan untuk dianalisis.")

st.subheader("🏘️ Performa per Tipe Properti")
by_type = df.groupby("type").agg(
    total_listing=("id", "count"),
    terjual=("status", lambda s: (s == "Terjual").sum()),
).reset_index()
by_type["persentase_terjual"] = (by_type["terjual"] / by_type["total_listing"] * 100).round(1)
st.dataframe(by_type.rename(columns={
    "type": "Tipe", "total_listing": "Total Listing", "terjual": "Terjual", "persentase_terjual": "% Terjual"
}), use_container_width=True, hide_index=True)
