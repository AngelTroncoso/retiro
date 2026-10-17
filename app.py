"""
Simulador de Plan de Retiro Chile
Aplicación Streamlit para calcular el capital necesario para el retiro.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
from calculos import (
    calcular_anos_hasta_retiro,
    calcular_anos_de_retiro,
    calcular_pension_afp,
    calcular_pension_total,
    calcular_escenarios,
    formatear_clp,
    calcular_distribucion_gastos
)

# Configuración de la página
st.set_page_config(
    page_title="Simulador de Retiro Chile",
    page_icon="💰",
    layout="wide"
)

# Cargar configuración de Chile
@st.cache_data
def cargar_config():
    with open('config_chile.json', 'r', encoding='utf-8') as f:
        return json.load(f)

@st.cache_data
def cargar_comunas():
    return pd.read_csv('comunas_santiago.csv')

config = cargar_config()
df_comunas = cargar_comunas()

# Inicializar session_state
if 'consentimiento' not in st.session_state:
    st.session_state.consentimiento = False

# Función para borrar datos
def borrar_datos():
    for key in list(st.session_state.keys()):
        if key != 'consentimiento':
            del st.session_state[key]
    st.session_state.consentimiento = False
    st.success("✅ Todos tus datos han sido borrados.")

# PANTALLA DE PRIVACIDAD Y CONSENTIMIENTO
if not st.session_state.consentimiento:
    st.title("🔒 Privacidad y Consentimiento")
    
    st.info("""
    ### Tus datos NO se guardan
    
    Esta aplicación respeta tu privacidad:
    
    - ✅ Tus datos se usan **solo mientras tienes la página abierta**
    - ✅ Se borran automáticamente al cerrar la página
    - ✅ NO se guardan en bases de datos
    - ✅ NO se guardan ni se comparten con terceros
    - ✅ NO se usan cookies de seguimiento
    - ✅ NO pedimos datos personales identificables (RUT, nombre, correo)
    
    Tus datos se procesan en el servidor de la aplicación solo durante tu sesión y no se guardan. Cumplimos con el espíritu de la Ley 19.628 
    y la Ley 21.719 de protección de datos personales de Chile.
    """)
    
    consentimiento_check = st.checkbox(
        "✓ Acepto el uso temporal de mis datos para esta simulación",
        value=False
    )
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Continuar", type="primary", disabled=not consentimiento_check):
            st.session_state.consentimiento = True
            st.rerun()
    
    st.divider()
    st.caption("Simulador educativo. No constituye asesoría financiera ni previsional.")
    st.stop()

# APLICACIÓN PRINCIPAL
st.title("💰 Simulador de Plan de Retiro Chile")

# Botón para borrar datos (siempre visible)
with st.sidebar:
    st.markdown("### 🔒 Privacidad")
    if st.button("🗑️ Borrar mis datos ahora", use_container_width=True):
        borrar_datos()
    st.caption("Tus datos solo existen mientras la página está abierta.")
    st.divider()

# Aviso de verificación
st.warning("""
⚠️ **Importante:** Los valores de políticas públicas son referenciales. 
Verifica los valores vigentes en:
- [Superintendencia de Pensiones](https://www.spensiones.cl)
- [SII - Valor UF](https://www.sii.cl)
- [IPS - Pensión Garantizada Universal](https://www.ips.gob.cl)
""")

# TABS PARA ORGANIZAR LA INTERFAZ
tab1, tab2, tab3 = st.tabs(["📋 Datos Personales", "💵 Gastos y Pensión", "📊 Resultados"])

# ========== TAB 1: DATOS PERSONALES ==========
with tab1:
    st.header("Datos Personales y Comuna")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sexo = st.selectbox(
            "Sexo (para edad legal de retiro)",
            ["Hombre", "Mujer"],
            help="Determina la edad legal de jubilación: 65 hombres, 60 mujeres"
        )
        
        edad_actual = st.number_input(
            "Edad actual",
            min_value=18,
            max_value=100,
            value=35,
            help="Tu edad hoy"
        )
        
        edad_retiro_default = config['edad_jubilacion_hombres']['valor'] if sexo == "Hombre" else config['edad_jubilacion_mujeres']['valor']
        edad_retiro = st.number_input(
            "Edad de retiro planeada",
            min_value=edad_actual + 1,
            max_value=100,
            value=edad_retiro_default,
            help="¿A qué edad planeas jubilarte?"
        )
        
        expectativa_vida = st.number_input(
            "Expectativa de vida",
            min_value=edad_retiro + 1,
            max_value=120,
            value=80,
            help="¿Hasta qué edad estimas vivir?"
        )
    
    with col2:
        comuna = st.selectbox(
            "Comuna de Santiago",
            df_comunas['comuna'].tolist(),
            help="Selecciona tu comuna para personalizar las sugerencias"
        )
        
        # Mostrar info de la comuna
        info_comuna = df_comunas[df_comunas['comuna'] == comuna].iloc[0]
        
        st.info(f"""
        **Datos de {comuna}:**
        - Edad promedio: {info_comuna['edad_promedio']} años
        - Mayores de 65: {info_comuna['pct_mayores_65']}%
        - Ingreso hogar referencial: {formatear_clp(info_comuna['ingreso_hogar_referencial'])}
        - Índice costo vida: {info_comuna['costo_vida_indice']}
        
        *Datos referenciales basados en Censo/CASEN/INE*
        """)
    
    # Validaciones
    if edad_retiro <= edad_actual:
        st.error("❌ La edad de retiro debe ser mayor a tu edad actual.")
    if expectativa_vida <= edad_retiro:
        st.error("❌ La expectativa de vida debe ser mayor a la edad de retiro.")

# ========== TAB 2: GASTOS Y PENSIÓN ==========
with tab2:
    st.header("Ingresos y Gastos")
    
    # SECCIÓN: INGRESOS Y PENSIÓN
    st.subheader("💼 Ingresos y Cotizaciones")
    
    col1, col2 = st.columns(2)
    with col1:
        sueldo_bruto = st.number_input(
            "Sueldo bruto mensual actual (CLP)",
            min_value=0,
            value=1000000,
            step=50000,
            help="Tu sueldo antes de descuentos"
        )
        
        anos_cotizados = st.number_input(
            "Años cotizados en AFP",
            min_value=0,
            max_value=int(edad_actual - 18),
            value=min(10, int(edad_actual - 18)),
            help="¿Cuántos años has cotizado?"
        )
    
    with col2:
        st.caption("**Pensión estimada:**")
        st.caption(f"Cotización AFP: {config['cotizacion_afp_obligatoria']['valor']*100:.1f}%")
        st.caption(f"Comisión AFP promedio: {config['comision_afp_promedio']['valor']*100:.2f}%")
        st.caption(f"PGU mensual: {formatear_clp(config['monto_pgu_mensual']['valor'])}")
    
    st.divider()
    
    # SECCIÓN: GASTOS POR CATEGORÍA
    st.subheader("💸 Categorías de Gastos")
    
    # Inicializar configuración de gastos
    gastos_config = {
        'valor_uf': config['valor_uf_referencia']['valor']
    }
    
    # Sugerencia basada en comuna
    indice_costo = info_comuna['costo_vida_indice']
    sugerencia_base = 800000
    sugerencia_comuna = int(sugerencia_base * indice_costo)
    
    st.info(f"💡 Sugerencia para {comuna}: Gasto promedio estimado ~{formatear_clp(sugerencia_comuna)}/mes")
    
    # 1. GASTOS GENERALES
    with st.expander("🏠 Gastos Generales", expanded=True):
        generales_activo = st.checkbox("Incluir gastos generales", value=True, key="gen_check")
        gastos_config['generales_activo'] = generales_activo
        
        if generales_activo:
            col1, col2 = st.columns(2)
            with col1:
                arriendo = st.number_input("Arriendo/Dividendo mensual", 0, value=int(sugerencia_comuna*0.35), step=10000)
                alimentacion = st.number_input("Alimentación mensual", 0, value=int(sugerencia_comuna*0.25), step=10000)
            with col2:
                transporte = st.number_input("Transporte mensual", 0, value=int(sugerencia_comuna*0.15), step=10000)
                servicios = st.number_input("Cuentas básicas (luz, agua, gas, internet)", 0, value=int(sugerencia_comuna*0.10), step=10000)
            
            gastos_config['generales_mensual'] = arriendo + alimentacion + transporte + servicios
            st.success(f"Total gastos generales: {formatear_clp(gastos_config['generales_mensual'])}/mes")
    
    # 2. PAGOS MENSUALES
    with st.expander("💳 Pagos Mensuales (créditos, tarjetas, suscripciones)"):
        pagos_activo = st.checkbox("Incluir pagos mensuales", value=False, key="pag_check")
        gastos_config['pagos_activo'] = pagos_activo
        
        if pagos_activo:
            pagos_mensual = st.number_input(
                "Total de pagos mensuales",
                0,
                value=150000,
                step=10000,
                help="Créditos de consumo, tarjetas, Netflix, Spotify, etc."
            )
            gastos_config['pagos_mensual'] = pagos_mensual
    
    # 3. HIJOS
    with st.expander("👶 Hijos"):
        hijos_activo = st.checkbox("Tengo hijos", value=False, key="hijos_check")
        gastos_config['hijos_activo'] = hijos_activo
        
        if hijos_activo:
            num_hijos = st.number_input("¿Cuántos hijos?", 1, 10, value=1)
            hijos = []
            
            for i in range(num_hijos):
                st.markdown(f"**Hijo {i+1}:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    edad_hijo = st.number_input(f"Edad actual", 0, 50, value=5, key=f"hijo_{i}_edad")
                with col2:
                    gasto_hijo = st.number_input(f"Gasto mensual", 0, value=200000, step=10000, key=f"hijo_{i}_gasto")
                with col3:
                    edad_limite = st.selectbox(f"Termina a los", [18, 25], index=0, key=f"hijo_{i}_limite")
                
                hijos.append({
                    'edad_actual': edad_hijo,
                    'gasto_mensual': gasto_hijo,
                    'edad_limite': edad_limite
                })
            
            gastos_config['hijos'] = hijos
    
    # 4. EDUCACIÓN
    with st.expander("🎓 Educación"):
        educacion_activo = st.checkbox("Incluir gastos de educación", value=False, key="edu_check")
        gastos_config['educacion_activo'] = educacion_activo
        
        if educacion_activo:
            col1, col2 = st.columns(2)
            with col1:
                anos_educacion = st.number_input(
                    "Años restantes de educación",
                    0, 20, value=5,
                    help="¿Cuántos años más de colegio/universidad?"
                )
            with col2:
                costo_uf = st.number_input(
                    "Costo anual en UF",
                    0.0, 500.0, value=100.0, step=10.0,
                    help="Costo anual de matrícula y colegiatura"
                )
            
            gastos_config['educacion'] = {
                'anos_restantes': anos_educacion,
                'costo_anual_uf': costo_uf
            }
            
            costo_clp = costo_uf * config['valor_uf_referencia']['valor']
            st.info(f"Costo anual: {formatear_clp(costo_clp)}")
    
    # 5. SALUD
    with st.expander("🏥 Salud"):
        salud_activo = st.checkbox("Incluir gastos de salud", value=True, key="salud_check")
        gastos_config['salud_activo'] = salud_activo
        
        if salud_activo:
            tipo_salud = st.radio("Sistema de salud", ["Fonasa 7%", "Isapre"])
            
            if tipo_salud == "Fonasa 7%":
                salud_mensual = sueldo_bruto * config['cotizacion_salud']['valor']
                st.info(f"Cotización Fonasa: {formatear_clp(salud_mensual)}/mes")
            else:
                uf_isapre = st.number_input("Plan Isapre (UF)", 0.0, 20.0, value=3.0, step=0.1)
                salud_mensual = uf_isapre * config['valor_uf_referencia']['valor']
                st.info(f"Plan Isapre: {formatear_clp(salud_mensual)}/mes")
            
            medicamentos = st.number_input("Medicamentos mensuales", 0, value=50000, step=10000)
            
            gastos_config['salud'] = {
                'mensual': salud_mensual + medicamentos
            }
            
            if info_comuna['pct_mayores_65'] > 12:
                st.warning(f"⚠️ {comuna} tiene {info_comuna['pct_mayores_65']}% de adultos mayores. Considera un mayor gasto en salud.")
    
    # 6. IMPREVISTOS
    with st.expander("⚠️ Fondo de Imprevistos"):
        imprevistos_activo = st.checkbox("Incluir fondo de emergencia", value=True, key="imp_check")
        gastos_config['imprevistos_activo'] = imprevistos_activo
        
        if imprevistos_activo:
            pct_imprevistos = st.slider(
                "% del gasto total para imprevistos",
                0, 30, 10,
                help="Recomendado: 10% para emergencias"
            )
            gastos_config['imprevistos_pct'] = pct_imprevistos / 100
    
    st.divider()
    
    # SUPUESTOS AVANZADOS
    with st.expander("⚙️ Supuestos Avanzados"):
        st.markdown("**Parámetros económicos:**")
        
        col1, col2 = st.columns(2)
        with col1:
            inflacion = st.number_input(
                "Inflación anual (%)",
                0.0, 20.0,
                value=config['inflacion_anual_defecto']['valor']*100,
                step=0.1,
                help="Meta del Banco Central: 3%"
            ) / 100
            
            valor_uf = st.number_input(
                "Valor UF actual (CLP)",
                10000, 100000,
                value=config['valor_uf_referencia']['valor'],
                step=100
            )
            gastos_config['valor_uf'] = valor_uf
        
        with col2:
            rentabilidad = st.number_input(
                "Rentabilidad real anual (%)",
                0.0, 15.0,
                value=config['rentabilidad_real_defecto']['valor']*100,
                step=0.1,
                help="Promedio histórico AFP: 3.5%"
            ) / 100
            
            comision_afp = st.number_input(
                "Comisión AFP (%)",
                0.0, 5.0,
                value=config['comision_afp_promedio']['valor']*100,
                step=0.01
            ) / 100

# ========== TAB 3: RESULTADOS ==========
with tab3:
    st.header("📊 Resultados de la Simulación")
    
    # Verificar que los datos básicos estén completos
    if edad_retiro <= edad_actual or expectativa_vida <= edad_retiro:
        st.error("⚠️ Por favor completa los datos básicos en la pestaña 'Datos Personales'.")
        st.stop()
    
    # CALCULAR PENSIÓN
    pension_afp = calcular_pension_afp(
        sueldo_bruto,
        anos_cotizados,
        config['cotizacion_afp_obligatoria']['valor'],
        comision_afp,
        rentabilidad,
        calcular_anos_hasta_retiro(edad_actual, edad_retiro),
        config['tope_imponible_uf']['valor'],
        gastos_config['valor_uf']
    )
    
    pension_total = calcular_pension_total(
        pension_afp,
        config['monto_pgu_mensual']['valor']
    )
    
    # CALCULAR ESCENARIOS
    escenarios = calcular_escenarios(
        edad_actual,
        edad_retiro,
        expectativa_vida,
        gastos_config,
        pension_total,
        inflacion,
        rentabilidad
    )
    
    # MOSTRAR MÉTRICAS PRINCIPALES (ESCENARIO BASE)
    st.subheader("💡 Escenario Base")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Capital Necesario",
            formatear_clp(escenarios['base']['capital_necesario']),
            help="Capital que necesitas al momento de jubilarte"
        )
    
    with col2:
        st.metric(
            "Ahorro Mensual Requerido",
            formatear_clp(escenarios['base']['ahorro_mensual']),
            help="Cuánto debes ahorrar cada mes desde hoy"
        )
    
    with col3:
        st.metric(
            "Pensión Mensual Estimada",
            formatear_clp(pension_total),
            help="AFP + PGU"
        )
    
    with col4:
        # Calcular gasto mensual promedio en retiro
        gasto_mensual_promedio = sum(escenarios['base']['gastos_anuales']) / len(escenarios['base']['gastos_anuales']) / 12
        brecha_mensual = max(0, gasto_mensual_promedio - pension_total)
        st.metric(
            "Brecha Mensual Promedio",
            formatear_clp(brecha_mensual),
            help="Diferencia entre gastos y pensión"
        )
    
    st.divider()
    
    # COMPARACIÓN DE ESCENARIOS
    st.subheader("📈 Comparación de Escenarios")
    
    df_escenarios = pd.DataFrame({
        'Escenario': ['Conservador', 'Base', 'Optimista'],
        'Capital Necesario': [
            escenarios['conservador']['capital_necesario'],
            escenarios['base']['capital_necesario'],
            escenarios['optimista']['capital_necesario']
        ],
        'Ahorro Mensual': [
            escenarios['conservador']['ahorro_mensual'],
            escenarios['base']['ahorro_mensual'],
            escenarios['optimista']['ahorro_mensual']
        ],
        'Inflación': [
            f"{escenarios['conservador']['inflacion']*100:.1f}%",
            f"{escenarios['base']['inflacion']*100:.1f}%",
            f"{escenarios['optimista']['inflacion']*100:.1f}%"
        ],
        'Rentabilidad': [
            f"{escenarios['conservador']['rentabilidad']*100:.1f}%",
            f"{escenarios['base']['rentabilidad']*100:.1f}%",
            f"{escenarios['optimista']['rentabilidad']*100:.1f}%"
        ]
    })
    
    st.dataframe(
        df_escenarios.style.format({
            'Capital Necesario': lambda x: formatear_clp(x),
            'Ahorro Mensual': lambda x: formatear_clp(x)
        }),
        hide_index=True,
        use_container_width=True
    )
    
    st.divider()
    
    # GRÁFICOS
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📉 Evolución del Capital en Retiro")
        
        # Simular evolución del capital durante el retiro (escenario base)
        anos_retiro = calcular_anos_de_retiro(edad_retiro, expectativa_vida)
        capital_inicial = escenarios['base']['capital_necesario']
        gastos_anuales = escenarios['base']['gastos_anuales']
        pension_anual = pension_total * 12
        rentabilidad_real = escenarios['base']['rentabilidad_real']
        
        evolucion = [capital_inicial]
        capital_actual = capital_inicial
        
        for i in range(len(gastos_anuales)):
            # Restar gasto del año
            capital_actual -= (gastos_anuales[i] - pension_anual)
            # Aplicar rentabilidad al capital restante
            capital_actual *= (1 + rentabilidad_real)
            evolucion.append(max(0, capital_actual))
        
        df_evolucion = pd.DataFrame({
            'Año de Retiro': range(len(evolucion)),
            'Capital (CLP)': evolucion,
            'Edad': [edad_retiro + i for i in range(len(evolucion))]
        })
        
        fig_evolucion = go.Figure()
        fig_evolucion.add_trace(go.Scatter(
            x=df_evolucion['Edad'],
            y=df_evolucion['Capital (CLP)'],
            mode='lines',
            name='Capital',
            line=dict(color='#1f77b4', width=3),
            fill='tozeroy',
            hovertemplate='Edad: %{x}<br>Capital: $%{y:,.0f}<extra></extra>'
        ))
        
        fig_evolucion.update_layout(
            xaxis_title="Edad",
            yaxis_title="Capital (CLP)",
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig_evolucion, use_container_width=True)
    
    with col2:
        st.subheader("🥧 Distribución de Gastos")
        
        distribucion = calcular_distribucion_gastos(gastos_config, gastos_config['valor_uf'])
        
        if distribucion:
            df_dist = pd.DataFrame({
                'Categoría': list(distribucion.keys()),
                'Monto Anual': list(distribucion.values())
            })
            
            fig_pie = px.pie(
                df_dist,
                values='Monto Anual',
                names='Categoría',
                hole=0.4,
                height=400
            )
            
            fig_pie.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='%{label}<br>%{value:,.0f} CLP<br>%{percent}<extra></extra>'
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No hay gastos configurados para mostrar.")
    
    st.divider()
    
    # COMPARACIÓN CON COMUNA
    st.subheader(f"📍 Comparación con {comuna}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Tu ingreso actual",
            formatear_clp(sueldo_bruto)
        )
    
    with col2:
        st.metric(
            f"Ingreso promedio en {comuna}",
            formatear_clp(info_comuna['ingreso_hogar_referencial'])
        )
    
    with col3:
        dif_pct = ((sueldo_bruto - info_comuna['ingreso_hogar_referencial']) / info_comuna['ingreso_hogar_referencial'] * 100)
        st.metric(
            "Diferencia",
            f"{dif_pct:+.1f}%"
        )
    
    st.divider()
    
    # RECOMENDACIONES PERSONALIZADAS
    st.subheader("💡 Recomendaciones Personalizadas")
    
    recomendaciones = []
    
    # Recomendación 1: Ahorro vs. ingreso
    pct_ahorro = (escenarios['base']['ahorro_mensual'] / sueldo_bruto * 100) if sueldo_bruto > 0 else 0
    if pct_ahorro > 30:
        recomendaciones.append(
            f"🔴 **Ahorro muy alto:** Necesitas ahorrar {pct_ahorro:.1f}% de tu sueldo ({formatear_clp(escenarios['base']['ahorro_mensual'])}). "
            f"Considera: reducir gastos, aumentar ingresos o revisar la edad de retiro."
        )
    elif pct_ahorro > 20:
        recomendaciones.append(
            f"🟡 **Ahorro moderado:** Necesitas ahorrar {pct_ahorro:.1f}% de tu sueldo. Es alto pero alcanzable con disciplina."
        )
    else:
        recomendaciones.append(
            f"🟢 **Ahorro razonable:** Necesitas ahorrar {pct_ahorro:.1f}% de tu sueldo. Es una meta alcanzable."
        )
    
    # Recomendación 2: Años de cotización
    anos_hasta_retiro = calcular_anos_hasta_retiro(edad_actual, edad_retiro)
    if anos_hasta_retiro < 10:
        recomendaciones.append(
            f"⏰ **Poco tiempo:** Solo tienes {anos_hasta_retiro} años hasta el retiro. Considera ahorros más agresivos o postergar la jubilación."
        )
    
    # Recomendación 3: Comuna con alto % adultos mayores
    if info_comuna['pct_mayores_65'] > 12:
        recomendaciones.append(
            f"🏥 **Salud en {comuna}:** Tu comuna tiene {info_comuna['pct_mayores_65']}% de adultos mayores. "
            f"Asegúrate de incluir gastos de salud adecuados (medicamentos, controles, seguros complementarios)."
        )
    
    # Recomendación 4: Brecha pensión-gastos
    if brecha_mensual > pension_total:
        recomendaciones.append(
            f"📉 **Brecha importante:** Tu brecha mensual ({formatear_clp(brecha_mensual)}) es mayor que tu pensión estimada. "
            f"Tu capital de retiro se agotará rápido. Considera reducir gastos o aumentar tus años de cotización."
        )
    
    # Recomendación 5: Diversificación
    recomendaciones.append(
        f"🎯 **Diversifica:** No dependas solo de la AFP. Considera APV (Ahorro Previsional Voluntario) "
        f"con beneficios tributarios, fondos mutuos o inversiones en instrumentos de renta fija."
    )
    
    # Mostrar recomendaciones
    for rec in recomendaciones:
        st.markdown(rec)
    
    st.divider()
    
    # DISCLAIMER FINAL
    st.warning("""
    ### ⚖️ Disclaimer Legal
    
    Este simulador es una **herramienta educativa** y los resultados son **estimaciones aproximadas**.
    
    **NO constituye:**
    - Asesoría financiera
    - Asesoría previsional
    - Recomendación de inversión
    - Garantía de rentabilidad futura
    
    **Recomendamos:**
    - Consultar con un asesor previsional certificado
    - Verificar los valores actuales en organismos oficiales (SP, IPS, SII)
    - Revisar tu situación particular con un planificador financiero
    
    Los cálculos asumen escenarios simplificados y no consideran todos los factores personales, 
    legales y tributarios que pueden afectar tu retiro real.
    """)

# Footer
st.divider()
st.caption("Simulador de Plan de Retiro Chile | Datos referenciales basados en fuentes públicas | Octubre 2026")
