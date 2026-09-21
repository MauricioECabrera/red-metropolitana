"""
=====================================================================
  flujo.py  ·  Orquestacion del pipeline completo con Prefect
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Corre todas las etapas en orden, de los archivos crudos al Gold
  publicado para el tablero:

    1. Catalogos            via batch
    2. MetroRiel            via batch
    3. Transurbano          via batch        si ya esta integrado
    4. Padron               via CDC
    5. Productor Kafka      via streaming    si ya esta integrado
    6. Consumidor Kafka     via streaming    si ya esta integrado
    7. dbt build            Bronze, Silver, Gold, features y reportes
    8. Publicar Gold        archivo del tablero
    9. Exportar modelo      DDL y diagrama

  Las etapas de ingesta tienen reintentos. Una etapa cuyo modulo
  todavia no existe en el repositorio se registra como OMITIDA.
  Cada corrida queda en lake/bronze/_control/ejecuciones.csv con
  la duracion de cada etapa.

  Todas las etapas son idempotentes: correr el flujo dos veces
  produce exactamente el mismo resultado.

  Ejecutar desde la raiz del repositorio:
    python -m orquestacion.flujo
=====================================================================
"""
import csv
import datetime
import importlib
import importlib.util
import os
import pathlib
import runpy
import shutil
import socket
import subprocess
import sys
import time

from prefect import flow, task

from ingesta.comun.bronze import LAKE_BRONZE, RAIZ

BITACORA_EJECUCIONES = LAKE_BRONZE / "_control" / "ejecuciones.csv"
COLUMNAS_BITACORA = ["ejecucion_id", "etapa", "estado", "segundos", "inicio"]

INGESTAS = [
    ("catalogos", "ingesta.batch.cargar_catalogos", False),
    ("metroriel", "ingesta.batch.cargar_metroriel", False),
    ("transurbano", "ingesta.batch.cargar_transurbano", False),
    ("padron_cdc", "ingesta.cdc.cargar_cdc", False),
    ("productor_kafka", "ingesta.streaming.productores.productor", True),
    ("consumidor_kafka", "ingesta.streaming.consumidores.consumidor", True),
]


def _modulo_existe(nombre):
    try:
        return importlib.util.find_spec(nombre) is not None
    except ModuleNotFoundError:
        return False


def _kafka_disponible():
    servidor = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
    host, puerto = servidor.split(",")[0].split(":")
    try:
        with socket.create_connection((host, int(puerto)), timeout=3):
            return True
    except OSError:
        return False


def _ejecutable_dbt():
    carpeta = pathlib.Path(sys.executable).parent
    return shutil.which("dbt", path=str(carpeta)) or shutil.which("dbt")


def _registrar(ejecucion_id, etapa, estado, segundos, inicio):
    BITACORA_EJECUCIONES.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not BITACORA_EJECUCIONES.exists()
    with BITACORA_EJECUCIONES.open("a", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS_BITACORA)
        if nuevo:
            escritor.writeheader()
        escritor.writerow({
            "ejecucion_id": ejecucion_id,
            "etapa": etapa,
            "estado": estado,
            "segundos": f"{segundos:.2f}",
            "inicio": f"{inicio:%Y-%m-%d %H:%M:%S}",
        })


@task(retries=2, retry_delay_seconds=5)
def ingestar(modulo):
    importlib.import_module(modulo).main()


@task
def construir_dbt():
    dbt = _ejecutable_dbt()
    if not dbt:
        raise RuntimeError("No se encontro dbt. Activar el entorno virtual .venv")
    entorno = {**os.environ, "DBT_PROFILES_DIR": str(RAIZ / "dbt")}
    if not (RAIZ / "dbt" / "dbt_packages").exists():
        subprocess.run([dbt, "deps"], cwd=RAIZ / "dbt", env=entorno, check=True)
    subprocess.run([dbt, "build"], cwd=RAIZ / "dbt", env=entorno, check=True)


@task
def ejecutar_script(ruta):
    runpy.run_path(str(ruta), run_name="__main__")


@flow(name="red-metropolitana", log_prints=True)
def flujo_red_metropolitana():
    ejecucion_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    resultados = []

    def etapa(nombre, funcion, *argumentos):
        inicio = datetime.datetime.now()
        reloj = time.perf_counter()
        try:
            funcion(*argumentos)
        except BaseException:
            segundos = time.perf_counter() - reloj
            _registrar(ejecucion_id, nombre, "ERROR", segundos, inicio)
            resultados.append((nombre, "ERROR", segundos))
            raise
        segundos = time.perf_counter() - reloj
        _registrar(ejecucion_id, nombre, "OK", segundos, inicio)
        resultados.append((nombre, "OK", segundos))

    requiere_kafka = [m for _, m, k in INGESTAS if k and _modulo_existe(m)]
    if requiere_kafka and not _kafka_disponible():
        raise RuntimeError("Kafka no responde. Levantarlo con: docker compose up -d")

    for nombre, modulo, _ in INGESTAS:
        if _modulo_existe(modulo):
            etapa(nombre, ingestar, modulo)
        else:
            _registrar(ejecucion_id, nombre, "OMITIDA", 0, datetime.datetime.now())
            resultados.append((nombre, "OMITIDA", 0.0))

    etapa("dbt_build", construir_dbt)
    etapa("publicar_gold", ejecutar_script, RAIZ / "scripts" / "publicar_gold.py")
    etapa("exportar_modelo", ejecutar_script, RAIZ / "scripts" / "exportar_modelo.py")

    print()
    print(f"Ejecucion {ejecucion_id}")
    print(f"{'etapa':<22}{'estado':<10}{'segundos':>10}")
    print("-" * 42)
    for nombre, estado, segundos in resultados:
        print(f"{nombre:<22}{estado:<10}{segundos:>10.2f}")
    print("-" * 42)
    print(f"{'total':<32}{sum(s for _, _, s in resultados):>10.2f}")
    print()
    return ejecucion_id


if __name__ == "__main__":
    flujo_red_metropolitana()