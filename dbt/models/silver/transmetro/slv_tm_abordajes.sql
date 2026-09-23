/*
Proyecto 1 - Red Metropolitana de Transporte
Autor: Diego de Jesus Urbina Chavez
*/
select
    abordaje_id,
    modo_codigo,
    persona_key,
    tarjeta_origen,
    estacion_key,
    zona_key,
    abordaje_ts,
    fecha_key,
    hora_key,
    tipo_abordaje,
    monto_q,
    _hash_fila,
    _lote_id,
    _fila_origen
from {{ ref('tm_validaciones_evaluado') }}
where motivo_rechazo_abordaje is null