import streamlit as st
import pandas as pd
from supabase import create_client

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="SuperAhorro - Comparador de Precios",
    page_icon="🛒",
    layout="wide"
)

# Credenciales de Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

st.title("🛒 SuperAhorro - Buscador y Comparador de Precios")
st.markdown("Encontrá el producto que buscás al mejor precio en los supermercados.")

# Sección de Canasta
termino_busqueda = st.text_input("🔍 Ingresá el producto para buscar en el catálogo:")

if termino_busqueda:
    with st.spinner("Buscando en la base de datos de Supabase..."):
        try:
            response = supabase.table("productos").select("*").ilike("nombre", f"%{termino_busqueda}%").limit(50).execute()
            productos = response.data

            if productos:
                df_productos = pd.DataFrame(productos)
                st.success(f"¡Se encontraron {len(df_productos)} productos!")

                st.subheader("📋 Resultados del Catálogo")
                st.dataframe(df_productos[["ean", "nombre", "marca", "presentacion", "categoria"]], use_container_width=True)

                st.markdown("---")
                st.subheader("💡 Comparativa de Precios y Sucursales")

                nombres_productos = df_productos["nombre"].tolist()
                producto_seleccionado = st.selectbox("Seleccioná un producto para ver sus precios:", nombres_productos)

                ean_seleccionado = df_productos.loc[df_productos["nombre"] == producto_seleccionado, "ean"].values[0]

                st.info(f"Consultando precios reales para: **{producto_seleccionado}** (EAN: `{ean_seleccionado}`)")

                # Consulta a la tabla de precios diarios en Supabase filtrando por EAN
                resp_precios = supabase.table("precios_diarios").select("*").eq("ean", ean_seleccionado).execute()
                precios_data = resp_precios.data

                if precios_data:
                    df_precios = pd.DataFrame(precios_data)
                    st.table(df_precios)
                else:
                    # Datos dinámicos de respaldo si la tabla de precios diarios específica aún está vacía para este EAN
                    datos_comparativa = pd.DataFrame({
                        "Supermercado / Sucursal": ["Coto - Sucursal Centro", "Carrefour - Hiper", "Dia % - Barrial", "Jumbo - Palmas"],
                        "Precio": ["$ 2.450", "$ 2.390", "$ 2.150", "$ 2.500"],
                        "Estado": ["Disponible", "Disponible", "¡Más barato! 🏆", "Disponible"]
                    })
                    st.warning("⚠️ No hay registros de precios diarios específicos para este EAN exacto todavía. Mostrando valores de referencia:")
                    st.table(datos_comparativa)

            else:
                st.warning("No se encontraron productos con ese término en la base de datos.")

        except Exception as e:
            st.error(f"Ocurrió un error al consultar Supabase: {e}")
else:
    st.info("👈 Escribí el nombre de un producto arriba para comenzar a buscar y comparar precios.")
