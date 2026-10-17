"""
Funciones de cálculo para el simulador de retiro Chile.
Todas las funciones son puras (sin efectos secundarios).
"""

def calcular_anos_hasta_retiro(edad_actual, edad_retiro):
    """Calcula los años desde hoy hasta el retiro."""
    return max(0, edad_retiro - edad_actual)


def calcular_anos_de_retiro(edad_retiro, expectativa_vida):
    """Calcula cuántos años durará el retiro."""
    return max(0, expectativa_vida - edad_retiro)


def calcular_pension_afp(sueldo_bruto, anos_cotizados, cotizacion, comision, rentabilidad_anual, anos_hasta_retiro, tope_imponible_uf, valor_uf):
    """
    Estima la pensión mensual de AFP considerando:
    - Ahorro acumulado actual (años ya cotizados)
    - Ahorro futuro (hasta el retiro)
    - Tope imponible
    
    Simplificación: usa fórmula de anualidad para estimar la pensión.
    """
    # Calcular sueldo imponible (con tope)
    tope_imponible_clp = tope_imponible_uf * valor_uf
    sueldo_imponible = min(sueldo_bruto, tope_imponible_clp)
    
    # Ahorro mensual neto (cotización - comisión)
    ahorro_mensual = sueldo_imponible * (cotizacion - comision)
    
    # Capital acumulado actual (simplificado: asumimos rentabilidad histórica)
    if anos_cotizados > 0 and rentabilidad_anual > 0:
        meses_cotizados = anos_cotizados * 12
        r_mensual = (1 + rentabilidad_anual) ** (1/12) - 1
        capital_actual = ahorro_mensual * (((1 + r_mensual) ** meses_cotizados - 1) / r_mensual)
    else:
        capital_actual = 0
    
    # Proyectar capital al retiro
    if anos_hasta_retiro > 0:
        capital_actual_proyectado = capital_actual * ((1 + rentabilidad_anual) ** anos_hasta_retiro)
        
        # Ahorro adicional hasta el retiro
        meses_hasta_retiro = anos_hasta_retiro * 12
        r_mensual = (1 + rentabilidad_anual) ** (1/12) - 1
        if r_mensual > 0:
            capital_futuro = ahorro_mensual * (((1 + r_mensual) ** meses_hasta_retiro - 1) / r_mensual)
        else:
            capital_futuro = ahorro_mensual * meses_hasta_retiro
        
        capital_total_retiro = capital_actual_proyectado + capital_futuro
    else:
        capital_total_retiro = capital_actual
    
    # Calcular pensión mensual usando tabla de mortalidad simplificada
    # Asumimos que el capital debe durar toda la expectativa de vida
    # y aplicamos rentabilidad durante el retiro
    anos_retiro = 20  # Simplificación: 20 años promedio de retiro
    meses_retiro = anos_retiro * 12
    r_mensual = (1 + rentabilidad_anual) ** (1/12) - 1
    
    if r_mensual > 0 and capital_total_retiro > 0:
        # Fórmula de anualidad: PMT = PV * r / (1 - (1+r)^-n)
        pension_mensual = capital_total_retiro * r_mensual / (1 - (1 + r_mensual) ** -meses_retiro)
    else:
        pension_mensual = capital_total_retiro / meses_retiro if meses_retiro > 0 else 0
    
    return max(0, pension_mensual)


def calcular_pension_total(pension_afp, monto_pgu):
    """Suma la pensión de AFP y la PGU."""
    return pension_afp + monto_pgu


def proyectar_gastos_anuales(gastos_config, edad_actual, anos_proyeccion, inflacion):
    """
    Proyecta los gastos año por año considerando:
    - Inflación
    - Gastos de hijos que terminan cuando cumplen edad límite
    - Educación con duración específica
    
    Retorna lista de gastos anuales proyectados.
    """
    gastos_por_ano = []
    
    for ano in range(anos_proyeccion):
        edad_en_ano = edad_actual + ano
        gasto_anual = 0
        
        # Gastos generales (si está activado)
        if gastos_config.get('generales_activo', False):
            gasto_anual += gastos_config.get('generales_mensual', 0) * 12
        
        # Pagos mensuales (si está activado)
        if gastos_config.get('pagos_activo', False):
            gasto_anual += gastos_config.get('pagos_mensual', 0) * 12
        
        # Hijos (solo si no han cumplido la edad límite)
        if gastos_config.get('hijos_activo', False):
            hijos = gastos_config.get('hijos', [])
            for hijo in hijos:
                edad_hijo_en_ano = hijo['edad_actual'] + ano
                edad_limite = hijo.get('edad_limite', 18)
                if edad_hijo_en_ano < edad_limite:
                    gasto_anual += hijo['gasto_mensual'] * 12
        
        # Educación (solo durante los años especificados)
        if gastos_config.get('educacion_activo', False):
            educacion = gastos_config.get('educacion', {})
            anos_restantes = educacion.get('anos_restantes', 0)
            if ano < anos_restantes:
                gasto_anual += educacion.get('costo_anual_uf', 0) * gastos_config.get('valor_uf', 37800)
        
        # Salud
        if gastos_config.get('salud_activo', False):
            salud = gastos_config.get('salud', {})
            gasto_anual += salud.get('mensual', 0) * 12
            
            # Aumentar gasto de salud por edad (1% adicional por cada año sobre 60)
            if edad_en_ano > 60:
                factor_edad = 1 + (edad_en_ano - 60) * 0.01
                gasto_anual += (salud.get('mensual', 0) * 12) * (factor_edad - 1)
        
        # Aplicar inflación acumulada
        gasto_anual_ajustado = gasto_anual * ((1 + inflacion) ** ano)
        
        # Agregar fondo de imprevistos
        pct_imprevistos = gastos_config.get('imprevistos_pct', 0.10)
        if gastos_config.get('imprevistos_activo', False):
            gasto_anual_ajustado *= (1 + pct_imprevistos)
        
        gastos_por_ano.append(gasto_anual_ajustado)
    
    return gastos_por_ano


def calcular_capital_necesario(gastos_anuales_retiro, pension_mensual, rentabilidad_real):
    """
    Calcula el capital necesario al momento del retiro para cubrir
    la brecha entre gastos y pensión.
    
    Usa valor presente de los flujos futuros.
    """
    capital = 0
    pension_anual = pension_mensual * 12
    
    for i, gasto_anual in enumerate(gastos_anuales_retiro):
        brecha_anual = max(0, gasto_anual - pension_anual)
        # Descontar al presente (año 0 del retiro)
        valor_presente = brecha_anual / ((1 + rentabilidad_real) ** i)
        capital += valor_presente
    
    return capital


def calcular_ahorro_mensual_requerido(capital_necesario, anos_hasta_retiro, rentabilidad_real):
    """
    Calcula el ahorro mensual necesario para alcanzar el capital objetivo
    usando la fórmula de cuota con interés compuesto.
    
    PMT = FV * r / ((1+r)^n - 1)
    """
    if anos_hasta_retiro <= 0:
        return capital_necesario / 12  # Ya está en edad de retiro
    
    meses = anos_hasta_retiro * 12
    r_mensual = (1 + rentabilidad_real) ** (1/12) - 1
    
    if r_mensual > 0:
        ahorro_mensual = capital_necesario * r_mensual / ((1 + r_mensual) ** meses - 1)
    else:
        ahorro_mensual = capital_necesario / meses
    
    return ahorro_mensual


def calcular_escenarios(edad_actual, edad_retiro, expectativa_vida, gastos_config, 
                       pension_mensual, inflacion_base, rentabilidad_base):
    """
    Calcula 3 escenarios: conservador, base y optimista.
    Ajusta inflación y rentabilidad para cada uno.
    """
    anos_hasta_retiro = calcular_anos_hasta_retiro(edad_actual, edad_retiro)
    anos_retiro = calcular_anos_de_retiro(edad_retiro, expectativa_vida)
    
    escenarios = {
        'conservador': {'inflacion': inflacion_base + 0.01, 'rentabilidad': rentabilidad_base - 0.015},
        'base': {'inflacion': inflacion_base, 'rentabilidad': rentabilidad_base},
        'optimista': {'inflacion': inflacion_base - 0.005, 'rentabilidad': rentabilidad_base + 0.015}
    }
    
    resultados = {}
    
    for nombre, params in escenarios.items():
        # Proyectar gastos durante el retiro
        gastos_anuales = proyectar_gastos_anuales(
            gastos_config, 
            edad_retiro, 
            anos_retiro, 
            params['inflacion']
        )
        
        # Calcular rentabilidad real
        rentabilidad_real = (1 + params['rentabilidad']) / (1 + params['inflacion']) - 1
        
        # Capital necesario
        capital = calcular_capital_necesario(gastos_anuales, pension_mensual, rentabilidad_real)
        
        # Ahorro mensual requerido
        ahorro_mensual = calcular_ahorro_mensual_requerido(capital, anos_hasta_retiro, rentabilidad_real)
        
        resultados[nombre] = {
            'capital_necesario': capital,
            'ahorro_mensual': ahorro_mensual,
            'gastos_anuales': gastos_anuales,
            'inflacion': params['inflacion'],
            'rentabilidad': params['rentabilidad'],
            'rentabilidad_real': rentabilidad_real
        }
    
    return resultados


def formatear_clp(valor):
    """Formatea un valor en CLP con separador de miles chileno (puntos)."""
    return f"${int(valor):,}".replace(',', '.')


def calcular_distribucion_gastos(gastos_config, valor_uf):
    """
    Calcula la distribución de gastos por categoría para el primer año.
    Retorna un diccionario con categorías y montos anuales.
    """
    distribucion = {}
    
    if gastos_config.get('generales_activo', False):
        distribucion['Gastos Generales'] = gastos_config.get('generales_mensual', 0) * 12
    
    if gastos_config.get('pagos_activo', False):
        distribucion['Pagos Mensuales'] = gastos_config.get('pagos_mensual', 0) * 12
    
    if gastos_config.get('hijos_activo', False):
        total_hijos = sum(h['gasto_mensual'] * 12 for h in gastos_config.get('hijos', []))
        if total_hijos > 0:
            distribucion['Hijos'] = total_hijos
    
    if gastos_config.get('educacion_activo', False):
        educacion = gastos_config.get('educacion', {})
        if educacion.get('anos_restantes', 0) > 0:
            distribucion['Educación'] = educacion.get('costo_anual_uf', 0) * valor_uf
    
    if gastos_config.get('salud_activo', False):
        distribucion['Salud'] = gastos_config.get('salud', {}).get('mensual', 0) * 12
    
    return distribucion
