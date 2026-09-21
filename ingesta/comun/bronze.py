"""
=====================================================================
  bronze.py  ·  Contrato de escritura a la capa Bronze
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Toda fuente que entra a Bronze pasa por la funcion cargar().
  Garantiza el mismo formato, las mismas columnas de metadata y la
  misma regla de idempotencia para las tres vias de ingesta.

  Ruta de escritura:
    lake/bronze/<fuente>/fecha_ingesta=AAAA-MM-DD/<lote_id>.parquet

  Columnas de metadata agregadas a cada fila:
    _hash_fila       md5 del contenido de la fila, independiente del
                     fin de linea del archivo de origen
    _fila_origen     numero de fila dentro del archivo crudo
    _archivo_origen  nombre del archivo crudo
    _lote_id         huella del archivo crudo
    _ingesta_ts      fecha y hora local de la carga

  Idempotencia: el lote_id es la huella del contenido del archivo.
  Si ya existe un parquet con ese lote_id, la carga se omite y se
  reportan las filas ya cargadas.
=====================================================================
"""
import csv
import datetime
import hashlib
import os
import pathlib

import duckdb
from dotenv import load_dotenv

RAIZ = pathlib.Path(__file__).resolve().parents[2]
load_dotenv(RAIZ / ".env")


def _ruta(variable, defecto):
    valor = pathlib.Path(os.getenv(variable, defecto))
    return valor if valor.is_absolute() else (RAIZ / valor).resolve()


DATOS_CRUDOS = _ruta("RUTA_DATOS_CRUDOS", "datos_red")
LAKE_BRONZE = _ruta("RUTA_LAKE_BRONZE", "lake/bronze")
STAGING = _ruta("RUTA_STAGING", "lake/staging")
BITACORA_CARGAS = LAKE_BRONZE / "_control" / "bitacora_cargas.csv"
COLUMNAS_BITACORA = ["ejecucion_ts", "fuente", "archivo_origen", "lote_id", "filas", "accion", "particion"]


def huella_archivo(ruta):
    contenido = pathlib.Path(ruta).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(contenido).hexdigest()[:16]


def lector_csv(ruta):
    return f"read_csv('{ruta.as_posix()}', all_varchar = true, header = true)"


def lector_jsonl(ruta):
    return f"(select json as payload from read_json_objects('{ruta.as_posix()}', format = 'newline_delimited'))"


def _lote_existente(fuente, lote_id):
    return next(iter((LAKE_BRONZE / fuente).glob(f"fecha_ingesta=*/{lote_id}.parquet")), None)


def _registrar(fila):
    BITACORA_CARGAS.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not BITACORA_CARGAS.exists()
    with BITACORA_CARGAS.open("a", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS_BITACORA)
        if nuevo:
            escritor.writeheader()
        escritor.writerow(fila)


def cargar(fuente, archivo, lector=lector_csv, directorio=None):
    ruta = (pathlib.Path(directorio) if directorio else DATOS_CRUDOS) / archivo
    lote_id = huella_archivo(ruta)
    ahora = datetime.datetime.now().replace(microsecond=0)
    con = duckdb.connect()
    con.execute("set threads = 1")
    con.execute("set preserve_insertion_order = true")

    existente = _lote_existente(fuente, lote_id)
    if existente:
        filas = con.sql(f"select count(*) from read_parquet('{existente.as_posix()}')").fetchone()[0]
        accion = "OMITIDO"
        particion = existente.parent.name
    else:
        particion = f"fecha_ingesta={ahora:%Y-%m-%d}"
        destino = LAKE_BRONZE / fuente / particion / f"{lote_id}.parquet"
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporal = destino.with_name(destino.name + ".tmp")
        con.execute(f"""
            copy (
                with origen as (
                    select * from {lector(ruta)}
                )
                select
                    *,
                    md5(to_json(row(*COLUMNS(*)))) as _hash_fila,
                    row_number() over () as _fila_origen,
                    '{archivo}' as _archivo_origen,
                    '{lote_id}' as _lote_id,
                    timestamp '{ahora:%Y-%m-%d %H:%M:%S}' as _ingesta_ts
                from origen
            ) to '{temporal.as_posix()}' (format parquet, compression zstd)
        """)
        os.replace(temporal, destino)
        filas = con.sql(f"select count(*) from read_parquet('{destino.as_posix()}')").fetchone()[0]
        accion = "CARGADO"

    con.close()
    resultado = {
        "ejecucion_ts": f"{ahora:%Y-%m-%d %H:%M:%S}",
        "fuente": fuente,
        "archivo_origen": archivo,
        "lote_id": lote_id,
        "filas": filas,
        "accion": accion,
        "particion": particion,
    }
    _registrar(resultado)
    return resultado


def imprimir_resumen(resultados):
    print()
    print(f"{'fuente':<28}{'filas':>12}  {'accion':<10}{'lote_id':<18}{'particion'}")
    print("-" * 92)
    for r in resultados:
        print(f"{r['fuente']:<28}{r['filas']:>12,}  {r['accion']:<10}{r['lote_id']:<18}{r['particion']}")
    print("-" * 92)
    print(f"{'total':<28}{sum(r['filas'] for r in resultados):>12,}")
    print()