select persona_key, version, vigente_desde, vigente_hasta
from {{ ref('slv_padron_scd2') }}
where vigente_hasta < vigente_desde