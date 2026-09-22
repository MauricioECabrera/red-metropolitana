{#
=====================================================================
  brz_transurbano_transacciones  ·  Vista Bronze de transacciones de
  Transurbano
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
=====================================================================
#}

select *
from {{ source('lake', 'transurbano_transacciones') }}
