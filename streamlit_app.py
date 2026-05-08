"""
Finanzas WL - App de finanzas personales
Conectada a Supabase con autenticación multi-usuario.
Versión 2.1: fix de compatibilidad con pandas 2.2+ (applymap → map).
"""

import streamlit as st
from supabase import create_client, Client
from datetime import date
from dateutil.relativedelta import relativedelta
import pandas as pd
import io

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


def df_movimientos(user_id):
    movs = get_movimientos(user_id)
    if not movs:
        return pd.DataFrame()
    df = pd.DataFrame(movs)
    df["fecha_devengo"] = pd.to_datetime(df["fecha_devengo"])
    df["inicio_pago"] = pd.to_datetime(df["inicio_pago"])
    df["monto_total"] = df["monto_total"].astype(float)
    return df


def expandir_a_caja(df):
    """Expande cada movimiento en N filas (una por cuota), con su mes de pago."""
    if df.empty:
        return df
    filas = []
    for _, m in df.iterrows():
        cuotas = int(m["cuotas"])
        monto_cuota = float(m["monto_total"]) / cuotas
        for i in range(cuotas):
            mes_pago = m["inicio_pago"] + relativedelta(months=i)
            filas.append({
                "tipo": m["tipo"],
                "categoria": m["categoria"],
                "concepto": m["concepto"],
                "monto_cuota": monto_cuota,
                "mes_pago": mes_pago.replace(day=1),
                "n_cuota": i + 1,
                "total_cuotas": cuotas,
            })
    return pd.DataFrame(filas)


def df_to_excel_bytes(df_dict):
    """Convierte un dict {nombre_hoja: df} a bytes Excel descargables."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for nombre, df in df_dict.items():
            df.to_excel(writer, sheet_name=nombre, index=False)
    return output.getvalue()


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
                        st.error("Confirmá tu email antes de iniciar sesión.")
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
                        st.success("✅ Cuenta creada. Revisá tu email para confirmar.")


# --- Pantalla: Cargar movimiento ---
def page_cargar(user):
    st.markdown("### Nuevo movimiento")

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
                f"📊 **Estado de Resultados**: {fmt_money(monto)} en {fecha_devengo.strftime('%m/%Y')} (devengado).\n\n"
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
    df = df_movimientos(user.id)
    if df.empty:
        st.info("No tenés movimientos cargados todavía.")
        return

    total_ing = df.loc[df["tipo"] == "Ingreso", "monto_total"].sum()
    total_gas = df.loc[df["tipo"].isin(["Gasto Fijo", "Gasto Variable"]), "monto_total"].sum()
    total_aho = df.loc[df["tipo"] == "Ahorro", "monto_total"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Ingresos", fmt_money(total_ing))
    col2.metric("Gastos", fmt_money(total_gas))
    col3.metric("Ahorro", fmt_money(total_aho))

    df_view = df.copy()
    df_view["Devengo"] = df_view["fecha_devengo"].dt.strftime("%d/%m/%Y")
    df_view["Inicio pago"] = df_view["inicio_pago"].dt.strftime("%d/%m/%Y")
    df_view = df_view[["Devengo", "tipo", "categoria", "concepto", "monto_total", "cuotas", "Inicio pago"]]
    df_view.columns = ["Devengo", "Tipo", "Categoría", "Concepto", "Monto", "Cuotas", "Inicio pago"]
    st.dataframe(df_view, hide_index=True, use_container_width=True)


# --- Pantalla: Estado de Resultados ---
def page_resultados(user):
    st.markdown("### Estado de Resultados")
    st.caption("Criterio devengado · Agrupado por mes de la fecha de devengo")

    df = df_movimientos(user.id)
    if df.empty:
        st.info("No tenés movimientos cargados todavía.")
        return

    df["mes"] = df["fecha_devengo"].dt.to_period("M").dt.to_timestamp()

    pivot = df.pivot_table(
        index="tipo",
        columns="mes",
        values="monto_total",
        aggfunc="sum",
        fill_value=0,
    )

    orden = ["Ingreso", "Gasto Fijo", "Gasto Variable", "Ahorro"]
    pivot = pivot.reindex([t for t in orden if t in pivot.index])

    pivot.loc["Resultado del período"] = (
        (pivot.loc["Ingreso"] if "Ingreso" in pivot.index else 0)
        - (pivot.loc["Gasto Fijo"] if "Gasto Fijo" in pivot.index else 0)
        - (pivot.loc["Gasto Variable"] if "Gasto Variable" in pivot.index else 0)
        - (pivot.loc["Ahorro"] if "Ahorro" in pivot.index else 0)
    )

    pivot.columns = [c.strftime("%m/%Y") for c in pivot.columns]
    pivot_fmt = pivot.copy().map(fmt_money)
    pivot_fmt.index.name = "Concepto"

    st.dataframe(pivot_fmt, use_container_width=True)

    st.markdown("##### Detalle por categoría")
    mes_sel = st.selectbox(
        "Seleccionar mes",
        options=sorted(df["mes"].unique(), reverse=True),
        format_func=lambda d: pd.Timestamp(d).strftime("%m/%Y"),
    )
    df_mes = df[df["mes"] == mes_sel]
    detalle = df_mes.groupby(["tipo", "categoria"], as_index=False)["monto_total"].sum()
    detalle.columns = ["Tipo", "Categoría", "Monto"]
    detalle["Monto"] = detalle["Monto"].apply(fmt_money)
    st.dataframe(detalle, hide_index=True, use_container_width=True)

    excel = df_to_excel_bytes({"Estado de Resultados": pivot.reset_index(),
                               "Detalle": detalle})
    st.download_button(
        "Descargar Estado de Resultados (Excel)",
        data=excel,
        file_name="estado_resultados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# --- Pantalla: Flujo de Fondos ---
def page_flujo(user):
    st.markdown("### Flujo de Fondos")
    st.caption("Criterio caja · Cuotas distribuidas en el mes que corresponde")

    df = df_movimientos(user.id)
    if df.empty:
        st.info("No tenés movimientos cargados todavía.")
        return

    col1, col2 = st.columns([2, 1])
    with col2:
        saldo_inicial = st.number_input("Saldo inicial", value=0.0, step=10000.0, format="%.2f")

    df_caja = expandir_a_caja(df)

    pivot = df_caja.pivot_table(
        index="tipo",
        columns="mes_pago",
        values="monto_cuota",
        aggfunc="sum",
        fill_value=0,
    )

    orden = ["Ingreso", "Gasto Fijo", "Gasto Variable", "Ahorro"]
    pivot = pivot.reindex([t for t in orden if t in pivot.index])

    flujo_neto = (
        (pivot.loc["Ingreso"] if "Ingreso" in pivot.index else 0)
        - (pivot.loc["Gasto Fijo"] if "Gasto Fijo" in pivot.index else 0)
        - (pivot.loc["Gasto Variable"] if "Gasto Variable" in pivot.index else 0)
        - (pivot.loc["Ahorro"] if "Ahorro" in pivot.index else 0)
    )

    pivot.loc["Flujo neto del mes"] = flujo_neto

    saldo_final = []
    saldo = saldo_inicial
    for v in flujo_neto:
        saldo += v
        saldo_final.append(saldo)
    pivot.loc["Saldo acumulado"] = saldo_final

    pivot.columns = [c.strftime("%m/%Y") for c in pivot.columns]
    pivot_fmt = pivot.copy().map(fmt_money)
    pivot_fmt.index.name = "Concepto"

    st.dataframe(pivot_fmt, use_container_width=True)

    st.markdown("##### Detalle de cuotas por mes")
    mes_sel = st.selectbox(
        "Seleccionar mes",
        options=sorted(df_caja["mes_pago"].unique(), reverse=True),
        format_func=lambda d: pd.Timestamp(d).strftime("%m/%Y"),
        key="flujo_mes",
    )
    df_mes = df_caja[df_caja["mes_pago"] == mes_sel].copy()
    df_mes["Cuota"] = df_mes.apply(lambda r: f"{r['n_cuota']}/{r['total_cuotas']}", axis=1)
    df_mes["Monto"] = df_mes["monto_cuota"].apply(fmt_money)
    df_mes = df_mes[["tipo", "categoria", "concepto", "Cuota", "Monto"]]
    df_mes.columns = ["Tipo", "Categoría", "Concepto", "Cuota", "Monto"]
    st.dataframe(df_mes, hide_index=True, use_container_width=True)

    excel = df_to_excel_bytes({"Flujo de Fondos": pivot.reset_index(),
                               "Detalle cuotas": df_mes})
    st.download_button(
        "Descargar Flujo de Fondos (Excel)",
        data=excel,
        file_name="flujo_de_fondos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


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
        "📊 Estado de Resultados",
        "📅 Flujo de Fondos",
    ])

    if "Cargar" in page:
        page_cargar(user)
    elif "Ver" in page:
        page_ver(user)
    elif "Estado" in page:
        page_resultados(user)
    elif "Flujo" in page:
        page_flujo(user)


# --- Router ---
if st.session_state.user is None:
    page_login()
else:
    app(st.session_state.user)
