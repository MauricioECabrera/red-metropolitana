{#
=====================================================================
  cdc_cuarentena  ·  Eventos rechazados del log CDC del padron
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
=====================================================================
#}

select
    'cdc_padron' as fuente,
    'padron' as proceso,
    motivo_rechazo_padron as motivo_rechazo,
    payload_original,
    _hash_fila,
    _lote_id,
    _fila_origen,
    _archivo_origen,
    _ingesta_ts
from {{ ref('cdc_padron_evaluado') }}
where motivo_rechazo_padron is not null