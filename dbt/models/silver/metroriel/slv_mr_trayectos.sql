{#
=====================================================================
  slv_mr_trayectos  ·  Trayectos completos validos de MetroRiel
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
=====================================================================
#}

select
    'MR:' || trayecto_id as trayecto_id,
    'P' || lpad(cast(persona_numero as varchar), 8, '0') as persona_key,
    tarjeta_origen,
    estacion_entrada_key as estacion_origen_key,
    estacion_salida_key as estacion_destino_key,
    zona_entrada_key as zona_origen_key,
    zona_salida_key as zona_destino_key,
    entrada_ts,
    salida_ts,
    cast(strftime(entrada_ts, '%Y%m%d') as integer) as fecha_key,
    cast(hour(entrada_ts) as integer) as hora_key,
    datediff('second', entrada_ts, salida_ts) as duracion_s,
    round(abs(km_salida - km_entrada), 2) as distancia_km,
    monto_q,
    _hash_fila,
    _lote_id,
    _fila_origen
from {{ ref('mr_viajes_evaluado') }}
where motivo_rechazo_trayecto is null