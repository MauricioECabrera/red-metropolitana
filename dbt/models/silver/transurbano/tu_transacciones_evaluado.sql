{#
=====================================================================
  tu_transacciones_evaluado  ·  Transacciones de Transurbano tipadas
  y evaluadas
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Una fila por registro de Bronze, sin excepcion. Cada fila lleva
  el motivo de rechazo por proceso, nulo si es valida:
    motivo_rechazo_transaccion   para slv_tu_transacciones

  Transurbano no entrega identificador de transaccion. La llave se
  construye con el lote y el numero de fila de origen, que son
  estables entre corridas porque el lote es la huella del archivo.
=====================================================================
#}

with extraido as (
    select
        fecha as fecha_texto,
        hora as hora_texto,
        num_tarjeta,
        nullif(trim(cod_parada), '') as cod_parada,
        ruta,
        monto_centavos,
        cod_estado,
        cast(to_json(struct_pack(fecha, hora, num_tarjeta, cod_parada, ruta, monto_centavos, cod_estado)) as varchar) as payload_original,
        _hash_fila,
        _lote_id,
        _fila_origen,
        _archivo_origen,
        _ingesta_ts
    from {{ ref('brz_transurbano_transacciones') }}
),

tipado as (
    select
        e.*,
        try_cast(regexp_extract(num_tarjeta, '^(\d{10})$', 1) as integer) as persona_numero,
        try_strptime(fecha_texto || ' ' || hora_texto, '%d/%m/%Y %H:%M:%S') as abordaje_ts,
        'TU:' || cod_parada as estacion_key,
        cast(try_cast(monto_centavos as integer) / 100.0 as decimal(10, 2)) as monto_q,
        row_number() over (partition by _hash_fila order by _lote_id, _fila_origen) as ocurrencia
    from extraido as e
),

con_paradas as (
    select
        t.*,
        p.zona_key
    from tipado as t
    left join {{ ref('dim_estacion_parada') }} as p
        on t.estacion_key = p.estacion_key
)

select
    *,
    case
        when ocurrencia > 1 then 'duplicado'
        when persona_numero is null then 'tarjeta_invalida'
        when abordaje_ts is null then 'fecha_invalida'
        when abordaje_ts > _ingesta_ts then 'fecha_futura'
        when zona_key is null then 'estacion_desconocida'
        when monto_q is null or monto_q < 0 then 'monto_invalido'
    end as motivo_rechazo_transaccion
from con_paradas
