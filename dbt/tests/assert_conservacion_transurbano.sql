with bronze as (
    select count(*) as filas from {{ ref('brz_transurbano_transacciones') }}
),

transaccion as (
    select
        (select count(*) from {{ ref('slv_tu_transacciones') }})
        + (select count(*) from {{ ref('cuarentena') }} where fuente = 'transurbano' and proceso = 'transaccion') as filas
),

abordaje as (
    select
        (select count(*) from {{ ref('slv_tu_abordajes') }})
        + (select count(*) from {{ ref('slv_tu_transacciones') }} where not es_abordaje_exitoso) as filas
),

validas as (
    select count(*) as filas from {{ ref('slv_tu_transacciones') }}
)

select 'transaccion' as proceso, b.filas as esperado, t.filas as obtenido
from bronze as b, transaccion as t
where b.filas <> t.filas

union all

select 'abordaje', v.filas, a.filas
from validas as v, abordaje as a
where v.filas <> a.filas
