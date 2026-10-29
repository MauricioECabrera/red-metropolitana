"""
=====================================================================
  ensemble.py · Ensemble de abandono y analisis de validacion
  Proyecto 2 · Ciencia de Datos · Red Metropolitana
  Autor: Adrian

  Evalua HistGradientBoostingClassifier con los folds compartidos.
  Compara Average Precision de entrenamiento y validacion.
  Calcula importancia por permutacion en validacion.

  Ejecutar desde la raiz del repositorio:
    python -m scripts.modelos.ensemble --corte A
=====================================================================
"""

import argparse
import json
import time

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline

from scripts.modelos.baseline import guardar_predicciones
from scripts.modelos.folds import crear_folds
from scripts.modelos.logistica import (
    CARPETA,
    VARIABLES,
    cargar_datos,
    verificar_folds,
)


PARAMETROS = {
    "learning_rate": 0.1,
    "max_iter": 100,
    "max_leaf_nodes": 15,
    "min_samples_leaf": 20,
    "l2_regularization": 1.0,
    "early_stopping": False,
    "random_state": 42,
}


def construir_pipeline():
    transformacion = ColumnTransformer(
        transformers=[
            ("numericas", "passthrough", VARIABLES),
        ],
        remainder="drop",
    )

    return Pipeline([
        ("transformacion", transformacion),
        ("clasificador", HistGradientBoostingClassifier(**PARAMETROS)),
    ])


def evaluar_ensemble(datos, particiones):
    variables = datos[VARIABLES]
    etiquetas = datos["etiqueta"].to_numpy(dtype=int)
    probabilidades = np.full(len(datos), np.nan)
    resultados = []
    importancias = []

    for numero, (entrenamiento, validacion) in enumerate(
        particiones, start=1
    ):
        print(f"\nFold {numero}/5: entrenando...", flush=True)

        modelo = construir_pipeline()
        inicio = time.perf_counter()

        modelo.fit(
            variables.iloc[entrenamiento],
            etiquetas[entrenamiento],
        )

        segundos_entrenamiento = time.perf_counter() - inicio
        inicio = time.perf_counter()

        prob_entrenamiento = modelo.predict_proba(
            variables.iloc[entrenamiento]
        )[:, 1]

        prob_validacion = modelo.predict_proba(
            variables.iloc[validacion]
        )[:, 1]

        segundos_prediccion = time.perf_counter() - inicio
        probabilidades[validacion] = prob_validacion

        ap_entrenamiento = average_precision_score(
            etiquetas[entrenamiento],
            prob_entrenamiento,
        )

        ap_validacion = average_precision_score(
            etiquetas[validacion],
            prob_validacion,
        )

        print(
            f"AP entrenamiento: {ap_entrenamiento:.6f} | "
            f"AP validacion: {ap_validacion:.6f}",
            flush=True,
        )

        print("Calculando importancia en validacion...", flush=True)
        inicio = time.perf_counter()

        importancia = permutation_importance(
            modelo,
            variables.iloc[validacion],
            etiquetas[validacion],
            scoring="average_precision",
            n_repeats=10,
            random_state=42,
            n_jobs=1,
        )

        segundos_importancia = time.perf_counter() - inicio

        resultados.append({
            "modelo": "ensemble",
            "fold": numero,
            "ap_entrenamiento": ap_entrenamiento,
            "ap_validacion": ap_validacion,
            "segundos_entrenamiento": segundos_entrenamiento,
            "segundos_prediccion": segundos_prediccion,
            "segundos_importancia": segundos_importancia,
        })

        for indice, variable in enumerate(VARIABLES):
            for repeticion, valor in enumerate(
                importancia.importances[indice], start=1
            ):
                importancias.append({
                    "variable": variable,
                    "fold": numero,
                    "repeticion": repeticion,
                    "caida_ap": valor,
                })

    if not np.isfinite(probabilidades).all():
        raise ValueError("Hay unidades sin prediccion de validacion.")

    return (
        pd.DataFrame(resultados),
        pd.DataFrame(importancias),
        probabilidades,
    )


def graficar_importancias(resumen):
    filas = resumen.sort_values("importancia_media")
    figura, eje = plt.subplots(figsize=(9, 5))

    eje.barh(
        filas["variable"],
        filas["importancia_media"],
        xerr=filas["importancia_desviacion"],
        capsize=3,
    )

    eje.axvline(0, color="black", linewidth=1)
    eje.set_xlabel("Caida de Average Precision al permutar")
    eje.set_title("Importancia de variables en validacion")
    figura.tight_layout()
    figura.savefig(CARPETA / "importancias_ensemble.png", dpi=160)
    plt.close(figura)


def main():
    argumentos = argparse.ArgumentParser()
    argumentos.add_argument("--corte", required=True, choices=["A"])
    argumentos.parse_args()

    archivo_comparacion = CARPETA / "comparacion_fase1.csv"

    if not archivo_comparacion.exists():
        raise ValueError("Primero ejecuta logistica.py.")

    inicio_total = time.perf_counter()
    datos = cargar_datos()
    etiquetas = datos["etiqueta"].to_numpy(dtype=int)
    particiones = list(crear_folds().split(datos[VARIABLES], etiquetas))

    verificar_folds(datos, particiones)

    resultados, importancias, probabilidades = evaluar_ensemble(
        datos,
        particiones,
    )

    resumen = resultados.groupby("modelo", as_index=False).agg(
        ap_entrenamiento_media=("ap_entrenamiento", "mean"),
        ap_validacion_media=("ap_validacion", "mean"),
        ap_validacion_desviacion=("ap_validacion", "std"),
    )

    resumen_importancias = importancias.groupby(
        "variable", as_index=False
    ).agg(
        importancia_media=("caida_ap", "mean"),
        importancia_desviacion=("caida_ap", "std"),
    ).sort_values("importancia_media", ascending=False)

    fase1 = pd.read_csv(archivo_comparacion)
    comparacion = pd.concat(
        [fase1, resumen],
        ignore_index=True,
        sort=False,
    )

    comparacion["brecha_ap"] = (
        comparacion["ap_entrenamiento_media"]
        - comparacion["ap_validacion_media"]
    )

    nuevas = datos[["unidad_id", "fecha_corte"]].copy()
    nuevas["modelo"] = "ensemble"
    nuevas["prob"] = probabilidades
    guardar_predicciones(nuevas)

    resultados.to_csv(CARPETA / "ensemble_por_fold.csv", index=False)
    comparacion.to_csv(CARPETA / "comparacion_fase2.csv", index=False)
    importancias.to_csv(
        CARPETA / "importancias_ensemble_detalle.csv",
        index=False,
    )
    resumen_importancias.to_csv(
        CARPETA / "importancias_ensemble.csv",
        index=False,
    )

    graficar_importancias(resumen_importancias)

    segundos_total = time.perf_counter() - inicio_total
    registro = {
        "parametros": PARAMETROS,
        "unidades": len(datos),
        "variables": VARIABLES,
        "repeticiones_permutacion_por_fold": 10,
        "segundos_entrenamiento_total": float(
            resultados["segundos_entrenamiento"].sum()
        ),
        "segundos_prediccion_total": float(
            resultados["segundos_prediccion"].sum()
        ),
        "segundos_importancia_total": float(
            resultados["segundos_importancia"].sum()
        ),
        "segundos_total": segundos_total,
    }

    (CARPETA / "configuracion_ensemble.json").write_text(
        json.dumps(registro, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    columnas = [
        "modelo",
        "ap_entrenamiento_media",
        "ap_validacion_media",
        "ap_validacion_desviacion",
        "brecha_ap",
    ]

    print("\nCOMPARACION DE FASE 2")
    print(comparacion[columnas].round(6).to_string(index=False))

    print("\nIMPORTANCIAS EN VALIDACION")
    print(resumen_importancias.round(6).to_string(index=False))

    logisticas = fase1[
        fase1["modelo"].isin(["logistica_l1", "logistica_l2"])
    ]

    if not logisticas.empty:
        ap_logistica = logisticas["ap_validacion_media"].max()
        ap_ensemble = resumen.iloc[0]["ap_validacion_media"]

        print(
            "\nDiferencia AP ensemble - mejor logistica: "
            f"{ap_ensemble - ap_logistica:.6f}"
        )

    print(
        "\nTiempo de entrenamiento, cinco folds: "
        f"{registro['segundos_entrenamiento_total']:.2f} segundos"
    )
    print(f"Tiempo total: {segundos_total:.2f} segundos")
    print("Predicciones del ensemble agregadas al CSV.")


if __name__ == "__main__":
    main()