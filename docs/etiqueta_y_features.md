# Definición de Población, Etiqueta y Diccionario de Features (Fase 2)
**Autor:** Diego de Jesús Urbina Chávez

## 1. Definición de la etiqueta
Positivo (1) si la persona no tiene ningún abordaje válido registrado en la capa Silver de ningún operador en los 30 días exactos que inician en la fecha de corte; de lo contrario es negativo (0).

## 2. Unidad elegida y justificación
Se seleccionó como unidad de análisis a la **Persona** (`persona_key`). Esta decisión mantiene la estrategia de identidad conformada en el Proyecto 1, donde las tarjetas de Transmetro (`TC-`), Transurbano y MetroRiel (`MR`) comparten el identificador numérico subyacente. Esto permite modelar el abandono real de la red metropolitana integrada y previene falsos abandonos en usuarios multimodales que alternan o sustituyen tarjetas.

## 3. Tabla de población
| Corte | Fecha Corte | Población | Positivos (Abandono) | Tasa Positiva | Cuenta Completa |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A** | 2026-07-01 | 59,515 | 7,098 | 0.1193 | 7,098 / 59,515 = 0.1193 |
| **B** | 2026-07-31 | 58,128 | 6,383 | 0.1098 | 6,383 / 58,128 = 0.1098 |
| **C** | 2026-08-30 | 57,711 | NULL | NULL | Etiqueta oculta (producción) |

## 4. Costo de la unidad
Al elegir a la persona como unidad consolidada, el costo metodológico radica en el operador Aerómetro, cuyo sistema emite un hash unidireccional de 12 caracteres que no puede vincularse con las tarjetas del padrón general ni del resto de operadores. Estas entidades se conservan con el prefijo `AM:`, representando usuarios tratados como independientes.

## 5. Diccionario de Features (10 variables)
Todas las variables se calculan estrictamente con eventos anteriores a la fecha de corte en una ventana máxima de 28 días desde la capa Silver:

| Feature | Tipo | Qué mide | Ventana | Origen Silver |
| :--- | :--- | :--- | :--- | :--- |
| `viajes_28d` | INTEGER | Abordajes válidos en los 28 días previos al corte | 28 días | `slv_*_abordajes` |
| `dias_desde_ultimo_viaje` | INTEGER | Días transcurridos entre el último viaje y la fecha de corte | 28 días | `slv_*_abordajes` |
| `gasto_28d_q` | DECIMAL(10,2) | Gasto total acumulado en quetzales en los 28 días previos | 28 días | `slv_*_abordajes` |
| `operadores_distintos_28d` | INTEGER | Cantidad de modos de transporte distintos utilizados | 28 días | `slv_*_abordajes` |
| `abordajes_fin_semana_28d`| INTEGER | Abordajes realizados en días sábado o domingo | 28 días | `slv_*_abordajes` |
| `viajes_7d` | INTEGER | Abordajes válidos en los 7 días previos al corte | 7 días | `slv_*_abordajes` |
| `dias_activos_28d` | INTEGER | Cantidad de días distintos con al menos un viaje | 28 días | `slv_*_abordajes` |
| `gasto_promedio_viaje_q` | DECIMAL(10,2) | Gasto promedio por abordaje (`gasto_28d_q` / `viajes_28d`) | 28 días | `slv_*_abordajes` |
| `proporcion_hora_pico_28d`| DECIMAL(5,4) | Fracción de abordajes en día hábil y franja pico | 28 días | `slv_*_abordajes`, `dim_fecha`, `dim_hora` |
| `tendencia_viajes_14d` | INTEGER | Viajes en los últimos 14 días menos viajes en los 14 días previos | 28 días | `slv_*_abordajes` |

## 6. Auditoría de fuga (Prueba de recorte)
Se ejecutó la prueba de recorte determinista contrastando las tablas generadas con el corte normal versus la recomputación forzada filtrando datos posteriores a la fecha de corte:
* **Corte A (2026-07-01 vs recorte 2026-06-30):** 59,515 filas comparadas. Diferencias encontradas: **0**.
* **Corte B (2026-07-31 vs recorte 2026-07-30):** 58,128 filas comparadas. Diferencias encontradas: **0**.
* **Lista de features que fallaron antes de corregir:** ninguna.