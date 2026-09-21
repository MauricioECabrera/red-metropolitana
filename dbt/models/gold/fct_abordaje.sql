{#
=====================================================================
  fct_abordaje  ·  Hecho principal de la red
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Grano: una validacion exitosa de una tarjeta al ingresar a un
  vehiculo o estacion, en cualquiera de los cuatro modos.
  Bitacora D-001.

  Las fuentes se declaran en la macro fuentes_abordaje. Cada modelo
  debe cumplir el contrato de columnas de slv_mr_abordajes.
=====================================================================
#}



with abordajes as (
    {% for fuente in fuentes_abordaje() %}
    select
        abordaje_id,
        modo_codigo,
        persona_key,
        estacion_key,
        zona_key,
        fecha_key,
        hora_key,
        tipo_abordaje,
        monto_q
    from {{ ref(fuente) }}
    {% if not loop.last %}union all{% endif %}
    {% endfor %}
)

select
    a.abordaje_id,
    {{ seudonimizar('a.persona_key') }} as persona_sk,
    m.modo_key,
    a.estacion_key,
    a.zona_key,
    a.fecha_key,
    a.hora_key,
    a.tipo_abordaje,
    f.es_dia_habil and h.es_franja_pico as es_hora_pico,
    1 as cantidad_abordajes,
    a.monto_q
from abordajes as a
inner join {{ ref('dim_modo') }} as m
    on a.modo_codigo = m.modo_codigo
inner join {{ ref('dim_fecha') }} as f
    on a.fecha_key = f.fecha_key
inner join {{ ref('dim_hora') }} as h
    on a.hora_key = h.hora_key