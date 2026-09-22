{#
=====================================================================
  rpt_volumen_por_capa  ·  Filas por fuente en cada capa
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Recorrido de cada fuente de operacion: lo que entro a Bronze, lo que
  sobrevivio a las reglas de calidad en Silver, lo que quedo retenido
  en cuarentena y lo que llego a fct_abordaje en Gold.

  El padron CDC no aparece aqui a proposito: no genera abordajes, no
  alimenta fct_abordaje y su volumen se reporta en rpt_calidad y en la
  evidencia del CDC.

  Al integrarse una fuente nueva se agrega su bloque en medido.
=====================================================================
#}

with medido as (
    select
        'metroriel' as fuente,
        'MR' as modo_codigo,
        (select count(*) from {{ ref('brz_metroriel_viajes') }}) as filas_bronze,
        (select count(*) from {{ ref('slv_mr_abordajes') }}) as filas_silver,
        (select count(*) from {{ ref('cuarentena') }} where fuente = 'metroriel') as filas_cuarentena

    union all

    select
        'transurbano',
        'TU',
        (select count(*) from {{ ref('brz_transurbano_transacciones') }}),
        (select count(*) from {{ ref('slv_tu_transacciones') }}),
        (select count(*) from {{ ref('cuarentena') }} where fuente = 'transurbano')
),

en_gold as (
    select
        d.modo_codigo,
        count(*) as filas_gold
    from {{ ref('fct_abordaje') }} as f
    inner join {{ ref('dim_modo') }} as d
        on f.modo_key = d.modo_key
    group by 1
)

select
    m.fuente,
    m.modo_codigo,
    m.filas_bronze,
    m.filas_silver,
    m.filas_cuarentena,
    coalesce(g.filas_gold, 0) as filas_gold,
    m.filas_silver - coalesce(g.filas_gold, 0) as filas_no_promovidas_a_gold
from medido as m
left join en_gold as g
    on m.modo_codigo = g.modo_codigo
order by m.fuente
