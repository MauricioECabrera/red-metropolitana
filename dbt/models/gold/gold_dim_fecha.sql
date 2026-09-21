{#
=====================================================================
  gold_dim_fecha  ·  Dimension conformada publicada en Gold
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
=====================================================================
#}

{{ config(alias='dim_fecha') }}

select *
from {{ ref('dim_fecha') }}