{#
=====================================================================
  cuarentena  ·  Registros rechazados de todas las fuentes
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Union de los modelos de cuarentena de cada fuente declarados en
  la macro fuentes_cuarentena. Un registro aparece una vez por cada
  proceso que lo rechaza.
=====================================================================
#}

{% for modelo in fuentes_cuarentena() %}
select
    fuente,
    proceso,
    motivo_rechazo,
    payload_original,
    _hash_fila,
    _lote_id,
    _fila_origen,
    _archivo_origen,
    _ingesta_ts
from {{ ref(modelo) }}
{% if not loop.last %}union all{% endif %}
{% endfor %}