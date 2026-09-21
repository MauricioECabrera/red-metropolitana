{#
=====================================================================
  brz_mr_estaciones  ·  Vista Bronze del catalogo mr_estaciones
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
=====================================================================
#}

select *
from {{ source('lake', 'mr_estaciones') }}