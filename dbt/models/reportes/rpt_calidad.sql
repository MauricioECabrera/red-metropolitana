{#
=====================================================================
  rpt_calidad  ·  Registros en cuarentena por regla
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Catalogo completo de reglas contra los rechazos observados. Una
  regla que nunca se disparo aparece con cero: es la evidencia de que
  se evaluo y no fallo, no de que falte.

  El porcentaje se mide siempre contra las filas de Bronze de la
  fuente, no contra el total de la red.

  Al integrarse una fuente nueva se agrega su bloque en volumen_bronze.
=====================================================================
#}

with volumen_bronze as (
    select 'aerometro' as fuente, count(*) as filas_bronze
    from {{ ref('brz_aerometro_boardings') }}

    union all

    select 'metroriel', count(*)
    from {{ ref('brz_metroriel_viajes') }}

    union all

    select 'transmetro', count(*)
    from {{ ref('brz_transmetro_validaciones') }}

    union all

    select 'transurbano', count(*)
    from {{ ref('brz_transurbano_transacciones') }}

    union all

    select 'cdc_padron', count(*)
    from {{ ref('brz_cdc_padron_usuarios') }}
),

rechazos as (
    select
        fuente,
        proceso,
        motivo_rechazo,
        count(*) as registros
    from {{ ref('cuarentena') }}
    group by 1, 2, 3
)

select
    c.fuente,
    c.proceso,
    c.orden,
    c.regla,
    c.descripcion,
    case when b.filas_bronze is null then 'pendiente de integrar' else 'integrada' end as estado_fuente,
    b.filas_bronze,
    coalesce(r.registros, 0) as registros_en_cuarentena,
    round(100.0 * coalesce(r.registros, 0) / nullif(b.filas_bronze, 0), 4) as porcentaje_de_bronze
from {{ ref('cat_reglas_calidad') }} as c
left join volumen_bronze as b
    on c.fuente = b.fuente
left join rechazos as r
    on c.fuente = r.fuente
    and c.proceso = r.proceso
    and c.regla = r.motivo_rechazo
order by c.fuente, c.proceso, c.orden
