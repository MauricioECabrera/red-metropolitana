with ultimo_dia as (
    select sum(tarjetas_activas) as activas
    from {{ ref('fct_estado_padron_diario') }}
    where fecha_key = (select max(fecha_key) from {{ ref('fct_estado_padron_diario') }})
),

vigente as (
    select count(*) as activas
    from {{ ref('slv_padron_scd2') }}
    where es_vigente and estado = 'ACTIVA'
)

select u.activas as foto_ultimo_dia, v.activas as padron_vigente
from ultimo_dia as u, vigente as v
where u.activas <> v.activas