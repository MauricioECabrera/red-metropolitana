# Evidencia de idempotencia

Generada por `python -m orquestacion.verificar_idempotencia`. El flujo completo se corrió dos veces seguidas y después de cada corrida se contaron todas las tablas de todas las capas. La huella es el XOR del hash de cada fila: no depende del orden y cambia si cambia una sola fila.

| | Corrida 1 | Corrida 2 |
|---|---|---|
| Ejecución | `20261108-134211` | `20261108-134330` |
| Inicio | 2026-11-08 13:42:07 | 2026-11-08 13:43:30 |
| Duración | 82.0 s | 76.1 s |
| Tablas medidas | 55 | 55 |
| Filas totales | 19,712,750 | 19,712,750 |

**Resultado: IDEMPOTENTE**

| Capa | Tabla | Filas corrida 1 | Filas corrida 2 | Huella corrida 1 | Huella corrida 2 | Igual |
|---|---|---:|---:|---|---|---|
| bronze | aerometro_boardings | 387,053 | 387,053 | `985a68d41e29b171` | `985a68d41e29b171` | sí |
| bronze | am_estaciones | 14 | 14 | `365deb3452d90563` | `365deb3452d90563` | sí |
| bronze | cdc_padron_usuarios | 77,636 | 77,636 | `e15d864a3808c474` | `e15d864a3808c474` | sí |
| bronze | metroriel_viajes | 590,844 | 590,844 | `e04a5d999a03181e` | `e04a5d999a03181e` | sí |
| bronze | mr_estaciones | 22 | 22 | `8b1b067228ef0dd4` | `8b1b067228ef0dd4` | sí |
| bronze | tm_estaciones | 104 | 104 | `b36a7d0f5e195fac` | `b36a7d0f5e195fac` | sí |
| bronze | transmetro_validaciones | 713,786 | 713,786 | `e4b0d8d959cccff1` | `e4b0d8d959cccff1` | sí |
| bronze | transurbano_transacciones | 1,635,788 | 1,635,788 | `d14d76c5256f4d06` | `d14d76c5256f4d06` | sí |
| bronze | tu_paradas | 328 | 328 | `ec5cdf924eb47691` | `ec5cdf924eb47691` | sí |
| seeds | seed_dim_zona | 16 | 16 | `43080dc382ad70ff` | `43080dc382ad70ff` | sí |
| seeds | seed_zona_alias | 32 | 32 | `9d747504ab95dc79` | `9d747504ab95dc79` | sí |
| silver | am_boardings_evaluado | 387,053 | 387,053 | `56a4163ef54b4e2f` | `56a4163ef54b4e2f` | sí |
| silver | am_cuarentena | 0 | 0 | `vacia` | `vacia` | sí |
| silver | cdc_cuarentena | 5,821 | 5,821 | `c5db35a110231a76` | `c5db35a110231a76` | sí |
| silver | cdc_padron_evaluado | 77,636 | 77,636 | `6bbb4715de4a121a` | `6bbb4715de4a121a` | sí |
| silver | cuarentena | 24,735 | 24,735 | `e5f40d3bfde518d8` | `e5f40d3bfde518d8` | sí |
| silver | dim_estacion_parada | 468 | 468 | `9c80d3b91448ec8d` | `9c80d3b91448ec8d` | sí |
| silver | dim_fecha | 730 | 730 | `f9186156bd67951f` | `f9186156bd67951f` | sí |
| silver | dim_hora | 24 | 24 | `dcc31d3c6dce54ff` | `dcc31d3c6dce54ff` | sí |
| silver | dim_modo | 4 | 4 | `cf79b810f87f5107` | `cf79b810f87f5107` | sí |
| silver | dim_persona | 94,734 | 94,734 | `41ffc38697584442` | `41ffc38697584442` | sí |
| silver | dim_zona | 16 | 16 | `ae65f3ebd54498ee` | `ae65f3ebd54498ee` | sí |
| silver | map_zona_alias | 28 | 28 | `dd5a347e5b510ec4` | `dd5a347e5b510ec4` | sí |
| silver | mr_cuarentena | 7,099 | 7,099 | `3cf5707ed937fa79` | `3cf5707ed937fa79` | sí |
| silver | mr_viajes_evaluado | 590,844 | 590,844 | `368b632b53163df8` | `368b632b53163df8` | sí |
| silver | slv_am_abordajes | 387,053 | 387,053 | `b4f76df3083d432f` | `b4f76df3083d432f` | sí |
| silver | slv_mr_abordajes | 590,844 | 590,844 | `6b0c6309a71b1714` | `6b0c6309a71b1714` | sí |
| silver | slv_mr_trayectos | 583,745 | 583,745 | `0bdf4489bcbfb589` | `0bdf4489bcbfb589` | sí |
| silver | slv_padron_scd2 | 70,902 | 70,902 | `f4fc27618d7298b9` | `f4fc27618d7298b9` | sí |
| silver | slv_tm_abordajes | 711,684 | 711,684 | `2ce2ab7a0042ce1d` | `2ce2ab7a0042ce1d` | sí |
| silver | slv_tu_abordajes | 1,549,718 | 1,549,718 | `a6f988d07e1ce03a` | `a6f988d07e1ce03a` | sí |
| silver | slv_tu_transacciones | 1,626,075 | 1,626,075 | `9ec7081042aa799e` | `9ec7081042aa799e` | sí |
| silver | tm_cuarentena | 2,102 | 2,102 | `037dbf367375b74d` | `037dbf367375b74d` | sí |
| silver | tm_validaciones_evaluado | 713,786 | 713,786 | `4b36119d86848f49` | `4b36119d86848f49` | sí |
| silver | tu_cuarentena | 9,713 | 9,713 | `1fa7f7d247844f9a` | `1fa7f7d247844f9a` | sí |
| silver | tu_transacciones_evaluado | 1,635,788 | 1,635,788 | `90213085753f2644` | `90213085753f2644` | sí |
| silver | usuarios_aerometro | 16,930 | 16,930 | `4c0d73b931fbc10b` | `4c0d73b931fbc10b` | sí |
| silver | usuarios_metroriel | 26,414 | 26,414 | `ff78f815ec01ba22` | `ff78f815ec01ba22` | sí |
| silver | usuarios_transurbano | 45,685 | 45,685 | `740bb41c6b09d255` | `740bb41c6b09d255` | sí |
| gold | dim_estacion | 468 | 468 | `f407707e93f6b602` | `f407707e93f6b602` | sí |
| gold | dim_fecha | 730 | 730 | `f9186156bd67951f` | `f9186156bd67951f` | sí |
| gold | dim_hora | 24 | 24 | `dcc31d3c6dce54ff` | `dcc31d3c6dce54ff` | sí |
| gold | dim_modo | 4 | 4 | `cf79b810f87f5107` | `cf79b810f87f5107` | sí |
| gold | dim_persona | 94,734 | 94,734 | `c4fb91e69e225508` | `c4fb91e69e225508` | sí |
| gold | dim_zona | 16 | 16 | `ae65f3ebd54498ee` | `ae65f3ebd54498ee` | sí |
| gold | fct_abordaje | 3,239,299 | 3,239,299 | `e830c7375954f275` | `e830c7375954f275` | sí |
| gold | fct_estado_padron_diario | 2,628,493 | 2,628,493 | `4499a9b804e02595` | `4499a9b804e02595` | sí |
| gold | fct_trayecto_od | 583,745 | 583,745 | `7549af7e9f336504` | `7549af7e9f336504` | sí |
| features | features_corte | 175,354 | 175,354 | `5f4ca5a8c47a0e7c` | `5f4ca5a8c47a0e7c` | sí |
| features | features_persona | 73,831 | 73,831 | `15bded768b6bfe4f` | `15bded768b6bfe4f` | sí |
| features | poblacion | 175,354 | 175,354 | `e6e8755f972aed05` | `e6e8755f972aed05` | sí |
| features | unidad_tarjetas | 175,354 | 175,354 | `fb56ee4689088155` | `fb56ee4689088155` | sí |
| reportes | cat_reglas_calidad | 43 | 43 | `bb3a1e9250c3f709` | `bb3a1e9250c3f709` | sí |
| reportes | rpt_calidad | 43 | 43 | `c1048f5e8b9919fb` | `c1048f5e8b9919fb` | sí |
| reportes | rpt_volumen_por_capa | 4 | 4 | `3d38a83c099d073f` | `3d38a83c099d073f` | sí |
