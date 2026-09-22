{#
=====================================================================
  tu_cuarentena  ·  Registros rechazados de Transurbano
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
=====================================================================
#}

select
    'transurbano' as fuente,
    'transaccion' as proceso,
    motivo_rechazo_transaccion as motivo_rechazo,
    payload_original,
    _hash_fila,
    _lote_id,
    _fila_origen,
    _archivo_origen,
    _ingesta_ts
from {{ ref('tu_transacciones_evaluado') }}
where motivo_rechazo_transaccion is not null
