{#
=====================================================================
  cdc_padron_evaluado  ·  Eventos del log CDC tipados y evaluados
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Una fila por evento de Bronze. Las operaciones se evaluan en orden
  de seq, que es la autoridad del orden del log. El estado previo de
  una persona lo define la ultima operacion INSERT o DELETE anterior.
  Bitacora D-005 y D-010.
=====================================================================
#}

with tipado as (
    select
        try_cast(seq as bigint) as seq,
        try_cast(commit_ts as timestamp) as commit_ts,
        upper(trim(op)) as operacion,
        tarjeta as tarjeta_origen,
        nullif(trim(perfil), '') as perfil,
        nullif(trim(zona_residencia), '') as zona_residencia_origen,
        nullif(trim(estado), '') as estado_origen,
        case
            when regexp_full_match(tarjeta, 'TC-\d{8}') then 'P' || lpad(cast(cast(substr(tarjeta, 4) as integer) as varchar), 8, '0')
            when regexp_full_match(tarjeta, '\d{10}') then 'P' || lpad(cast(cast(tarjeta as integer) as varchar), 8, '0')
            when regexp_full_match(tarjeta, 'MR\d{7}') then 'P' || lpad(cast(cast(substr(tarjeta, 3) as integer) as varchar), 8, '0')
        end as persona_key,
        case
            when tarjeta like 'TC-%' then 'TM'
            when regexp_full_match(tarjeta, '\d{10}') then 'TU'
            when tarjeta like 'MR%' then 'MR'
        end as formato_llave,
        cast(to_json(struct_pack(seq, commit_ts, op, tarjeta, perfil, zona_residencia, estado)) as varchar) as payload_original,
        _hash_fila,
        _lote_id,
        _fila_origen,
        _archivo_origen,
        _ingesta_ts
    from {{ ref('brz_cdc_padron_usuarios') }}
),

con_zona as (
    select
        t.*,
        z.zona_key as zona_residencia_key,
        row_number() over (partition by t.seq order by t._lote_id, t._fila_origen) as ocurrencia
    from tipado as t
    left join {{ ref('map_zona_alias') }} as z
        on upper(trim(t.zona_residencia_origen)) = z.alias_normalizado
),

formato as (
    select
        *,
        case
            when seq is null then 'secuencia_invalida'
            when ocurrencia > 1 then 'duplicado'
            when tarjeta_origen = 'SIN-TARJETA' then 'llave_centinela'
            when persona_key is null then 'tarjeta_invalida'
            when operacion not in ('INSERT', 'UPDATE', 'DELETE') then 'operacion_invalida'
            when commit_ts is null then 'fecha_invalida'
            when commit_ts > _ingesta_ts then 'fecha_futura'
            when operacion <> 'DELETE' and perfil not in ('estudiante', 'trabajador', 'adulto_mayor', 'general') then 'perfil_invalido'
            when operacion <> 'DELETE' and zona_residencia_key is null then 'zona_desconocida'
        end as motivo_formato
    from con_zona
),

estado_previo as (
    select
        *,
        last_value(case when motivo_formato is null and operacion in ('INSERT', 'DELETE') then operacion end ignore nulls)
            over (partition by persona_key order by seq rows between unbounded preceding and 1 preceding) as ultima_alta_o_baja
    from formato
)

select
    *,
    coalesce(
        motivo_formato,
        case
            when operacion = 'UPDATE' and ultima_alta_o_baja = 'DELETE' then 'actualizacion_sobre_baja'
            when operacion = 'DELETE' and ultima_alta_o_baja = 'DELETE' then 'baja_repetida'
        end
    ) as motivo_rechazo_padron
from estado_previo