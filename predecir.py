"""
=====================================================================
  predecir.py  ·  Prediccion de abandono con el modelo congelado
  Proyecto 2  ·  Ciencia de Datos  ·  Red Metropolitana

  python predecir.py --datos <carpeta> --fecha-corte 2026-08-30
    [--salida predicciones/predicciones_2026-08-30.csv]

  Carga modelos/modelo_churn_v1.joblib y nunca llama a fit(): el
  entrenamiento es responsabilidad exclusiva de entrenar_modelo.py.
  Las variables que lee de features.features_corte son las que dice
  el .json de metadatos del modelo, no una lista escrita a mano, asi
  que el script no cambia cuando cambie el modelo elegido.

  Antes de predecir compara, para cada uno de los nueve archivos
  crudos de la carpeta de datos, sus filas contra las que ya estan
  cargadas en Bronze. Si no coinciden, el almacen no corresponde a
  esos datos y el script se detiene sin escribir ningun CSV: es la
  comprobacion que evita que la prueba de invarianza quede invalida
  por un almacen desactualizado.

  Expone predecir(datos, fecha_corte, salida) para que el flujo la
  pueda llamar directamente.
=====================================================================
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import duckdb
import joblib
import sklearn

from ingesta.comun.bronze import lector_csv, lector_jsonl
from scripts.conteos_bronze import contar_bronze
from scripts.modelos.baseline import RAIZ, WAREHOUSE


CARPETA_MODELOS = RAIZ / "modelos"
RUTA_MODELO = CARPETA_MODELOS / "modelo_churn_v1.joblib"
RUTA_METADATOS = CARPETA_MODELOS / "modelo_churn_v1.json"
CARPETA_PREDICCIONES = RAIZ / "predicciones"

ARCHIVOS = {
    "tm_estaciones.csv": "tm_estaciones",
    "tu_paradas.csv": "tu_paradas",
    "mr_estaciones.csv": "mr_estaciones",
    "am_estaciones.csv": "am_estaciones",
    "cdc_padron_usuarios.csv": "cdc_padron_usuarios",
    "transurbano_transacciones.csv": "transurbano_transacciones",
    "transmetro_validaciones.csv": "transmetro_validaciones",
    "aerometro_boardings.csv": "aerometro_boardings",
    "metroriel_viajes.jsonl": "metroriel_viajes",
}

LECTORES = {
    "metroriel_viajes.jsonl": lector_jsonl,
}


class CorteVacio(ValueError):
    """El corte pedido no tiene filas con los datos actualmente cargados."""


def contar_carpeta(conexion, carpeta, archivo):
    ruta = carpeta / archivo
    lector = LECTORES.get(archivo, lector_csv)
    return conexion.execute(f"select count(*) from {lector(ruta)}").fetchone()[0]


def verificar_consistencia(carpeta):
    conexion = duckdb.connect()

    for archivo, fuente in ARCHIVOS.items():
        filas_carpeta = contar_carpeta(conexion, carpeta, archivo)
        filas_bronze = contar_bronze(conexion, fuente)

        if filas_carpeta != filas_bronze:
            conexion.close()
            raise RuntimeError(
                "El almacén no corresponde a la carpeta de datos: corré el flujo"
            )

    conexion.close()


def asegurar_corte(fecha_corte):
    with duckdb.connect(str(WAREHOUSE), read_only=True) as conexion:
        existe = conexion.execute(
            """
            select count(*) from features.features_corte
            where fecha_corte = cast(? as date)
            """,
            [fecha_corte],
        ).fetchone()[0]

    if existe:
        return

    entorno = {**os.environ, "DBT_PROFILES_DIR": str(RAIZ / "dbt")}
    dbt = [sys.executable, "-m", "dbt.cli.main"]
    subprocess.run(
        [
            *dbt, "build", "--select", "poblacion", "features_corte",
            "--vars", json.dumps({"fecha_corte": fecha_corte}),
        ],
        cwd=RAIZ / "dbt",
        env=entorno,
        check=True,
    )


def cargar_metadatos():
    if not RUTA_MODELO.exists() or not RUTA_METADATOS.exists():
        raise RuntimeError(
            f"No existe {RUTA_MODELO} o {RUTA_METADATOS}. Primero corré "
            "scripts/entrenar_modelo.py."
        )

    return json.loads(RUTA_METADATOS.read_text(encoding="utf-8"))


def cargar_corte_a_predecir(fecha_corte, variables):
    columnas = ", ".join(f"f.{v}" for v in variables)

    with duckdb.connect(str(WAREHOUSE), read_only=True) as conexion:
        datos = conexion.execute(
            f"""
            select f.unidad_id, {columnas}, t.tarjetas
            from features.features_corte f
            left join features.unidad_tarjetas t on f.unidad_id = t.unidad_id
            where f.fecha_corte = cast(? as date)
            order by f.unidad_id
            """,
            [fecha_corte],
        ).df()

    if datos.empty:
        raise CorteVacio(f"El corte {fecha_corte} esta vacio.")

    if datos.duplicated("unidad_id").any():
        raise ValueError(f"Hay unidades duplicadas en el corte {fecha_corte}.")

    if datos[variables].isna().any().any():
        raise ValueError(f"Hay nulos en las variables del corte {fecha_corte}.")

    if datos["tarjetas"].isna().any():
        raise ValueError(
            f"Hay unidades sin tarjetas en features.unidad_tarjetas para "
            f"el corte {fecha_corte}."
        )

    datos["unidad_id"] = datos["unidad_id"].astype(str)
    datos[variables] = datos[variables].astype(float)

    return datos


def predecir(datos, fecha_corte, salida=None):
    inicio = time.perf_counter()
    carpeta = Path(datos)

    if salida is None:
        salida = CARPETA_PREDICCIONES / f"predicciones_{fecha_corte}.csv"
    else:
        salida = Path(salida)

    verificar_consistencia(carpeta)
    asegurar_corte(fecha_corte)

    metadatos = cargar_metadatos()
    variables = metadatos["variables"]

    corte = cargar_corte_a_predecir(fecha_corte, variables)

    modelo = joblib.load(RUTA_MODELO)

    if sklearn.__version__ != metadatos["version_scikit_learn"]:
        print(
            f"Aviso: scikit-learn instalado ({sklearn.__version__}) "
            f"difiere del usado para entrenar ({metadatos['version_scikit_learn']})."
        )

    puntaje = modelo.predict_proba(corte[variables])[:, 1]
    umbral = metadatos["umbral"]
    contactar = (puntaje >= umbral).astype(int)

    resultado = corte[["unidad_id", "tarjetas"]].copy()
    resultado["puntaje"] = puntaje
    resultado["contactar"] = contactar

    salida.parent.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(salida, index=False, float_format="%.12f")

    segundos = time.perf_counter() - inicio

    print(f"Filas escritas: {len(resultado):,}")
    print(f"Contactados: {int(resultado['contactar'].sum()):,}")
    print(f"Umbral usado: {umbral:.2f}")
    print(f"Segundos: {segundos:.2f}")
    print(f"Salida: {salida}")

    return salida


def main():
    argumentos = argparse.ArgumentParser()
    argumentos.add_argument("--datos", required=True)
    argumentos.add_argument("--fecha-corte", required=True)
    argumentos.add_argument("--salida", default=None)
    parametros = argumentos.parse_args()

    predecir(parametros.datos, parametros.fecha_corte, parametros.salida)


if __name__ == "__main__":
    main()
