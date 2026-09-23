/*
Proyecto 1 - Red Metropolitana de Transporte
Autor: Diego de Jesus Urbina Chavez
*/
select
    'transmetro' as fuente,
    'abordaje' as proceso,
    motivo_rechazo_abordaje as motivo_rechazo,
    payload_original,
    _hash_fila,
    _lote_id,
    _fila_origen,
    _archivo_origen,
    _ingesta_ts
from {{ ref('tm_validaciones_evaluado') }}
where motivo_rechazo_abordaje is not null