{#
=====================================================================
  brz_metroriel_viajes  ·  Vista Bronze de viajes de MetroRiel
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
=====================================================================
#}

select *
from {{ source('lake', 'metroriel_viajes') }}