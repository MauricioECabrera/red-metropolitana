{#
=====================================================================
  dim_fecha  ·  Dimension conformada de calendario
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
=====================================================================
#}

with calendario as (
    select cast(unnest(generate_series(date '2026-01-01', date '2027-12-31', interval 1 day)) as date) as fecha
)

select
    cast(strftime(fecha, '%Y%m%d') as integer) as fecha_key,
    fecha,
    year(fecha) as anio,
    month(fecha) as mes,
    case month(fecha)
        when 1 then 'Enero' when 2 then 'Febrero' when 3 then 'Marzo'
        when 4 then 'Abril' when 5 then 'Mayo' when 6 then 'Junio'
        when 7 then 'Julio' when 8 then 'Agosto' when 9 then 'Septiembre'
        when 10 then 'Octubre' when 11 then 'Noviembre' when 12 then 'Diciembre'
    end as nombre_mes,
    day(fecha) as dia,
    isodow(fecha) as dia_semana_num,
    case isodow(fecha)
        when 1 then 'Lunes' when 2 then 'Martes' when 3 then 'Miércoles'
        when 4 then 'Jueves' when 5 then 'Viernes' when 6 then 'Sábado'
        when 7 then 'Domingo'
    end as nombre_dia,
    weekofyear(fecha) as semana_iso,
    isodow(fecha) <= 5 as es_dia_habil,
    isodow(fecha) >= 6 as es_fin_de_semana
from calendario