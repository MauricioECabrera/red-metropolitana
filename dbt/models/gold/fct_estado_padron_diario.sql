{#
=====================================================================
  fct_estado_padron_diario  ·  Foto diaria del padron de usuarios
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Grano: una persona del padron por dia calendario, con la version
  del SCD Tipo 2 vigente al cierre de ese dia. Una persona aparece
  desde el dia de su primer evento en el log.

  tarjetas_activas es una medida semi-aditiva: se suma entre zonas
  y perfiles de un mismo dia, nunca entre dias. Bitacora D-011.
=====================================================================
#}

with periodo as (
    select
        cast(min(vigente_desde) as date) as desde,
        cast(max(vigente_desde) as date) as hasta
    from {{ ref('slv_padron_scd2') }}
),

dias as (
    select f.fecha_key, f.fecha, f.fecha + interval 1 day as cierre
    from {{ ref('dim_fecha') }} as f, periodo as p
    where f.fecha between p.desde and p.hasta
),

foto as (
    select
        d.fecha_key,
        s.persona_key,
        s.estado,
        s.perfil,
        s.zona_residencia_key
    from dias as d
    inner join {{ ref('slv_padron_scd2') }} as s
        on s.vigente_desde < d.cierre
        and (s.vigente_hasta is null or s.vigente_hasta >= d.cierre)
)

select
    fecha_key,
    {{ seudonimizar('persona_key') }} as persona_sk,
    zona_residencia_key,
    perfil,
    estado,
    1 as cantidad_personas,
    case when estado = 'ACTIVA' then 1 else 0 end as tarjetas_activas
from foto