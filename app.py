import streamlit as st
import pandas as pd
from supabase import create_client, Client

# Configuración de página optimizada para celulares
st.set_page_config(
    page_title="SuperAhorro Argentina",
    page_icon="🛒",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilos CSS personalizados para que luzca como una App de celular nativa
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 50px;
        font-weight: bold;
        font-size: 16px;
    }
    .card-ganador {
        background-color: #d4edda;
        border: 2px solid #28a745;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        color: #155724;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

SUPABASE_URL = "https://mtfiiqmfhgvbhxphkysd.supabase.co"
SUPABASE_KEY = "sb_publishable_zue_bcg3IzHV_GwvKk0HNQ_bq6_R9ei"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("🛒 SuperAhorro")
st.caption("Comparador de precios y promos bancarias en vivo 🇦🇷")

@st.cache_data(ttl=30)
def cargar_datos():
    res_p = supabase.table("productos").select("ean, nombre").execute()
    prods = {p['nombre']: p['ean'] for p in res_p.data}
    
    res_pr = supabase.table("precios_diarios").select("ean, supermercado, precio_lista, precio_promocion").execute()
    df_precios = pd.DataFrame(res_pr.data)
    
    res_promos = supabase.table("promociones").select("*").eq("activo", True).execute()
    df_promos = pd.DataFrame(res_promos.data)
    
    return prods, df_precios, df_promos

productos_dict, df_precios, df_promos = cargar_datos()
lista_nombres = list(productos_dict.keys())

# Formulario principal vertical (ideal para celular)
with st.form("form_superahorro"):
    st.subheader("📦 Tu Canasta")
    productos_seleccionados = st.multiselect(
        "Elegí los productos que querés comprar:",
        options=lista_nombres,
        default=lista_nombres
    )
    
    st.subheader("💳 Tus Beneficios")
    col1, col2 = st.columns(2)
    with col1:
        medios_pago = ["Cuenta DNI", "BNA MODO", "Galicia", "BBVA", "Sin Promoción / Efectivo"]
        medio_pago = st.selectbox("Medio de Pago", medios_pago)
    with col2:
        dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        dia_semana = st.selectbox("Día de Compra", dias, index=5) # Sábado por defecto
        
    submitted = st.form_submit_button("🔍 Calcular Supermercado Más Barato")

if submitted:
    if not productos_seleccionados:
        st.warning("⚠️ Seleccioná al menos un producto.")
    else:
        eans_sel = [productos_dict[n] for n in productos_seleccionados]
        df_filtrado = df_precios[df_precios['ean'].isin(eans_sel)].copy()
        
        if df_filtrado.empty:
            st.error("❌ No hay precios para los productos seleccionados.")
        else:
            df_filtrado['precio_efectivo'] = df_filtrado['precio_promocion'].fillna(df_filtrado['precio_lista'])
            totales_super = df_filtrado.groupby('supermercado')['precio_efectivo'].sum().reset_index()
            totales_super.rename(columns={'precio_efectivo': 'subtotal_canasta'}, inplace=True)

            resultados = []
            for _, row in totales_super.iterrows():
                super_name = row['supermercado']
                subtotal = row['subtotal_canasta']

                promo_aplicable = pd.DataFrame()
                if not df_promos.empty:
                    promo_aplicable = df_promos[
                        (df_promos['supermercado'].str.lower() == super_name.lower()) & 
                        (df_promos['banco_medio_pago'].str.lower() == medio_pago.lower()) &
                        ((df_promos['dia_semana'].str.lower() == dia_semana.lower()) | (df_promos['dia_semana'] == 'todos'))
                    ]

                descuento_monto = 0.0
                detalle_promo = "Sin descuento bancario"

                if not promo_aplicable.empty:
                    p = promo_aplicable.iloc[0]
                    pct = float(p['descuento_porcentaje'])
                    tope = float(p['tope_reintegro']) if pd.notnull(p['tope_reintegro']) else None
                    
                    descuento_teorico = subtotal * (pct / 100.0)
                    if tope and descuento_teorico > tope:
                        descuento_monto = tope
                        detalle_promo = f"{pct:.0f}% desc. (Tope \${tope:,.0f})"
                    else:
                        descuento_monto = descuento_teorico
                        detalle_promo = f"{pct:.0f}% desc. con {medio_pago}"

                total_final = subtotal - descuento_monto
                resultados.append({
                    'Supermercado': super_name,
                    'Subtotal': subtotal,
                    'Descuento': descuento_monto,
                    'Total Final': total_final,
                    'Promoción': detalle_promo,
                    '_total_num': total_final
                })

            df_resultado = pd.DataFrame(resultados).sort_values(by='_total_num')
            ganador = df_resultado.iloc[0]
            segundo = df_resultado.iloc[1] if len(df_resultado) > 1 else None

            # Tarjeta destacada del ganador
            st.markdown("---")
            st.markdown(f"""
                <div class="card-ganador">
                    <h3>🏆 ¡MEJOR OPCIÓN: {ganador['Supermercado'].upper()}!</h3>
                    <h2>\${ganador['Total Final']:,.2f}</h2>
                    <p>{ganador['Promoción']}</p>
                </div>
            """, unsafe_allow_html=True)

            if segundo is not None:
                ahorro = segundo['_total_num'] - ganador['_total_num']
                if ahorro > 0:
                    st.success(f"💡 **¡Ahorrás \${ahorro:,.2f}** comprando acá en lugar de en {segundo['Supermercado']}!")

            st.markdown("#### 📊 Detalle de Canasta")
            for _, r in df_resultado.iterrows():
                with st.expander(f"📍 {r['Supermercado']} — Total: \${r['Total Final']:,.2f}"):
                    st.write(f"• Subtotal sin promo: \${r['Subtotal']:,.2f}")
                    st.write(f"• Descuento aplicado: \${r['Descuento']:,.2f}")
                    st.write(f"• Beneficio: {r['Promoción']}")
