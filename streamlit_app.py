"""
Finanzas WL - App de finanzas personales
Conectada a Supabase con autenticación multi-usuario.

Versión 4.3 — Auth parte 2: Google, sesión persistente y sidebar mobile
- Botón "Continuar con Google" en el login (Supabase OAuth, flujo implícito:
  un JS mueve los tokens del fragmento #... a query params y la app inicia
  la sesión). Requiere el provider Google configurado en Supabase.
- Sesión persistente: el refresh token se guarda en una cookie (30 días).
  Al cerrar el navegador y volver, la app restaura la sesión sola. Nuevo
  requirement: extra-streamlit-components (actualizar requirements.txt).
- Mobile: al elegir una pestaña del menú, la sidebar se cierra sola
  (workaround con JS sobre selectores internos de Streamlit; best effort).

Versión 4.2 — Auth confiable + pulido de Inicio y login
- Recuperación de contraseña DENTRO de la app: "¿Olvidaste tu contraseña?"
  en el login + pantalla para crear la nueva (el mail debe configurarse con
  token_hash, ver instrucciones). Ya no se pierden cuentas.
- Nuevo .streamlit/config.toml: tema claro forzado (los celulares en modo
  oscuro ya no rompen la visual), color primario navy (adiós flash rojo al
  cargar) y toolbar minimal.
- Logo nuevo de alta resolución (logo_completo_transparente.png), centrado.
- Inicio reordenado: KPIs → Disponible real → Ritmo de gasto variable
  (nuevo: gastado a hoy, promedio diario y proyectado a fin de mes) →
  Composición por categoría (más grande) → Evolución mensual. Se eliminó
  el gráfico de evolución del saldo.
- Colores semánticos: ingresos y saldos en navy; naranja solo para gastos;
  verde/rojo reservados para resultado positivo/negativo.
- Movimientos: filtro por categoría; "None" ya no aparece en las tablas.
- Placeholder de email: "Escribe tu mail". Link a wlhnos.vercel.app en el
  pie del login.

Versión 4.1 — Pulido visual y defaults
- Ocultos los anchors ("clips") que Streamlit agrega a los títulos.
- Removidos los emojis de títulos, menú y botones para un look profesional.
- Tarjetas KPI parejas: misma altura mínima, números con dígitos tabulares y
  tamaño que se achica solo si el monto es largo (ya no se cortan).
- Ajustes responsive para mobile (tarjetas y tipografía).
- Todos los selectores de mes (Inicio, detalle del ER, detalle del FF y
  conciliación) arrancan por defecto en el mes en curso, no en el último mes
  con datos (que podía ser futuro por cuotas proyectadas).

Versión 4.0 — Tanda 2C: Reestructura de pantallas
- Menú reducido a 5: Inicio · Cargar movimiento · Movimientos · Reportes ·
  Configuración. Inicio absorbe el Dashboard; Reportes une Estado de
  Resultados y Flujo de Fondos con un selector devengado/caja.
- "Resultado" ya no resta el Ahorro: Resultado = Ingresos − Gastos. El ER
  muestra además "Resultado después de ahorro". El saldo (caja) sigue
  descontando el ahorro porque ese dinero sale de la cuenta.
- "Ajustar saldo inicial" (delta aditivo, críptico) reemplazado por
  "Conciliar saldo": el usuario informa su saldo real a fin de mes y la app
  calcula y guarda el ajuste sola.

Versión 3.9 — Tanda 2B: Tipo desde la categoría + Copiar fijos del mes anterior
- Cargar/Editar: el selector de tipo queda en Ingreso / Gasto / Ahorro. Para
  Gasto, la categoría ya trae su clasificación (se muestra "· fijo" o
  "· variable") y el movimiento se guarda con el tipo correcto. Los reportes
  no cambian. Sin migración: categorias.tipo ya existía.
- Nuevo en Cargar movimiento: expander "Copiar fijos e ingresos del mes
  anterior" — grilla editable (montos y conceptos) con tilde por fila; los
  que parecen ya cargados este mes vienen destildados. Carga en lote.

Versión 3.8 — Tanda 2A: Carga simplificada, filtros y disponible real
- Cargar movimiento: una sola fecha por defecto. Toggle "Pago en cuotas o en
  otra fecha": si está apagado, cuotas=1 e inicio de pago = fecha del
  movimiento (la carga típica baja de 7 campos a 4).
- Ver movimientos: filtros por mes y por tipo; los totales y la tabla
  respetan el filtro.
- Dashboard: nueva sección "Disponible real" — saldo a fin del mes en curso,
  comprometido en cuotas futuras ya cargadas, y el neto disponible.
- Rendimiento: get_movimientos con caché (ttl 30s); el conteo de movimientos
  por categoría en Configuración pasa de ~28 consultas a 1.

Versión 3.7 — Fixes críticos pre-rollout (sesión por usuario)
- FIX CRÍTICO: el cliente Supabase ya no usa @st.cache_resource (era compartido
  entre TODOS los usuarios conectados al mismo tiempo: el login de un usuario
  pisaba la sesión de los demás). Ahora los tokens viven en st.session_state
  (individual por navegador) y la sesión se rehidrata en cada ejecución.
- Esto también arregla el vencimiento del token (~1 hora): set_session
  refresca automáticamente y la app ya no "se vacía" en silencio.
- do_signout ya no limpia cachés globales (no le rompe la conexión al resto).
- FIX: en Ver movimientos, el selector "Tipo" del form de edición salió del
  st.form (los widgets dentro de un form no refrescan): al cambiar el tipo
  ahora se actualizan las categorías y ya no se puede guardar un movimiento
  con categoría de otro tipo.

Versión 3.6 — Ajustes finos sobre Tanda 3
- "plata" → "dinero" en toda la app
- Estado de Resultados: removidos los gráficos de evolución mensual y torta
  por categoría (ahora viven en Dashboard, una sola fuente de verdad)
- Inicio: "Saldo actual" usa el mes en curso (no el último con datos), para
  no mostrar saldos proyectados de meses futuros como si fueran "actuales"
- Dashboard: gráfico de torta rediseñado con filtros propios (selector de mes
  con opción "Todos" y selector de tipo: Todos / Gasto Fijo / Gasto Variable / Ahorro)

Versión 3.5 — Tanda 3: Pestañas Inicio y Dashboard
- Pestaña "🏠 Inicio" como default al loguearse: bienvenida, resumen rápido,
  guía de pestañas y aclaración corta de devengado vs caja.
- Pestaña "📊 Dashboard" con KPIs del mes seleccionado, evolución del saldo,
  evolución mensual con selector de serie (resuelve el problema de escala
  cuando se mostraban Ingresos vs Gastos en un mismo gráfico) y gastos por
  categoría del mes.
- Refactor: cálculo de saldos encadenados extraído a calcular_estado_flujo()
  para que page_flujo y page_dashboard compartan la misma fuente de verdad.

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
from datetime import date, datetime, timedelta
import hashlib
import secrets as _secrets
import httpx
from urllib.parse import quote
import extra_streamlit_components as stx
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
APP_URL = "https://finanzas-personales-app.streamlit.app"

NAVY = "#102250"        # Principal corporativo
CYAN = "#1595BC"        # Secundario corporativo
GREEN = "#1C913D"       # Apoyo (positivo)
GREY = "#6C6D6D"        # Apoyo (neutro)
ORANGE = "#EA5E2D"      # Apoyo (alerta)
RED = "#C0392B"         # Solo para resultados negativos
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

LOGO_PATH = "logo_completo_transparente.png"
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
    --red: {RED};
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
    min-height: 86px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    container-type: inline-size;
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
    font-size: clamp(0.95rem, 9cqw, 1.45rem);
    font-weight: 600;
    color: var(--navy);
    line-height: 1.1;
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
}}

/* Ocultar los anchors ("clips") que Streamlit agrega a los títulos */
[data-testid="stHeaderActionElements"] {{ display: none !important; }}
.stMarkdown h1 a, .stMarkdown h2 a, .stMarkdown h3 a,
.stMarkdown h4 a, .stMarkdown h5 a, .stMarkdown h6 a {{ display: none !important; }}

/* Mobile */
@media (max-width: 640px) {{
    .block-container {{ padding-left: 0.9rem !important; padding-right: 0.9rem !important; }}
    .metric-card {{ min-height: 72px; padding: 12px 14px; }}
    .page-header .page-title {{ font-size: 1.4rem !important; }}
}}
.metric-card.metric-green .metric-value {{ color: var(--green); }}
.metric-card.metric-orange .metric-value {{ color: var(--orange); }}
.metric-card.metric-cyan .metric-value {{ color: var(--cyan); }}
.metric-card.metric-red .metric-value {{ color: var(--red); }}

/* Toolbar de Streamlit (Share / GitHub / lápiz) oculta */
[data-testid="stToolbar"] {{ display: none !important; }}

.google-btn {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    width: 100%;
    padding: 0.55rem 1rem;
    background: white;
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--navy) !important;
    font-weight: 600;
    font-size: 0.95rem;
    text-decoration: none !important;
    box-shadow: 0 1px 2px rgba(16, 34, 80, 0.05);
    transition: box-shadow 0.15s ease;
}}
.google-btn:hover {{
    box-shadow: 0 3px 8px rgba(16, 34, 80, 0.12);
}}

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
def init_supabase() -> Client:
    # SIN @st.cache_resource: cache_resource es GLOBAL al servidor (compartido
    # entre todos los usuarios conectados). El cliente se crea por ejecución y
    # la sesión de cada usuario se rehidrata desde st.session_state, que sí es
    # individual por navegador.
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

sb = init_supabase()

# ============================================================================
# ESTADO DE SESIÓN
# ============================================================================
if "user" not in st.session_state:
    st.session_state.user = None
if "sb_tokens" not in st.session_state:
    st.session_state.sb_tokens = None

# ----------------------------------------------------------------------------
# COOKIE DE SESIÓN PERSISTENTE
# Guarda el refresh token 30 días para que cerrar el navegador no desloguee.
# ----------------------------------------------------------------------------
cookie_manager = stx.CookieManager(key="wl_cookies")

def _guardar_cookie_sesion(refresh_token: str, key: str):
    try:
        cookie_manager.set(
            "wl_rt", refresh_token,
            expires_at=datetime.now() + timedelta(days=30),
            key=key,
        )
    except Exception:
        pass

# Si no hay sesión en esta pestaña pero hay cookie, restaurar.
if not st.session_state.sb_tokens and not st.session_state.user:
    _rt_cookie = None
    try:
        _rt_cookie = cookie_manager.get("wl_rt")
    except Exception:
        pass
    if _rt_cookie:
        try:
            r = sb.auth.refresh_session(_rt_cookie)
            if r and r.session:
                st.session_state.sb_tokens = {
                    "access_token": r.session.access_token,
                    "refresh_token": r.session.refresh_token,
                }
                st.session_state.user = r.user
                # Supabase rota el refresh token: guardar el nuevo.
                _guardar_cookie_sesion(r.session.refresh_token, "ck_restore")
        except Exception:
            try:
                cookie_manager.delete("wl_rt", key="ck_del_invalid")
            except Exception:
                pass

# Rehidratar la sesión de ESTE usuario en cada ejecución del script.
# Si el access token venció, set_session lo refresca solo con el refresh token;
# en ese caso guardamos los tokens nuevos.
if st.session_state.sb_tokens:
    try:
        sb.auth.set_session(
            st.session_state.sb_tokens["access_token"],
            st.session_state.sb_tokens["refresh_token"],
        )
        s = sb.auth.get_session()
        if s:
            if s.refresh_token != st.session_state.sb_tokens.get("refresh_token"):
                # Hubo refresh (rotación): actualizar también la cookie.
                _guardar_cookie_sesion(s.refresh_token, "ck_rotate")
            st.session_state.sb_tokens = {
                "access_token": s.access_token,
                "refresh_token": s.refresh_token,
            }
    except Exception:
        # Token inválido o vencido sin posibilidad de refresh: volver al login.
        st.session_state.user = None
        st.session_state.sb_tokens = None

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
        if r.user and r.session:
            # Guardar los tokens en la sesión de ESTE navegador.
            st.session_state.sb_tokens = {
                "access_token": r.session.access_token,
                "refresh_token": r.session.refresh_token,
            }
            _guardar_cookie_sesion(r.session.refresh_token, "ck_login")
            # Si es la primera vez que entra (todavía no tiene categorías),
            # le sembramos el set por defecto.
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
    try:
        cookie_manager.delete("wl_rt", key="ck_del_logout")
    except Exception:
        pass
    st.session_state.user = None
    st.session_state.sb_tokens = None
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

@st.cache_data(ttl=30, show_spinner=False)
def conteo_movs_por_categoria(user_id: str, tipo: str) -> dict:
    """Una sola consulta: {nombre_categoria: cantidad de movimientos} para un tipo."""
    res = (
        sb.table("movimientos").select("categoria")
        .eq("user_id", user_id).eq("tipo", tipo).execute().data
    )
    out = {}
    for r in res:
        out[r["categoria"]] = out.get(r["categoria"], 0) + 1
    return out

# ============================================================================
# ACCESO A DATOS: MOVIMIENTOS
# ============================================================================
@st.cache_data(ttl=30, show_spinner=False)
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
    df["concepto"] = df["concepto"].fillna("")
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

def _default_mes_idx(meses_ts):
    """Índice del mes en curso en la lista; si no está, el mes más reciente
    no futuro; si todos son futuros, el primero. Evita que los selectores
    arranquen en meses proyectados por cuotas."""
    hoy = date.today()
    mes_act = pd.Timestamp(hoy.year, hoy.month, 1)
    candidatos = [i for i, m in enumerate(meses_ts) if pd.Timestamp(m) <= mes_act]
    if not candidatos:
        return 0
    return max(candidatos, key=lambda i: pd.Timestamp(meses_ts[i]))

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
# CÁLCULO DE ESTADO DE FLUJO (criterio caja)
# ============================================================================
def calcular_estado_flujo(user_id: str):
    """
    Calcula todo el estado de Flujo de Fondos del usuario en criterio caja.
    Se usa tanto en page_flujo (para la tabla detallada) como en page_dashboard
    (para los KPIs y gráficos).

    Devuelve None si el usuario no tiene movimientos. Si tiene, retorna un dict:
        {
            "df_caja":          DataFrame de cuotas expandidas
            "pivot_completo":   DataFrame pivot indexado por tipo, columnas = meses
            "flujo_neto":       Series indexada por mes con el flujo neto
            "meses_todos":      lista de Timestamps de meses con datos (ordenados)
            "ajustes_manuales": dict {date(yyyy,mm,01) -> ajuste_float}
            "saldo_auto":       dict {mes_ts -> saldo inicial sin ajuste}
            "ajuste":           dict {mes_ts -> ajuste aplicado al mes}
            "saldos_ini":       dict {mes_ts -> saldo inicial efectivo (auto + ajuste)}
            "saldos_fin":       dict {mes_ts -> saldo final (saldos_ini + flujo)}
        }
    """
    df = df_movimientos(user_id)
    if df.empty:
        return None
    df_caja = expandir_a_caja(df)
    if df_caja.empty:
        return None

    pivot_completo = df_caja.pivot_table(
        index="tipo", columns="mes_pago", values="monto_cuota",
        aggfunc="sum", fill_value=0,
    )
    orden = ["Ingreso", "Gasto Fijo", "Gasto Variable", "Ahorro"]
    pivot_completo = pivot_completo.reindex([t for t in orden if t in pivot_completo.index])

    flujo_neto = (
        (pivot_completo.loc["Ingreso"] if "Ingreso" in pivot_completo.index else 0)
        - (pivot_completo.loc["Gasto Fijo"] if "Gasto Fijo" in pivot_completo.index else 0)
        - (pivot_completo.loc["Gasto Variable"] if "Gasto Variable" in pivot_completo.index else 0)
        - (pivot_completo.loc["Ahorro"] if "Ahorro" in pivot_completo.index else 0)
    )

    ajustes_manuales = get_saldos_iniciales_manuales(user_id)

    meses_todos = list(flujo_neto.index)
    saldo_auto, ajuste_map, saldos_ini, saldos_fin = {}, {}, {}, {}
    saldo_anterior = 0.0
    for mes_ts in meses_todos:
        mes_d = mes_ts.date().replace(day=1) if hasattr(mes_ts, "date") else mes_ts
        auto = saldo_anterior
        aj = float(ajustes_manuales.get(mes_d, 0.0))
        si = auto + aj
        sf = si + float(flujo_neto.loc[mes_ts])
        saldo_auto[mes_ts] = auto
        ajuste_map[mes_ts] = aj
        saldos_ini[mes_ts] = si
        saldos_fin[mes_ts] = sf
        saldo_anterior = sf

    return {
        "df_caja": df_caja,
        "pivot_completo": pivot_completo,
        "flujo_neto": flujo_neto,
        "meses_todos": meses_todos,
        "ajustes_manuales": ajustes_manuales,
        "saldo_auto": saldo_auto,
        "ajuste": ajuste_map,
        "saldos_ini": saldos_ini,
        "saldos_fin": saldos_fin,
    }

# ============================================================================
# UI HELPERS
# ============================================================================
def render_logo(ancho_px: int = 160):
    b64 = load_logo_b64(LOGO_PATH)
    if b64:
        st.markdown(
            f"<div style='text-align:center;'>"
            f"<img src='data:image/png;base64,{b64}' width='{ancho_px}' "
            f"alt='WL HNOS &amp; ASOC'/></div>",
            unsafe_allow_html=True,
        )
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
_GOOGLE_SVG = (
    "<svg width='18' height='18' viewBox='0 0 48 48'>"
    "<path fill='#FFC107' d='M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3l5.7-5.7C34.5 6.1 29.5 4 24 4 13 4 4 13 4 24s9 20 20 20 20-9 20-20c0-1.2-.1-2.3-.4-3.5z'/>"
    "<path fill='#FF3D00' d='M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.9 1.2 8 3l5.7-5.7C34.5 6.1 29.5 4 24 4 16.3 4 9.7 8.3 6.3 14.7z'/>"
    "<path fill='#4CAF50' d='M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z'/>"
    "<path fill='#1976D2' d='M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.3 4.3-4.1 5.6l6.2 5.2C36.9 40.4 44 35 44 24c0-1.2-.1-2.3-.4-3.5z'/>"
    "</svg>"
)

def _pkce_par():
    """Genera (verifier, challenge) PKCE; el verifier persiste en la sesión."""
    if not st.session_state.get("pkce_verifier"):
        st.session_state.pkce_verifier = _secrets.token_urlsafe(64)
    v = st.session_state.pkce_verifier
    ch = base64.urlsafe_b64encode(hashlib.sha256(v.encode()).digest()).decode().rstrip("=")
    return v, ch

def page_login():
    _oe = st.session_state.pop("oauth_error", None)
    if _oe:
        st.error(f"No se pudo completar el ingreso con Google: {_oe}")
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
            email = st.text_input("Email", placeholder="Escribe tu mail")
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
            email = st.text_input("Email", key="su_email", placeholder="Escribe tu mail")
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
                        st.success("Cuenta creada. Ya podés entrar desde la pestaña "
                                   "\"Iniciar sesión\" con tu mail y contraseña.")

    _verifier, _challenge = _pkce_par()
    # El verifier viaja en una cookie para que la pestaña que vuelve de Google
    # (que es una sesión nueva de Streamlit) pueda completar el intercambio.
    try:
        cookie_manager.set("wl_pkce", _verifier,
                           expires_at=datetime.now() + timedelta(minutes=15),
                           key="ck_pkce")
    except Exception:
        pass
    _auth_url = (f"{st.secrets['SUPABASE_URL'].strip().rstrip('/')}/auth/v1/authorize"
                 f"?provider=google&redirect_to={quote(APP_URL, safe='')}"
                 f"&code_challenge={_challenge}&code_challenge_method=s256")
    st.markdown(
        f"<a href='{_auth_url}' target='_blank' rel='noopener' class='google-btn'>"
        f"{_GOOGLE_SVG} Continuar con Google</a>",
        unsafe_allow_html=True,
    )
    st.write("")

    with st.expander("¿Olvidaste tu contraseña?"):
        with st.form("reset_pw"):
            email_r = st.text_input("Email", key="rp_email", placeholder="Escribe tu mail")
            ok_r = st.form_submit_button("Enviarme el link de recuperación",
                                         use_container_width=True)
            if ok_r:
                if not email_r or "@" not in email_r:
                    st.error("Escribí tu mail")
                else:
                    try:
                        sb.auth.reset_password_for_email(email_r)
                    except Exception:
                        pass
                    # Mismo mensaje exista o no la cuenta (no revelar emails registrados)
                    st.success("Si esa cuenta existe, te enviamos un mail con el link "
                               "para crear una nueva contraseña. Revisá también spam.")

    st.markdown(
        "<div class='login-footer'>WL HNOS &amp; ASOC · Catamarca · "
        "<a href='https://wlhnos.vercel.app/' target='_blank' "
        "style='color: var(--cyan); text-decoration: none;'>wlhnos.vercel.app</a></div>",
        unsafe_allow_html=True,
    )

# ============================================================================
# PANTALLA: NUEVA CONTRASEÑA (llega desde el link del mail de recuperación)
# ============================================================================
def page_nueva_password():
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        render_logo(ancho_px=150)
        st.markdown(
            "<div style='text-align:center; margin-top:8px;'>"
            "<h1 style='margin-bottom:4px;'>Crear nueva contraseña</h1></div>",
            unsafe_allow_html=True,
        )
        with st.form("nueva_pw"):
            p1 = st.text_input("Nueva contraseña", type="password",
                               help="Mínimo 6 caracteres")
            p2 = st.text_input("Repetir contraseña", type="password")
            ok = st.form_submit_button("Guardar y entrar", use_container_width=True)
        if ok:
            if len(p1) < 6:
                st.error("Mínimo 6 caracteres")
            elif p1 != p2:
                st.error("Las contraseñas no coinciden")
            else:
                try:
                    r = sb.auth.verify_otp({
                        "token_hash": st.session_state.recovery_token_hash,
                        "type": "recovery",
                    })
                    if r and r.session:
                        sb.auth.update_user({"password": p1})
                        s = sb.auth.get_session()
                        tok = s or r.session
                        st.session_state.sb_tokens = {
                            "access_token": tok.access_token,
                            "refresh_token": tok.refresh_token,
                        }
                        st.session_state.user = r.user
                        st.session_state.recovery_token_hash = None
                        st.rerun()
                    else:
                        st.error("El link no es válido. Pedí uno nuevo desde el login.")
                except Exception:
                    st.session_state.recovery_token_hash = None
                    st.error("El link venció o ya fue usado. Volvé al login y pedí "
                             "uno nuevo desde la opción de contraseña olvidada.")
        if st.button("Volver al inicio de sesión", use_container_width=True):
            st.session_state.recovery_token_hash = None
            st.rerun()

# ============================================================================
# PANTALLA: CARGAR MOVIMIENTO
# ============================================================================
def _opciones_categorias(user_id, grupo):
    """
    {label: (nombre_categoria, tipo_db)} para el grupo elegido.
    grupo "Gasto" une Gasto Fijo + Gasto Variable; la categoría elegida
    determina el tipo que se guarda (el usuario ya no clasifica a mano).
    """
    if grupo == "Gasto":
        out = {}
        for tipo_db, sufijo in [("Gasto Fijo", "fijo"), ("Gasto Variable", "variable")]:
            for c in get_categorias(user_id, tipo_db):
                out[f"{c['nombre']} · {sufijo}"] = (c["nombre"], tipo_db)
        return dict(sorted(out.items()))
    return {c["nombre"]: (c["nombre"], grupo) for c in get_categorias(user_id, grupo)}

def page_cargar(user):
    page_header("Nuevo movimiento",
                "Cargá ingresos, gastos o ahorro con criterio devengado y caja.")

    grupo = st.selectbox(
        "Tipo",
        ["Ingreso", "Gasto", "Ahorro"],
        index=1,
        key="tipo_select",
    )
    opciones_cat = _opciones_categorias(user.id, grupo)

    # Fuera del form para que muestre/oculte los campos de cuotas al instante.
    en_cuotas = st.toggle(
        "Pago en cuotas o en otra fecha",
        value=False,
        key="cargar_en_cuotas",
        help="Activalo solo si el pago no es el mismo día del movimiento "
             "(cuotas, tarjeta, pago diferido).",
    )

    with st.form("nuevo_mov", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha_devengo = st.date_input("Fecha del movimiento", value=date.today(),
                                          format="DD/MM/YYYY")
        with col2:
            if not opciones_cat:
                st.warning(f"Sin categorías de tipo '{grupo}'. Creá una en Configuración.")
                cat_lbl = None
            else:
                cat_lbl = st.selectbox("Categoría", list(opciones_cat.keys()))

        concepto = st.text_input("Concepto / Nota", placeholder="Ej: Período 05/26")
        monto = st.number_input("Monto total", min_value=0.0, step=1000.0,
                                format="%.2f", value=None, placeholder="0,00")

        if en_cuotas:
            col3, col4 = st.columns(2)
            with col3:
                cuotas = st.number_input("Cuotas", min_value=1, max_value=36, value=1, step=1)
            with col4:
                inicio_pago = st.date_input("Inicio pago (primera cuota)", value=date.today(),
                                            format="DD/MM/YYYY")
            st.caption(
                "El movimiento completo impacta en el Estado de Resultados en su fecha "
                "(devengado); las cuotas se reparten en el Flujo de Fondos desde el inicio "
                "de pago (caja)."
            )
        else:
            cuotas = 1
            inicio_pago = None  # se usa la fecha del movimiento

        ok = st.form_submit_button("Guardar movimiento", use_container_width=True)
        if ok:
            if not cat_lbl:
                st.error("Elegí una categoría")
            elif not monto or monto <= 0:
                st.error("El monto debe ser mayor a cero")
            else:
                try:
                    categoria, tipo = opciones_cat[cat_lbl]
                    inicio_efectivo = inicio_pago if en_cuotas else fecha_devengo
                    insert_movimiento(user.id, fecha_devengo, tipo, categoria, concepto,
                                      monto, cuotas, inicio_efectivo)
                    st.success(f"{tipo} de {fmt_money(monto)} guardado")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

    st.divider()
    with st.expander("Copiar fijos e ingresos del mes anterior"):
        if st.session_state.pop("flash_copia", None):
            st.success("Movimientos copiados")
        hoy = date.today()
        per_dest = pd.Period(date(hoy.year, hoy.month, 1), "M")
        per_orig = per_dest - 1
        df_all = df_movimientos(user.id)
        base = pd.DataFrame()
        if not df_all.empty:
            base = df_all[
                df_all["tipo"].isin(["Gasto Fijo", "Ingreso"])
                & (df_all["fecha_devengo"].dt.to_period("M") == per_orig)
                & (df_all["cuotas"] == 1)
            ].copy()
        if base.empty:
            st.caption(
                f"No hay gastos fijos ni ingresos (sin cuotas) cargados en "
                f"{per_orig.strftime('%m/%Y')} para copiar."
            )
        else:
            ya = df_all[df_all["fecha_devengo"].dt.to_period("M") == per_dest]
            claves_ya = set(zip(ya["tipo"], ya["categoria"], ya["concepto"].fillna("")))
            base = base.sort_values(["tipo", "categoria"]).reset_index(drop=True)
            base["_clave"] = list(zip(base["tipo"], base["categoria"],
                                      base["concepto"].fillna("")))
            base["Cargar"] = ~base["_clave"].isin(claves_ya)

            ed = pd.DataFrame({
                "Cargar": base["Cargar"],
                "Tipo": base["tipo"],
                "Categoría": base["categoria"],
                "Concepto": base["concepto"].fillna(""),
                "Monto": base["monto_total"],
                "Fecha nueva": (base["fecha_devengo"] + pd.DateOffset(months=1))
                                .dt.strftime("%d/%m/%Y"),
            })
            st.caption(
                f"Gastos fijos e ingresos de **{per_orig.strftime('%m/%Y')}** → "
                f"**{per_dest.strftime('%m/%Y')}**. Editá montos (aumentos) y conceptos, "
                f"y destildá lo que no corresponda. Los que parecen ya cargados este mes "
                f"vienen destildados."
            )
            ed_out = st.data_editor(
                ed, hide_index=True, use_container_width=True,
                disabled=["Tipo", "Categoría", "Fecha nueva"],
                key="copiar_fijos_editor",
            )
            n_sel = int(ed_out["Cargar"].sum())
            if st.button(f"Cargar {n_sel} movimiento(s) en {per_dest.strftime('%m/%Y')}",
                         disabled=n_sel == 0, key="btn_copiar_fijos"):
                fechas_nuevas = (base["fecha_devengo"] + pd.DateOffset(months=1)).dt.date.tolist()
                errores = 0
                for (_, row), fnueva in zip(ed_out.iterrows(), fechas_nuevas):
                    if not row["Cargar"] or not row["Monto"] or float(row["Monto"]) <= 0:
                        continue
                    try:
                        insert_movimiento(user.id, fnueva, row["Tipo"], row["Categoría"],
                                          row["Concepto"], float(row["Monto"]), 1, fnueva)
                    except Exception:
                        errores += 1
                st.cache_data.clear()
                if errores:
                    st.warning(f"Hubo {errores} error(es) al copiar; revisá la lista.")
                else:
                    st.session_state["flash_copia"] = True
                st.rerun()

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

    # --- Filtros ---
    meses_disp = sorted(df["fecha_devengo"].dt.strftime("%m/%Y").unique(),
                        key=lambda s: (s[3:], s[:2]), reverse=True)
    cats_disp = sorted(df["categoria"].unique())
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        mes_f = st.selectbox("Mes", ["Todos"] + meses_disp, key="ver_mes_f")
    with col_f2:
        tipo_f = st.selectbox("Tipo", ["Todos", "Ingreso", "Gasto Fijo",
                                       "Gasto Variable", "Ahorro"], key="ver_tipo_f")
    with col_f3:
        cat_f = st.selectbox("Categoría", ["Todas"] + cats_disp, key="ver_cat_f")
    if mes_f != "Todos":
        df = df[df["fecha_devengo"].dt.strftime("%m/%Y") == mes_f]
    if tipo_f != "Todos":
        df = df[df["tipo"] == tipo_f]
    if cat_f != "Todas":
        df = df[df["categoria"] == cat_f]
    if df.empty:
        st.info("No hay movimientos con esos filtros.")
        return

    total_ing = df.loc[df["tipo"] == "Ingreso", "monto_total"].sum()
    total_gas = df.loc[df["tipo"].isin(["Gasto Fijo", "Gasto Variable"]), "monto_total"].sum()
    total_aho = df.loc[df["tipo"] == "Ahorro", "monto_total"].sum()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(metric_card("Ingresos", fmt_money(total_ing)),
                    unsafe_allow_html=True)
    with col2:
        st.markdown(metric_card("Gastos", fmt_money(total_gas), "orange"),
                    unsafe_allow_html=True)
    with col3:
        st.markdown(metric_card("Ahorro", fmt_money(total_aho), "cyan"),
                    unsafe_allow_html=True)

    st.write("")

    df_view = df.copy()
    df_view["concepto"] = df_view["concepto"].fillna("")
    df_view["Fecha"] = df_view["fecha_devengo"].dt.strftime("%d/%m/%Y")
    df_view["Inicio pago"] = df_view["inicio_pago"].dt.strftime("%d/%m/%Y")
    df_view["Monto"] = df_view["monto_total"].apply(fmt_money)
    df_view = df_view[["Fecha", "tipo", "categoria", "concepto",
                       "Monto", "cuotas", "Inicio pago"]]
    df_view.columns = ["Fecha", "Tipo", "Categoría", "Concepto",
                       "Monto", "Cuotas", "Inicio pago"]
    st.dataframe(df_view, hide_index=True, use_container_width=True)

    st.divider()
    st.markdown("##### Editar / Eliminar")

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

    st.caption(f"Editando: {label_sel}")

    # El selector de Tipo va FUERA del form: los widgets dentro de un st.form
    # no disparan rerun. Tipo simplificado a Ingreso/Gasto/Ahorro: la categoría
    # determina si un gasto es Fijo o Variable.
    grupos = ["Ingreso", "Gasto", "Ahorro"]
    grupo_mov = "Gasto" if mov["tipo"] in ("Gasto Fijo", "Gasto Variable") else mov["tipo"]
    grupo_e = st.selectbox("Tipo", grupos, index=grupos.index(grupo_mov),
                           key=f"e_tipo_{mov_id}")

    opciones_cat = _opciones_categorias(user.id, grupo_e)
    # Ofrecer la categoría original aunque esté inactiva (solo si el grupo coincide).
    lbl_orig = None
    if grupo_e == grupo_mov:
        if grupo_mov == "Gasto":
            sufijo = "fijo" if mov["tipo"] == "Gasto Fijo" else "variable"
            lbl_orig = f"{mov['categoria']} · {sufijo}"
        else:
            lbl_orig = mov["categoria"]
        if lbl_orig not in opciones_cat:
            opciones_cat = {lbl_orig: (mov["categoria"], mov["tipo"]), **opciones_cat}

    if not opciones_cat:
        st.warning(f"Sin categorías activas de tipo '{grupo_e}'. Creá una en Configuración.")

    with st.form(f"edit_{mov_id}"):
        col1, col2 = st.columns(2)
        with col1:
            fecha_e = st.date_input("Fecha del movimiento",
                                    value=pd.to_datetime(mov["fecha_devengo"]).date(),
                                    format="DD/MM/YYYY", key=f"e_fdev_{mov_id}")
        with col2:
            if opciones_cat:
                labels = list(opciones_cat.keys())
                cat_idx = labels.index(lbl_orig) if lbl_orig in labels else 0
                cat_lbl_e = st.selectbox("Categoría", labels, index=cat_idx,
                                         key=f"e_cat_{mov_id}")
            else:
                cat_lbl_e = None

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
            guardar = st.form_submit_button("Guardar cambios", use_container_width=True)
        with col_d:
            eliminar = st.form_submit_button("Eliminar", use_container_width=True)

        if guardar:
            if not cat_lbl_e:
                st.error("Elegí una categoría")
            elif monto_e <= 0:
                st.error("El monto debe ser mayor a cero")
            else:
                try:
                    cat_e, tipo_db_e = opciones_cat[cat_lbl_e]
                    update_movimiento(user.id, mov_id, fecha_e, tipo_db_e, cat_e,
                                      concepto_e, monto_e, cuotas_e, inicio_e)
                    st.success("Movimiento actualizado")
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
            if st.button("Sí, eliminar", use_container_width=True, key=f"si_del_{mov_id}"):
                try:
                    delete_movimiento(user.id, mov_id)
                    st.session_state.pop(f"confirmar_del_{mov_id}", None)
                    st.success("Movimiento eliminado")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al eliminar: {e}")
        with c2:
            if st.button("Cancelar", use_container_width=True, key=f"no_del_{mov_id}"):
                st.session_state.pop(f"confirmar_del_{mov_id}", None)
                st.rerun()

# ============================================================================
# PANTALLA: ESTADO DE RESULTADOS
# ============================================================================
def _reporte_resultados(user):
    st.caption("Criterio devengado · Agrupado por el mes de la fecha del movimiento.")

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

    def _fila(t):
        return pivot.loc[t] if t in pivot.index else 0
    resultado = _fila("Ingreso") - _fila("Gasto Fijo") - _fila("Gasto Variable")
    pivot.loc["Resultado del período"] = resultado
    pivot.loc["Resultado después de ahorro"] = resultado - _fila("Ahorro")
    orden_final = [r for r in ["Ingreso", "Gasto Fijo", "Gasto Variable",
                               "Resultado del período", "Ahorro",
                               "Resultado después de ahorro"] if r in pivot.index]
    pivot = pivot.reindex(orden_final)

    pivot.columns = [c.strftime("%m/%Y") for c in pivot.columns]
    pivot_fmt = pivot.copy().map(fmt_money)
    pivot_fmt.index.name = "Concepto"
    st.dataframe(pivot_fmt, use_container_width=True)

    st.caption(
        "Los gráficos de evolución mensual y de gastos por categoría viven en **Inicio**."
    )

    st.markdown("##### Detalle por categoría")
    meses_disp = sorted(df["mes"].unique(), reverse=True)
    mes_sel = st.selectbox(
        "Seleccionar mes",
        options=meses_disp,
        index=_default_mes_idx(meses_disp),
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
def _reporte_flujo(user):
    st.caption("Criterio caja · Cuotas distribuidas en el mes que corresponde.")

    df = df_movimientos(user.id)
    if df.empty:
        st.info("No tenés movimientos cargados todavía.")
        return

    # ------------------------------------------------------------------------
    # CÁLCULO COMPARTIDO con page_dashboard (sobre TODOS los meses)
    # ------------------------------------------------------------------------
    estado = calcular_estado_flujo(user.id)
    if estado is None:
        st.info("No hay cuotas que mostrar.")
        return
    df_caja = estado["df_caja"]
    pivot_completo = estado["pivot_completo"]
    flujo_neto_completo = estado["flujo_neto"]
    meses_todos = estado["meses_todos"]
    ajustes_manuales = estado["ajustes_manuales"]
    saldo_auto = estado["saldo_auto"]
    ajuste = estado["ajuste"]
    saldos_ini = estado["saldos_ini"]
    saldos_fin = estado["saldos_fin"]

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
            f"El primer mes con movimientos ({primer_lbl}) arranca con saldo inicial $0,00. "
            f"Si tenías dinero antes de empezar a usar la app, conciliá el saldo de ese mes "
            f"abajo: decile a la app cuánto tenías realmente y listo."
        )

    # ------------------------------------------------------------------------
    # AJUSTAR saldo inicial de un mes (widgets sueltos para preview en vivo)
    # ------------------------------------------------------------------------
    st.divider()
    st.markdown("##### Conciliar saldo")
    st.caption(
        "Elegí un mes y decile a la app cuál es tu saldo REAL a fin de ese mes "
        "(lo que ves en tu billetera o banco). La diferencia se registra como "
        "ajuste y se arrastra a los meses siguientes."
    )

    meses_opts_lbl = [m.strftime("%m/%Y") for m in meses_rango]
    meses_opts_ts = list(meses_rango)

    col_mes, col_saldo = st.columns([1, 2])
    with col_mes:
        mes_idx = st.selectbox(
            "Mes",
            options=list(range(len(meses_opts_lbl))),
            format_func=lambda i: meses_opts_lbl[i],
            index=_default_mes_idx(meses_opts_ts),
            key="conc_mes_idx",
        )
    mes_ts_sel = meses_opts_ts[mes_idx]
    mes_lbl_sel = meses_opts_lbl[mes_idx]
    saldo_fin_actual = float(saldos_fin[mes_ts_sel])
    ajuste_actual = float(ajuste[mes_ts_sel])

    with col_saldo:
        # Key dinámica por mes: al cambiar el selector, el input se resetea
        # al saldo calculado de ese mes.
        saldo_real = st.number_input(
            f"Tu saldo real a fin de {mes_lbl_sel}",
            value=saldo_fin_actual,
            step=10000.0,
            format="%.2f",
            key=f"conc_input_{mes_ts_sel.isoformat()}",
        )

    delta = float(saldo_real or 0.0) - saldo_fin_actual
    if abs(delta) < 0.005:
        st.caption(
            f"✅ Coincide con el saldo calculado por la app "
            f"({fmt_money(saldo_fin_actual)}). No hay nada que ajustar."
        )
    else:
        st.markdown(
            f"<div style='background: var(--bg-soft); border: 1px solid var(--border); "
            f"border-radius: 8px; padding: 12px 16px; margin: 8px 0;'>"
            f"<div style='color: var(--text-muted); font-size: 0.85rem;'>Vista previa para {mes_lbl_sel}:</div>"
            f"<div style='font-family: Poppins, sans-serif; color: var(--navy); margin-top: 4px;'>"
            f"Según la app: {fmt_money(saldo_fin_actual)} · Tu saldo real: {fmt_money(float(saldo_real or 0.0))} · "
            f"Ajuste a registrar: <strong>{fmt_money(delta)}</strong>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

    if st.button("Guardar conciliación", key="btn_conciliar", disabled=abs(delta) < 0.005):
        try:
            nuevo_ajuste = ajuste_actual + delta
            if abs(nuevo_ajuste) < 0.005:
                delete_saldo_inicial(user.id, mes_ts_sel.date())
                st.success(f"Conciliado: {mes_lbl_sel} vuelve al cálculo automático.")
            else:
                upsert_saldo_inicial(user.id, mes_ts_sel.date(), nuevo_ajuste)
                st.success(f"Conciliado: saldo de {mes_lbl_sel} = {fmt_money(float(saldo_real))}.")
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
    meses_det = sorted(df_caja_rango["mes_pago"].unique(), reverse=True)
    mes_sel = st.selectbox(
        "Seleccionar mes",
        options=meses_det,
        index=_default_mes_idx(meses_det),
        format_func=lambda d: pd.Timestamp(d).strftime("%m/%Y"),
        key="flujo_mes_detalle",
    )
    df_mes = df_caja_rango[df_caja_rango["mes_pago"] == mes_sel].copy()
    df_mes["concepto"] = df_mes["concepto"].fillna("")
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
# PANTALLA: REPORTES (Estado de Resultados + Flujo de Fondos)
# ============================================================================
def page_reportes(user):
    page_header("Reportes", "Dos miradas sobre los mismos datos: devengado y caja.")
    criterio = st.radio(
        "Criterio",
        ["Estado de Resultados", "Flujo de Fondos"],
        horizontal=True,
        key="rep_criterio",
        label_visibility="collapsed",
    )
    with st.expander("¿Cuál es la diferencia entre los dos?"):
        st.markdown(
            "**Estado de Resultados (criterio devengado)**\n\n"
            "Mira el mes en el que ocurrió el hecho económico, sin importar cuándo "
            "lo pagaste. Si comprás algo en 12 cuotas en mayo, el gasto entero "
            "aparece en mayo. Responde: *¿qué tan bien me fue este mes?*\n\n"
            "**Flujo de Fondos (criterio caja)**\n\n"
            "Mira el mes en el que efectivamente entra o sale el dinero. Si comprás "
            "algo en 12 cuotas en mayo, cada cuota aparece en su mes. Responde: "
            "*¿cuánto dinero tengo / voy a tener cada mes?*"
        )
    st.write("")
    if "Resultados" in criterio:
        _reporte_resultados(user)
    else:
        _reporte_flujo(user)

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
            ok_nueva = st.form_submit_button("Agregar", use_container_width=True)
        if ok_nueva:
            n = (nuevo_nombre or "").strip()
            if not n:
                st.error("Ingresá un nombre")
            elif categoria_existe(user.id, n, tipo_sel):
                st.error(f"Ya existe la categoría '{n}' para tipo {tipo_sel}")
            else:
                try:
                    insert_categoria(user.id, n, tipo_sel)
                    st.success(f"Categoría '{n}' creada")
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
    conteos = conteo_movs_por_categoria(user.id, tipo_sel)

    st.markdown(f"##### Activas ({len(cats_activas)})")
    if not cats_activas:
        st.caption("No hay categorías activas.")
    for c in cats_activas:
        _row_categoria(user, c, activa=True, conteos=conteos)

    if cats_inactivas:
        with st.expander(f"Inactivas ({len(cats_inactivas)})"):
            for c in cats_inactivas:
                _row_categoria(user, c, activa=False, conteos=conteos)


def _row_categoria(user, c, activa, conteos):
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
                            st.success(f"Renombrada a '{n}'")
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
            afectados = conteos.get(nombre_actual, 0)
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
# PANTALLA: INICIO (DEFAULT AL LOGUEARSE)
# ============================================================================
def _nombre_de_usuario(user):
    """Devuelve la parte local del email como nombre amigable, con primera mayúscula."""
    email = getattr(user, "email", "") or ""
    local = email.split("@")[0] if "@" in email else email
    # Si tiene puntos o guiones, capitalizamos cada parte
    parts = [p.capitalize() for p in local.replace(".", " ").replace("-", " ").split()]
    return " ".join(parts) if parts else "👋"

def page_inicio(user):
    nombre = _nombre_de_usuario(user)
    page_header(f"Hola, {nombre}", "Tus finanzas desde un solo lugar.")

    estado = calcular_estado_flujo(user.id)
    if estado is None:
        st.info(
            "**Es tu primera vez por acá.** Para empezar:\n\n"
            "1. Andá a **Cargar movimiento** y registrá un ingreso, gasto o ahorro.\n"
            "2. Si ya tenías dinero antes de empezar, abrí **Reportes → Flujo de Fondos** "
            "y conciliá tu saldo: le decís a la app cuánto tenés realmente y listo.\n"
            "3. Volvé acá para ver tu resumen mes a mes."
        )
        return

    _dashboard_body(user, estado)

# ============================================================================
# CUERPO DEL DASHBOARD (se muestra dentro de Inicio)
# ============================================================================
def _dashboard_body(user, estado):
    pivot_completo = estado["pivot_completo"]
    flujo_neto = estado["flujo_neto"]
    meses_todos = estado["meses_todos"]
    saldos_fin = estado["saldos_fin"]

    # --- Selector de mes (default = último con datos) ---
    meses_lbl = [m.strftime("%m/%Y") for m in meses_todos]
    mes_idx = st.selectbox(
        "Mes a analizar",
        options=list(range(len(meses_lbl))),
        format_func=lambda i: meses_lbl[i],
        index=_default_mes_idx(meses_todos),
        key="dash_mes_idx",
    )
    mes_sel = meses_todos[mes_idx]
    mes_lbl_sel = meses_lbl[mes_idx]

    # --- 4 KPIs del mes seleccionado (criterio caja) ---
    def safe_get(pivot, tipo, mes):
        if tipo in pivot.index and mes in pivot.columns:
            return float(pivot.loc[tipo, mes])
        return 0.0

    ingresos_mes = safe_get(pivot_completo, "Ingreso", mes_sel)
    gastos_mes = (safe_get(pivot_completo, "Gasto Fijo", mes_sel)
                  + safe_get(pivot_completo, "Gasto Variable", mes_sel))
    ahorro_mes = safe_get(pivot_completo, "Ahorro", mes_sel)
    resultado_mes = ingresos_mes - gastos_mes  # el Ahorro no es un gasto: se muestra aparte
    saldo_fin_mes = float(saldos_fin[mes_sel])

    st.markdown(f"##### Mes: {mes_lbl_sel}")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(metric_card("Ingresos", fmt_money(ingresos_mes)),
                    unsafe_allow_html=True)
    with col2:
        st.markdown(metric_card("Gastos", fmt_money(gastos_mes), "orange"),
                    unsafe_allow_html=True)
    with col3:
        st.markdown(metric_card("Ahorro", fmt_money(ahorro_mes), "cyan"),
                    unsafe_allow_html=True)
    with col4:
        color_res = "green" if resultado_mes >= 0 else "red"
        st.markdown(metric_card("Resultado", fmt_money(resultado_mes), color_res),
                    unsafe_allow_html=True)

    st.caption(
        f"Saldo final estimado a fin de {mes_lbl_sel}: **{fmt_money(saldo_fin_mes)}** "
        f"(criterio caja). Resultado = Ingresos − Gastos; el Ahorro se muestra aparte: "
        f"igual sale de tu saldo, pero no es dinero perdido."
    )

    st.divider()

    # ------------------------------------------------------------------------
    # DISPONIBLE REAL (independiente del mes seleccionado arriba)
    # Saldo a fin del mes en curso vs cuotas de gastos ya comprometidas a futuro.
    # ------------------------------------------------------------------------
    hoy_d = date.today()
    mes_curso_ts = pd.Timestamp(hoy_d.year, hoy_d.month, 1)
    df_caja_all = estado["df_caja"]
    comprometido = float(df_caja_all[
        (df_caja_all["mes_pago"] > mes_curso_ts) &
        (df_caja_all["tipo"].isin(["Gasto Fijo", "Gasto Variable"]))
    ]["monto_cuota"].sum())

    saldo_hoy = None
    for m_ts in meses_todos:
        if pd.Timestamp(m_ts) <= mes_curso_ts:
            saldo_hoy = float(saldos_fin[m_ts])
        else:
            break

    if saldo_hoy is not None:
        st.markdown("##### Disponible real")
        cd1, cd2, cd3 = st.columns(3)
        with cd1:
            st.markdown(metric_card(f"Saldo a fin de {mes_curso_ts.strftime('%m/%Y')}",
                                    fmt_money(saldo_hoy)), unsafe_allow_html=True)
        with cd2:
            st.markdown(metric_card("Comprometido en cuotas futuras",
                                    fmt_money(comprometido), "orange"), unsafe_allow_html=True)
        with cd3:
            neto = saldo_hoy - comprometido
            st.markdown(metric_card("Disponible neto", fmt_money(neto),
                                    "" if neto >= 0 else "red"), unsafe_allow_html=True)
        st.caption(
            "El comprometido son las cuotas de gastos ya cargadas que vencen en meses "
            "futuros: ese dinero conviene tenerlo reservado, no gastarlo."
        )
        st.divider()

    # ------------------------------------------------------------------------
    # RITMO DE GASTO VARIABLE (mes en curso)
    # ------------------------------------------------------------------------
    dias_transc = hoy_d.day
    dias_mes = pd.Timestamp(hoy_d).days_in_month
    gv_curso = safe_get(pivot_completo, "Gasto Variable", mes_curso_ts)
    if gv_curso > 0:
        st.markdown("##### Ritmo de gasto variable (mes en curso)")
        rg1, rg2, rg3 = st.columns(3)
        with rg1:
            st.markdown(metric_card("Gastado al día de hoy", fmt_money(gv_curso)),
                        unsafe_allow_html=True)
        with rg2:
            st.markdown(metric_card("Promedio diario", fmt_money(gv_curso / dias_transc),
                                    "orange"), unsafe_allow_html=True)
        with rg3:
            st.markdown(metric_card(f"Proyectado a fin de {mes_curso_ts.strftime('%m/%Y')}",
                                    fmt_money(gv_curso / dias_transc * dias_mes), "orange"),
                        unsafe_allow_html=True)
        st.caption(
            f"Los fijos y el ahorro ya están definidos; el mes se juega en los variables. "
            f"Promedio = gasto variable acumulado dividido los {dias_transc} días "
            f"transcurridos. El proyectado asume que seguís a este ritmo."
        )
        st.divider()

    # Ventana de meses para el gráfico de evolución (hasta 12, terminando en el mes elegido)
    start_idx = max(0, mes_idx - 11)
    meses_chart = meses_todos[start_idx:mes_idx + 1]

    # ------------------------------------------------------------------------
    # GRÁFICO 1: Composición por categoría (gastos + ahorro) con filtros propios
    # ------------------------------------------------------------------------
    st.markdown("##### Composición por categoría")

    # Selectores propios para este gráfico (independientes del selector principal)
    col_t1, col_t2 = st.columns([3, 2])
    with col_t1:
        # Default = mes principal del Dashboard; opción extra "Todos los meses"
        meses_lbl_torta = ["Todos los meses"] + meses_lbl
        idx_default = meses_lbl_torta.index(mes_lbl_sel) if mes_lbl_sel in meses_lbl_torta else 1
        mes_torta_sel = st.selectbox(
            "Mes",
            options=meses_lbl_torta,
            index=idx_default,
            key="dash_torta_mes",
        )
    with col_t2:
        tipo_torta_sel = st.selectbox(
            "Tipo",
            options=["Todos", "Gasto Fijo", "Gasto Variable", "Ahorro"],
            index=0,
            key="dash_torta_tipo",
        )

    df_caja = estado["df_caja"]

    # Filtrar por tipo
    if tipo_torta_sel == "Todos":
        df_torta_base = df_caja[df_caja["tipo"].isin(["Gasto Fijo", "Gasto Variable", "Ahorro"])].copy()
    else:
        df_torta_base = df_caja[df_caja["tipo"] == tipo_torta_sel].copy()

    # Filtrar por mes
    if mes_torta_sel != "Todos los meses":
        df_torta_base = df_torta_base[
            df_torta_base["mes_pago"].dt.strftime("%m/%Y") == mes_torta_sel
        ]

    if df_torta_base.empty:
        st.caption("No hay datos en la selección.")
    else:
        df_torta = (df_torta_base.groupby("categoria", as_index=False)["monto_cuota"].sum()
                    .sort_values("monto_cuota", ascending=False))
        total_torta = df_torta["monto_cuota"].sum()
        paleta = [NAVY, CYAN, ORANGE, GREEN, GREY,
                  NAVY_HOVER, "#3aa9c9", "#f08259", "#3fa85a", "#9aa0a6"]
        fig_torta = px.pie(
            df_torta, names="categoria", values="monto_cuota",
            hole=0.55,
            color_discrete_sequence=paleta,
        )
        fig_torta.update_traces(
            textposition="outside",
            textinfo="label+percent",
            marker=dict(line=dict(color="white", width=2)),
        )
        fig_torta = aplicar_tema_plotly(fig_torta, height=470)
        fig_torta.update_layout(margin=dict(t=40, b=40, l=10, r=10))
        fig_torta.update_layout(showlegend=False)
        st.plotly_chart(fig_torta, use_container_width=True, config={"displayModeBar": False})
        st.caption(
            f"Total {tipo_torta_sel.lower() if tipo_torta_sel != 'Todos' else 'gastos + ahorro'} "
            f"en {mes_torta_sel.lower() if mes_torta_sel != 'Todos los meses' else 'todos los meses'}: "
            f"**{fmt_money(total_torta)}**"
        )

    # ------------------------------------------------------------------------
    # GRÁFICO 2: Evolución mensual con selector de serie
    # (resuelve el problema de escala: cuando elegís una sola serie se autoescala bien)
    # ------------------------------------------------------------------------
    st.markdown("##### Evolución mensual")
    serie_sel = st.radio(
        "Mostrar",
        options=["Resultado", "Ingresos", "Gastos", "Ahorro", "Todo"],
        horizontal=True,
        index=0,
        key="dash_serie",
    )

    # Misma ventana de meses que el gráfico de saldo
    fig_evol = go.Figure()
    x_lbls = [m.strftime("%m/%Y") for m in meses_chart]

    def serie_de(tipo):
        return [safe_get(pivot_completo, tipo, m) for m in meses_chart]

    def serie_gastos():
        return [safe_get(pivot_completo, "Gasto Fijo", m)
                + safe_get(pivot_completo, "Gasto Variable", m) for m in meses_chart]

    def serie_resultado():
        return [safe_get(pivot_completo, "Ingreso", m)
                - safe_get(pivot_completo, "Gasto Fijo", m)
                - safe_get(pivot_completo, "Gasto Variable", m) for m in meses_chart]

    if serie_sel == "Resultado":
        vals = serie_resultado()
        colores = [GREEN if v >= 0 else RED for v in vals]
        fig_evol.add_trace(go.Bar(x=x_lbls, y=vals, name="Resultado",
                                  marker_color=colores, marker_line_width=0))
    elif serie_sel == "Ingresos":
        fig_evol.add_trace(go.Bar(x=x_lbls, y=serie_de("Ingreso"),
                                  name="Ingresos", marker_color=NAVY, marker_line_width=0))
    elif serie_sel == "Gastos":
        fig_evol.add_trace(go.Bar(x=x_lbls, y=serie_gastos(),
                                  name="Gastos", marker_color=ORANGE, marker_line_width=0))
    elif serie_sel == "Ahorro":
        fig_evol.add_trace(go.Bar(x=x_lbls, y=serie_de("Ahorro"),
                                  name="Ahorro", marker_color=CYAN, marker_line_width=0))
    else:  # Todo
        for tipo, color in [("Ingreso", NAVY), ("Gasto Fijo", ORANGE),
                            ("Gasto Variable", "#f08259"), ("Ahorro", CYAN)]:
            fig_evol.add_trace(go.Scatter(
                x=x_lbls, y=serie_de(tipo), name=tipo,
                mode="lines+markers",
                line=dict(color=color, width=2.5),
                marker=dict(size=7, color=color),
            ))

    fig_evol = aplicar_tema_plotly(fig_evol, height=320)
    if serie_sel == "Todo":
        st.caption(
            "Las series están en la misma escala — si los ingresos son mucho mayores que "
            "los gastos individuales, estos se ven aplastados contra el cero. "
            "Para análisis detallado, elegí una serie a la vez."
        )
    st.plotly_chart(fig_evol, use_container_width=True, config={"displayModeBar": False})


# ============================================================================
# APP PRINCIPAL (LOGUEADO)
# ============================================================================
_SIDEBAR_MOBILE_JS = """
<script>
// En mobile, al elegir una pestaña del menú la sidebar queda abierta tapando
// el contenido. Esto la cierra automáticamente. Best effort: usa selectores
// internos de Streamlit que pueden cambiar entre versiones.
try {
    const doc = window.parent.document;
    if (!doc.__wlSidebarHook) {
        doc.__wlSidebarHook = true;
        doc.addEventListener("click", function (e) {
            if (window.parent.innerWidth > 768) return;
            const sb = e.target.closest('section[data-testid="stSidebar"]');
            if (!sb) return;
            const lbl = e.target.closest("label");
            if (!lbl) return;
            setTimeout(function () {
                const btn =
                    doc.querySelector('[data-testid="stSidebarCollapseButton"] button') ||
                    doc.querySelector('section[data-testid="stSidebar"] button[kind="headerNoPadding"]');
                if (btn) btn.click();
            }, 200);
        }, true);
    }
} catch (e) {}
</script>
"""

def app(user):
    components.html(_SIDEBAR_MOBILE_JS, height=0)
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
            f"{user.email}"
            f"</div>",
            unsafe_allow_html=True,
        )
        if st.button("Cerrar sesión", use_container_width=True):
            do_signout()
        st.divider()

    page = st.sidebar.radio("Menú", [
        "Inicio",
        "Cargar movimiento",
        "Movimientos",
        "Reportes",
        "Configuración",
    ], label_visibility="collapsed")

    if "Inicio" in page:
        page_inicio(user)
    elif "Cargar" in page:
        page_cargar(user)
    elif "Movimientos" in page:
        page_ver(user)
    elif "Reportes" in page:
        page_reportes(user)
    elif "Configuración" in page:
        page_configuracion(user)

# ============================================================================
# ROUTER
# ============================================================================
# Vuelta del login con Google: PKCE, el código llega en ?code= (legible por el servidor).
_qp = st.query_params
if _qp.get("error_description"):
    st.session_state["oauth_error"] = _qp.get("error_description")
    st.query_params.clear()
    st.rerun()

if _qp.get("code"):
    _verifier = None
    try:
        _verifier = cookie_manager.get("wl_pkce")
    except Exception:
        pass
    if not _verifier:
        _verifier = st.session_state.get("pkce_verifier")

    if not _verifier and st.session_state.get("pkce_intentos", 0) < 2:
        # La cookie todavía no llegó del navegador (primer render): esperar
        # un ciclo; el componente de cookies dispara un rerun solo.
        st.session_state["pkce_intentos"] = st.session_state.get("pkce_intentos", 0) + 1
        st.stop()

    if _verifier:
        try:
            resp = httpx.post(
                f"{st.secrets['SUPABASE_URL'].strip().rstrip('/')}/auth/v1/token?grant_type=pkce",
                json={"auth_code": _qp.get("code"), "code_verifier": _verifier},
                headers={"apikey": st.secrets["SUPABASE_KEY"],
                         "Content-Type": "application/json"},
                timeout=15,
            )
            data = resp.json()
            if resp.status_code == 200 and data.get("access_token"):
                sb.auth.set_session(data["access_token"], data["refresh_token"])
                u = sb.auth.get_user()
                if u and u.user:
                    st.session_state.sb_tokens = {
                        "access_token": data["access_token"],
                        "refresh_token": data["refresh_token"],
                    }
                    st.session_state.user = u.user
                    _guardar_cookie_sesion(data["refresh_token"], "ck_oauth")
                    try:
                        seed_categorias_si_vacio(u.user.id)
                    except Exception:
                        pass
                else:
                    st.session_state["oauth_error"] = "no se pudo leer el usuario."
            else:
                st.session_state["oauth_error"] = (
                    data.get("error_description") or data.get("msg") or str(data)
                )
        except Exception as e:
            st.session_state["oauth_error"] = str(e)
    else:
        st.session_state["oauth_error"] = (
            "no llegó el código de verificación del navegador. Probá de nuevo."
        )
    st.session_state["pkce_intentos"] = 0
    st.session_state["pkce_verifier"] = None
    try:
        cookie_manager.delete("wl_pkce", key="ck_pkce_del")
    except Exception:
        pass
    st.query_params.clear()
    st.rerun()

# Si la URL trae el token del mail de recuperación, capturarlo y limpiar la URL.
if _qp.get("type") == "recovery" and _qp.get("token_hash"):
    st.session_state.recovery_token_hash = _qp.get("token_hash")
    st.query_params.clear()

if st.session_state.get("recovery_token_hash"):
    page_nueva_password()
elif st.session_state.user is None:
    page_login()
else:
    app(st.session_state.user)
