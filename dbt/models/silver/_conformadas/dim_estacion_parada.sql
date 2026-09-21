{#
=====================================================================
  dim_estacion_parada  ·  Dimension conformada de puntos de abordaje
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
=====================================================================
#}

with tm as (
    select
        'TM' as modo_codigo,
        estacion_id as codigo_origen,
        nombre as nombre_punto,
        linea as linea_ruta,
        zona as zona_origen,
        try_cast(lat as double) as latitud,
        try_cast(lon as double) as longitud,
        cast(null as double) as km_trazado,
        _lote_id
    from {{ ref('brz_tm_estaciones') }}
    qualify _ingesta_ts = max(_ingesta_ts) over ()
),

tu as (
    select
        'TU' as modo_codigo,
        cod_parada as codigo_origen,
        descripcion as nombre_punto,
        ruta as linea_ruta,
        sector as zona_origen,
        cast(null as double) as latitud,
        cast(null as double) as longitud,
        cast(null as double) as km_trazado,
        _lote_id
    from {{ ref('brz_tu_paradas') }}
    qualify _ingesta_ts = max(_ingesta_ts) over ()
),

mr as (
    select
        'MR' as modo_codigo,
        id_estacion as codigo_origen,
        nombre_estacion as nombre_punto,
        'MetroRiel' as linea_ruta,
        zona_nombre as zona_origen,
        cast(null as double) as latitud,
        cast(null as double) as longitud,
        try_cast(km as double) as km_trazado,
        _lote_id
    from {{ ref('brz_mr_estaciones') }}
    qualify _ingesta_ts = max(_ingesta_ts) over ()
),

am as (
    select
        'AM' as modo_codigo,
        station_code as codigo_origen,
        station_name as nombre_punto,
        axis as linea_ruta,
        district as zona_origen,
        cast(null as double) as latitud,
        cast(null as double) as longitud,
        cast(null as double) as km_trazado,
        _lote_id
    from {{ ref('brz_am_estaciones') }}
    qualify _ingesta_ts = max(_ingesta_ts) over ()
),

unificado as (
    select * from tm
    union all select * from tu
    union all select * from mr
    union all select * from am
)

select
    u.modo_codigo || ':' || u.codigo_origen as estacion_key,
    m.modo_key,
    u.modo_codigo,
    u.codigo_origen,
    u.nombre_punto,
    u.linea_ruta,
    a.zona_key,
    u.zona_origen,
    u.latitud,
    u.longitud,
    u.km_trazado,
    u._lote_id as lote_origen
from unificado as u
inner join {{ ref('dim_modo') }} as m
    on u.modo_codigo = m.modo_codigo
left join {{ ref('map_zona_alias') }} as a
    on upper(trim(u.zona_origen)) = a.alias_normalizado