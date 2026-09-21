{#
=====================================================================
  brz_cdc_padron_usuarios  ·  Vista Bronze del log CDC del padron
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
=====================================================================
#}

select *
from {{ source('lake', 'cdc_padron_usuarios') }}