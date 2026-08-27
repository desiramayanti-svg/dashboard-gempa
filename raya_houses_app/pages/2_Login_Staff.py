import streamlit as st
import db
import style
import auth

st.set_page_config(page_title="Raya Houses | Login Staff", page_icon="🔐", layout="centered")
db.init_db()
style.inject()
style.header("Login Staff", "Akses panel internal untuk staff dan agent Raya Houses.")
auth.sidebar_user_box()

user = auth.current_user()

if user:
    st.success(f"Anda sudah login sebagai **{user['staff_name']}** ({user['role']}).")
    st.write("Silakan buka menu manajemen di sidebar sesuai peran Anda.")
    if st.button("Logout"):
        auth.logout()
        st.rerun()
else:
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)
        if submitted:
            if auth.login(username, password):
                st.success("Login berhasil!")
                st.rerun()
            else:
                st.error("Username atau password salah, atau akun tidak aktif.")

    with st.expander("ℹ️ Akun demo untuk uji coba"):
        st.markdown(
            """
            | Username | Password | Role |
            |---|---|---|
            | admin | admin123 | Admin |
            | manager | manager123 | Manager |
            | finance | finance123 | Finance |
            | agent.andi | agent123 | Agent |

            ⚠️ Ganti seluruh password akun demo ini sebelum aplikasi digunakan secara produksi.
            """
        )
