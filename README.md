# Simulador de Plan de Retiro Chile

Aplicación web desarrollada con Streamlit para calcular el capital necesario para el retiro en Chile, considerando edad, gastos proyectados, pensión AFP + PGU y personalización por comuna de Santiago.

## 🔒 Privacidad

Tus datos **NO se almacenan**. Se usan únicamente durante tu sesión activa y se borran al cerrar la página. No se guardan en bases de datos, no se envían a servidores externos y no se utilizan cookies de seguimiento.

## ⚖️ Disclaimer

**Simulador educativo.** No constituye asesoría financiera ni previsional. Consulta con un asesor previsional certificado para tu situación particular.

## 🚀 Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📋 Parámetros legales

Los valores de cotizaciones, PGU, edades de jubilación y otros parámetros están en `config_chile.json`. Verifica los valores vigentes en:
- [Superintendencia de Pensiones](https://www.spensiones.cl)
- [SII - Valor UF](https://www.sii.cl)
- [IPS - Pensión Garantizada Universal](https://www.ips.gob.cl)

## 📊 Características

- Cálculo de capital necesario y ahorro mensual requerido
- 3 escenarios: conservador, base y optimista
- Personalización por comuna de Santiago (52 comunas)
- Categorías de gastos: generales, pagos, hijos, educación, salud, imprevistos
- Gráficos interactivos de evolución del capital
- Recomendaciones personalizadas según perfil

---

Desarrollado con ❤️ para ayudar a planificar el retiro en Chile
