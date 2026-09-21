{#
=====================================================================
  mr_cuarentena  ·  Registros rechazados de MetroRiel
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
=====================================================================
#}

select
    'metroriel' as fuente,
    'abordaje' as proceso,
    motivo_rechazo_abordaje as motivo_rechazo,
    payload_original,
    _hash_fila,
    _lote_id,
    _fila_origen,
    _archivo_origen,
    _ingesta_ts
from {{ ref('mr_viajes_evaluado') }}
where motivo_rechazo_abordaje is not null

union all

select
    'metroriel' as fuente,
    'trayecto' as proceso,
    motivo_rechazo_trayecto as motivo_rechazo,
    payload_original,
    _hash_fila,
    _lote_id,
    _fila_origen,
    _archivo_origen,
    _ingesta_ts
from {{ ref('mr_viajes_evaluado') }}
where motivo_rechazo_trayecto is not null