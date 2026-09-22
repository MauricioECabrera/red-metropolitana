{#
=====================================================================
  slv_tu_transacciones  ·  Transacciones validas de Transurbano
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Todas las transacciones bien formadas, exitosas o no. El codigo de
  estado se conserva: una transaccion rechazada por el validador es
  un hecho real del operador, no un error de datos. Decision D-006.
=====================================================================
#}

select
    'TU:' || _lote_id || ':' || _fila_origen as transaccion_id,
    'P' || lpad(cast(persona_numero as varchar), 8, '0') as persona_key,
    num_tarjeta as tarjeta_origen,
    estacion_key,
    zona_key,
    ruta,
    abordaje_ts,
    cast(strftime(abordaje_ts, '%Y%m%d') as integer) as fecha_key,
    cast(hour(abordaje_ts) as integer) as hora_key,
    cod_estado,
    case cod_estado
        when '7' then 'SALDO_INSUF'
        when '9' then 'TARJETA_INVALIDA'
        else 'OK'
    end as estado_validacion,
    cod_estado in ('1', '2', '3') as es_abordaje_exitoso,
    monto_q,
    _hash_fila,
    _lote_id,
    _fila_origen
from {{ ref('tu_transacciones_evaluado') }}
where motivo_rechazo_transaccion is null
