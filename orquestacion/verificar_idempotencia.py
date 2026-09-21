"""
=====================================================================
  verificar_idempotencia.py  ·  Demostracion de idempotencia
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Corre el flujo completo dos veces seguidas y despues de cada
  corrida cuenta todas las tablas de todas las capas: los archivos
  de Bronze en el lake y las tablas de seeds, silver, gold, features
  y reportes en el warehouse.

  Por tabla registra dos cosas:
    filas    cantidad de filas
    huella   XOR del hash de cada fila, independiente del orden.
             Si una sola fila cambia, la huella cambia.

  Compara las dos corridas, escribe la evidencia en
  docs/evidencias/idempotencia.md y termina con error si cualquier
  tabla difiere en filas o en contenido.

  Ejecutar desde la raiz del repositorio:
    python -m orquestacion.verificar_idempotencia
=====================================================================
"""
import datetime
import sys
import time

import duckdb

from ingesta.comun.bronze import LAKE_BRONZE, RAIZ
from orquestacion.flujo import flujo_red_metropolitana

WAREHOUSE = RAIZ / "warehouse" / "red_metropolitana.duckdb"
EVIDENCIA = RAIZ / "docs" / "evidencias" / "idempotencia.md"
ESQUEMAS = ("seeds", "silver", "gold", "features", "reportes")
ORDEN_CAPAS = {"bronze": 0, "seeds": 1, "silver": 2, "gold": 3, "features": 4, "reportes": 5}


def contar():
    con = duckdb.connect()
    medidas = {}
    for carpeta in sorted(p for p in LAKE_BRONZE.iterdir() if p.is_dir() and not p.name.startswith("_")):
        patron = (carpeta / "*" / "*.parquet").as_posix()
        filas, huella = con.execute(f"select count(*), bit_xor(hash(t)) from read_parquet('{patron}') as t").fetchone()
        medidas[("bronze", carpeta.name)] = (filas, huella)
    con.execute(f"attach '{WAREHOUSE.as_posix()}' as wh (read_only)")
    tablas = con.execute(
        "select table_schema, table_name from information_schema.tables "
        "where table_catalog = 'wh' and table_type = 'BASE TABLE' "
        f"and table_schema in ({', '.join(repr(e) for e in ESQUEMAS)}) order by 1, 2"
    ).fetchall()
    for esquema, tabla in tablas:
        filas, huella = con.execute(f"select count(*), bit_xor(hash(t)) from wh.{esquema}.{tabla} as t").fetchone()
        medidas[(esquema, tabla)] = (filas, huella)
    con.close()
    return medidas


def corrida(numero):
    print(f"\n=== Corrida {numero} ===\n")
    inicio = datetime.datetime.now()
    reloj = time.perf_counter()
    ejecucion_id = flujo_red_metropolitana()
    segundos = time.perf_counter() - reloj
    return ejecucion_id, inicio, segundos, contar()


def formato_huella(valor):
    return "vacia" if valor is None else f"{int(valor) & 0xFFFFFFFFFFFFFFFF:016x}"


def main():
    primera = corrida(1)
    segunda = corrida(2)
    medidas_1, medidas_2 = primera[3], segunda[3]
    claves = sorted(set(medidas_1) | set(medidas_2), key=lambda k: (ORDEN_CAPAS.get(k[0], 9), k[1]))

    filas_tabla = []
    diferencias = 0
    for clave in claves:
        f1, h1 = medidas_1.get(clave, (None, None))
        f2, h2 = medidas_2.get(clave, (None, None))
        igual = f1 == f2 and h1 == h2
        diferencias += 0 if igual else 1
        filas_tabla.append((clave[0], clave[1], f1, f2, formato_huella(h1), formato_huella(h2), igual))

    total_1 = sum(f for f, _ in medidas_1.values())
    total_2 = sum(f for f, _ in medidas_2.values())
    resultado = "IDEMPOTENTE" if diferencias == 0 else f"NO IDEMPOTENTE: {diferencias} tablas difieren"

    lineas = [
        "# Evidencia de idempotencia",
        "",
        "Generada por `python -m orquestacion.verificar_idempotencia`. El flujo completo se corrió dos veces "
        "seguidas y después de cada corrida se contaron todas las tablas de todas las capas. La huella es el XOR "
        "del hash de cada fila: no depende del orden y cambia si cambia una sola fila.",
        "",
        "| | Corrida 1 | Corrida 2 |",
        "|---|---|---|",
        f"| Ejecución | `{primera[0]}` | `{segunda[0]}` |",
        f"| Inicio | {primera[1]:%Y-%m-%d %H:%M:%S} | {segunda[1]:%Y-%m-%d %H:%M:%S} |",
        f"| Duración | {primera[2]:.1f} s | {segunda[2]:.1f} s |",
        f"| Tablas medidas | {len(medidas_1)} | {len(medidas_2)} |",
        f"| Filas totales | {total_1:,} | {total_2:,} |",
        "",
        f"**Resultado: {resultado}**",
        "",
        "| Capa | Tabla | Filas corrida 1 | Filas corrida 2 | Huella corrida 1 | Huella corrida 2 | Igual |",
        "|---|---|---:|---:|---|---|---|",
    ]
    for capa, tabla, f1, f2, h1, h2, igual in filas_tabla:
        lineas.append(f"| {capa} | {tabla} | {f1:,} | {f2:,} | `{h1}` | `{h2}` | {'sí' if igual else '**NO**'} |")
    EVIDENCIA.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCIA.write_text("\n".join(lineas) + "\n", encoding="utf-8")

    print()
    print(f"{'capa':<10}{'tabla':<34}{'corrida 1':>12}{'corrida 2':>12}  igual")
    print("-" * 76)
    for capa, tabla, f1, f2, _, _, igual in filas_tabla:
        print(f"{capa:<10}{tabla:<34}{f1:>12,}{f2:>12,}  {'si' if igual else 'NO'}")
    print("-" * 76)
    print(f"{'total':<44}{total_1:>12,}{total_2:>12,}")
    print()
    print(resultado)
    print(f"Evidencia escrita en {EVIDENCIA.relative_to(RAIZ)}")
    print()
    sys.exit(0 if diferencias == 0 else 1)


if __name__ == "__main__":
    main()