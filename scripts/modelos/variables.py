"""
=====================================================================
  variables.py · Variables compartidas del modelo de abandono
  Proyecto 2 · Ciencia de Datos · Red Metropolitana
  Autor: Adrian

  Define las diez variables predictivas del contrato de features.
  El identificador, la fecha de corte y la etiqueta no son predictores.

  Ejecutar desde la raiz del repositorio:
    python -c "from scripts.modelos.variables import VARIABLES; print(VARIABLES)"
=====================================================================
"""

VARIABLES = [
    "viajes_28d",
    "dias_desde_ultimo_viaje",
    "gasto_28d_q",
    "operadores_distintos_28d",
    "abordajes_fin_semana_28d",
    "viajes_7d",
    "dias_activos_28d",
    "gasto_promedio_viaje_q",
    "proporcion_hora_pico_28d",
    "tendencia_viajes_14d",
]