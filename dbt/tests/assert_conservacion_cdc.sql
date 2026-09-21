with bronze as (
    select count(*) as filas from {{ ref('brz_cdc_padron_usuarios') }}
),

evaluado as (
    select
        count(*) filter (where motivo_rechazo_padron is null)
        + (select count(*) from {{ ref('cdc_cuarentena') }}) as filas
    from {{ ref('cdc_padron_evaluado') }}
)

select b.filas as bronze, e.filas as validos_mas_cuarentena
from bronze as b, evaluado as e
where b.filas <> e.filas