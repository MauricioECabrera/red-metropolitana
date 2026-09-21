{#
=====================================================================
  dim_zona  ·  Dimension conformada de zona
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
=====================================================================
#}

with cobertura as (
    select
        zona_key,
        count(*) as puntos_de_abordaje,
        count(distinct modo_codigo) as modos_con_servicio,
        string_agg(distinct modo_codigo, ', ' order by modo_codigo) as modos_lista
    from {{ ref('dim_estacion_parada') }}
    group by zona_key
)

select
    z.zona_key,
    z.zona_nombre,
    z.tipo_division,
    z.municipio,
    coalesce(c.puntos_de_abordaje, 0) as puntos_de_abordaje,
    coalesce(c.modos_con_servicio, 0) as modos_con_servicio,
    coalesce(c.modos_lista, 'Sin servicio') as modos_lista,
    coalesce(c.modos_con_servicio, 0) > 0 as tiene_servicio
from {{ ref('seed_dim_zona') }} as z
left join cobertura as c
    on z.zona_key = c.zona_key