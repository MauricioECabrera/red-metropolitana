{{ config(materialized='incremental', unique_key=['unidad_id', 'fecha_corte']) }}

/*
Proyecto 2 - Red Metropolitana de Transporte
Autor: Diego de Jesus Urbina Chavez
*/

{% set fuentes = fuentes_abordaje() %}
{% set fecha_corte = var('fecha_corte', '2026-07-01') %}

with todos_abordajes as (
    {% for fuente in fuentes %}
    select persona_key as unidad_id, abordaje_ts, modo_codigo, monto_q, fecha_key, hora_key,
           try_cast(strftime(abordaje_ts, '%w') as integer) as dia_semana
    from {{ ref(fuente) }}
    {% if not loop.last %} union all {% endif %}
    {% endfor %}
),
con_dims as (
    select
        a.*,
        case when f.es_dia_habil = true and h.es_franja_pico = true then 1 else 0 end as es_pico
    from todos_abordajes a
    left join {{ ref('dim_fecha') }} f on a.fecha_key = f.fecha_key
    left join {{ ref('dim_hora') }} h on a.hora_key = h.hora_key
),
pob as (
    select unidad_id, etiqueta 
    from {{ ref('poblacion') }}
    where fecha_corte = cast('{{ fecha_corte }}' as date)
),
features as (
    select 
        p.unidad_id,
        cast('{{ fecha_corte }}' as date) as fecha_corte,
        count(a.abordaje_ts) as viajes_28d,
        date_diff('day', max(cast(a.abordaje_ts as date)), cast('{{ fecha_corte }}' as date)) as dias_desde_ultimo_viaje,
        sum(coalesce(a.monto_q, 0)) as gasto_28d_q,
        count(distinct a.modo_codigo) as operadores_distintos_28d,
        sum(case when a.dia_semana in (0, 6) then 1 else 0 end) as abordajes_fin_semana_28d,
        sum(case when a.abordaje_ts >= cast('{{ fecha_corte }}' as date) - interval 7 day then 1 else 0 end) as viajes_7d,
        count(distinct cast(a.abordaje_ts as date)) as dias_activos_28d,
        case 
            when count(a.abordaje_ts) = 0 then cast(0.00 as decimal(10,2))
            else round(sum(coalesce(a.monto_q, 0)) / count(a.abordaje_ts), 2)
        end as gasto_promedio_viaje_q,
        case 
            when count(a.abordaje_ts) = 0 then cast(0.0000 as decimal(5,4))
            else round(sum(a.es_pico) * 1.0 / count(a.abordaje_ts), 4)
        end as proporcion_hora_pico_28d,
        sum(case when a.abordaje_ts >= cast('{{ fecha_corte }}' as date) - interval 14 day then 1 else 0 end) -
        sum(case when a.abordaje_ts < cast('{{ fecha_corte }}' as date) - interval 14 day then 1 else 0 end) as tendencia_viajes_14d,
        p.etiqueta
    from pob p
    left join con_dims a 
           on p.unidad_id = a.unidad_id
          and a.abordaje_ts >= cast('{{ fecha_corte }}' as date) - interval 28 day
          and a.abordaje_ts < cast('{{ fecha_corte }}' as date)
    group by p.unidad_id, p.etiqueta
)
select * from features