# Evidencia de idempotencia

Generada por `python -m orquestacion.verificar_idempotencia`. El flujo completo se corrió dos veces seguidas y después de cada corrida se contaron todas las tablas de todas las capas. La huella es el XOR del hash de cada fila: no depende del orden y cambia si cambia una sola fila.

| | Corrida 1 | Corrida 2 |
|---|---|---|
| Ejecución | `20260920-232156` | `20260920-232207` |
| Inicio | 2026-09-20 23:21:52 | 2026-09-20 23:22:07 |
| Duración | 14.1 s | 9.1 s |
| Tablas medidas | 32 | 32 |
| Filas totales | 2,524,678 | 2,524,678 |

**Resultado: IDEMPOTENTE**

| Capa | Tabla | Filas corrida 1 | Filas corrida 2 | Huella corrida 1 | Huella corrida 2 | Igual |
|---|---|---:|---:|---|---|---|
| bronze | am_estaciones | 14 | 14 | `e96a3d31b8a9430b` | `e96a3d31b8a9430b` | sí |
| bronze | cdc_padron_usuarios | 31,050 | 31,050 | `2e5efd03408b924d` | `2e5efd03408b924d` | sí |
| bronze | metroriel_viajes | 299,100 | 299,100 | `450575a4c66dc22f` | `450575a4c66dc22f` | sí |
| bronze | mr_estaciones | 22 | 22 | `214e60178d15877c` | `214e60178d15877c` | sí |
| bronze | tm_estaciones | 104 | 104 | `f406f053f0161694` | `f406f053f0161694` | sí |
| bronze | tu_paradas | 328 | 328 | `67fa8553987b6935` | `67fa8553987b6935` | sí |
| seeds | seed_dim_zona | 16 | 16 | `43080dc382ad70ff` | `43080dc382ad70ff` | sí |
| seeds | seed_zona_alias | 32 | 32 | `9d747504ab95dc79` | `9d747504ab95dc79` | sí |
| silver | cdc_cuarentena | 2,768 | 2,768 | `f18d355147e2fb6e` | `f18d355147e2fb6e` | sí |
| silver | cdc_padron_evaluado | 31,050 | 31,050 | `6cd2419caa22ebee` | `6cd2419caa22ebee` | sí |
| silver | cuarentena | 6,357 | 6,357 | `086302fbc6abffa5` | `086302fbc6abffa5` | sí |
| silver | dim_estacion_parada | 468 | 468 | `9c80d3b91448ec8d` | `9c80d3b91448ec8d` | sí |
| silver | dim_fecha | 730 | 730 | `f9186156bd67951f` | `f9186156bd67951f` | sí |
| silver | dim_hora | 24 | 24 | `dcc31d3c6dce54ff` | `dcc31d3c6dce54ff` | sí |
| silver | dim_modo | 4 | 4 | `cf79b810f87f5107` | `cf79b810f87f5107` | sí |
| silver | dim_persona | 36,134 | 36,134 | `a3b60a3d0032c09d` | `a3b60a3d0032c09d` | sí |
| silver | dim_zona | 16 | 16 | `ae65f3ebd54498ee` | `ae65f3ebd54498ee` | sí |
| silver | map_zona_alias | 28 | 28 | `dd5a347e5b510ec4` | `dd5a347e5b510ec4` | sí |
| silver | mr_cuarentena | 3,589 | 3,589 | `f9ee37aa814904cb` | `f9ee37aa814904cb` | sí |
| silver | mr_viajes_evaluado | 299,100 | 299,100 | `24b581d929a73b48` | `24b581d929a73b48` | sí |
| silver | slv_mr_abordajes | 299,100 | 299,100 | `5fe46a2db2565196` | `5fe46a2db2565196` | sí |
| silver | slv_mr_trayectos | 295,511 | 295,511 | `26a668b4a023bc53` | `26a668b4a023bc53` | sí |
| silver | slv_padron_scd2 | 27,428 | 27,428 | `e78a531da6fd64c8` | `e78a531da6fd64c8` | sí |
| gold | dim_estacion | 468 | 468 | `f407707e93f6b602` | `f407707e93f6b602` | sí |
| gold | dim_fecha | 730 | 730 | `f9186156bd67951f` | `f9186156bd67951f` | sí |
| gold | dim_hora | 24 | 24 | `dcc31d3c6dce54ff` | `dcc31d3c6dce54ff` | sí |
| gold | dim_modo | 4 | 4 | `cf79b810f87f5107` | `cf79b810f87f5107` | sí |
| gold | dim_persona | 36,134 | 36,134 | `91117d84d19624c8` | `91117d84d19624c8` | sí |
| gold | dim_zona | 16 | 16 | `ae65f3ebd54498ee` | `ae65f3ebd54498ee` | sí |
| gold | fct_abordaje | 299,100 | 299,100 | `ca61012534b00a10` | `ca61012534b00a10` | sí |
| gold | fct_estado_padron_diario | 559,718 | 559,718 | `40f59db49263767f` | `40f59db49263767f` | sí |
| gold | fct_trayecto_od | 295,511 | 295,511 | `67b0cc74c3a47888` | `67b0cc74c3a47888` | sí |
