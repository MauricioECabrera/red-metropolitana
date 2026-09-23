/*
Proyecto 1 - Red Metropolitana de Transporte
Autor: Diego de Jesus Urbina Chavez
*/
with base as (
    select *,
           'AM:' || boarding_id as abordaje_id,
           'AM' as modo_codigo,
           'AM:' || station_code as estacion_key,
           try_cast(replace(replace(timestamp_utc, 'T', ' '), 'Z', '') as timestamp) - interval 6 hour as abordaje_ts,
           try_cast(fare as decimal(10,2)) as monto_q,
           row_number() over (partition by boarding_id order by _lote_id, _fila_origen) as rn
    from {{ ref('brz_aerometro_boardings') }}
),
evaluado as (
    select b.*,
           'AM:' || b.user_hash as persona_key,
           b.user_hash as tarjeta_origen,
           e.zona_key,
           try_cast(strftime(b.abordaje_ts, '%Y%m%d') as integer) as fecha_key,
           try_cast(strftime(b.abordaje_ts, '%H') as integer) as hora_key,
           'ENTRADA' as tipo_abordaje,
           cast(to_json(struct_pack(
               boarding_id := b.boarding_id, 
               user_hash := b.user_hash, 
               station_code := b.station_code, 
               axis := b.axis, 
               timestamp_utc := b.timestamp_utc, 
               cabin_number := b.cabin_number, 
               fare := b.fare
           )) as varchar) as payload_original,
           case
               when try_cast(b.boarding_id as integer) is null then 'identificador_invalido'
               when b.rn > 1 then 'duplicado'
               when regexp_matches(b.user_hash, '^[0-9a-f]{12}$') = false then 'tarjeta_invalida'
               when b.abordaje_ts is null then 'fecha_invalida'
               when b.abordaje_ts > try_cast(b._ingesta_ts as timestamp) then 'fecha_futura'
               when e.zona_key is null then 'estacion_desconocida'
               when b.monto_q is null or b.monto_q < 0 then 'monto_invalido'
               else null
           end as motivo_rechazo_abordaje
    from base b
    left join {{ ref('dim_estacion_parada') }} e on b.estacion_key = e.estacion_key
)
select * from evaluado