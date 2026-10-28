{{ config(materialized='incremental', unique_key=['unidad_id', 'fecha_corte']) }}

/*
Proyecto 2 - Red Metropolitana de Transporte
Autor: Diego de Jesus Urbina Chavez
*/

{% set fuentes = fuentes_abordaje() %}
{% set fecha_corte = var('fecha_corte', '2026-07-01') %}

with todos_abordajes as (
    {% for fuente in fuentes %}
    select persona_key as unidad_id, abordaje_ts
    from {{ ref(fuente) }}
    {% if not loop.last %} union all {% endif %}
    {% endfor %}
),
poblacion_base as (
    select unidad_id
    from todos_abordajes
    where abordaje_ts >= cast('{{ fecha_corte }}' as date) - interval 28 day
      and abordaje_ts < cast('{{ fecha_corte }}' as date)
    group by unidad_id
    having count(*) >= 2
),
bajas_cdc as (
    select persona_key as unidad_id
    from {{ ref('slv_padron_scd2') }}
    where estado = 'INACTIVA' 
      and vigente_desde < cast('{{ fecha_corte }}' as date)
),
poblacion_activa as (
    select p.unidad_id
    from poblacion_base p
    where not exists (
        select 1 from bajas_cdc b where p.unidad_id = b.unidad_id
    )
),
etiqueta as (
    select 
        p.unidad_id,
        cast('{{ fecha_corte }}' as date) as fecha_corte,
        case 
            when cast('{{ fecha_corte }}' as date) = cast('2026-08-30' as date) then null
            when count(a.abordaje_ts) = 0 then 1
            else 0 
        end as etiqueta
    from poblacion_activa p
    left join todos_abordajes a 
           on p.unidad_id = a.unidad_id
          and a.abordaje_ts >= cast('{{ fecha_corte }}' as date)
          and a.abordaje_ts < cast('{{ fecha_corte }}' as date) + interval 30 day
    group by p.unidad_id
)
select * from etiqueta