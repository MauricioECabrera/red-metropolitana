select fecha_key, persona_sk, count(*) as filas
from {{ ref('fct_estado_padron_diario') }}
group by fecha_key, persona_sk
having count(*) > 1