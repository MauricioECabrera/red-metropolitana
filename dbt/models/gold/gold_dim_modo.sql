{#
=====================================================================
  gold_dim_modo  ·  Dimension conformada publicada en Gold
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
=====================================================================
#}

{{ config(alias='dim_modo') }}

select *
from {{ ref('dim_modo') }}