"""
=====================================================================
  publicar_gold.py  ·  Publica la capa Gold para el tablero
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Copia unicamente el esquema gold del warehouse a un archivo
  separado, warehouse/tablero_gold.duckdb, que es el unico archivo
  al que se conecta Tableau.

  Dos motivos:
    1. DuckDB no permite que Tableau lea el warehouse mientras dbt
       escribe en el. Con un archivo aparte, dbt nunca se bloquea.
    2. El tablero solo puede ver Gold. Silver, con la llave de
       persona sin seudonimizar, no existe en el archivo publicado.

  Ejecutar desde la raiz del repositorio, con Tableau cerrado:
    python scripts/publicar_gold.py
=====================================================================
"""
import os
import pathlib
import sys
import time

import duckdb

RAIZ = pathlib.Path(__file__).resolve().parents[1]
WAREHOUSE = RAIZ / "warehouse" / "red_metropolitana.duckdb"
TABLERO = RAIZ / "warehouse" / "tablero_gold.duckdb"


def main():
    inicio = time.perf_counter()
    temporal = TABLERO.with_name(TABLERO.name + ".tmp")
    if temporal.exists():
        temporal.unlink()

    con = duckdb.connect(str(temporal))
    con.execute(f"attach '{WAREHOUSE.as_posix()}' as origen (read_only)")
    tablas = [
        fila[0]
        for fila in con.execute(
            "select table_name from information_schema.tables "
            "where table_catalog = 'origen' and table_schema = 'gold' order by table_name"
        ).fetchall()
    ]
    if not tablas:
        con.close()
        temporal.unlink()
        print("El warehouse no tiene tablas en gold. Correr primero .\\scripts\\dbt.ps1 build")
        sys.exit(1)

    con.execute("create schema gold")
    conteos = []
    for tabla in tablas:
        con.execute(f"create table gold.{tabla} as select * from origen.gold.{tabla}")
        conteos.append((tabla, con.execute(f"select count(*) from gold.{tabla}").fetchone()[0]))
    con.execute("detach origen")
    con.execute("checkpoint")
    con.close()

    try:
        os.replace(temporal, TABLERO)
    except PermissionError:
        temporal.unlink()
        print("No se pudo reemplazar tablero_gold.duckdb. Cerrar Tableau y volver a ejecutar.")
        sys.exit(1)

    print()
    print(f"{'tabla':<22}{'filas':>12}")
    print("-" * 34)
    for tabla, filas in conteos:
        print(f"{tabla:<22}{filas:>12,}")
    print("-" * 34)
    print(f"Publicado en {TABLERO.relative_to(RAIZ)} en {time.perf_counter() - inicio:.1f} s")
    print()


if __name__ == "__main__":
    main()