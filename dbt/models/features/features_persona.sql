/*
Proyecto 1 - Red Metropolitana de Transporte
Autor: Diego de Jesus Urbina Chavez
*/
{% set fuentes = fuentes_abordaje() %}

with unificados as (
    {% for fuente in fuentes %}
    select
        persona_key,
        modo_codigo,
        zona_key,
        abordaje_ts,
        fecha_key,
        hora_key,
        monto_q
    from {{ ref(fuente) }}
    {% if not loop.last %} union all {% endif %}
    {% endfor %}
),
con_dims as (
    select
        u.*,
        f.fecha,
        case when f.es_dia_habil = true and h.es_franja_pico = true then 1 else 0 end as es_pico
    from unificados u
    left join {{ ref('dim_fecha') }} f on u.fecha_key = f.fecha_key
    left join {{ ref('dim_hora') }} h on u.hora_key = h.hora_key
    where f.fecha <= cast('{{ env_var("FECHA_CORTE_FEATURES", "2026-07-15") }}' as date)
),
agregados_generales as (
    select
        persona_key,
        case when persona_key like 'P%' then 'vinculada' else 'solo_aerometro' end as tipo_identidad,
        count(*) as abordajes_total,
        count(distinct fecha_key) as dias_activos,
        count(distinct modo_codigo) as modos_distintos,
        sum(case when fecha >= cast('{{ env_var("FECHA_CORTE_FEATURES", "2026-07-15") }}' as date) - interval 7 day then 1 else 0 end) as abordajes_7d,
        sum(case when fecha >= cast('{{ env_var("FECHA_CORTE_FEATURES", "2026-07-15") }}' as date) - interval 30 day then 1 else 0 end) as abordajes_30d,
        sum(case when fecha >= cast('{{ env_var("FECHA_CORTE_FEATURES", "2026-07-15") }}' as date) - interval 90 day then 1 else 0 end) as abordajes_90d,
        date_diff('day', max(fecha), cast('{{ env_var("FECHA_CORTE_FEATURES", "2026-07-15") }}' as date)) as dias_desde_ultimo_abordaje,
        round(sum(es_pico) * 1.0 / count(*), 4) as proporcion_hora_pico,
        sum(coalesce(monto_q, 0)) as gasto_total_q,
        round(sum(coalesce(monto_q, 0)) / count(*), 2) as gasto_promedio_q
    from con_dims
    group by 1, 2
),
ranking_modos as (
    select persona_key, modo_codigo, count(*) as conteo,
           row_number() over (partition by persona_key order by count(*) desc, modo_codigo asc) as rn
    from con_dims
    group by 1, 2
),
ranking_zonas as (
    select persona_key, zona_key, count(*) as conteo,
           row_number() over (partition by persona_key order by count(*) desc, zona_key asc) as rn
    from con_dims
    group by 1, 2
)
select
    {{ seudonimizar('a.persona_key') }} as persona_sk,
    a.tipo_identidad,
    a.abordajes_7d,
    a.abordajes_30d,
    a.abordajes_90d,
    a.abordajes_total,
    a.dias_activos,
    a.modos_distintos,
    rm.modo_codigo as modo_mas_usado,
    a.dias_desde_ultimo_abordaje,
    a.proporcion_hora_pico,
    rz.zona_key as zona_origen_mas_frecuente,
    a.gasto_total_q,
    a.gasto_promedio_q
from agregados_generales a
left join ranking_modos rm on a.persona_key = rm.persona_key and rm.rn = 1
left join ranking_zonas rz on a.persona_key = rz.persona_key and rz.rn = 1