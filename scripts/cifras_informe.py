"""
=====================================================================
  cifras_informe.py  ·  Cifras verificadas para el informe de Fase 1
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Consulta el warehouse y emite todas las cifras que sustentan el
  documento de datos y conclusiones de la Fase 1. Cada bloque es
  independiente: si una consulta falla porque una columna tiene otro
  nombre, el script lo reporta y continua con las demas.

  Ejecutar desde la raiz del repositorio:
    python scripts/cifras_informe.py
=====================================================================
"""
import pathlib
import sys

import duckdb

RAIZ = pathlib.Path(__file__).resolve().parents[1]
WAREHOUSE = RAIZ / "warehouse" / "red_metropolitana.duckdb"


def bloque(con, titulo, sql):
    print()
    print("=" * 78)
    print(titulo)
    print("=" * 78)
    try:
        filas = con.execute(sql).fetchall()
        columnas = [d[0] for d in con.description]
        print(" | ".join(columnas))
        print("-" * 78)
        for fila in filas:
            print(" | ".join("" if v is None else str(v) for v in fila))
        if not filas:
            print("(sin filas)")
    except Exception as error:
        print(f"NO DISPONIBLE: {error}")


def main():
    if not WAREHOUSE.exists():
        sys.exit(f"No se encontro {WAREHOUSE}")
    con = duckdb.connect(str(WAREHOUSE), read_only=True)

    bloque(con, "ESTRUCTURA DE TABLAS CLAVE", """
        select table_schema, table_name, string_agg(column_name, ', ' order by ordinal_position) as columnas
        from information_schema.columns
        where table_name in (
            'cdc_padron_evaluado', 'slv_padron_scd2', 'am_boardings_evaluado',
            'tm_validaciones_evaluado', 'slv_am_abordajes', 'slv_tm_abordajes',
            'cuarentena', 'rpt_calidad', 'rpt_volumen_por_capa', 'features_persona'
        )
        group by 1, 2 order by 1, 2
    """)

    bloque(con, "1.1 ABORDAJES POR MODO EN GOLD", """
        select m.modo_codigo, m.modo_nombre, count(*) as abordajes,
               round(sum(f.monto_q), 2) as monto_q,
               count(distinct f.persona_sk) as personas
        from gold.fct_abordaje f join gold.dim_modo m using (modo_key)
        group by 1, 2 order by 1
    """)

    bloque(con, "1.1 VOLUMEN POR CAPA", "select * from reportes.rpt_volumen_por_capa order by 1")

    bloque(con, "1.2 OPERACIONES DEL LOG CDC", """
        select operacion, count(*) as registros
        from silver.cdc_padron_evaluado group by 1 order by 1
    """)

    bloque(con, "1.2 PADRON ANTES Y DESPUES DE LOS BORRADOS", """
        select
            count(*) as personas_en_padron,
            count(*) filter (where estado = 'ACTIVA') as activas_al_cierre,
            count(*) filter (where estado = 'INACTIVA') as dadas_de_baja
        from silver.slv_padron_scd2 where es_vigente
    """)

    bloque(con, "1.2 VERSIONES DEL SCD TIPO 2", """
        select count(*) as versiones, count(distinct persona_key) as personas,
               max(version) as max_versiones_por_persona
        from silver.slv_padron_scd2
    """)

    bloque(con, "1.2 USUARIOS UNICOS POR OPERADOR", """
        select 'transurbano' as operador, count(*) as usuarios from silver.usuarios_transurbano
        union all select 'metroriel', count(*) from silver.usuarios_metroriel
        union all select 'aerometro', count(*) from silver.usuarios_aerometro
        order by 1
    """)

    bloque(con, "1.3 CUARENTENA POR FUENTE Y MOTIVO", """
        select fuente, proceso, motivo_rechazo, count(*) as registros
        from silver.cuarentena group by 1, 2, 3 order by 1, 4 desc
    """)

    bloque(con, "1.3 REPORTE DE CALIDAD POR REGLA", "select * from reportes.rpt_calidad order by 1, 2, 3")

    bloque(con, "1.3 IDENTIDAD DE USUARIO EN GOLD", """
        select tipo_identidad, estado_padron, count(*) as personas
        from gold.dim_persona group by 1, 2 order by 1, 2
    """)

    bloque(con, "1.3 PERSONAS MULTIMODALES", """
        with p as (
            select f.persona_sk, count(distinct m.modo_codigo) as modos
            from gold.fct_abordaje f join gold.dim_modo m using (modo_key)
            group by 1
        )
        select modos, count(*) as personas from p group by 1 order by 1
    """)

    bloque(con, "1.4 MEDIDAS DEL HECHO PRINCIPAL", """
        select count(*) as abordajes,
               round(sum(monto_q), 2) as monto_total_q,
               count(distinct persona_sk) as personas_distintas,
               round(100.0 * count(*) filter (where es_hora_pico) / count(*), 1) as pct_hora_pico
        from gold.fct_abordaje
    """)

    bloque(con, "1.4 TRAYECTOS METRORIEL", """
        select count(*) as trayectos,
               round(avg(duracion_s) / 60.0, 1) as duracion_promedio_min,
               round(sum(distancia_km), 1) as distancia_total_km
        from gold.fct_trayecto_od
    """)

    bloque(con, "1.4 ESTADO DIARIO DEL PADRON", """
        select count(*) as filas, count(distinct fecha_key) as dias,
               sum(tarjetas_activas) filter (where fecha_key = (select max(fecha_key) from gold.fct_estado_padron_diario)) as activas_ultimo_dia
        from gold.fct_estado_padron_diario
    """)

    bloque(con, "COBERTURA POR ZONA", """
        select zona_nombre, tiene_servicio, modos_con_servicio, puntos_de_abordaje
        from silver.dim_zona order by tiene_servicio, zona_nombre
    """)

    bloque(con, "DISTRIBUCION HORARIA POR MODO", """
        select f.hora_key,
               count(*) filter (where m.modo_codigo = 'AM') as aerometro,
               count(*) filter (where m.modo_codigo = 'MR') as metroriel,
               count(*) filter (where m.modo_codigo = 'TM') as transmetro,
               count(*) filter (where m.modo_codigo = 'TU') as transurbano
        from gold.fct_abordaje f join gold.dim_modo m using (modo_key)
        group by 1 order by 1
    """)

    bloque(con, "DEMANDA POR ZONA", """
        select z.zona_nombre, count(*) as abordajes
        from gold.fct_abordaje f join gold.dim_zona z using (zona_key)
        group by 1 order by 2 desc
    """)

    bloque(con, "RANGO DE FECHAS CON DATOS", """
        select min(fecha_key) as desde, max(fecha_key) as hasta, count(distinct fecha_key) as dias
        from gold.fct_abordaje
    """)

    con.close()
    print()


if __name__ == "__main__":
    main()