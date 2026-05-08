"""
Finanzas WL - App de finanzas personales
Conectada a Supabase con autenticación multi-usuario.
"""

import streamlit as st
from supabase import create_client, Client
from datetime import date
import pandas as pd

# --- Configuración de página ---
st.set_page_config(
    page_title="Finanzas WL",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --- Estilos (branding WL HNOS & ASOC) ---
st.markdown("""
<style>
    .stFormSubmitButton button, div[data-testid="stFormSubmitButton"] button {
        background-color: #102250 !important;
        color: white !important;
        border: none !important;
    }
    .stFormSubmitButton button:hover, div[data-testid="stFormSubmitButton"] button:hover {
        background-color: #1a2e6a !important;
        color: white !important;
    }
    h1, h2, h3 { color: #102250; }
</style>
""", unsafe_allow_html=True)


# --- Conexión a Supabase ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


sb = init_supabase()


# --- Estado de sesión ---
if "user" not in st.session_state:
    st.session_state.user = None


# --- Autenticación ---
def do_signup(email, password):
    try:
        r = sb.auth.sign_up({"email": email, "password": password})
        return r.user, None
    except Exception as e:
        return None, str(e)


def do_signin(email, password):
    try:
        r = sb.auth.sign_in_with_password({"email": email, "password": password})
        return r.user, None
    except Exception as e:
        return None, str(e)


def do_signout():
    try:
        sb.auth.sign_out()
    except Exception:
        pass
    st.session_state.user = None
    st.cache_data.clear()
    st.rerun()


# --- Acceso a datos ---
@st.cache_data(ttl=30, show_spinner=False)
def get_categorias(user_id: str, tipo: str = None):
    q = sb.table("categorias").select("*").eq("user_id", user_id).eq("activa", True)
    if tipo:
        q = q.eq("tipo", tipo)
    return q.order("nombre").execute().data


def get_movimientos(user_id: str, limit: int = None):
    q = (
        sb.table("movimientos")
        .select("*")
        .eq("user_id", user_id)
        .order("fecha_devengo", desc=True)
        .order("id", desc=True)
    )
    if limit:
        q = q.limit(limit)
    return q.execute().data


def insert_movimiento(user_id, fecha_devengo, tipo, categoria, concepto, monto, cuotas, inicio_pago):
    payload = {
        "user_id": user_id,
        "fecha_devengo": fecha_devengo.isoformat(),
        "tipo": tipo,
        "categoria": categoria,
        "concepto": concepto or None,
        "monto_total": float(monto),
        "cuotas": int(cuotas),
        "inicio_pago": inicio_pago.isoformat(),
    }
    return sb.table("movimientos").insert(payload).execute()


# --- Helpers ---
def fmt_money(n):
    try:
        return f"${n:,.0f}".replace(",", ".")
    except Exception:
        return str(n)


# --- Pantalla de login ---
def page_login():
    st.markdown("# 💰 Finanzas WL")
    st.caption("Tu Excel de finanzas, ahora desde el celular")
    st.write("")

    tab_in, tab_up = st.tabs(["Iniciar sesión", "Crear cuenta"])

    with tab_in:
        with st.form("login"):
            email = st.text_input("Email")
            password = st.text_input("Contraseña", type="password")
            ok = st.form_submit_button("Entrar", use_container_width=True)
            if ok:
                user, err = do_signin(email, password)
                if err:
                    if "Invalid login credentials" in err:
                        st.error("Email o contraseña incorrectos")
                    elif "Email not confirmed" in err:
                        st.error("Confirmá tu email antes de iniciar sesión (revisá tu bandeja de entrada).")
                    else:
                        st.error(f"Error: {err}")
                else:
                    st.session_state.user = user
                    st.rerun()

    with tab_up:
        with st.form("signup"):
            email = st.text_input("Email", key="su_email")
            password = st.text_input("Contraseña", type="password", key="su_pw",
                                     help="Mínimo 6 caracteres")
            password2 = st.text_input("Repetir contraseña", type="password", key="su_pw2")
            ok = st.form_submit_button("Crear cuenta", use_container_width=True)
            if ok:
                if not email or "@" not in email:
                    st.error("Email inválido")
                elif password != password2:
                    st.error("Las contraseñas no coinciden")
                elif len(password) < 6:
                    st.error("Mínimo 6 caracteres")
                else:
                    user, err = do_signup(email, password)
                    if err:
                        st.error(f"Error: {err}")
                    else:
                        st.success("✅ Cuenta creada. Revisá tu email para confirmar y después iniciá sesión.")


# --- Pantalla: Cargar movimiento ---
def page_cargar(user):
    st.markdown("### Nuevo movimiento")

    # Tipo fuera del form para que el dropdown de Categoría se actualice al cambiarlo
    tipo = st.selectbox(
        "Tipo",
        ["Ingreso", "Gasto Fijo", "Gasto Variable", "Ahorro"],
        index=1,
        key="tipo_select",
    )

    cats = get_categorias(user.id, tipo)

    with st.form("nuevo_mov", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha_devengo = st.date_input("Fecha devengo", value=date.today(), format="DD/MM/YYYY")
        with col2:
            if not cats:
                st.warning(f"Sin categorías de tipo '{tipo}'.")
                categoria = None
            else:
                categoria = st.selectbox("Categoría", [c["nombre"] for c in cats])

        concepto = st.text_input("Concepto / Nota", placeholder="Ej: Período 05/26")
        monto = st.number_input("Monto total", min_value=0.0, step=1000.0,
                                format="%.2f", value=0.0)

        col3, col4 = st.columns(2)
        with col3:
            cuotas = st.number_input("Cuotas", min_value=1, max_value=36, value=1, step=1)
        with col4:
            inicio_pago = st.date_input("Inicio pago", value=date.today(), format="DD/MM/YYYY")

        if cuotas > 1 and monto > 0:
            cuota_mensual = monto / cuotas
            st.info(
                f"📊 **Estado de Resultados**: {fmt_money(monto)} en {fecha_devengo.strftime('%m/%Y')} (entero, devengado).\n\n"
                f"📅 **Flujo de Fondos**: {fmt_money(cuota_mensual)}/mes × {cuotas} desde {inicio_pago.strftime('%m/%Y')} (caja)."
            )

        ok = st.form_submit_button("Guardar movimiento", use_container_width=True)
        if ok:
            if not categoria:
                st.error("Elegí una categoría")
            elif monto <= 0:
                st.error("El monto debe ser mayor a cero")
            else:
                try:
                    insert_movimiento(user.id, fecha_devengo, tipo, categoria, concepto,
                                      monto, cuotas, inicio_pago)
                    st.success(f"✅ {tipo} de {fmt_money(monto)} guardado")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

    # Últimos 10 movimientos
    st.divider()
    st.markdown("##### Últimos movimientos")
    movs = get_movimientos(user.id, limit=10)
    if not movs:
        st.caption("Todavía no cargaste ningún movimiento.")
        return

    emoji_map = {"Ingreso": "🟢", "Gasto Fijo": "🔴", "Gasto Variable": "🟠", "Ahorro": "🔵"}
    for m in movs:
        emoji = emoji_map.get(m["tipo"], "⚪")
        sign = "+ " if m["tipo"] == "Ingreso" else ""
        cuotas_lbl = f" · {m['cuotas']} cuotas" if m["cuotas"] > 1 else ""
        fecha_fmt = pd.to_datetime(m["fecha_devengo"]).strftime("%d/%m/%Y")
        line = (
            f"{emoji} **{m['categoria']}** — {m['concepto'] or ''}  \n"
            f"<span style='color: gray; font-size: 0.85em;'>{fecha_fmt}{cuotas_lbl}</span> · "
            f"**{sign}{fmt_money(m['monto_total'])}**"
        )
        st.markdown(line, unsafe_allow_html=True)


# --- Pantalla: Ver movimientos ---
def page_ver(user):
    st.markdown("### Todos los movimientos")
    movs = get_movimientos(user.id)
    if not movs:
        st.info("No tenés movimientos cargados todavía.")
        return

    df = pd.DataFrame(movs)
    df["Devengo"] = pd.to_datetime(df["fecha_devengo"]).dt.strftime("%d/%m/%Y")
    df["Inicio pago"] = pd.to_datetime(df["inicio_pago"]).dt.strftime("%d/%m/%Y")
    df = df[["Devengo", "tipo", "categoria", "concepto", "monto_total", "cuotas", "Inicio pago"]]
    df.columns = ["Devengo", "Tipo", "Categoría", "Concepto", "Monto", "Cuotas", "Inicio pago"]

    # Resumen rápido arriba
    total_ingresos = sum(m["monto_total"] for m in movs if m["tipo"] == "Ingreso")
    total_gastos = sum(m["monto_total"] for m in movs if m["tipo"] in ("Gasto Fijo", "Gasto Variable"))
    total_ahorro = sum(m["monto_total"] for m in movs if m["tipo"] == "Ahorro")

    col1, col2, col3 = st.columns(3)
    col1.metric("Ingresos", fmt_money(total_ingresos))
    col2.metric("Gastos", fmt_money(total_gastos))
    col3.metric("Ahorro", fmt_money(total_ahorro))

    st.dataframe(df, hide_index=True, use_container_width=True)


# --- App principal (logueado) ---
def app(user):
    with st.sidebar:
        st.markdown(f"**👤 {user.email}**")
        st.divider()
        if st.button("Cerrar sesión", use_container_width=True):
            do_signout()

    page = st.sidebar.radio("Menú", [
        "📝 Cargar movimiento",
        "📋 Ver movimientos",
    ])

    if "Cargar" in page:
        page_cargar(user)
    elif "Ver" in page:
        page_ver(user)


# --- Router ---
if st.session_state.user is None:
    page_login()
else:
    app(st.session_state.user)
