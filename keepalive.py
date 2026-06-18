"""
keepalive.py - Mantiene despierta la app de Streamlit.

Streamlit Community Cloud (free) duerme la app tras 12 h sin trafico real.
Un GET comun NO alcanza: la pagina dormida igual responde HTTP 200 y el proceso
Python nunca arranca. Por eso este script usa un navegador real (Chromium
headless): carga la app de verdad y, si esta dormida, clickea el boton
"Yes, get this app back up!" y espera a que el contenedor de Streamlit aparezca.

Lo ejecuta la GitHub Action .github/workflows/keepalive.yml cada pocas horas.
La URL se lee de la variable de entorno STREAMLIT_URL (definida en el workflow);
si no esta, usa la URL por defecto de mas abajo.
"""

import os
import re
import sys

from playwright.sync_api import sync_playwright

URL = os.environ.get(
    "STREAMLIT_URL",
    "https://finanzas-personales-app.streamlit.app",
)


def main() -> None:
    print(f"Visitando {URL}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1) Cargar la app
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"ERROR: no se pudo cargar la URL: {e}")
            browser.close()
            sys.exit(1)

        # 2) Si esta dormida, buscar el boton de despertar y clickearlo
        woke = False
        try:
            boton = page.get_by_role(
                "button", name=re.compile("get this app back up", re.I)
            )
            if boton.count() == 0:
                boton = page.get_by_text(re.compile("get this app back up", re.I))

            if boton.count() > 0:
                print("La app estaba DORMIDA -> clickeo para despertarla")
                boton.first.click()
                woke = True
        except Exception as e:
            print(f"Aviso al buscar el boton de despertar (continuo igual): {e}")

        # 3) Confirmar que la app quedo arriba (aparece el contenedor de Streamlit)
        try:
            page.wait_for_selector(
                '[data-testid="stApp"], .stApp',
                timeout=120000 if woke else 60000,
            )
            print(
                "WAKE: la app quedo despierta"
                if woke
                else "OK: la app ya estaba despierta"
            )
        except Exception as e:
            accion = "despertarla" if woke else "cargarla"
            print(f"ERROR: no se confirmo la app arriba tras {accion}: {e}")
            browser.close()
            sys.exit(1)

        browser.close()


if __name__ == "__main__":
    main()
