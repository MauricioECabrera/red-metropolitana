"""
Proyecto 2 - Red Metropolitana de Transporte
Autor: Diego de Jesus Urbina Chavez
"""
import argparse
import duckdb
import pandas as pd

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fecha-corte', required=True)
    parser.add_argument('--recorte', required=True)
    args = parser.parse_args()

    print(f"Iniciando prueba de recorte para corte {args.fecha_corte} con límite al {args.recorte}...")

    con = duckdb.connect('warehouse/red_metropolitana.duckdb', read_only=True)
    
    df_normal = con.sql(f"SELECT * FROM features.features_corte WHERE fecha_corte = '{args.fecha_corte}'").df()
    
    query_recortada = f"""
    with todos_abordajes as (
        select persona_key as unidad_id, abordaje_ts, modo_codigo, monto_q, fecha_key, hora_key,
               try_cast(strftime(abordaje_ts, '%w') as integer) as dia_semana
        from silver.slv_mr_abordajes where abordaje_ts <= '{args.recorte} 23:59:59'
        union all select persona_key as unidad_id, abordaje_ts, modo_codigo, monto_q, fecha_key, hora_key, try_cast(strftime(abordaje_ts, '%w') as integer) from silver.slv_tm_abordajes where abordaje_ts <= '{args.recorte} 23:59:59'
        union all select persona_key as unidad_id, abordaje_ts, modo_codigo, monto_q, fecha_key, hora_key, try_cast(strftime(abordaje_ts, '%w') as integer) from silver.slv_am_abordajes where abordaje_ts <= '{args.recorte} 23:59:59'
        union all select persona_key as unidad_id, abordaje_ts, modo_codigo, monto_q, fecha_key, hora_key, try_cast(strftime(abordaje_ts, '%w') as integer) from silver.slv_tu_abordajes where abordaje_ts <= '{args.recorte} 23:59:59'
    ),
    con_dims as (
        select
            a.*,
            case when f.es_dia_habil = true and h.es_franja_pico = true then 1 else 0 end as es_pico
        from todos_abordajes a
        left join silver.dim_fecha f on a.fecha_key = f.fecha_key
        left join silver.dim_hora h on a.hora_key = h.hora_key
    ),
    pob as (
        select unidad_id, etiqueta from features.poblacion where fecha_corte = '{args.fecha_corte}'
    )
    select 
        p.unidad_id, cast('{args.fecha_corte}' as date) as fecha_corte,
        count(a.abordaje_ts) as viajes_28d,
        date_diff('day', max(cast(a.abordaje_ts as date)), cast('{args.fecha_corte}' as date)) as dias_desde_ultimo_viaje,
        sum(coalesce(a.monto_q, 0)) as gasto_28d_q,
        count(distinct a.modo_codigo) as operadores_distintos_28d,
        sum(case when a.dia_semana in (0, 6) then 1 else 0 end) as abordajes_fin_semana_28d,
        sum(case when a.abordaje_ts >= cast('{args.fecha_corte}' as date) - interval 7 day then 1 else 0 end) as viajes_7d,
        count(distinct cast(a.abordaje_ts as date)) as dias_activos_28d,
        case 
            when count(a.abordaje_ts) = 0 then cast(0.00 as decimal(10,2))
            else round(sum(coalesce(a.monto_q, 0)) / count(a.abordaje_ts), 2)
        end as gasto_promedio_viaje_q,
        case 
            when count(a.abordaje_ts) = 0 then cast(0.0000 as decimal(5,4))
            else round(sum(a.es_pico) * 1.0 / count(a.abordaje_ts), 4)
        end as proporcion_hora_pico_28d,
        sum(case when a.abordaje_ts >= cast('{args.fecha_corte}' as date) - interval 14 day then 1 else 0 end) -
        sum(case when a.abordaje_ts < cast('{args.fecha_corte}' as date) - interval 14 day then 1 else 0 end) as tendencia_viajes_14d,
        p.etiqueta
    from pob p
    left join con_dims a on p.unidad_id = a.unidad_id 
      and a.abordaje_ts >= cast('{args.fecha_corte}' as date) - interval 28 day
      and a.abordaje_ts < cast('{args.fecha_corte}' as date)
    group by p.unidad_id, p.etiqueta
    """
    
    df_recortada = con.sql(query_recortada).df()

    diferencias = pd.concat([df_normal, df_recortada]).drop_duplicates(keep=False)
    
    print(f"Filas comparadas: {len(df_normal)}")
    print(f"Diferencias encontradas: {len(diferencias)}")
    
    if len(diferencias) == 0:
        print("Resultado: ÉXITO. Las dos tablas son idénticas. No hay fuga de datos.")
    else:
        print("Resultado: FALLO. Hay diferencias (fuga de datos detectada).")

if __name__ == '__main__':
    main()