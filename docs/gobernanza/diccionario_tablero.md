# Diccionario de métricas del tablero

El tablero consulta las tablas del esquema `gold` en DuckDB. Los resultados
corresponden a los datos cargados en la ejecución analizada; cambian si se
regeneran los datos o se aplican filtros.

| Métrica | Fuente Gold | Cálculo | Interpretación y límite |
|---|---|---|---|
| Abordajes por modo | `fct_abordaje`, `dim_modo` | `SUM(cantidad_abordajes)` agrupada por modo | Cuenta validaciones exitosas de entrada. Un transbordo registrado como nuevo abordaje cuenta nuevamente; no equivale a personas distintas. |
| Demanda por zona y hora | `fct_abordaje`, `dim_zona`, `dim_hora` | `SUM(cantidad_abordajes)` por zona de abordaje y hora local | Describe dónde y cuándo se valida una entrada; no indica el destino. |
| Zonas sin servicio | `dim_zona` | Zonas con `tiene_servicio = false` o cero puntos de abordaje | Mide ausencia de puntos registrados en el catálogo; no demuestra que nadie pueda desplazarse desde la zona. |
| Personas multimodales | `fct_abordaje`, `dim_persona`, `dim_modo` | `COUNTD(persona_sk)` para personas con `COUNTD(modo_key) >= 2` en el período analizado | Identifica uso de dos o más modos por una misma identidad vinculada. No prueba un transbordo en un mismo viaje. Aerómetro no puede vincularse con los otros modos; la cifra subestima el uso multimodal real. |
| Demanda de otros modos en el corredor | `fct_abordaje`, `dim_zona`, `dim_modo`, `dim_hora` | `SUM(cantidad_abordajes)` en zonas 1, 6, 8, 12 y 17, excluyendo MetroRiel | Muestra actividad de los otros modos en esas zonas, no conexiones comprobadas con MetroRiel. |
| Trayectos MetroRiel origen–destino | `fct_trayecto_od`, dos roles de `dim_zona` | `SUM(cantidad_trayectos)` por zona de origen y zona de destino | Solo incluye trayectos con entrada y salida válidas. Un viaje sin salida conserva su abordaje, pero no aparece en esta matriz. |

## Cifras de comprobación de esta ejecución

- Abordajes de la red: 1,651,158.
- Personas multimodales identificables: 36,827.
- Abordajes de otros modos en las cinco zonas del corredor: 424,096.
- Trayectos MetroRiel con origen y destino: 295,511.
- Zona 6 → Zona 8: 16,131 trayectos.
- Zona 8 → Zona 6: 15,797 trayectos.
- Par de zonas 6 y 8, ambos sentidos: 31,928 trayectos.

Estos conteos documentan la ejecución revisada, no metas ni valores permanentes.
No se suman abordajes y trayectos: un trayecto MetroRiel también aporta su
entrada a `fct_abordaje`.