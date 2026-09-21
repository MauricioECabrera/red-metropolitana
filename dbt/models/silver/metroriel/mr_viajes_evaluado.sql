{#
=====================================================================
  mr_viajes_evaluado  ·  Viajes de MetroRiel tipados y evaluados
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Una fila por registro de Bronze, sin excepcion. Cada fila lleva
  el motivo de rechazo por proceso, nulo si es valida:
    motivo_rechazo_abordaje   para slv_mr_abordajes
    motivo_rechazo_trayecto   para slv_mr_trayectos
=====================================================================
#}

with extraido as (
    select
        payload->>'$.trip_id' as trip_id_texto,
        payload->>'$.card' as tarjeta_origen,
        payload->>'$.entry.station' as estacion_entrada_texto,
        payload->>'$.entry.ts' as entrada_ts_texto,
        payload->>'$.exit.station' as estacion_salida_texto,
        payload->>'$.exit.ts' as salida_ts_texto,
        payload->>'$.fare_gtq' as tarifa_texto,
        coalesce(json_type(payload->'$.exit'), 'NULL') = 'NULL' as sin_salida,
        cast(payload as varchar) as payload_original,
        _hash_fila,
        _lote_id,
        _fila_origen,
        _archivo_origen,
        _ingesta_ts
    from {{ ref('brz_metroriel_viajes') }}
),

tipado as (
    select
        e.*,
        try_cast(trip_id_texto as bigint) as trayecto_id,
        try_cast(regexp_extract(tarjeta_origen, '^MR(\d{7})$', 1) as integer) as persona_numero,
        try_cast(entrada_ts_texto as timestamp) as entrada_ts,
        try_cast(salida_ts_texto as timestamp) as salida_ts,
        try_cast(tarifa_texto as decimal(10, 2)) as monto_q,
        'MR:' || try_cast(estacion_entrada_texto as integer) as estacion_entrada_key,
        'MR:' || try_cast(estacion_salida_texto as integer) as estacion_salida_key
    from extraido as e
),

con_estaciones as (
    select
        t.*,
        eo.zona_key as zona_entrada_key,
        eo.km_trazado as km_entrada,
        ed.zona_key as zona_salida_key,
        ed.km_trazado as km_salida,
        row_number() over (partition by t.trayecto_id order by t._lote_id, t._fila_origen) as ocurrencia
    from tipado as t
    left join {{ ref('dim_estacion_parada') }} as eo
        on t.estacion_entrada_key = eo.estacion_key
    left join {{ ref('dim_estacion_parada') }} as ed
        on t.estacion_salida_key = ed.estacion_key
),

evaluado as (
    select
        *,
        case
            when trayecto_id is null then 'identificador_invalido'
            when ocurrencia > 1 then 'duplicado'
            when persona_numero is null then 'tarjeta_invalida'
            when entrada_ts is null then 'fecha_invalida'
            when entrada_ts > _ingesta_ts then 'fecha_futura'
            when zona_entrada_key is null then 'estacion_desconocida'
            when monto_q is null or monto_q < 0 then 'monto_invalido'
        end as motivo_rechazo_abordaje
    from con_estaciones
)

select
    *,
    case
        when motivo_rechazo_abordaje is not null then motivo_rechazo_abordaje
        when sin_salida then 'viaje_sin_salida'
        when salida_ts is null then 'fecha_invalida'
        when salida_ts < entrada_ts then 'salida_anterior_a_entrada'
        when zona_salida_key is null then 'estacion_desconocida'
        when estacion_salida_key = estacion_entrada_key then 'origen_igual_destino'
    end as motivo_rechazo_trayecto
from evaluado