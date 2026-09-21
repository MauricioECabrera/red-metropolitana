{#
=====================================================================
  dim_zona  ·  Dimension conformada de zona
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
  Autor: Miguel Eduardo Cabrera Giron
=====================================================================
#}

select
    zona_key,
    zona_nombre,
    tipo_division,
    municipio
from {{ ref('seed_dim_zona') }}