/*
Proyecto 1 - Red Metropolitana de Transporte
Autor: Diego de Jesus Urbina Chavez
*/
with base as (
    select *,
           'TM:' || validacion_id as abordaje_id,
           'TM' as modo_codigo,
           'TM:' || estacion_id as estacion_key,
           try_strptime(fecha_hora, '%Y-%m-%d %H:%M:%S') as abordaje_ts,
           try_cast(tarifa as decimal(10,2)) as monto_q,
           row_number() over (partition by validacion_id order by _lote_id, _fila_origen) as rn
    from {{ ref('brz_transmetro_validaciones') }}
),
evaluado as (
    select b.*,
           'P' || lpad(try_cast(regexp_extract(b.tarjeta, '^TC-(\d{8})$', 1) as integer)::varchar, 8, '0') as persona_key,
           b.tarjeta as tarjeta_origen,
           e.zona_key,
           try_cast(strftime(b.abordaje_ts, '%Y%m%d') as integer) as fecha_key,
           try_cast(strftime(b.abordaje_ts, '%H') as integer) as hora_key,
           b.tipo as tipo_abordaje,
           cast(to_json(struct_pack(
               validacion_id := b.validacion_id, 
               tarjeta := b.tarjeta, 
               estacion_id := b.estacion_id, 
               linea := b.linea, 
               fecha_hora := b.fecha_hora, 
               tarifa := b.tarifa, 
               tipo := b.tipo
           )) as varchar) as payload_original,
           case
               when try_cast(b.validacion_id as integer) is null then 'identificador_invalido'
               when b.rn > 1 then 'duplicado'
               when regexp_matches(b.tarjeta, '^TC-\d{8}$') = false then 'tarjeta_invalida'
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