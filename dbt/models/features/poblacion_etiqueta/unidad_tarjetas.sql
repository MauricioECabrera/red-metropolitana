{{ config(materialized='incremental', unique_key=['unidad_id', 'fecha_corte']) }}

/*
Proyecto 2 - Red Metropolitana de Transporte
Autor: Diego de Jesus Urbina Chavez
*/

{% set fuentes = fuentes_abordaje() %}
{% set fecha_corte = var('fecha_corte', '2026-07-01') %}

with todas_tarjetas as (
    {% for fuente in fuentes %}
    select distinct persona_key as unidad_id, tarjeta_origen
    from {{ ref(fuente) }}
    where tarjeta_origen is not null
      and abordaje_ts < cast('{{ fecha_corte }}' as date)
    {% if not loop.last %} union {% endif %}
    {% endfor %}
),
pob as (
    select unidad_id
    from {{ ref('poblacion') }}
    where fecha_corte = cast('{{ fecha_corte }}' as date)
),
tarjetas_agrupadas as (
    select
        p.unidad_id,
        cast('{{ fecha_corte }}' as date) as fecha_corte,
        string_agg(t.tarjeta_origen, ';' order by t.tarjeta_origen) as tarjetas
    from pob p
    inner join todas_tarjetas t on p.unidad_id = t.unidad_id
    group by p.unidad_id
)
select * from tarjetas_agrupadas