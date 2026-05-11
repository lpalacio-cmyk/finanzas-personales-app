"""
Finanzas WL - App de finanzas personales
Conectada a Supabase con autenticación multi-usuario.

Versión 3.4 — Tanda 2.1: Saldo inicial como AJUSTE ADITIVO (no override)
- El monto en saldos_iniciales se interpreta como un DELTA sobre el cálculo automático.
- Fórmula: Saldo inicial M = Saldo final M-1 + Ajuste manual M
- Para el primer mes con datos: SF M-1 = 0, entonces el ajuste = saldo inicial de partida.
- Para meses intermedios: el ajuste reconcilia discrepancias y se preserva en meses posteriores.
- UI: el form muestra "automático + tu ajuste = saldo efectivo" en vivo.
- Cargar ajuste = 0 borra el registro (vuelve al cálculo puro).
- Fila opcional "Ajuste" en la pivot, solo si hay ajustes en el rango.

Versión 3.3 — Tanda 2: Saldos iniciales por mes (persistentes y editables)
- Tabla nueva en Supabase: saldos_iniciales (user_id, mes, monto)
- Saldo inicial de cada mes se calcula encadenadamente desde el primero
- Form para ajustar el saldo inicial de cualquier mes y persistirlo
- Bug resuelto: el saldo inicial ya no se borra al cambiar de pestaña

Versión 3.2 — Tanda 1 de mejoras UX:
- Formato monetario es-AR ($77.569,90 con punto miles y coma decimal)
- Separadores es-AR aplicados también a tooltips y axis de Plotly
- "Fecha devengo" → "Fecha del movimiento" en formularios
- Inputs de monto vacíos por default (placeholder "0,00") en lugar de "0.00" preescrito
- En Flujo de Fondos: "Flujo neto del mes" → "Flujo neto", "Saldo acumulado" → "Saldo final"
- Eliminado el gráfico de "Flujo neto y saldo acumulado"

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
        # Defensa: limpiar cualquier sesión previa que pudiera estar contaminada
        # antes de iniciar la nueva. Evita que el cliente Supabase cacheado quede
        # con headers/tokens del usuario anterior.
        try:
            sb.auth.sign_out()
        except Exception:
            pass
        st.cache_data.clear()

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
    st.cache_resource.clear()  # fuerza recreación del cliente Supabase con sesión limpia
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
# ACCESO A DATOS: SALDOS INICIALES MANUALES
# ============================================================================
@st.cache_data(ttl=30, show_spinner=False)
def get_saldos_iniciales_manuales(user_id: str) -> dict:
    """
    Retorna un dict {date(yyyy,mm,01): ajuste_float} con los ajustes manuales
    cargados por el usuario.

    SEMÁNTICA (v3.4):
    El valor guardado es un DELTA (ajuste aditivo) sobre el saldo inicial calculado
    automáticamente del mes anterior. Para el primer mes con datos, el saldo final
    del mes anterior es 0, entonces el ajuste funciona como saldo de partida absoluto.

    Fórmula completa: Saldo inicial M = Saldo final M-1 + ajustes.get(M, 0)
    """
    res = (
        sb.table("saldos_iniciales").select("mes, monto")
        .eq("user_id", user_id).execute().data
    )
    out = {}
    for r in res:
        d = pd.to_datetime(r["mes"]).date().replace(day=1)
        out[d] = float(r["monto"])
    return out

def upsert_saldo_inicial(user_id, mes_date, monto):
    """
    Inserta o actualiza el saldo inicial manual del mes indicado.
    `mes_date` debe ser un objeto date; se normaliza al primer día del mes.
    """
    mes_norm = mes_date.replace(day=1)
    payload = {
        "user_id": user_id,
        "mes": mes_norm.isoformat(),
        "monto": float(monto),
        "updated_at": "now()",
    }
    # Si ya existe (user_id+mes), update; si no, insert.
    existing = (
        sb.table("saldos_iniciales").select("id")
        .eq("user_id", user_id).eq("mes", mes_norm.isoformat()).execute().data
    )
    if existing:
        return (
            sb.table("saldos_iniciales")
            .update({"monto": float(monto), "updated_at": "now()"})
            .eq("user_id", user_id).eq("mes", mes_norm.isoformat()).execute()
        )
    return sb.table("saldos_iniciales").insert(payload).execute()

def delete_saldo_inicial(user_id, mes_date):
    mes_norm = mes_date.replace(day=1)
    return (
        sb.table("saldos_iniciales").delete()
        .eq("user_id", user_id).eq("mes", mes_norm.isoformat()).execute()
    )

# ============================================================================
# HELPERS
# ============================================================================
def fmt_money(n, decimals: int = 2):
    """
    Formato monetario es-AR: $77.569,90 / -$5.500,25
    - Punto como separador de miles
    - Coma como separador decimal
    - Signo negativo antes del símbolo $
    - Por defecto 2 decimales; pasar decimals=0 para enteros redondeados.
    """
    try:
        if n is None or (isinstance(n, float) and pd.isna(n)):
            return "—"
        v = float(n)
        signo = "-" if v < 0 else ""
        # Truco de intercambio: formato US primero, luego swap.
        s = f"{abs(v):,.{decimals}f}"             # '77,569.90'
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{signo}${s}"
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
        # es-AR: primer carácter = decimal, segundo = miles -> "1.000.000,00"
        separators=",.",
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
        # Forzar número completo (sin 1k/1M/1G); junto con separators=",." -> "1.000.000"
        tickformat=",",
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
            fecha_devengo = st.date_input("Fecha del movimiento", value=date.today(),
                                          format="DD/MM/YYYY")
        with col2:
            if not cats:
                st.warning(f"Sin categorías de tipo '{tipo}'. Creá una en ⚙️ Configuración.")
                categoria = None
            else:
                categoria = st.selectbox("Categoría", [c["nombre"] for c in cats])

        concepto = st.text_input("Concepto / Nota", placeholder="Ej: Período 05/26")
        monto = st.number_input("Monto total", min_value=0.0, step=1000.0,
                                format="%.2f", value=None, placeholder="0,00")

        col3, col4 = st.columns(2)
        with col3:
            cuotas = st.number_input("Cuotas", min_value=1, max_value=36, value=1, step=1)
        with col4:
            inicio_pago = st.date_input("Inicio pago", value=date.today(),
                                        format="DD/MM/YYYY")

        if cuotas > 1 and monto and monto > 0:
            cuota_mensual = monto / cuotas
            st.info(
                f"📊 **Estado de Resultados**: {fmt_money(monto)} en {fecha_devengo.strftime('%m/%Y')} (devengado).\n\n"
                f"📅 **Flujo de Fondos**: {fmt_money(cuota_mensual)}/mes × {cuotas} desde {inicio_pago.strftime('%m/%Y')} (caja)."
            )

        ok = st.form_submit_button("Guardar movimiento", use_container_width=True)
        if ok:
            if not categoria:
                st.error("Elegí una categoría")
            elif not monto or monto <= 0:
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
    df_view["Fecha"] = df_view["fecha_devengo"].dt.strftime("%d/%m/%Y")
    df_view["Inicio pago"] = df_view["inicio_pago"].dt.strftime("%d/%m/%Y")
    df_view["Monto"] = df_view["monto_total"].apply(fmt_money)
    df_view = df_view[["Fecha", "tipo", "categoria", "concepto",
                       "Monto", "cuotas", "Inicio pago"]]
    df_view.columns = ["Fecha", "Tipo", "Categoría", "Concepto",
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
            fecha_e = st.date_input("Fecha del movimiento",
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
                "Criterio devengado · Agrupado por el mes de la fecha del movimiento.")

    df = df_movimientos(user.id)
    if df.empty:
        st.info("No tenés movimientos cargados todavía.")
        return

    desde_def, hasta_def = rango_fechas_default(df, "fecha_devengo")
    fechas = st.date_input(
        "Rango de fechas",
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
    if df_caja.empty:
        st.info("No hay cuotas que mostrar.")
        return

    # --- Rango de fechas por default (últimos 12 meses) ---
    hasta_def = df_caja["mes_pago"].max().date()
    desde_def = (hasta_def - relativedelta(months=11)).replace(day=1)
    minimo = df_caja["mes_pago"].min().date()
    if desde_def < minimo:
        desde_def = minimo.replace(day=1)

    fechas = st.date_input(
        "Rango de fechas (mes de pago)",
        value=(desde_def, hasta_def),
        format="DD/MM/YYYY",
        key="rango_ff",
    )
    if isinstance(fechas, tuple) and len(fechas) == 2:
        desde, hasta = fechas
    else:
        desde, hasta = desde_def, hasta_def

    # ------------------------------------------------------------------------
    # CÁLCULO DE SALDOS ENCADENADO (sobre TODOS los meses, no solo el rango)
    # ------------------------------------------------------------------------
    pivot_completo = df_caja.pivot_table(
        index="tipo", columns="mes_pago", values="monto_cuota",
        aggfunc="sum", fill_value=0,
    )
    orden = ["Ingreso", "Gasto Fijo", "Gasto Variable", "Ahorro"]
    pivot_completo = pivot_completo.reindex([t for t in orden if t in pivot_completo.index])

    flujo_neto_completo = (
        (pivot_completo.loc["Ingreso"] if "Ingreso" in pivot_completo.index else 0)
        - (pivot_completo.loc["Gasto Fijo"] if "Gasto Fijo" in pivot_completo.index else 0)
        - (pivot_completo.loc["Gasto Variable"] if "Gasto Variable" in pivot_completo.index else 0)
        - (pivot_completo.loc["Ahorro"] if "Ahorro" in pivot_completo.index else 0)
    )

    # Ajustes manuales cargados por el usuario (delta sobre el cálculo automático)
    ajustes_manuales = get_saldos_iniciales_manuales(user.id)

    # Recorremos meses en orden cronológico y encadenamos saldos.
    # Para cada mes:
    #   saldo_automatico = saldo_final del mes anterior (o 0 si es el primero)
    #   ajuste = ajustes_manuales.get(mes, 0)
    #   saldo_inicial = saldo_automatico + ajuste
    #   saldo_final = saldo_inicial + flujo_neto
    meses_todos = list(flujo_neto_completo.index)
    saldo_auto = {}   # {Timestamp -> float}  saldo inicial sin ajuste
    ajuste = {}       # {Timestamp -> float}  delta cargado (0 si no hay)
    saldos_ini = {}   # {Timestamp -> float}  saldo inicial efectivo (auto + ajuste)
    saldos_fin = {}   # {Timestamp -> float}  saldo final del mes

    saldo_anterior = 0.0  # saldo final del mes previo
    for mes_ts in meses_todos:
        mes_d = mes_ts.date().replace(day=1) if hasattr(mes_ts, "date") else mes_ts
        auto = saldo_anterior
        aj = float(ajustes_manuales.get(mes_d, 0.0))
        si = auto + aj
        sf = si + float(flujo_neto_completo.loc[mes_ts])
        saldo_auto[mes_ts] = auto
        ajuste[mes_ts] = aj
        saldos_ini[mes_ts] = si
        saldos_fin[mes_ts] = sf
        saldo_anterior = sf

    # ------------------------------------------------------------------------
    # Filtrar al rango pedido para mostrar
    # ------------------------------------------------------------------------
    meses_rango = [m for m in meses_todos
                   if desde <= (m.date() if hasattr(m, "date") else m) <= hasta]
    if not meses_rango:
        st.info("No hay cuotas en el rango seleccionado.")
        return

    pivot_rango = pivot_completo.loc[:, meses_rango].copy()

    # ------------------------------------------------------------------------
    # Armar tabla final
    # Filas: Saldo inicial → [Ajuste si hay alguno en rango] → tipos → Flujo neto → Saldo final
    # ------------------------------------------------------------------------
    hay_ajustes_en_rango = any(ajuste[m] != 0.0 for m in meses_rango)
    filas_ordenadas = ["Saldo inicial"]
    if hay_ajustes_en_rango:
        filas_ordenadas.append("Ajuste")
    filas_ordenadas += list(pivot_rango.index) + ["Flujo neto", "Saldo final"]

    pivot_final = pd.DataFrame(index=filas_ordenadas, columns=pivot_rango.columns, dtype=float)

    for m in meses_rango:
        pivot_final.loc["Saldo inicial", m] = saldos_ini[m]
        if hay_ajustes_en_rango:
            pivot_final.loc["Ajuste", m] = ajuste[m]
        for tipo in pivot_rango.index:
            pivot_final.loc[tipo, m] = pivot_rango.loc[tipo, m]
        pivot_final.loc["Flujo neto", m] = float(flujo_neto_completo.loc[m])
        pivot_final.loc["Saldo final", m] = saldos_fin[m]

    pivot_final.columns = [c.strftime("%m/%Y") for c in pivot_final.columns]
    pivot_fmt = pivot_final.copy().map(fmt_money)
    pivot_fmt.index.name = "Concepto"
    st.dataframe(pivot_fmt, use_container_width=True)

    # Aviso si el primer mes con datos no tiene ajuste cargado (arranca en $0)
    primer_mes_global = meses_todos[0]
    primer_mes_global_d = (primer_mes_global.date().replace(day=1)
                           if hasattr(primer_mes_global, "date") else primer_mes_global)
    if primer_mes_global_d not in ajustes_manuales:
        primer_lbl = primer_mes_global.strftime("%m/%Y")
        st.caption(
            f"⚠ El primer mes con movimientos ({primer_lbl}) arranca con saldo inicial $0,00. "
            f"Si tenías plata antes de empezar a usar la app, cargá el saldo de partida como un "
            f"ajuste manual abajo (el ajuste para el primer mes funciona como saldo absoluto)."
        )

    # ------------------------------------------------------------------------
    # AJUSTAR saldo inicial de un mes (widgets sueltos para preview en vivo)
    # ------------------------------------------------------------------------
    st.divider()
    st.markdown("##### ✏ Ajustar saldo inicial")
    st.caption(
        "El ajuste se SUMA al saldo inicial calculado automáticamente. "
        "Sirve para reconciliar discrepancias (si el saldo real es distinto al calculado) "
        "y se preserva en los meses siguientes. Para el primer mes con movimientos, "
        "el ajuste funciona como saldo de partida absoluto. Cargá 0 y guardá para borrarlo."
    )

    meses_opts_lbl = [m.strftime("%m/%Y") for m in meses_rango]
    meses_opts_ts = list(meses_rango)

    col_mes, col_aj = st.columns([1, 2])
    with col_mes:
        mes_idx = st.selectbox(
            "Mes",
            options=list(range(len(meses_opts_lbl))),
            format_func=lambda i: meses_opts_lbl[i],
            index=0,
            key="aj_mes_idx",
        )
    mes_ts_sel = meses_opts_ts[mes_idx]
    mes_lbl_sel = meses_opts_lbl[mes_idx]
    auto_sel = float(saldo_auto[mes_ts_sel])
    ajuste_actual = float(ajuste[mes_ts_sel])

    with col_aj:
        # Key dinámica por mes: al cambiar el selector, el input se "resetea" al ajuste de ese mes.
        ajuste_input = st.number_input(
            "Tu ajuste manual (positivo o negativo)",
            value=ajuste_actual,
            step=10000.0,
            format="%.2f",
            key=f"aj_input_{mes_ts_sel.isoformat()}",
        )

    ajuste_efectivo = float(ajuste_input or 0.0)
    saldo_efectivo = auto_sel + ajuste_efectivo

    # Preview en vivo: el usuario ve qué pasa antes de guardar
    st.markdown(
        f"<div style='background: var(--bg-soft); border: 1px solid var(--border); "
        f"border-radius: 8px; padding: 12px 16px; margin: 8px 0;'>"
        f"<div style='color: var(--text-muted); font-size: 0.85rem;'>Vista previa para {mes_lbl_sel}:</div>"
        f"<div style='font-family: \"Poppins\", sans-serif; color: var(--navy); margin-top: 4px;'>"
        f"{fmt_money(auto_sel)} <span style='color: var(--text-muted);'>(automático)</span> "
        f"+ {fmt_money(ajuste_efectivo)} <span style='color: var(--text-muted);'>(ajuste)</span> = "
        f"<strong>{fmt_money(saldo_efectivo)}</strong> "
        f"<span style='color: var(--text-muted);'>(saldo inicial efectivo)</span>"
        f"</div></div>",
        unsafe_allow_html=True,
    )

    if st.button("💾 Guardar ajuste", use_container_width=False, key="btn_guardar_aj"):
        try:
            if ajuste_efectivo == 0.0:
                # Si el usuario puso 0, borramos el registro (si existía)
                if mes_ts_sel.date().replace(day=1) in ajustes_manuales:
                    delete_saldo_inicial(user.id, mes_ts_sel.date())
                    st.success(f"✅ Ajuste de {mes_lbl_sel} eliminado. Vuelve al cálculo automático.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.info("No hay nada que guardar (ajuste = 0 y no había registro previo).")
            else:
                upsert_saldo_inicial(user.id, mes_ts_sel.date(), ajuste_efectivo)
                st.success(
                    f"✅ Ajuste de {fmt_money(ajuste_efectivo)} guardado para {mes_lbl_sel}. "
                    f"Saldo inicial efectivo: {fmt_money(saldo_efectivo)}."
                )
                st.cache_data.clear()
                st.rerun()
        except Exception as e:
            st.error(f"Error al guardar: {e}")

    # ------------------------------------------------------------------------
    # Detalle de cuotas por mes (igual que antes)
    # ------------------------------------------------------------------------
    st.divider()
    st.markdown("##### Detalle de cuotas por mes")
    df_caja_rango = df_caja[
        (df_caja["mes_pago"].dt.date >= desde) &
        (df_caja["mes_pago"].dt.date <= hasta)
    ].copy()
    mes_sel = st.selectbox(
        "Seleccionar mes",
        options=sorted(df_caja_rango["mes_pago"].unique(), reverse=True),
        format_func=lambda d: pd.Timestamp(d).strftime("%m/%Y"),
        key="flujo_mes_detalle",
    )
    df_mes = df_caja_rango[df_caja_rango["mes_pago"] == mes_sel].copy()
    df_mes["Cuota"] = df_mes.apply(lambda r: f"{r['n_cuota']}/{r['total_cuotas']}", axis=1)
    df_mes["Monto"] = df_mes["monto_cuota"].apply(fmt_money)
    df_mes = df_mes[["tipo", "categoria", "concepto", "Cuota", "Monto"]]
    df_mes.columns = ["Tipo", "Categoría", "Concepto", "Cuota", "Monto"]
    st.dataframe(df_mes, hide_index=True, use_container_width=True)

    excel = df_to_excel_bytes({
        "Flujo de Fondos": pivot_final.reset_index(),
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
