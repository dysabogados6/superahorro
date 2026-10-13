import pandas as pd
import random
import streamlit as st
from supabase import create_client

# Configuración de la página (Diseño optimizado para celulares)
st.set_page_config(page_title="SuperAhorro", page_icon="🛒", layout="centered")

# Conexión a Supabase usando los secretos configurados en Streamlit Cloud
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


@st.cache_resource
def init_connection():
  return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_connection()

st.markdown(
    """
    <h2 style='text-align: center;'>🛒 SuperAhorro</h2>
    <p style='text-align: center; color: gray;'>Comparador de precios y promos en vivo AR</p>
""",
    unsafe_allow_html=True,
)

# --- 1. SECCIÓN CANASTA / BÚSQUEDA ---
st.markdown("### 📦 Tu Canasta")

# Obtener productos existentes en la base de datos
try:
  res_prod = supabase.table("productos").select("*").execute()
  lista_productos = res_prod.data if res_prod.data else []
except Exception as e:
  lista_productos = []
  st.error(f"Error al conectar con Supabase: {e}")

nombres_productos = [p["nombre"] for p in lista_productos]

# Selector de productos múltiples
productos_seleccionados = st.multiselect(
    "Elegí o buscá los productos que querés comprar:", nombres_productos
)

# Opción para agregar un producto nuevo si no existe
with st.expander("➕ ¿No encontrás un producto? Agregalo acá"):
  nuevo_nombre = st.text_input("Nombre del producto (ej: Yogur Griego Natural)")
  nueva_marca = st.text_input("Marca (ej: Yagurísimo / Día)")
  nueva_categoria = st.selectbox(
      "Categoría", ["Lácteos", "Almacén", "Bebidas", "Limpieza", "Frescos"]
  )

  if st.button("Guardar producto en la base"):
    if nuevo_nombre and nueva_marca:
      try:
        # Generamos un EAN numérico corto de 12 dígitos para cumplir con la restricción
        ean_corto = str(random.randint(100000000000, 999999999999))

        supabase.table("productos").insert({
            "nombre": nuevo_nombre,
            "marca": nueva_marca,
            "categoria": nueva_categoria,
            "ean": ean_corto,
        }).execute()
        st.success(f"¡'{nuevo_nombre}' agregado con éxito! Recargá la página.")
        st.rerun()
      except Exception as e:
        st.error(f"Error al guardar: {e}")
    else:
      st.warning("Completá el nombre y la marca del producto.")

# --- 2. SECCIÓN BENEFICIOS ---
st.markdown("### 💳 Tus Beneficios")
col1, col2 = st.columns(2)
with col1:
  medio_pago = st.selectbox(
      "Medio de Pago", ["Ninguno", "Cuenta DNI", "Modo", "Tarjeta Galicia"]
  )
with col2:
  dia_compra = st.selectbox(
      "Día de Compra", ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
  )

# Botón de cálculo
if st.button("🔍 Calcular Supermercado Más Barato", use_container_width=True):
  if not productos_seleccionados:
    st.warning("Por favor elegí al menos un producto para calcular.")
  else:
    st.info("Calculando los mejores precios y descuentos vigentes...")
