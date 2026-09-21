{#
=====================================================================
  gold_dim_estacion  ·  Dimension conformada publicada en Gold
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
=====================================================================
#}

{{ config(alias='dim_estacion') }}

select
    estacion_key,
    modo_key,
    modo_codigo,
    codigo_origen,
    nombre_punto,
    linea_ruta,
    zona_key,
    latitud,
    longitud,
    km_trazado
from {{ ref('dim_estacion_parada') }}