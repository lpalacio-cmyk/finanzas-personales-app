# Finanzas Personales - WL HNOS & ASOC

App de finanzas personales construida con Streamlit y Supabase.
Cada usuario gestiona sus propios movimientos (ingresos, gastos fijos, gastos variables, ahorro)
con criterio devengado y caja, soportando cuotas.

## Stack

- **Frontend**: Streamlit
- **Base de datos**: Supabase (PostgreSQL)
- **Autenticación**: Supabase Auth (email + contraseña)
- **Hosting**: Streamlit Cloud

## Funcionalidades actuales

- Registro / login con email y contraseña
- Carga de movimientos con cuotas
- Vista de últimos movimientos y vista completa
- 20 categorías iniciales creadas automáticamente al registrarse

## Próximas funcionalidades

- Estado de Resultados (criterio devengado)
- Flujo de Fondos (criterio caja, con cuotas distribuidas)
- Configuración de categorías
- Exportar a Excel

## Setup en Streamlit Cloud

1. Conectar este repositorio en [share.streamlit.io](https://share.streamlit.io).
2. En la sección **Secrets** del deploy, agregar:

```toml
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_KEY = "eyJ..."
```

3. Deploy.
