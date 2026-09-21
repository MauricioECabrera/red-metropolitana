{#
=====================================================================
  fct_trayecto_od  ·  Trayectos origen destino de MetroRiel
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Grano: un trayecto de MetroRiel con entrada y salida validadas.
  Bitacora D-001.
=====================================================================
#}

select
    t.trayecto_id,
    {{ seudonimizar('t.persona_key') }} as persona_sk,
    t.estacion_origen_key,
    t.estacion_destino_key,
    t.zona_origen_key,
    t.zona_destino_key,
    t.fecha_key,
    t.hora_key,
    f.es_dia_habil and h.es_franja_pico as es_hora_pico,
    1 as cantidad_trayectos,
    t.duracion_s,
    t.distancia_km,
    t.monto_q
from {{ ref('slv_mr_trayectos') }} as t
inner join {{ ref('dim_fecha') }} as f
    on t.fecha_key = f.fecha_key
inner join {{ ref('dim_hora') }} as h
    on t.hora_key = h.hora_key