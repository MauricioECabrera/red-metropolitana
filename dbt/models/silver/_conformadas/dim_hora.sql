{#
=====================================================================
  dim_hora  ·  Dimension conformada de hora del dia
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
  Autor: Miguel Eduardo Cabrera Giron
=====================================================================
#}

with horas as (
    select unnest(range(0, 24)) as hora
)

select
    cast(hora as integer) as hora_key,
    lpad(cast(hora as varchar), 2, '0') || ':00' as hora_etiqueta,
    case
        when hora between 6 and 8 then 'Pico mañana'
        when hora between 16 and 18 then 'Pico tarde'
        when hora between 9 and 15 then 'Valle'
        else 'Extremo'
    end as franja_horaria,
    (hora between 6 and 8) or (hora between 16 and 18) as es_franja_pico
from horas