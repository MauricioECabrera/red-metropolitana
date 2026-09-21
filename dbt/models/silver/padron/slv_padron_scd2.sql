{#
=====================================================================
  slv_padron_scd2  ·  Historial del padron de usuarios, SCD Tipo 2
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Una fila por version de una persona. Se abre una version nueva
  cuando cambia el perfil, la zona de residencia o el estado. Un
  DELETE no borra: cierra la version vigente y abre una INACTIVA
  que conserva los ultimos atributos conocidos.

  Se construye desde la secuencia del log y no con dbt snapshot,
  para que dos corridas produzcan exactamente el mismo historial.
  Bitacora D-010.
=====================================================================
#}

with eventos as (
    select
        persona_key,
        formato_llave,
        seq,
        commit_ts,
        operacion,
        case when operacion = 'DELETE' then 'INACTIVA' else 'ACTIVA' end as estado,
        perfil,
        zona_residencia_key
    from {{ ref('cdc_padron_evaluado') }}
    where motivo_rechazo_padron is null
),

atributos as (
    select
        persona_key,
        seq,
        operacion,
        estado,
        coalesce(perfil, last_value(perfil ignore nulls) over w) as perfil,
        coalesce(zona_residencia_key, last_value(zona_residencia_key ignore nulls) over w) as zona_residencia_key,
        first_value(formato_llave) over (partition by persona_key order by seq) as formato_llave_origen,
        max(commit_ts) over (partition by persona_key order by seq rows between unbounded preceding and current row) as vigente_desde
    from eventos
    window w as (partition by persona_key order by seq rows between unbounded preceding and 1 preceding)
),

cambios as (
    select
        *,
        lag(estado) over (partition by persona_key order by seq) as estado_anterior,
        lag(perfil) over (partition by persona_key order by seq) as perfil_anterior,
        lag(zona_residencia_key) over (partition by persona_key order by seq) as zona_anterior
    from atributos
),

versiones as (
    select *
    from cambios
    where estado_anterior is null
        or estado is distinct from estado_anterior
        or perfil is distinct from perfil_anterior
        or zona_residencia_key is distinct from zona_anterior
)

select
    persona_key,
    row_number() over (partition by persona_key order by seq) as version,
    estado,
    perfil,
    zona_residencia_key,
    formato_llave_origen,
    operacion as operacion_origen,
    seq as seq_desde,
    vigente_desde,
    lead(vigente_desde) over (partition by persona_key order by seq) as vigente_hasta,
    lead(seq) over (partition by persona_key order by seq) is null as es_vigente
from versiones