"""
=====================================================================
  baseline.py · Lineas base de abandono para el corte A
  Proyecto 2 · Ciencia de Datos · Red Metropolitana
  Autor: Adrian

  Evalua una referencia constante con la tasa positiva de todo A,
  segun el enunciado, y un ranking fijo de inactividad reciente.

  La metrica utilizada es Average Precision.
  El ranking es un puntaje y no una probabilidad calibrada.

  Ejecutar desde la raiz del repositorio:
    python -m scripts.modelos.baseline --corte A
=====================================================================
"""

import argparse
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from scripts.modelos.folds import crear_folds


RAIZ = Path(__file__).resolve().parents[2]
WAREHOUSE = RAIZ / "warehouse" / "red_metropolitana.duckdb"
SALIDA = RAIZ / "scripts" / "modelos" / "predicciones_cv.csv"
ASIGNACION = RAIZ / "scripts" / "modelos" / "asignacion_folds.csv"

FECHA_CORTE = "2026-07-01"
COLUMNAS_SALIDA = ["unidad_id", "fecha_corte", "modelo", "prob"]


def cargar_datos():
    with duckdb.connect(str(WAREHOUSE), read_only=True) as conexion:
        datos = conexion.execute(
            """
            select
                unidad_id,
                fecha_corte,
                dias_desde_ultimo_viaje,
                etiqueta
            from features.features_corte
            where fecha_corte = cast(? as date)
            order by unidad_id
            """,
            [FECHA_CORTE],
        ).df()

    if datos.empty:
        raise ValueError("El corte A no contiene filas.")

    if datos.isna().any().any():
        raise ValueError("Hay valores nulos en las columnas requeridas.")

    if datos.duplicated(["unidad_id", "fecha_corte"]).any():
        raise ValueError("Hay claves duplicadas en el corte A.")

    if not datos["etiqueta"].isin([0, 1]).all():
        raise ValueError("Las etiquetas deben ser 0 o 1.")

    for clase in (0, 1):
        if datos["etiqueta"].eq(clase).sum() < 5:
            raise ValueError(f"La clase {clase} tiene menos de cinco casos.")

    if not datos["dias_desde_ultimo_viaje"].between(1, 28).all():
        raise ValueError("La recencia debe estar entre 1 y 28 dias.")

    datos["unidad_id"] = datos["unidad_id"].astype(str)
    datos["fecha_corte"] = (
        pd.to_datetime(datos["fecha_corte"]).dt.strftime("%Y-%m-%d")
    )

    return datos


def evaluar_baselines(datos):
    etiquetas = datos["etiqueta"].to_numpy(dtype=int)
    tasa = float(etiquetas.mean())

    puntajes = {
        "baseline_tasa": np.full(len(datos), tasa),
        "baseline_ranking": (
            datos["dias_desde_ultimo_viaje"].to_numpy(dtype=float) / 28.0
        ),
    }

    particiones = list(crear_folds().split(datos, etiquetas))
    asignacion = np.zeros(len(datos), dtype=int)
    resultados = []
    predicciones = []

    for numero, (entrenamiento, validacion) in enumerate(particiones, start=1):
        asignacion[validacion] = numero

        for nombre, valores in puntajes.items():
            ap_entrenamiento = average_precision_score(
                etiquetas[entrenamiento],
                valores[entrenamiento],
            )
            ap_validacion = average_precision_score(
                etiquetas[validacion],
                valores[validacion],
            )

            resultados.append({
                "modelo": nombre,
                "fold": numero,
                "ap_entrenamiento": ap_entrenamiento,
                "ap_validacion": ap_validacion,
            })

            filas = datos.iloc[validacion][
                ["unidad_id", "fecha_corte"]
            ].copy()
            filas["modelo"] = nombre
            filas["prob"] = valores[validacion]
            predicciones.append(filas)

    if np.any(asignacion == 0):
        raise ValueError("Hay unidades sin fold de validacion.")

    tabla_folds = datos[["unidad_id", "fecha_corte"]].copy()
    tabla_folds["fold"] = asignacion

    return (
        pd.DataFrame(resultados),
        pd.concat(predicciones, ignore_index=True),
        tabla_folds,
    )


def guardar_predicciones(nuevas):
    claves = ["unidad_id", "fecha_corte", "modelo"]

    if nuevas.duplicated(claves).any():
        raise ValueError("Las nuevas predicciones tienen claves duplicadas.")

    if nuevas["prob"].isna().any() or not nuevas["prob"].between(0, 1).all():
        raise ValueError("Los puntajes deben estar entre cero y uno.")

    if SALIDA.exists():
        anteriores = pd.read_csv(
            SALIDA,
            dtype={"unidad_id": str, "fecha_corte": str, "modelo": str},
        )

        if list(anteriores.columns) != COLUMNAS_SALIDA:
            raise ValueError("El CSV existente no cumple el contrato.")

        reemplazar = (
            anteriores["modelo"].isin(nuevas["modelo"].unique())
            & anteriores["fecha_corte"].eq(FECHA_CORTE)
        )

        completas = pd.concat(
            [anteriores.loc[~reemplazar], nuevas],
            ignore_index=True,
        )
    else:
        completas = nuevas.copy()

    if completas.duplicated(claves).any():
        raise ValueError("El CSV final contiene claves duplicadas.")

    completas = completas[COLUMNAS_SALIDA].sort_values(claves)

    temporal = SALIDA.with_suffix(".csv.tmp")
    completas.to_csv(temporal, index=False)
    temporal.replace(SALIDA)


def main():
    argumentos = argparse.ArgumentParser()
    argumentos.add_argument("--corte", required=True, choices=["A"])
    argumentos.parse_args()

    datos = cargar_datos()
    resultados, predicciones, asignacion = evaluar_baselines(datos)

    guardar_predicciones(predicciones)
    asignacion.to_csv(ASIGNACION, index=False)

    resumen = resultados.groupby("modelo", sort=False).agg(
        ap_entrenamiento_media=("ap_entrenamiento", "mean"),
        ap_validacion_media=("ap_validacion", "mean"),
        ap_validacion_desviacion=("ap_validacion", "std"),
    )

    print(f"Unidades del corte A: {len(datos):,}")
    print(f"Positivos: {datos['etiqueta'].eq(1).sum():,}")
    print(f"Tasa positiva: {datos['etiqueta'].mean():.6f}")

    print("\nRESULTADOS POR FOLD")
    print(resultados.round(6).to_string(index=False))

    print("\nRESUMEN")
    print(resumen.round(6).to_string())

    print("\nPREDICCIONES GENERADAS")
    print(predicciones.groupby("modelo").size().to_string())
    print(f"\nCSV: {SALIDA}")
    print(f"Asignacion de folds: {ASIGNACION}")


if __name__ == "__main__":
    main()