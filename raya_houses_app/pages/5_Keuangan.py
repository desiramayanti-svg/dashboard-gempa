from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import streamlit as st

import db
import style
import auth

st.set_page_config(page_title="Raya Houses | Keuangan", page_icon="💰", layout="wide")
db.init_db()
style.inject()
style.header("Keuangan", "Pantau arus kas, komisi, dan laba perusahaan.")
auth.sidebar_user_box()

user = auth.require_login(allowed_roles=["Admin", "Manager", "Finance"])

tab_summary, tab_list, tab_add = st.tabs(["📊 Ringkasan", "📋 Riwayat Transaksi", "➕ Catat Transaksi"])

all_tx = db.list_transactions()
df_all = pd.DataFrame(all_tx)

with tab_summary:
    if df_all.empty:
        st.info("Belum ada data transaksi.")
    else:
        df_all["date"] = pd.to_datetime(df_all["date"])
        pemasukan = df_all.loc[df_all["amount"] > 0, "amount"].sum()
        pengeluaran = -df_all.loc[df_all["amount"] < 0, "amount"].sum()
        laba = pemasukan - pengeluaran

        c1, c2, c3 = st.columns(3)
        c1.metric("💵 Total Pemasukan", style.format_rupiah(pemasukan))
        c2.metric("💸 Total Pengeluaran", style.format_rupiah(pengeluaran))
        c3.metric("📈 Laba Bersih", style.format_rupiah(laba))

        df_all["bulan"] = df_all["date"].dt.to_period("M").astype(str)
        monthly = df_all.groupby("bulan").apply(
            lambda g: pd.Series({
                "Pemasukan": g.loc[g["amount"] > 0, "amount"].sum(),
                "Pengeluaran": -g.loc[g["amount"] < 0, "amount"].sum(),
            })
        ).reset_index()
        monthly_melt = monthly.melt(id_vars="bulan", value_vars=["Pemasukan", "Pengeluaran"], var_name="Jenis", value_name="Nilai")

        fig = px.bar(monthly_melt, x="bulan", y="Nilai", color="Jenis", barmode="group",
                     title="Arus Kas Bulanan", color_discrete_map={"Pemasukan": "#F2A93B", "Pengeluaran": "#8B1E1E"})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Rincian per Jenis Transaksi")
        by_type = df_all.groupby("type")["amount"].sum().reset_index().sort_values("amount")
        fig2 = px.bar(by_type, x="amount", y="type", orientation="h", title="Total Nilai per Jenis Transaksi",
                      color="amount", color_continuous_scale="oranges")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

with tab_list:
    c1, c2, c3 = st.columns(3)
    f_type = c1.selectbox("Filter Jenis", ["Semua"] + db.TRANSACTION_TYPES)
    start_date = c2.date_input("Dari Tanggal", value=date.today() - timedelta(days=365))
    end_date = c3.date_input("Sampai Tanggal", value=date.today())

    filters = {
        "type": None if f_type == "Semua" else f_type,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
    }
    tx = db.list_transactions(filters)
    if not tx:
        st.info("Tidak ada transaksi pada rentang ini.")
    else:
        df = pd.DataFrame(tx)
        df["amount_fmt"] = df["amount"].apply(style.format_rupiah)
        st.dataframe(
            df[["id", "date", "type", "amount_fmt", "listing_title", "agent_name", "description"]].rename(
                columns={"amount_fmt": "amount", "listing_title": "listing", "agent_name": "agent"}
            ),
            use_container_width=True, hide_index=True,
        )

        if user["role"] == "Admin":
            del_id = st.number_input("ID transaksi yang ingin dihapus", min_value=0, step=1)
            if st.button("🗑️ Hapus Transaksi") and del_id:
                db.delete_transaction(int(del_id))
                st.success("Transaksi dihapus.")
                st.rerun()

with tab_add:
    listings = db.list_listings()
    listing_options = {"(Tidak terkait listing)": None}
    listing_options.update({f"#{l['id']} - {l['title']}": l["id"] for l in listings})
    agents = db.list_staff(role="Agent")
    agent_options = {"(Tidak terkait agent)": None}
    agent_options.update({a["name"]: a["id"] for a in agents})

    with st.form("add_tx_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        ttype = c1.selectbox("Jenis Transaksi*", db.TRANSACTION_TYPES)
        amount = c2.number_input(
            "Nominal (Rp) — gunakan angka negatif untuk pengeluaran*",
            step=100_000.0, format="%.0f",
        )
        tdate = c1.date_input("Tanggal*", value=date.today())
        listing_label = c2.selectbox("Listing Terkait", list(listing_options.keys()))
        agent_label = c1.selectbox("Agent Terkait", list(agent_options.keys()))
        description = st.text_area("Keterangan")

        submitted = st.form_submit_button("💾 Simpan Transaksi", use_container_width=True)
        if submitted:
            db.add_transaction(
                listing_options[listing_label], agent_options[agent_label], ttype,
                amount, tdate.strftime("%Y-%m-%d"), description,
            )
            st.success("Transaksi berhasil dicatat.")
