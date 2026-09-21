{#
=====================================================================
  brz_tu_paradas  ·  Vista Bronze del catalogo tu_paradas
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
  Autor: Miguel Eduardo Cabrera Giron
=====================================================================
#}

select *
from {{ source('lake', 'tu_paradas') }}