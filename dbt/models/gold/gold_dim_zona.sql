{#
=====================================================================
  gold_dim_zona  ·  Dimension conformada publicada en Gold
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
=====================================================================
#}

{{ config(alias='dim_zona') }}

select *
from {{ ref('dim_zona') }}