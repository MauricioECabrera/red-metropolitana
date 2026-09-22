{#
=====================================================================
  slv_tu_abordajes  ·  Abordajes validos de Transurbano
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Solo las transacciones con validacion exitosa, segun el grano de
  fct_abordaje declarado en D-001. Las transacciones con estado 7 y 9
  quedan en slv_tu_transacciones y no entran a Gold.
=====================================================================
#}

select
    transaccion_id as abordaje_id,
    'TU' as modo_codigo,
    persona_key,
    tarjeta_origen,
    estacion_key,
    zona_key,
    abordaje_ts,
    fecha_key,
    hora_key,
    'ENTRADA' as tipo_abordaje,
    monto_q,
    _hash_fila,
    _lote_id,
    _fila_origen
from {{ ref('slv_tu_transacciones') }}
where es_abordaje_exitoso
