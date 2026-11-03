{{ config(materialized='table') }}

/*
Proyecto 2 - Red Metropolitana de Transporte
Autor: Diego de Jesus Urbina Chavez
*/

{% set fuentes = fuentes_abordaje() %}

with todas_tarjetas as (
    {% for fuente in fuentes %}
    select distinct persona_key as unidad_id, tarjeta_origen
    from {{ ref(fuente) }}
    where tarjeta_origen is not null
    {% if not loop.last %} union {% endif %}
    {% endfor %}
),
poblacion_total as (
    select distinct unidad_id
    from {{ ref('poblacion') }}
),
tarjetas_agrupadas as (
    select
        t.unidad_id,
        string_agg(t.tarjeta_origen, ';' order by t.tarjeta_origen) as tarjetas
    from todas_tarjetas t
    inner join poblacion_total p on t.unidad_id = p.unidad_id
    group by t.unidad_id
)
select * from tarjetas_agrupadas