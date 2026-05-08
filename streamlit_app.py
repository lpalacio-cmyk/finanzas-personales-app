"""
Finanzas WL - App de finanzas personales
Conectada a Supabase con autenticación multi-usuario.

Versión 3.1 — Rebranding:
- Identidad visual WL HNOS & ASOC (logo, tipografía Open Sans + Poppins, paleta del manual de marca)
- Login rediseñado con card central
- Métricas como cards custom
- Charts con paleta corporativa
- PWA con logo real (icon-192.png + icon-512.png)
"""

import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
from datetime import date
from dateutil.relativedelta import relativedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import os
import base64

# ============================================================================
# CONSTANTES DE MARCA (Manual de Identidad WL HNOS & ASOC)
# ============================================================================
NAVY = "#102250"        # Principal corporativo
CYAN = "#1595BC"        # Secundario corporativo
GREEN = "#1C913D"       # Apoyo (positivo)
GREY = "#6C6D6D"        # Apoyo (neutro)
ORANGE = "#EA5E2D"      # Apoyo (alerta)
WHITE = "#FFFFFF"

# Colores derivados (para fondos suaves, hovers, etc.)
NAVY_HOVER = "#1a2e6a"
NAVY_LIGHT = "#e8ecf5"
BG_SOFT = "#f7f8fb"
BORDER = "#e5e7eb"
TEXT_MUTED = "#6b7280"

# Mapeo color por tipo de movimiento (para charts y métricas)
COLOR_TIPO = {
    "Ingreso": GREEN,
    "Gasto Fijo": NAVY,
    "Gasto Variable": ORANGE,
    "Ahorro": CYAN,
}

# ============================================================================
# CARGA DE LOGO (cached)
# ============================================================================
@st.cache_data(show_spinner=False)
def load_logo_bytes(path: str):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return None

@st.cache_data(show_spinner=False)
def load_logo_b64(path: str):
    b = load_logo_bytes(path)
    return base64.b64encode(b).decode() if b else None

LOGO_PATH = "logo.png"
ICON_192_PATH = "icon-192.png"
ICON_512_PATH = "icon-512.png"

# ============================================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================================
_logo_bytes = load_logo_bytes(LOGO_PATH)
_page_icon = "💰"
if _logo_bytes:
    try:
        from PIL import Image
        _page_icon = Image.open(io.BytesIO(_logo_bytes))
    except Exception:
        pass

st.set_page_config(
    page_title="Finanzas WL",
    page_icon=_page_icon,
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============================================================================
# PWA: meta tags inyectados al <head>
# ============================================================================
def inject_pwa_meta():
    icon_192_b64 = load_logo_b64(ICON_192_PATH)
    icon_512_b64 = load_logo_b64(ICON_512_PATH)

    if icon_192_b64 and icon_512_b64:
        icon_192_url = f"data:image/png;base64,{icon_192_b64}"
        icon_512_url = f"data:image/png;base64,{icon_512_b64}"
        apple_touch_icon = icon_192_url
        manifest_icons = (
            f'[{{"src":"{icon_192_url}","sizes":"192x192","type":"image/png","purpose":"any maskable"}},'
            f'{{"src":"{icon_512_url}","sizes":"512x512","type":"image/png","purpose":"any maskable"}}]'
        )
    else:
        # Fallback SVG con emoji (si el usuario aún no subió los íconos)
        svg_icon = (
            "data:image/svg+xml;utf8,"
            "<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 192 192%22>"
            "<rect width=%22192%22 height=%22192%22 fill=%22%23102250%22 rx=%2224%22/>"
            "<text x=%2296%22 y=%22130%22 font-size=%22120%22 text-anchor=%22middle%22 fill=%22white%22>💰</text>"
            "</svg>"
        )
        apple_touch_icon = svg_icon
        manifest_icons = f'[{{"src":"{svg_icon}","sizes":"192x192","type":"image/svg+xml"}}]'

    components.html(f"""
    <script>
    (function() {{
        try {{
            const parent = window.parent.document;
            const head = parent.head;

            const manifestStr = '{{"name":"Finanzas WL","short_name":"Finanzas","start_url":".","display":"standalone","background_color":"#ffffff","theme_color":"#102250","icons":{manifest_icons}}}';
            const manifestBlob = new Blob([manifestStr], {{type: 'application/manifest+json'}});
            const manifestURL = URL.createObjectURL(manifestBlob);

            const tags = [
                {{tag: 'meta', selector: 'meta[name="apple-mobile-web-app-capable"]', attrs: {{name: 'apple-mobile-web-app-capable', content: 'yes'}}}},
                {{tag: 'meta', selector: 'meta[name="mobile-web-app-capable"]', attrs: {{name: 'mobile-web-app-capable', content: 'yes'}}}},
                {{tag: 'meta', selector: 'meta[name="apple-mobile-web-app-status-bar-style"]', attrs: {{name: 'apple-mobile-web-app-status-bar-style', content: 'default'}}}},
                {{tag: 'meta', selector: 'meta[name="apple-mobile-web-app-title"]', attrs: {{name: 'apple-mobile-web-app-title', content: 'Finanzas WL'}}}},
                {{tag: 'meta', selector: 'meta[name="theme-color"]', attrs: {{name: 'theme-color', content: '#102250'}}}},
                {{tag: 'link', selector: 'link[rel="manifest"]', attrs: {{rel: 'manifest', href: manifestURL}}}},
                {{tag: 'link', selector: 'link[rel="apple-touch-icon"]', attrs: {{rel: 'apple-touch-icon', href: '{apple_touch_icon}'}}}},
            ];
            tags.forEach(t => {{
                if (!parent.querySelector(t.selector)) {{
                    const el = parent.createElement(t.tag);
                    Object.keys(t.attrs).forEach(k => el.setAttribute(k, t.attrs[k]));
                    head.appendChild(el);
                }}
            }});
        }} catch(e) {{
            console.warn('PWA inject failed:', e);
        }}
    }})();
    </script>
    """, height=0)

inject_pwa_meta()

# ============================================================================
# CSS BRANDING
# ============================================================================
CSS_BRANDING = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;500;600;700&family=Poppins:wght@500;600;700&display=swap');

:root {{
    --navy: {NAVY};
    --cyan: {CYAN};
    --green: {GREEN};
    --orange: {ORANGE};
    --grey: {GREY};
    --navy-hover: {NAVY_HOVER};
    --navy-light: {NAVY_LIGHT};
    --bg-soft: {BG_SOFT};
    --border: {BORDER};
    --text-muted: {TEXT_MUTED};
}}

html, body, [class*="css"], .stMarkdown, .stTextInput, .stSelectbox, .stNumberInput,
.stDateInput, .stRadio, .stButton, .stMetric, .stDataFrame, .stTabs, .stForm {{
    font-family: 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}}
h1, h2, h3, h4, h5, h6 {{
    font-family: 'Poppins', 'Open Sans', sans-serif !important;
    color: var(--navy) !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
}}
h1 {{ font-size: 1.85rem !important; }}
h2 {{ font-size: 1.4rem !important; }}
h3 {{ font-size: 1.15rem !important; }}

header[data-testid="stHeader"] {{ background: transparent !important; }}
.block-container {{
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 720px !important;
}}

section[data-testid="stSidebar"] {{
    background-color: white !important;
    border-right: 1px solid var(--border);
}}
section[data-testid="stSidebar"] .stRadio > div {{ gap: 0.25rem; }}
section[data-testid="stSidebar"] .stRadio label {{
    padding: 0.6rem 0.75rem;
    border-radius: 8px;
    transition: background 0.15s;
}}
section[data-testid="stSidebar"] .stRadio label:hover {{
    background: var(--navy-light);
}}

.stFormSubmitButton button,
div[data-testid="stFormSubmitButton"] button {{
    background-color: var(--navy) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.55rem 1.25rem !important;
    transition: background 0.15s ease, transform 0.05s ease !important;
    box-shadow: 0 1px 2px rgba(16, 34, 80, 0.15) !important;
}}
.stFormSubmitButton button:hover,
div[data-testid="stFormSubmitButton"] button:hover {{
    background-color: var(--navy-hover) !important;
    color: white !important;
    box-shadow: 0 2px 4px rgba(16, 34, 80, 0.2) !important;
}}

.stButton > button {{
    border-radius: 8px !important;
    border: 1px solid var(--border) !important;
    color: var(--navy) !important;
    background: white !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
}}
.stButton > button:hover {{
    border-color: var(--cyan) !important;
    color: var(--cyan) !important;
    background: white !important;
}}
.stButton > button:focus {{
    box-shadow: 0 0 0 3px rgba(21, 149, 188, 0.2) !important;
    border-color: var(--cyan) !important;
}}

.stTextInput input, .stNumberInput input, .stDateInput input,
.stTextArea textarea {{
    border-radius: 8px !important;
    border: 1px solid var(--border) !important;
    font-family: 'Open Sans', sans-serif !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}}
.stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus,
.stTextArea textarea:focus {{
    border-color: var(--cyan) !important;
    box-shadow: 0 0 0 3px rgba(21, 149, 188, 0.15) !important;
}}
.stSelectbox > div > div {{
    border-radius: 8px !important;
    border: 1px solid var(--border) !important;
}}
.stSelectbox > div > div:focus-within {{
    border-color: var(--cyan) !important;
    box-shadow: 0 0 0 3px rgba(21, 149, 188, 0.15) !important;
}}

.stTabs [data-baseweb="tab-list"] {{
    gap: 1.5rem;
    border-bottom: 1px solid var(--border);
}}
.stTabs [data-baseweb="tab"] {{
    height: auto;
    padding: 0.6rem 0.25rem !important;
    background-color: transparent !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
}}
.stTabs [aria-selected="true"] {{
    color: var(--navy) !important;
    border-bottom: 2.5px solid var(--cyan) !important;
}}

.stDataFrame [data-testid="stTable"] thead tr th,
.stDataFrame thead tr th {{
    background-color: var(--bg-soft) !important;
    color: var(--navy) !important;
    font-weight: 600 !important;
    border-bottom: 2px solid var(--navy-light) !important;
}}

.metric-card {{
    background: white;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 16px;
    box-shadow: 0 1px 2px rgba(16, 34, 80, 0.04);
    transition: box-shadow 0.15s ease;
}}
.metric-card:hover {{
    box-shadow: 0 4px 12px rgba(16, 34, 80, 0.08);
}}
.metric-card .metric-label {{
    font-size: 0.78rem;
    color: var(--text-muted);
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 6px;
}}
.metric-card .metric-value {{
    font-family: 'Poppins', sans-serif;
    font-size: 1.45rem;
    font-weight: 600;
    color: var(--navy);
    line-height: 1.1;
}}
.metric-card.metric-green .metric-value {{ color: var(--green); }}
.metric-card.metric-orange .metric-value {{ color: var(--orange); }}
.metric-card.metric-cyan .metric-value {{ color: var(--cyan); }}

.mov-row {{
    background: white;
    border: 1px solid var(--border);
    border-left: 3px solid var(--grey);
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
}}
.mov-row.mov-ingreso {{ border-left-color: var(--green); }}
.mov-row.mov-fijo    {{ border-left-color: var(--navy); }}
.mov-row.mov-variable{{ border-left-color: var(--orange); }}
.mov-row.mov-ahorro  {{ border-left-color: var(--cyan); }}
.mov-row .mov-info {{ flex: 1; min-width: 0; }}
.mov-row .mov-cat {{
    font-weight: 600;
    color: var(--navy);
    font-size: 0.95rem;
}}
.mov-row .mov-desc {{
    color: var(--text-muted);
    font-size: 0.82rem;
    margin-top: 2px;
}}
.mov-row .mov-monto {{
    font-family: 'Poppins', sans-serif;
    font-weight: 600;
    color: var(--navy);
    white-space: nowrap;
}}
.mov-row.mov-ingreso .mov-monto {{ color: var(--green); }}

.login-footer {{
    text-align: center;
    margin-top: 24px;
    color: var(--text-muted);
    font-size: 0.75rem;
}}

.page-header {{ margin-bottom: 1rem; }}
.page-header .page-title {{
    color: var(--navy);
    font-family: 'Poppins', sans-serif;
    font-weight: 600;
    font-size: 1.5rem;
    margin: 0;
}}
.page-header .page-caption {{
    color: var(--text-muted);
    font-size: 0.85rem;
    margin-top: 2px;
}}

hr {{
    border-color: var(--border) !important;
    margin: 1.25rem 0 !important;
}}

.stAlert {{ border-radius: 8px !important; }}

footer {{ visibility: hidden !important; }}
#MainMenu {{ visibility: hidden !important; }}
.modebar {{ display: none !important; }}
</style>
"""

st.markdown(CSS_BRANDING, unsafe_allow_html=True)

# ============================================================================
# CONEXIÓN A SUPABASE
# ============================================================================
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

sb = init_supabase()

# ============================================================================
# ESTADO DE SESIÓN
# ============================================================================
if "user" not in st.session_state:
    st.session_state.user = None

# ============================================================================
# AUTENTICACIÓN
# ============================================================================
def do_signup(email, password):
    try:
        r = sb.auth.sign_up({"email": email, "password": password})
        return r.user, None
    except Exception as e:
        return None, str(e)

def do_signin(email, password):
    try:
        r = sb.auth.sign_in_with_password({"email": email, "password": password})
        # Si es la primera vez que entra (todavía no tiene categorías),
        # le sembramos el set por defecto.
        if r.user:
            try:
                seed_categorias_si_vacio(r.user.id)
            except Exception:
                pass
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

# ============================================================================
# ACCESO A DATOS: CATEGORÍAS
# ============================================================================
CATEGORIAS_DEFAULT = {
    "Ingreso": [
        "Sueldo",
        "Honorarios",
        "Alquileres cobrados",
        "Rendimientos / Intereses",
        "Otros ingresos",
    ],
    "Gasto Fijo": [
        "Alquiler / Expensas",
        "Servicios (luz/gas/agua)",
        "Internet",
        "Telefonía",
        "Prepaga / Obra social",
        "Seguros",
        "Cuotas crédito",
        "Tarjeta de crédito",
    ],
    "Gasto Variable": [
        "Supermercado",
        "Comida / Restaurantes",
        "Transporte / Combustible",
        "Salud (farmacia/médicos)",
        "Indumentaria",
        "Educación",
        "Entretenimiento",
        "Hogar y mantenimiento",
        "Regalos",
        "Viajes",
    ],
    "Ahorro": [
        "Plazo fijo",
        "Dólares",
        "Inversiones (CEDEARs / FCI / Acciones)",
        "Caja de ahorro",
        "Otros",
    ],
}

def seed_categorias_si_vacio(user_id: str) -> bool:
    """Si el usuario no tiene categorías, crea el set por defecto.
    Devuelve True si sembró, False si ya tenía."""
    try:
        res = (
            sb.table("categorias").select("id", count="exact")
            .eq("user_id", user_id).limit(1).execute()
        )
        if (res.count or 0) > 0:
            return False
        rows = []
        for tipo, nombres in CATEGORIAS_DEFAULT.items():
            for nombre in nombres:
                rows.append({
                    "user_id": user_id,
                    "nombre": nombre,
                    "tipo": tipo,
                    "activa": True,
                })
        if rows:
            sb.table("categorias").insert(rows).execute()
        return True
    except Exception:
        # No romper el login si falla el seed
        return False
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

# ============================================================================
# ACCESO A DATOS: MOVIMIENTOS
# ============================================================================
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

# ============================================================================
# HELPERS
# ============================================================================
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
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for nombre, df in df_dict.items():
            df.to_excel(writer, sheet_name=nombre, index=False)
    return output.getvalue()

def rango_fechas_default(df, columna="fecha_devengo"):
    if df.empty:
        hoy = date.today()
        return hoy.replace(day=1), hoy
    hasta = df[columna].max().date()
    desde = (hasta - relativedelta(months=11)).replace(day=1)
    minimo = df[columna].min().date()
    if desde < minimo:
        desde = minimo.replace(day=1)
    return desde, hasta

# ============================================================================
# UI HELPERS
# ============================================================================
def render_logo(ancho_px: int = 160):
    if _logo_bytes:
        st.image(_logo_bytes, width=ancho_px)
    else:
        st.markdown(
            f"<div style='font-size:{ancho_px//3}px; text-align:center;'>💰</div>",
            unsafe_allow_html=True,
        )

def page_header(titulo: str, caption: str = ""):
    cap_html = f"<div class='page-caption'>{caption}</div>" if caption else ""
    st.markdown(
        f"<div class='page-header'>"
        f"<div class='page-title'>{titulo}</div>"
        f"{cap_html}"
        f"</div>",
        unsafe_allow_html=True,
    )

def metric_card(label: str, value: str, color: str = ""):
    cls = f"metric-card metric-{color}" if color else "metric-card"
    return (
        f"<div class='{cls}'>"
        f"<div class='metric-label'>{label}</div>"
        f"<div class='metric-value'>{value}</div>"
        f"</div>"
    )

def aplicar_tema_plotly(fig: go.Figure, height: int = 320):
    fig.update_layout(
        font=dict(family="Open Sans, sans-serif", color=NAVY, size=12),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
        height=height,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, x=0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11),
        ),
        hoverlabel=dict(font_family="Open Sans, sans-serif", font_size=12),
    )
    fig.update_xaxes(
        showgrid=False,
        linecolor=BORDER,
        tickfont=dict(size=11, color=TEXT_MUTED),
    )
    fig.update_yaxes(
        gridcolor=BORDER,
        linecolor=BORDER,
        tickfont=dict(size=11, color=TEXT_MUTED),
    )
    return fig

# ============================================================================
# PANTALLA: LOGIN
# ============================================================================
def page_login():
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        render_logo(ancho_px=140)

    st.markdown(
        "<div style='text-align:center; margin-top:8px;'>"
        "<h1 style='margin-bottom:4px;'>Finanzas para protagonistas</h1>"
        f"<div style='color:{TEXT_MUTED}; font-size:0.9rem;'>"
        "Tus finanzas desde un solo lugar"
        "</div></div>",
        unsafe_allow_html=True,
    )

    st.write("")  # respiro entre header y tabs

    tab_in, tab_up = st.tabs(["Iniciar sesión", "Crear cuenta"])

    with tab_in:
        with st.form("login"):
            email = st.text_input("Email", placeholder="tu@email.com")
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
            email = st.text_input("Email", key="su_email", placeholder="tu@email.com")
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

    st.markdown(
        "<div class='login-footer'>WL HNOS &amp; ASOC · Catamarca</div>",
        unsafe_allow_html=True,
    )

# ============================================================================
# PANTALLA: CARGAR MOVIMIENTO
# ============================================================================
def page_cargar(user):
    page_header("Nuevo movimiento",
                "Cargá ingresos, gastos o ahorro con criterio devengado y caja.")

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
            fecha_devengo = st.date_input("Fecha devengo", value=date.today(),
                                          format="DD/MM/YYYY")
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
            inicio_pago = st.date_input("Inicio pago", value=date.today(),
                                        format="DD/MM/YYYY")

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

    cls_map = {
        "Ingreso": "mov-ingreso",
        "Gasto Fijo": "mov-fijo",
        "Gasto Variable": "mov-variable",
        "Ahorro": "mov-ahorro",
    }
    for m in movs:
        cls = cls_map.get(m["tipo"], "")
        sign = "+ " if m["tipo"] == "Ingreso" else ""
        cuotas_lbl = f" · {m['cuotas']} cuotas" if m["cuotas"] > 1 else ""
        fecha_fmt = pd.to_datetime(m["fecha_devengo"]).strftime("%d/%m/%Y")
        concepto_lbl = m["concepto"] or m["tipo"]
        st.markdown(
            f"<div class='mov-row {cls}'>"
            f"  <div class='mov-info'>"
            f"    <div class='mov-cat'>{m['categoria']}</div>"
            f"    <div class='mov-desc'>{concepto_lbl} · {fecha_fmt}{cuotas_lbl}</div>"
            f"  </div>"
            f"  <div class='mov-monto'>{sign}{fmt_money(m['monto_total'])}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

# ============================================================================
# PANTALLA: VER / EDITAR / BORRAR MOVIMIENTOS
# ============================================================================
def page_ver(user):
    page_header("Movimientos",
                "Tus movimientos cargados. Podés editar o eliminar abajo.")

    df = df_movimientos(user.id)
    if df.empty:
        st.info("No tenés movimientos cargados todavía.")
        return

    total_ing = df.loc[df["tipo"] == "Ingreso", "monto_total"].sum()
    total_gas = df.loc[df["tipo"].isin(["Gasto Fijo", "Gasto Variable"]), "monto_total"].sum()
    total_aho = df.loc[df["tipo"] == "Ahorro", "monto_total"].sum()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(metric_card("Ingresos", fmt_money(total_ing), "green"),
                    unsafe_allow_html=True)
    with col2:
        st.markdown(metric_card("Gastos", fmt_money(total_gas), "orange"),
                    unsafe_allow_html=True)
    with col3:
        st.markdown(metric_card("Ahorro", fmt_money(total_aho), "cyan"),
                    unsafe_allow_html=True)

    st.write("")

    df_view = df.copy()
    df_view["Devengo"] = df_view["fecha_devengo"].dt.strftime("%d/%m/%Y")
    df_view["Inicio pago"] = df_view["inicio_pago"].dt.strftime("%d/%m/%Y")
    df_view = df_view[["Devengo", "tipo", "categoria", "concepto",
                       "monto_total", "cuotas", "Inicio pago"]]
    df_view.columns = ["Devengo", "Tipo", "Categoría", "Concepto",
                       "Monto", "Cuotas", "Inicio pago"]
    st.dataframe(df_view, hide_index=True, use_container_width=True)

    st.divider()
    st.markdown("##### ✏️ Editar / Eliminar")

    movs = df.to_dict("records")
    def label_mov(m):
        f = pd.to_datetime(m["fecha_devengo"]).strftime("%d/%m/%Y")
        return f"{f} · {m['tipo']} · {m['categoria']} · {fmt_money(m['monto_total'])} · {m['concepto'] or ''}"

    opciones = {label_mov(m): m["id"] for m in movs}
    label_sel = st.selectbox(
        "Elegí el movimiento",
        options=list(opciones.keys()),
        index=None,
        placeholder="Elegir movimiento…",
    )

    if not label_sel:
        return

    mov_id = opciones[label_sel]
    mov = next(m for m in movs if m["id"] == mov_id)

    with st.form(f"edit_{mov_id}"):
        st.caption(f"Editando: {label_sel}")

        tipos_opts = ["Ingreso", "Gasto Fijo", "Gasto Variable", "Ahorro"]
        tipo_idx = tipos_opts.index(mov["tipo"])
        tipo_e = st.selectbox("Tipo", tipos_opts, index=tipo_idx, key=f"e_tipo_{mov_id}")

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
            st.session_state[f"confirmar_del_{mov_id}"] = True
            st.rerun()

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

# ============================================================================
# PANTALLA: ESTADO DE RESULTADOS
# ============================================================================
def page_resultados(user):
    page_header("Estado de Resultados",
                "Criterio devengado · Agrupado por mes de la fecha de devengo.")

    df = df_movimientos(user.id)
    if df.empty:
        st.info("No tenés movimientos cargados todavía.")
        return

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

    st.markdown("##### 📈 Evolución mensual")
    df_evol_rows = []
    for tipo in orden:
        if tipo in pivot_meses.index:
            for mes, val in pivot_meses.loc[tipo].items():
                df_evol_rows.append({"Mes": mes, "Tipo": tipo, "Monto": float(val)})
    df_evol = pd.DataFrame(df_evol_rows)
    if not df_evol.empty:
        fig_evol = px.line(
            df_evol, x="Mes", y="Monto", color="Tipo",
            markers=True,
            color_discrete_map=COLOR_TIPO,
        )
        fig_evol.update_traces(line=dict(width=2.5), marker=dict(size=7))
        fig_evol = aplicar_tema_plotly(fig_evol, height=320)
        fig_evol.update_xaxes(tickformat="%m/%Y")
        st.plotly_chart(fig_evol, use_container_width=True,
                        config={"displayModeBar": False})

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
        tipo_gasto = st.selectbox("Tipo", ["Ambos", "Gasto Fijo", "Gasto Variable"],
                                  key="tipo_torta")

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
        paleta_torta = [NAVY, CYAN, ORANGE, GREEN, GREY,
                        NAVY_HOVER, "#3aa9c9", "#f08259", "#3fa85a", "#9aa0a6"]
        fig_torta = px.pie(
            df_torta, names="categoria", values="monto_total",
            hole=0.55,
            color_discrete_sequence=paleta_torta,
        )
        fig_torta.update_traces(
            textposition="outside",
            textinfo="label+percent",
            marker=dict(line=dict(color="white", width=2)),
        )
        fig_torta = aplicar_tema_plotly(fig_torta, height=380)
        fig_torta.update_layout(showlegend=False)
        st.plotly_chart(fig_torta, use_container_width=True,
                        config={"displayModeBar": False})

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

# ============================================================================
# PANTALLA: FLUJO DE FONDOS
# ============================================================================
def page_flujo(user):
    page_header("Flujo de Fondos",
                "Criterio caja · Cuotas distribuidas en el mes que corresponde.")

    df = df_movimientos(user.id)
    if df.empty:
        st.info("No tenés movimientos cargados todavía.")
        return

    df_caja = expandir_a_caja(df)

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

    st.markdown("##### 📊 Flujo neto y saldo acumulado")
    meses_lbl = [c.strftime("%m/%Y") for c in pivot_meses.columns]
    df_chart = pd.DataFrame({
        "Mes": meses_lbl,
        "Flujo neto": list(pivot_meses.loc["Flujo neto del mes"].values),
        "Saldo acumulado": list(pivot_meses.loc["Saldo acumulado"].values),
    })

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_chart["Mes"], y=df_chart["Flujo neto"],
        name="Flujo neto",
        marker_color=[GREEN if v >= 0 else ORANGE for v in df_chart["Flujo neto"]],
        marker_line_width=0,
    ))
    fig.add_trace(go.Scatter(
        x=df_chart["Mes"], y=df_chart["Saldo acumulado"],
        name="Saldo acumulado", mode="lines+markers",
        line=dict(color=NAVY, width=3),
        marker=dict(size=7, color=NAVY),
        yaxis="y2",
    ))
    fig = aplicar_tema_plotly(fig, height=360)
    fig.update_layout(
        yaxis=dict(title="Flujo neto", showgrid=True, gridcolor=BORDER,
                   tickfont=dict(size=11, color=TEXT_MUTED)),
        yaxis2=dict(title="Saldo", overlaying="y", side="right", showgrid=False,
                    tickfont=dict(size=11, color=TEXT_MUTED)),
        bargap=0.35,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

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

# ============================================================================
# PANTALLA: CONFIGURACIÓN DE CATEGORÍAS
# ============================================================================
def page_configuracion(user):
    page_header("Configuración de categorías",
                "Las categorías se usan al cargar movimientos. Si desactivás una, "
                "deja de aparecer en el selector pero los movimientos viejos se conservan.")

    tipo_sel = st.selectbox(
        "Tipo",
        ["Ingreso", "Gasto Fijo", "Gasto Variable", "Ahorro"],
        key="cfg_tipo",
    )

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
    cat_id = c["id"]
    nombre_actual = c["nombre"]
    tipo_actual = c["tipo"]

    edit_key = f"edit_cat_{cat_id}"
    if st.session_state.get(edit_key):
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
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            afectados = contar_movimientos_categoria(user.id, nombre_actual, tipo_actual)
            badge = (f"  <span style='color:{TEXT_MUTED};font-size:0.8em;'>"
                     f"({afectados} mov.)</span>") if afectados > 0 else ""
            st.markdown(
                f"<div style='padding-top:8px;'><strong style='color:{NAVY};'>{nombre_actual}</strong>{badge}</div>",
                unsafe_allow_html=True,
            )
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

# ============================================================================
# APP PRINCIPAL (LOGUEADO)
# ============================================================================
def app(user):
    with st.sidebar:
        if _logo_bytes:
            st.image(_logo_bytes, width=120)
        st.markdown(
            f"<div style='color:{TEXT_MUTED}; font-size:0.78rem; margin-top:4px;'>"
            f"WL HNOS &amp; ASOC"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='margin:14px 0 6px; color:{NAVY}; font-weight:600; font-size:0.9rem;'>"
            f"👤 {user.email}"
            f"</div>",
            unsafe_allow_html=True,
        )
        if st.button("Cerrar sesión", use_container_width=True):
            do_signout()
        st.divider()

    page = st.sidebar.radio("Menú", [
        "📝 Cargar movimiento",
        "📋 Ver movimientos",
        "📊 Estado de Resultados",
        "📅 Flujo de Fondos",
        "⚙️ Configuración",
    ], label_visibility="collapsed")

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

# ============================================================================
# ROUTER
# ============================================================================
if st.session_state.user is None:
    page_login()
else:
    app(st.session_state.user)
