{#
=====================================================================
  cuarentena  ·  Registros rechazados de todas las fuentes
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Un registro puede aparecer una vez por cada proceso que lo rechaza.
  Cada fuente agrega aqui su bloque union all con las mismas columnas.
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