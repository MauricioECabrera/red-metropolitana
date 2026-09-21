select persona_key, count(*) as vigentes
from {{ ref('slv_padron_scd2') }}
where es_vigente
group by persona_key
having count(*) <> 1