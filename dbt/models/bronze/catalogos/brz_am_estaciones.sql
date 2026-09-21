{#
=====================================================================
  brz_am_estaciones  ·  Vista Bronze del catalogo am_estaciones
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
  Autor: Miguel Eduardo Cabrera Giron
=====================================================================
#}

select *
from {{ source('lake', 'am_estaciones') }}