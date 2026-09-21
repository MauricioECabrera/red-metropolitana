with bronze as (
    select count(*) as filas from {{ ref('brz_metroriel_viajes') }}
),

abordaje as (
    select
        (select count(*) from {{ ref('slv_mr_abordajes') }})
        + (select count(*) from {{ ref('cuarentena') }} where fuente = 'metroriel' and proceso = 'abordaje') as filas
),

trayecto as (
    select
        (select count(*) from {{ ref('slv_mr_trayectos') }})
        + (select count(*) from {{ ref('cuarentena') }} where fuente = 'metroriel' and proceso = 'trayecto') as filas
)

select 'abordaje' as proceso, b.filas as bronze, a.filas as silver_mas_cuarentena
from bronze as b, abordaje as a
where b.filas <> a.filas

union all

select 'trayecto', b.filas, t.filas
from bronze as b, trayecto as t
where b.filas <> t.filas