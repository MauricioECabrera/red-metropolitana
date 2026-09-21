{#
=====================================================================
  brz_tm_estaciones  ·  Vista Bronze del catalogo tm_estaciones
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
  Autor: Miguel Eduardo Cabrera Giron
=====================================================================
#}

select *
from {{ source('lake', 'tm_estaciones') }}