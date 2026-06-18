"""
keepalive.py - Mantiene despierta la app de Streamlit.

Streamlit Community Cloud (free) duerme la app tras 12 h sin trafico real.
Un GET comun NO alcanza: la pagina dormida igual responde HTTP 200 (una shell
estatica) y la app recien arranca cuando el navegador ejecuta el JavaScript y
abre el WebSocket. Por eso usamos un navegador real (Chromium headless): visita
la app de verdad (eso abre sesion y resetea el reloj de inactividad = la mantiene
despierta) y, si la encuentra dormida, clickea el boton "Yes, get this app back up!".

OJO: solo funciona en apps PUBLICAS de Streamlit (sin viewer-auth). Si la app pide
iniciar sesion de Streamlit para verla, el robot anonimo no puede entrar.

Como la pantalla de dormido se dibuja por JavaScript (y a veces tarda), este script:
  - reintenta hasta ~45s buscando el boton (no chequea una sola vez),
  - busca tanto en la pagina como dentro de cualquier iframe,
  - clickea el boton directo por JS (mas robusto que depender del tipo de elemento),
  - si NO lo encuentra, imprime un diagnostico (frames + texto visible) para saber por que.

Lo ejecuta la GitHub Action .github/workflows/keepalive.yml.
La URL se lee de la variable de entorno STREAMLIT_URL (definida en el workflow);
si no esta, usa la URL por defecto de mas abajo.

Solo termina con error (exit 1, avisa por mail) si NO puede ni cargar la pagina.
"""

import os
import sys
import time

from playwright.sync_api import sync_playwright

URL = os.environ.get(
    "STREAMLIT_URL",
    "https://finanzas-personales-app.streamlit.app",
)

# Busca un boton/enlace cuyo texto contenga "get this app back up" (sin distinguir
# mayusculas) y lo clickea. El boton de Streamlit dormido dice "Yes, get this app back up!".
JS_CLICK = r"""
() => {
  const rx = /get this app back up/i;
  const candidatos = document.querySelectorAll(
    'button, a, [role="button"], input[type="button"], input[type="submit"]'
  );
  const el = Array.from(candidatos).find(
    e => rx.test(((e.textContent || e.value || '')).trim())
  );
  if (el) { el.click(); return true; }
  return false;
}
"""


def intentar_despertar(page) -> bool:
    """Intenta clickear el boton de despertar en la pagina y en cada iframe."""
    for frame in page.frames:
        try:
            if frame.evaluate(JS_CLICK):
                return True
        except Exception:
            pass
    return False


def main() -> None:
    print(f"Visitando {URL}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1) Cargar la pagina (con margen)
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        except Exception as e:
            print(f"ERROR: no se pudo cargar la URL: {e}")
            browser.close()
            sys.exit(1)

        print(f"Pagina cargada. Titulo: {page.title()!r}")

        # 2) Reintentar hasta ~45s: la pantalla de dormido puede tardar en renderizar
        desperto = False
        deadline = time.time() + 45
        while time.time() < deadline:
            page.wait_for_timeout(3000)
            if intentar_despertar(page):
                desperto = True
                break

        # 3) Resultado
        if desperto:
            print("La app estaba DORMIDA -> clickee 'get this app back up'")
            page.wait_for_timeout(60000)  # le doy tiempo a arrancar
            print("WAKE: la app quedo arrancando")
        else:
            # No se encontro el boton: imprimir diagnostico para entender por que
            print("No encontre el boton de despertar. Diagnostico:")
            print(f"  frames ({len(page.frames)}): {[f.url for f in page.frames]}")
            try:
                texto = page.inner_text("body")[:400].replace("\n", " ")
                print(f"  texto visible (primeros 400 chars): {texto!r}")
            except Exception as e:
                print(f"  (no pude leer el texto del body: {e})")
            print("OK: la app parece despierta (o no se detecto la pantalla de dormido)")

        browser.close()


if __name__ == "__main__":
    main()
