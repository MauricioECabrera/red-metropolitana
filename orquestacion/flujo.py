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
   10. Conteos de Bronze    filas esperadas contra filas cargadas
   11. Tiempos              segundos por etapa de la ejecucion
   12. Historial            cuantas corridas hay y cuando se hicieron

  Las etapas de ingesta tienen reintentos. Una etapa cuyo modulo
  todavia no existe en el repositorio se registra como OMITIDA.
  Si hay etapas de streaming, el flujo levanta Kafka con
  docker compose up -d --wait antes de ingestar.
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


def _corridas():
    if not BITACORA_EJECUCIONES.exists():
        return []
    with BITACORA_EJECUCIONES.open(newline="", encoding="utf-8") as f:
        registros = list(csv.DictReader(f))
    corridas = {}
    for r in registros:
        c = corridas.setdefault(r["ejecucion_id"], {"inicio": r["inicio"], "segundos": 0.0, "estado": "OK"})
        c["segundos"] += float(r["segundos"])
        if r["estado"] == "ERROR":
            c["estado"] = "ERROR"
    return list(corridas.items())


def _imprimir_historial():
    corridas = _corridas()
    print(f"Corridas registradas: {len(corridas)}")
    print(f"{'n':>3}  {'ejecucion':<17}{'inicio':<21}{'segundos':>9}  estado")
    print("-" * 62)
    for numero, (ejecucion_id, c) in enumerate(corridas, start=1):
        print(f"{numero:>3}  {ejecucion_id:<17}{c['inicio']:<21}{c['segundos']:>9.2f}  {c['estado']}")
    print("-" * 62)
    print()


@task(retries=2, retry_delay_seconds=5)
def ingestar(modulo):
    importlib.import_module(modulo).main()


@task
def construir_dbt():
    entorno = {**os.environ, "DBT_PROFILES_DIR": str(RAIZ / "dbt")}
    dbt = [sys.executable, "-m", "dbt.cli.main"]
    if not (RAIZ / "dbt" / "dbt_packages").exists():
        subprocess.run([*dbt, "deps"], cwd=RAIZ / "dbt", env=entorno, check=True)
    subprocess.run([*dbt, "build"], cwd=RAIZ / "dbt", env=entorno, check=True)


@task
def ejecutar_script(ruta):
    runpy.run_path(str(ruta), run_name="__main__")


@task
def levantar_kafka():
    subprocess.run(["docker", "compose", "up", "-d", "--wait"], cwd=RAIZ, check=True)


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
    if requiere_kafka:
        etapa("kafka", levantar_kafka)
        if not _kafka_disponible():
            raise RuntimeError("Kafka no responde despues de docker compose up -d --wait")

    for nombre, modulo, _ in INGESTAS:
        if _modulo_existe(modulo):
            etapa(nombre, ingestar, modulo)
        else:
            _registrar(ejecucion_id, nombre, "OMITIDA", 0, datetime.datetime.now())
            resultados.append((nombre, "OMITIDA", 0.0))

    etapa("dbt_build", construir_dbt)
    etapa("publicar_gold", ejecutar_script, RAIZ / "scripts" / "publicar_gold.py")
    etapa("exportar_modelo", ejecutar_script, RAIZ / "scripts" / "exportar_modelo.py")
    etapa("conteos_bronze", ejecutar_script, RAIZ / "scripts" / "conteos_bronze.py")
    ejecutar_script(RAIZ / "scripts" / "tiempos_flujo.py")

    print()
    print(f"Ejecucion {ejecucion_id}")
    print(f"{'etapa':<22}{'estado':<10}{'segundos':>10}")
    print("-" * 42)
    for nombre, estado, segundos in resultados:
        print(f"{nombre:<22}{estado:<10}{segundos:>10.2f}")
    print("-" * 42)
    print(f"{'total':<32}{sum(s for _, _, s in resultados):>10.2f}")
    print()
    _imprimir_historial()
    return ejecucion_id


if __name__ == "__main__":
    flujo_red_metropolitana()