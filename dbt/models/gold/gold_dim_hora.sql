{#
=====================================================================
  gold_dim_hora  ·  Dimension conformada publicada en Gold
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
=====================================================================
#}

{{ config(alias='dim_hora') }}

select *
from {{ ref('dim_hora') }}