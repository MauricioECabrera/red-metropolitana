{#
=====================================================================
  gold_dim_persona  ·  Dimension de persona publicada en Gold
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Sin llave de persona ni tarjeta: la persona se identifica solo con
  persona_sk. Bitacora D-007.
=====================================================================
#}

{{ config(alias='dim_persona') }}

select
    {{ seudonimizar('persona_key') }} as persona_sk,
    tipo_identidad,
    en_padron,
    estado_padron,
    perfil_vigente,
    zona_residencia_key,
    formato_llave_padron,
    versiones_padron
from {{ ref('dim_persona') }}