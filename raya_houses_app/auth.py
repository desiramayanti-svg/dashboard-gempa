"""Helper otentikasi & kontrol akses berbasis peran (role) untuk Streamlit session_state."""
import streamlit as st
import db

ROLE_ALL = ["Admin", "Manager", "Agent", "Finance", "Marketing"]


def current_user():
    return st.session_state.get("auth")


def is_logged_in() -> bool:
    return current_user() is not None


def login(username: str, password: str) -> bool:
    user = db.authenticate(username, password)
    if user:
        st.session_state["auth"] = user
        return True
    return False


def logout():
    st.session_state.pop("auth", None)


def require_login(allowed_roles=None):
    """Panggil di awal halaman terproteksi. Menghentikan render jika tidak berhak akses."""
    user = current_user()
    if not user:
        st.warning("🔒 Silakan login terlebih dahulu untuk mengakses halaman ini.")
        st.info("Buka menu **Login Staff** di sidebar untuk masuk.")
        st.stop()
    if allowed_roles and user["role"] not in allowed_roles:
        st.error(f"⛔ Akses ditolak. Halaman ini hanya untuk role: {', '.join(allowed_roles)}.")
        st.caption(f"Anda login sebagai **{user['staff_name']}** ({user['role']}).")
        st.stop()
    return user


def sidebar_user_box():
    user = current_user()
    with st.sidebar:
        st.divider()
        if user:
            st.markdown(f"**👤 {user['staff_name']}**")
            st.caption(f"Role: {user['role']}")
            if st.button("Logout", use_container_width=True):
                logout()
                st.rerun()
        else:
            st.caption("Belum login. Buka halaman **Login Staff** untuk masuk ke panel internal.")
