{#
=====================================================================
  map_zona_alias  ·  Resolucion de texto de zona a zona_key
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
  Autor: Miguel Eduardo Cabrera Giron
=====================================================================
#}

select distinct
    alias_normalizado,
    zona_key
from {{ ref('seed_zona_alias') }}