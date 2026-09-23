# Diccionario de Features
**Fecha de corte declarada:** 2026-07-15

**Propósito analítico:**
Esta tabla permite predecir qué usuarios están en riesgo de abandonar la red de transporte (fuga de usuarios o *churn*), permitiendo a la Agencia dirigir campañas de retención específicas antes de perderlos.

| Columna | Tipo | Definición |
| :--- | :--- | :--- |
| `persona_sk` | VARCHAR | Identificador seudonimizado de la persona. |
| `tipo_identidad` | VARCHAR | `vinculada` si proviene de tarjeta de transporte, `solo_aerometro` si es un hash. |
| `abordajes_7d` | BIGINT | Abordajes en los últimos 7 días hasta el corte. |
| `abordajes_30d` | BIGINT | Abordajes en los últimos 30 días hasta el corte. |
| `abordajes_90d` | BIGINT | Abordajes en los últimos 90 días hasta el corte. |
| `abordajes_total` | BIGINT | Total de abordajes históricos hasta el corte. |
| `dias_activos` | BIGINT | Días distintos en los que la persona tuvo al menos un abordaje. |
| `modos_distintos` | BIGINT | Cantidad de modos de transporte distintos usados por la persona. |
| `modo_mas_usado` | VARCHAR | Código de modo con mayor cantidad de abordajes (desempate alfabético). |
| `dias_desde_ultimo_abordaje` | BIGINT | Días transcurridos entre la fecha del último abordaje y el corte. |
| `proporcion_hora_pico` | DECIMAL | Ratio de abordajes en hora pico sobre abordajes totales (0 a 1). |
| `zona_origen_mas_frecuente` | VARCHAR | Código de la zona donde la persona aborda con mayor frecuencia. |
| `gasto_total_q` | DECIMAL | Suma histórica del monto pagado en quetzales. |
| `gasto_promedio_q` | DECIMAL | Gasto promedio por viaje en quetzales. |