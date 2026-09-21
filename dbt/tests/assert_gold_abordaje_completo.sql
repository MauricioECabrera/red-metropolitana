with silver as (
    select count(*) as filas from {{ ref('slv_mr_abordajes') }}
),

gold as (
    select count(*) as filas from {{ ref('fct_abordaje') }}
)

select s.filas as silver, g.filas as gold
from silver as s, gold as g
where s.filas <> g.filas