with silver as (
    select sum(filas) as filas
    from (
        {% for fuente in fuentes_abordaje() %}
        select count(*) as filas from {{ ref(fuente) }}
        {% if not loop.last %}union all{% endif %}
        {% endfor %}
    )
),

gold as (
    select count(*) as filas from {{ ref('fct_abordaje') }}
)

select s.filas as silver, g.filas as gold
from silver as s, gold as g
where s.filas <> g.filas