{#
=====================================================================
  slv_mr_abordajes  ·  Abordajes validos de MetroRiel
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
=====================================================================
#}

select
    'MR:' || trayecto_id as abordaje_id,
    'MR' as modo_codigo,
    'P' || lpad(cast(persona_numero as varchar), 8, '0') as persona_key,
    tarjeta_origen,
    estacion_entrada_key as estacion_key,
    zona_entrada_key as zona_key,
    entrada_ts as abordaje_ts,
    cast(strftime(entrada_ts, '%Y%m%d') as integer) as fecha_key,
    cast(hour(entrada_ts) as integer) as hora_key,
    'ENTRADA' as tipo_abordaje,
    monto_q,
    _hash_fila,
    _lote_id,
    _fila_origen
from {{ ref('mr_viajes_evaluado') }}
where motivo_rechazo_abordaje is null