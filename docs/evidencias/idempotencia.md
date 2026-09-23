# Evidencia de idempotencia

Generada por `python -m orquestacion.verificar_idempotencia`. El flujo completo se corrió dos veces seguidas y después de cada corrida se contaron todas las tablas de todas las capas. La huella es el XOR del hash de cada fila: no depende del orden y cambia si cambia una sola fila.

| | Corrida 1 | Corrida 2 |
|---|---|---|
| Ejecución | `20260922-203051` | `20260922-203106` |
| Inicio | 2026-09-22 20:30:47 | 2026-09-22 20:31:06 |
| Duración | 18.9 s | 15.1 s |
| Tablas medidas | 42 | 42 |
| Filas totales | 6,687,556 | 6,687,556 |

**Resultado: IDEMPOTENTE**

| Capa | Tabla | Filas corrida 1 | Filas corrida 2 | Huella corrida 1 | Huella corrida 2 | Igual |
|---|---|---:|---:|---|---|---|
| bronze | am_estaciones | 14 | 14 | `e96a3d31b8a9430b` | `e96a3d31b8a9430b` | sí |
| bronze | cdc_padron_usuarios | 31,050 | 31,050 | `2e5efd03408b924d` | `2e5efd03408b924d` | sí |
| bronze | metroriel_viajes | 299,100 | 299,100 | `450575a4c66dc22f` | `450575a4c66dc22f` | sí |
| bronze | mr_estaciones | 22 | 22 | `214e60178d15877c` | `214e60178d15877c` | sí |
| bronze | tm_estaciones | 104 | 104 | `f406f053f0161694` | `f406f053f0161694` | sí |
| bronze | transurbano_transacciones | 832,791 | 832,791 | `a652fb2d7baa9de6` | `a652fb2d7baa9de6` | sí |
| bronze | tu_paradas | 328 | 328 | `67fa8553987b6935` | `67fa8553987b6935` | sí |
| seeds | seed_dim_zona | 16 | 16 | `43080dc382ad70ff` | `43080dc382ad70ff` | sí |
| seeds | seed_zona_alias | 32 | 32 | `9d747504ab95dc79` | `9d747504ab95dc79` | sí |
| silver | cdc_cuarentena | 2,768 | 2,768 | `f18d355147e2fb6e` | `f18d355147e2fb6e` | sí |
| silver | cdc_padron_evaluado | 31,050 | 31,050 | `6cd2419caa22ebee` | `6cd2419caa22ebee` | sí |
| silver | cuarentena | 11,360 | 11,360 | `3d71bb1c6ad553bd` | `3d71bb1c6ad553bd` | sí |
| silver | dim_estacion_parada | 468 | 468 | `9c80d3b91448ec8d` | `9c80d3b91448ec8d` | sí |
| silver | dim_fecha | 730 | 730 | `f9186156bd67951f` | `f9186156bd67951f` | sí |
| silver | dim_hora | 24 | 24 | `dcc31d3c6dce54ff` | `dcc31d3c6dce54ff` | sí |
| silver | dim_modo | 4 | 4 | `cf79b810f87f5107` | `cf79b810f87f5107` | sí |
| silver | dim_persona | 49,717 | 49,717 | `6a026bacc1ad8af8` | `6a026bacc1ad8af8` | sí |
| silver | dim_zona | 16 | 16 | `ae65f3ebd54498ee` | `ae65f3ebd54498ee` | sí |
| silver | map_zona_alias | 28 | 28 | `dd5a347e5b510ec4` | `dd5a347e5b510ec4` | sí |
| silver | mr_cuarentena | 3,589 | 3,589 | `f9ee37aa814904cb` | `f9ee37aa814904cb` | sí |
| silver | mr_viajes_evaluado | 299,100 | 299,100 | `24b581d929a73b48` | `24b581d929a73b48` | sí |
| silver | slv_mr_abordajes | 299,100 | 299,100 | `5fe46a2db2565196` | `5fe46a2db2565196` | sí |
| silver | slv_mr_trayectos | 295,511 | 295,511 | `26a668b4a023bc53` | `26a668b4a023bc53` | sí |
| silver | slv_padron_scd2 | 27,428 | 27,428 | `e78a531da6fd64c8` | `e78a531da6fd64c8` | sí |
| silver | slv_tu_abordajes | 786,398 | 786,398 | `46dad40df1851c0f` | `46dad40df1851c0f` | sí |
| silver | slv_tu_transacciones | 827,788 | 827,788 | `f549c7fa3d8d8bfd` | `f549c7fa3d8d8bfd` | sí |
| silver | tu_cuarentena | 5,003 | 5,003 | `3512b9e7ac7eac18` | `3512b9e7ac7eac18` | sí |
| silver | tu_transacciones_evaluado | 832,791 | 832,791 | `90d17d28965bccf2` | `90d17d28965bccf2` | sí |
| silver | usuarios_metroriel | 22,885 | 22,885 | `4e2d76b0b9052aea` | `4e2d76b0b9052aea` | sí |
| silver | usuarios_transurbano | 36,567 | 36,567 | `f8e33342fc388762` | `f8e33342fc388762` | sí |
| gold | dim_estacion | 468 | 468 | `f407707e93f6b602` | `f407707e93f6b602` | sí |
| gold | dim_fecha | 730 | 730 | `f9186156bd67951f` | `f9186156bd67951f` | sí |
| gold | dim_hora | 24 | 24 | `dcc31d3c6dce54ff` | `dcc31d3c6dce54ff` | sí |
| gold | dim_modo | 4 | 4 | `cf79b810f87f5107` | `cf79b810f87f5107` | sí |
| gold | dim_persona | 49,717 | 49,717 | `659632679df3e5d2` | `659632679df3e5d2` | sí |
| gold | dim_zona | 16 | 16 | `ae65f3ebd54498ee` | `ae65f3ebd54498ee` | sí |
| gold | fct_abordaje | 1,085,498 | 1,085,498 | `fd1ccb28538ddf7e` | `fd1ccb28538ddf7e` | sí |
| gold | fct_estado_padron_diario | 559,718 | 559,718 | `40f59db49263767f` | `40f59db49263767f` | sí |
| gold | fct_trayecto_od | 295,511 | 295,511 | `67b0cc74c3a47888` | `67b0cc74c3a47888` | sí |
| reportes | cat_reglas_calidad | 43 | 43 | `bb3a1e9250c3f709` | `bb3a1e9250c3f709` | sí |
| reportes | rpt_calidad | 43 | 43 | `5985b5a15378a6f5` | `5985b5a15378a6f5` | sí |
| reportes | rpt_volumen_por_capa | 2 | 2 | `bf796c38d1ec28b7` | `bf796c38d1ec28b7` | sí |
