select
    a.alias_crudo,
    a.zona_key
from {{ ref('seed_zona_alias') }} as a
left join {{ ref('seed_dim_zona') }} as z
    on a.zona_key = z.zona_key
where z.zona_key is null