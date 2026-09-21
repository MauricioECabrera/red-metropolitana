{#
=====================================================================
  dim_persona  ·  Dimension conformada de persona
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
  
  Una fila por persona conocida por la red: toda persona que aparece
  en algun abordaje de las fuentes integradas o en el padron. Los
  atributos del padron son los de la version vigente del SCD Tipo 2.
  Bitacora D-002 y D-011.
=====================================================================
#}

with personas as (
    {% for fuente in fuentes_abordaje() %}
    select distinct persona_key from {{ ref(fuente) }}
    union
    {% endfor %}
    select distinct persona_key from {{ ref('slv_padron_scd2') }}
),

vigente as (
    select *
    from {{ ref('slv_padron_scd2') }}
    where es_vigente
)

select
    p.persona_key,
    case when p.persona_key like 'AM:%' then 'solo_aerometro' else 'vinculada' end as tipo_identidad,
    v.persona_key is not null as en_padron,
    coalesce(v.estado, 'SIN_REGISTRO') as estado_padron,
    v.perfil as perfil_vigente,
    v.zona_residencia_key,
    v.formato_llave_origen as formato_llave_padron,
    v.version as versiones_padron
from personas as p
left join vigente as v
    on p.persona_key = v.persona_key