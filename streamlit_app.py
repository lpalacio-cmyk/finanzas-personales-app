"""
Finanzas WL - App de finanzas personales
Conectada a Supabase con autenticación multi-usuario.

Versión 3.0:
- Editar y borrar movimientos
- Configuración de categorías (alta/baja/renombrar con cascada)
- Gráficos en reportes (Plotly)
- Filtro por rango de fechas en Estado de Resultados y Flujo de Fondos
- Meta tags PWA para "Agregar a inicio" en celular
"""

import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
from datetime import date
from dateutil.relativedelta import relativedelta
import pandas as pd
import plotly.express as px
import io

# --- Configuración de página ---
st.set_page_config(
    page_title="Finanzas WL",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --- PWA: meta tags inyectados al <head> ---
# Streamlit no expone el <head> directamente, así que usamos un componente
# invisible (height=0) que ejecuta JS y mueve los tags al head del documento padre.
def inject_pwa_meta():
    components.html("""
    <script>
    (function() {
        try {
            const parent = window.parent.document;
            const head = parent.head;

            // Manifest inline (data URL) — para Chrome Android "Agregar a pantalla principal"
            const manifest = {
                "name": "Finanzas WL",
                "short_name": "Finanzas",
                "start_url": ".",
                "display": "standalone",
                "background_color": "#ffffff",
                "theme_color": "#102250",
                "icons": [
                    {
                        "src": "data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 192 192%22><rect width=%22192%22 height=%22192%22 fill=%22%23102250%22 rx=%2224%22/><text x=%2296%22 y=%22130%22 font-size=%22120%22 text-anchor=%22middle%22 fill=%22white%22>💰</text></svg>",
                        "sizes": "192x192",
                        "type": "image/svg+xml"
                    }
                ]
            };
            const manifestBlob = new Blob([JSON.stringify(manifest)], {type: 'application/manifest+json'});
            const manifestURL = URL.createObjectURL(manifestBlob);

            const tags = [
                {tag: 'meta', attrs: {name: 'apple-mobile-web-app-capable', content: 'yes'}},
                {tag: 'meta', attrs: {name: 'mobile-web-app-capable', content: 'yes'}},
                {tag: 'meta', attrs: {name: 'apple-mobile-web-app-status-bar-style', content: 'default'}},
                {tag: 'meta', attrs: {name: 'apple-mobile-web-app-title', content: 'Finanzas WL'}},
                {tag: 'meta', attrs: {name: 'theme-color', content: '#102250'}},
                {tag: 'link', attrs: {rel: 'manifest', href: manifestURL}},
                {tag: 'link', attrs: {rel: 'apple-touch-icon', href: 'data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 192 192%22><rect width=%22192%22 height=%22192%22 fill=%22%23102250%22 rx=%2224%22/><text x=%2296%22 y=%22130%22 font-size=%22120%22 text-anchor=%22middle%22 fill=%22white%22>💰</text></svg>'}},
            ];

            tags.forEach(t => {
                // Evitar duplicados
                const sel = t.tag + Object.keys(t.attrs).map(k => `[${k}="${t.attrs[k]}"]`).join('');
                if (!parent.querySelector(t.tag + (t.attrs.name ? `[name="${t.attrs.name}"]` : '') + (t.attrs.rel ? `[rel="${t.attrs.rel}"]` : ''))) {
                    const el = parent.createElement(t.tag);
                    Object.keys(t.attrs).forEach(k => el.setAttribute(k, t.attrs[k]));
                    head.appendChild(el);
                }
            });
        } catch(e) {
            console.warn('PWA inject failed:', e);
        }
    })();
    </script>
    """, height=0)

inject_pwa_meta()

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

# --- Acceso a datos: Categorías ---
@st.cache_data(ttl=30, show_spinner=False)
def get_categorias(user_id: str, tipo: str = None, solo_activas: bool = True):
    q = sb.table("categorias").select("*").eq("user_id", user_id)
    if solo_activas:
        q = q.eq("activa", True)
    if tipo:
        q = q.eq("tipo", tipo)
    return q.order("nombre").execute().data

def categoria_existe(user_id, nombre, tipo, excluir_id=None):
    q = (
        sb.table("categorias").select("id")
        .eq("user_id", user_id).eq("tipo", tipo).eq("nombre", nombre)
    )
    res = q.execute().data
    if excluir_id:
        res = [r for r in res if r["id"] != excluir_id]
    return len(res) > 0

def insert_categoria(user_id, nombre, tipo):
    payload = {"user_id": user_id, "nombre": nombre, "tipo": tipo, "activa": True}
    return sb.table("categorias").insert(payload).execute()

def update_categoria(user_id, cat_id, nombre=None, activa=None):
    payload = {}
    if nombre is not None:
        payload["nombre"] = nombre
    if activa is not None:
        payload["activa"] = activa
    if not payload:
        return None
    return (
        sb.table("categorias").update(payload)
        .eq("id", cat_id).eq("user_id", user_id).execute()
    )

def renombrar_categoria_en_movimientos(user_id, nombre_viejo, nombre_nuevo):
    """Propaga el rename a todos los movimientos del usuario."""
    return (
        sb.table("movimientos").update({"categoria": nombre_nuevo})
        .eq("user_id", user_id).eq("categoria", nombre_viejo).execute()
    )

def contar_movimientos_categoria(user_id, nombre, tipo):
    res = (
        sb.table("movimientos").select("id", count="exact")
        .eq("user_id", user_id).eq("categoria", nombre).eq("tipo", tipo).execute()
    )
    return res.count or 0

# --- Acceso a datos: Movimientos ---
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

def update_movimiento(user_id, mov_id, fecha_devengo, tipo, categoria, concepto, monto, cuotas, inicio_pago):
    payload = {
        "fecha_devengo": fecha_devengo.isoformat(),
        "tipo": tipo,
        "categoria": categoria,
        "concepto": concepto or None,
        "monto_total": float(monto),
        "cuotas": int(cuotas),
        "inicio_pago": inicio_pago.isoformat(),
    }
    return (
        sb.table("movimientos").update(payload)
        .eq("id", mov_id).eq("user_id", user_id).execute()
    )

def delete_movimiento(user_id, mov_id):
    return (
        sb.table("movimientos").delete()
        .eq("id", mov_id).eq("user_id", user_id).execute()
    )

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

def rango_fechas_default(df, columna="fecha_devengo"):
    """Devuelve (desde, hasta) para usar como default en filtros."""
    if df.empty:
        hoy = date.today()
        return hoy.replace(day=1), hoy
    hasta = df[columna].max().date()
    # Default: últimos 12 meses para que las tablas sean legibles
    desde = (hasta - relativedelta(months=11)).replace(day=1)
    minimo = df[columna].min().date()
    if desde < minimo:
        desde = minimo.replace(day=1)
    return desde, hasta

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
                st.warning(f"Sin categorías de tipo '{tipo}'. Creá una en ⚙️ Configuración.")
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

# --- Pantalla: Ver / Editar / Borrar movimientos ---
def page_ver(user):
    st.markdown("### Movimientos")

    df = df_movimientos(user.id)
    if df.empty:
        st.info("No tenés movimientos cargados todavía.")
        return

    # Métricas globales
    total_ing = df.loc[df["tipo"] == "Ingreso", "monto_total"].sum()
    total_gas = df.loc[df["tipo"].isin(["Gasto Fijo", "Gasto Variable"]), "monto_total"].sum()
    total_aho = df.loc[df["tipo"] == "Ahorro", "monto_total"].sum()
    col1, col2, col3 = st.columns(3)
    col1.metric("Ingresos", fmt_money(total_ing))
    col2.metric("Gastos", fmt_money(total_gas))
    col3.metric("Ahorro", fmt_money(total_aho))

    # Tabla
    df_view = df.copy()
    df_view["Devengo"] = df_view["fecha_devengo"].dt.strftime("%d/%m/%Y")
    df_view["Inicio pago"] = df_view["inicio_pago"].dt.strftime("%d/%m/%Y")
    df_view = df_view[["Devengo", "tipo", "categoria", "concepto", "monto_total", "cuotas", "Inicio pago"]]
    df_view.columns = ["Devengo", "Tipo", "Categoría", "Concepto", "Monto", "Cuotas", "Inicio pago"]
    st.dataframe(df_view, hide_index=True, use_container_width=True)

    st.divider()
    st.markdown("##### ✏️ Editar / Eliminar")

    # Selector de movimiento — etiqueta legible
    movs = df.to_dict("records")
    def label_mov(m):
        f = pd.to_datetime(m["fecha_devengo"]).strftime("%d/%m/%Y")
        return f"{f} · {m['tipo']} · {m['categoria']} · {fmt_money(m['monto_total'])} · {m['concepto'] or ''}"

    opciones = {label_mov(m): m["id"] for m in movs}
    label_sel = st.selectbox(
        "Elegí el movimiento a editar / eliminar",
        options=list(opciones.keys()),
        index=None,
        placeholder="Elegir movimiento…",
    )

    if not label_sel:
        return

    mov_id = opciones[label_sel]
    mov = next(m for m in movs if m["id"] == mov_id)

    # --- Form de edición ---
    with st.form(f"edit_{mov_id}"):
        st.caption(f"Editando: {label_sel}")

        tipos_opts = ["Ingreso", "Gasto Fijo", "Gasto Variable", "Ahorro"]
        tipo_idx = tipos_opts.index(mov["tipo"])
        tipo_e = st.selectbox("Tipo", tipos_opts, index=tipo_idx, key=f"e_tipo_{mov_id}")

        # Categorías del tipo seleccionado, incluyendo la actual aunque esté inactiva
        cats_activas = get_categorias(user.id, tipo_e, solo_activas=True)
        nombres_cats = [c["nombre"] for c in cats_activas]
        if mov["categoria"] not in nombres_cats:
            nombres_cats = [mov["categoria"]] + nombres_cats

        col1, col2 = st.columns(2)
        with col1:
            fecha_e = st.date_input("Fecha devengo",
                                    value=pd.to_datetime(mov["fecha_devengo"]).date(),
                                    format="DD/MM/YYYY", key=f"e_fdev_{mov_id}")
        with col2:
            cat_idx = nombres_cats.index(mov["categoria"]) if mov["categoria"] in nombres_cats else 0
            cat_e = st.selectbox("Categoría", nombres_cats, index=cat_idx, key=f"e_cat_{mov_id}")

        concepto_e = st.text_input("Concepto / Nota",
                                   value=mov["concepto"] or "", key=f"e_con_{mov_id}")
        monto_e = st.number_input("Monto total",
                                  min_value=0.0, step=1000.0, format="%.2f",
                                  value=float(mov["monto_total"]), key=f"e_mon_{mov_id}")

        col3, col4 = st.columns(2)
        with col3:
            cuotas_e = st.number_input("Cuotas", min_value=1, max_value=36,
                                       value=int(mov["cuotas"]), step=1, key=f"e_cuo_{mov_id}")
        with col4:
            inicio_e = st.date_input("Inicio pago",
                                     value=pd.to_datetime(mov["inicio_pago"]).date(),
                                     format="DD/MM/YYYY", key=f"e_inip_{mov_id}")

        col_g, col_d = st.columns(2)
        with col_g:
            guardar = st.form_submit_button("💾 Guardar cambios", use_container_width=True)
        with col_d:
            eliminar = st.form_submit_button("🗑️ Eliminar", use_container_width=True)

        if guardar:
            if monto_e <= 0:
                st.error("El monto debe ser mayor a cero")
            else:
                try:
                    update_movimiento(user.id, mov_id, fecha_e, tipo_e, cat_e,
                                      concepto_e, monto_e, cuotas_e, inicio_e)
                    st.success("✅ Movimiento actualizado")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al actualizar: {e}")

        if eliminar:
            # Marcamos para confirmación en el siguiente render
            st.session_state[f"confirmar_del_{mov_id}"] = True
            st.rerun()

    # --- Confirmación de eliminación (fuera del form) ---
    if st.session_state.get(f"confirmar_del_{mov_id}"):
        st.warning(f"¿Confirmás eliminar este movimiento? **{label_sel}**")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Sí, eliminar", use_container_width=True, key=f"si_del_{mov_id}"):
                try:
                    delete_movimiento(user.id, mov_id)
                    st.session_state.pop(f"confirmar_del_{mov_id}", None)
                    st.success("Movimiento eliminado")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al eliminar: {e}")
        with c2:
            if st.button("❌ Cancelar", use_container_width=True, key=f"no_del_{mov_id}"):
                st.session_state.pop(f"confirmar_del_{mov_id}", None)
                st.rerun()

# --- Pantalla: Estado de Resultados ---
def page_resultados(user):
    st.markdown("### Estado de Resultados")
    st.caption("Criterio devengado · Agrupado por mes de la fecha de devengo")

    df = df_movimientos(user.id)
    if df.empty:
        st.info("No tenés movimientos cargados todavía.")
        return

    # Filtro de fechas
    desde_def, hasta_def = rango_fechas_default(df, "fecha_devengo")
    fechas = st.date_input(
        "Rango de fechas (devengo)",
        value=(desde_def, hasta_def),
        format="DD/MM/YYYY",
        key="rango_er",
    )
    if isinstance(fechas, tuple) and len(fechas) == 2:
        desde, hasta = fechas
    else:
        desde, hasta = desde_def, hasta_def

    df = df[
        (df["fecha_devengo"].dt.date >= desde) &
        (df["fecha_devengo"].dt.date <= hasta)
    ].copy()

    if df.empty:
        st.info("No hay movimientos en el rango seleccionado.")
        return

    df["mes"] = df["fecha_devengo"].dt.to_period("M").dt.to_timestamp()

    # --- Pivot principal ---
    pivot = df.pivot_table(
        index="tipo", columns="mes", values="monto_total",
        aggfunc="sum", fill_value=0,
    )
    orden = ["Ingreso", "Gasto Fijo", "Gasto Variable", "Ahorro"]
    pivot = pivot.reindex([t for t in orden if t in pivot.index])

    pivot.loc["Resultado del período"] = (
        (pivot.loc["Ingreso"] if "Ingreso" in pivot.index else 0)
        - (pivot.loc["Gasto Fijo"] if "Gasto Fijo" in pivot.index else 0)
        - (pivot.loc["Gasto Variable"] if "Gasto Variable" in pivot.index else 0)
        - (pivot.loc["Ahorro"] if "Ahorro" in pivot.index else 0)
    )

    pivot_meses = pivot.copy()
    pivot.columns = [c.strftime("%m/%Y") for c in pivot.columns]
    pivot_fmt = pivot.copy().map(fmt_money)
    pivot_fmt.index.name = "Concepto"
    st.dataframe(pivot_fmt, use_container_width=True)

    # --- Gráfico: evolución mensual ---
    st.markdown("##### 📈 Evolución mensual")
    df_evol_rows = []
    for tipo in ["Ingreso", "Gasto Fijo", "Gasto Variable", "Ahorro"]:
        if tipo in pivot_meses.index:
            for mes, val in pivot_meses.loc[tipo].items():
                df_evol_rows.append({"Mes": mes, "Tipo": tipo, "Monto": float(val)})
    df_evol = pd.DataFrame(df_evol_rows)
    if not df_evol.empty:
        fig_evol = px.line(
            df_evol, x="Mes", y="Monto", color="Tipo",
            markers=True,
            color_discrete_map={
                "Ingreso": "#16a34a",
                "Gasto Fijo": "#dc2626",
                "Gasto Variable": "#f59e0b",
                "Ahorro": "#2563eb",
            },
        )
        fig_evol.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=320,
            xaxis_title="",
            yaxis_title="",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        )
        fig_evol.update_xaxes(tickformat="%m/%Y")
        st.plotly_chart(fig_evol, use_container_width=True,
                        config={"displayModeBar": False})

    # --- Gráfico: torta de gastos por categoría ---
    st.markdown("##### 🥧 Gastos por categoría")
    meses_disp = sorted(df["mes"].unique(), reverse=True)
    col_a, col_b = st.columns([3, 1])
    with col_a:
        mes_torta = st.selectbox(
            "Mes",
            options=["Todo el rango"] + [pd.Timestamp(d).strftime("%m/%Y") for d in meses_disp],
            key="mes_torta_er",
        )
    with col_b:
        tipo_gasto = st.selectbox("Tipo", ["Ambos", "Gasto Fijo", "Gasto Variable"], key="tipo_torta")

    df_gastos = df[df["tipo"].isin(["Gasto Fijo", "Gasto Variable"])].copy()
    if tipo_gasto != "Ambos":
        df_gastos = df_gastos[df_gastos["tipo"] == tipo_gasto]
    if mes_torta != "Todo el rango":
        df_gastos = df_gastos[df_gastos["mes"].dt.strftime("%m/%Y") == mes_torta]

    if df_gastos.empty:
        st.caption("No hay gastos en la selección.")
    else:
        df_torta = df_gastos.groupby("categoria", as_index=False)["monto_total"].sum()
        df_torta = df_torta.sort_values("monto_total", ascending=False)
        fig_torta = px.pie(
            df_torta, names="categoria", values="monto_total",
            hole=0.45,
        )
        fig_torta.update_traces(
            textposition="outside",
            textinfo="label+percent",
        )
        fig_torta.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=380,
            showlegend=False,
        )
        st.plotly_chart(fig_torta, use_container_width=True,
                        config={"displayModeBar": False})

    # --- Detalle por categoría ---
    st.markdown("##### Detalle por categoría")
    mes_sel = st.selectbox(
        "Seleccionar mes",
        options=meses_disp,
        format_func=lambda d: pd.Timestamp(d).strftime("%m/%Y"),
        key="mes_detalle_er",
    )
    df_mes = df[df["mes"] == mes_sel]
    detalle = df_mes.groupby(["tipo", "categoria"], as_index=False)["monto_total"].sum()
    detalle.columns = ["Tipo", "Categoría", "Monto"]
    detalle["Monto"] = detalle["Monto"].apply(fmt_money)
    st.dataframe(detalle, hide_index=True, use_container_width=True)

    # --- Descarga Excel ---
    excel = df_to_excel_bytes({
        "Estado de Resultados": pivot.reset_index(),
        "Detalle": detalle,
    })
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

    df_caja = expandir_a_caja(df)

    # Filtro de fechas (sobre mes_pago)
    if not df_caja.empty:
        hasta_def = df_caja["mes_pago"].max().date()
        desde_def = (hasta_def - relativedelta(months=11)).replace(day=1)
        minimo = df_caja["mes_pago"].min().date()
        if desde_def < minimo:
            desde_def = minimo.replace(day=1)
    else:
        hoy = date.today()
        desde_def, hasta_def = hoy.replace(day=1), hoy

    col1, col2 = st.columns([2, 1])
    with col1:
        fechas = st.date_input(
            "Rango de fechas (mes de pago)",
            value=(desde_def, hasta_def),
            format="DD/MM/YYYY",
            key="rango_ff",
        )
    with col2:
        saldo_inicial = st.number_input("Saldo inicial", value=0.0,
                                        step=10000.0, format="%.2f")

    if isinstance(fechas, tuple) and len(fechas) == 2:
        desde, hasta = fechas
    else:
        desde, hasta = desde_def, hasta_def

    df_caja = df_caja[
        (df_caja["mes_pago"].dt.date >= desde) &
        (df_caja["mes_pago"].dt.date <= hasta)
    ].copy()

    if df_caja.empty:
        st.info("No hay cuotas en el rango seleccionado.")
        return

    pivot = df_caja.pivot_table(
        index="tipo", columns="mes_pago", values="monto_cuota",
        aggfunc="sum", fill_value=0,
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

    pivot_meses = pivot.copy()
    pivot.columns = [c.strftime("%m/%Y") for c in pivot.columns]
    pivot_fmt = pivot.copy().map(fmt_money)
    pivot_fmt.index.name = "Concepto"
    st.dataframe(pivot_fmt, use_container_width=True)

    # --- Gráfico: flujo neto + saldo acumulado ---
    st.markdown("##### 📊 Flujo neto y saldo acumulado")
    meses_lbl = [c.strftime("%m/%Y") for c in pivot_meses.columns]
    df_chart = pd.DataFrame({
        "Mes": meses_lbl,
        "Flujo neto": list(pivot_meses.loc["Flujo neto del mes"].values),
        "Saldo acumulado": list(pivot_meses.loc["Saldo acumulado"].values),
    })

    import plotly.graph_objects as go
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_chart["Mes"], y=df_chart["Flujo neto"],
        name="Flujo neto",
        marker_color=["#16a34a" if v >= 0 else "#dc2626" for v in df_chart["Flujo neto"]],
    ))
    fig.add_trace(go.Scatter(
        x=df_chart["Mes"], y=df_chart["Saldo acumulado"],
        name="Saldo acumulado", mode="lines+markers",
        line=dict(color="#102250", width=3),
        yaxis="y2",
    ))
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=360,
        xaxis_title="",
        yaxis=dict(title="Flujo neto", showgrid=True),
        yaxis2=dict(title="Saldo", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        bargap=0.3,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # --- Detalle de cuotas por mes ---
    st.markdown("##### Detalle de cuotas por mes")
    mes_sel = st.selectbox(
        "Seleccionar mes",
        options=sorted(df_caja["mes_pago"].unique(), reverse=True),
        format_func=lambda d: pd.Timestamp(d).strftime("%m/%Y"),
        key="flujo_mes_detalle",
    )
    df_mes = df_caja[df_caja["mes_pago"] == mes_sel].copy()
    df_mes["Cuota"] = df_mes.apply(lambda r: f"{r['n_cuota']}/{r['total_cuotas']}", axis=1)
    df_mes["Monto"] = df_mes["monto_cuota"].apply(fmt_money)
    df_mes = df_mes[["tipo", "categoria", "concepto", "Cuota", "Monto"]]
    df_mes.columns = ["Tipo", "Categoría", "Concepto", "Cuota", "Monto"]
    st.dataframe(df_mes, hide_index=True, use_container_width=True)

    # --- Descarga Excel ---
    excel = df_to_excel_bytes({
        "Flujo de Fondos": pivot.reset_index(),
        "Detalle cuotas": df_mes,
    })
    st.download_button(
        "Descargar Flujo de Fondos (Excel)",
        data=excel,
        file_name="flujo_de_fondos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# --- Pantalla: Configuración de categorías ---
def page_configuracion(user):
    st.markdown("### ⚙️ Configuración de categorías")
    st.caption(
        "Las categorías se usan al cargar movimientos. Si desactivás una, "
        "deja de aparecer en el selector pero los movimientos viejos se conservan."
    )

    tipo_sel = st.selectbox(
        "Tipo",
        ["Ingreso", "Gasto Fijo", "Gasto Variable", "Ahorro"],
        key="cfg_tipo",
    )

    # --- Agregar nueva ---
    with st.form(f"nueva_cat_{tipo_sel}", clear_on_submit=True):
        st.markdown("##### Agregar categoría")
        col1, col2 = st.columns([3, 1])
        with col1:
            nuevo_nombre = st.text_input(
                "Nombre",
                placeholder=f"Ej: Internet (categoría {tipo_sel.lower()})",
                label_visibility="collapsed",
            )
        with col2:
            ok_nueva = st.form_submit_button("➕ Agregar", use_container_width=True)
        if ok_nueva:
            n = (nuevo_nombre or "").strip()
            if not n:
                st.error("Ingresá un nombre")
            elif categoria_existe(user.id, n, tipo_sel):
                st.error(f"Ya existe la categoría '{n}' para tipo {tipo_sel}")
            else:
                try:
                    insert_categoria(user.id, n, tipo_sel)
                    st.success(f"✅ Categoría '{n}' creada")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    st.divider()

    # --- Listado: activas + inactivas ---
    cats_todas = get_categorias(user.id, tipo_sel, solo_activas=False)
    if not cats_todas:
        st.info(f"No hay categorías cargadas de tipo {tipo_sel}.")
        return

    cats_activas = [c for c in cats_todas if c["activa"]]
    cats_inactivas = [c for c in cats_todas if not c["activa"]]

    st.markdown(f"##### Activas ({len(cats_activas)})")
    if not cats_activas:
        st.caption("No hay categorías activas.")
    for c in cats_activas:
        _row_categoria(user, c, activa=True)

    if cats_inactivas:
        with st.expander(f"Inactivas ({len(cats_inactivas)})"):
            for c in cats_inactivas:
                _row_categoria(user, c, activa=False)


def _row_categoria(user, c, activa):
    """Renderiza una fila editable de categoría."""
    cat_id = c["id"]
    nombre_actual = c["nombre"]
    tipo_actual = c["tipo"]

    # Estado de "modo edición"
    edit_key = f"edit_cat_{cat_id}"
    if st.session_state.get(edit_key):
        # Form de edición
        with st.form(f"form_edit_cat_{cat_id}"):
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                nuevo = st.text_input(
                    "Nuevo nombre", value=nombre_actual,
                    key=f"new_name_{cat_id}", label_visibility="collapsed",
                )
            with col2:
                guardar = st.form_submit_button("💾", use_container_width=True)
            with col3:
                cancelar = st.form_submit_button("✖", use_container_width=True)

            if guardar:
                n = (nuevo or "").strip()
                if not n:
                    st.error("El nombre no puede quedar vacío")
                elif n == nombre_actual:
                    st.session_state.pop(edit_key, None)
                    st.rerun()
                elif categoria_existe(user.id, n, tipo_actual, excluir_id=cat_id):
                    st.error(f"Ya existe '{n}' para tipo {tipo_actual}")
                else:
                    # Contar movimientos afectados
                    afectados = contar_movimientos_categoria(user.id, nombre_actual, tipo_actual)
                    try:
                        update_categoria(user.id, cat_id, nombre=n)
                        if afectados > 0:
                            renombrar_categoria_en_movimientos(user.id, nombre_actual, n)
                            st.success(
                                f"✅ Renombrada a '{n}'. {afectados} movimiento(s) actualizados."
                            )
                        else:
                            st.success(f"✅ Renombrada a '{n}'")
                        st.session_state.pop(edit_key, None)
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            if cancelar:
                st.session_state.pop(edit_key, None)
                st.rerun()
    else:
        # Vista normal (no edición)
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            afectados = contar_movimientos_categoria(user.id, nombre_actual, tipo_actual)
            badge = f"  <span style='color:gray;font-size:0.85em;'>({afectados} mov.)</span>" if afectados > 0 else ""
            st.markdown(f"**{nombre_actual}**{badge}", unsafe_allow_html=True)
        with col2:
            if st.button("✏️", key=f"btn_edit_{cat_id}", help="Renombrar",
                         use_container_width=True):
                st.session_state[edit_key] = True
                st.rerun()
        with col3:
            if activa:
                if st.button("🚫", key=f"btn_desact_{cat_id}", help="Desactivar",
                             use_container_width=True):
                    try:
                        update_categoria(user.id, cat_id, activa=False)
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                if st.button("✅", key=f"btn_react_{cat_id}", help="Reactivar",
                             use_container_width=True):
                    try:
                        update_categoria(user.id, cat_id, activa=True)
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

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
        "⚙️ Configuración",
    ])

    if "Cargar" in page:
        page_cargar(user)
    elif "Ver" in page:
        page_ver(user)
    elif "Estado" in page:
        page_resultados(user)
    elif "Flujo" in page:
        page_flujo(user)
    elif "Configuración" in page:
        page_configuracion(user)

# --- Router ---
if st.session_state.user is None:
    page_login()
else:
    app(st.session_state.user)
