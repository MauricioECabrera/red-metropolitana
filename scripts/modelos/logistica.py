"""
=====================================================================
  logistica.py · Regresion logistica regularizada del corte A
  Proyecto 2 · Ciencia de Datos · Red Metropolitana
  Autor: Adrian

  Compara penalizaciones L1 y L2 mediante cinco folds compartidos.
  El escalado se ajusta dentro del entrenamiento de cada fold.
  Selecciona la configuracion por Average Precision de validacion.

  Ejecutar desde la raiz del repositorio:
    python -m scripts.modelos.logistica --corte A
=====================================================================
"""

import argparse
import time
import warnings

import duckdb
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from scripts.modelos.baseline import (
    ASIGNACION,
    FECHA_CORTE,
    RAIZ,
    WAREHOUSE,
    evaluar_baselines,
    guardar_predicciones,
)
from scripts.modelos.folds import crear_folds


VARIABLES = [
    "viajes_28d",
    "dias_desde_ultimo_viaje",
    "gasto_28d_q",
    "operadores_distintos_28d",
    "abordajes_fin_semana_28d",
]

LAMBDAS = [0.001, 0.01, 0.1, 1.0, 10.0, 100.0]
CARPETA = RAIZ / "scripts" / "modelos"


def cargar_datos():
    columnas = ", ".join(VARIABLES)

    with duckdb.connect(str(WAREHOUSE), read_only=True) as conexion:
        datos = conexion.execute(
            f"""
            select unidad_id, fecha_corte, {columnas}, etiqueta
            from features.features_corte
            where fecha_corte = cast(? as date)
            order by unidad_id
            """,
            [FECHA_CORTE],
        ).df()

    if datos.empty:
        raise ValueError("El corte A esta vacio.")

    if datos.isna().any().any():
        raise ValueError("Hay nulos; revisar antes de entrenar.")

    if datos.duplicated(["unidad_id", "fecha_corte"]).any():
        raise ValueError("Hay claves duplicadas.")

    if not datos["etiqueta"].isin([0, 1]).all():
        raise ValueError("Hay etiquetas distintas de 0 y 1.")

    for clase in (0, 1):
        if datos["etiqueta"].eq(clase).sum() < 5:
            raise ValueError(f"La clase {clase} tiene menos de cinco casos.")

    datos[VARIABLES] = datos[VARIABLES].astype(float)

    if not np.isfinite(datos[VARIABLES].to_numpy()).all():
        raise ValueError("Hay valores no finitos.")

    datos["unidad_id"] = datos["unidad_id"].astype(str)
    datos["fecha_corte"] = (
        pd.to_datetime(datos["fecha_corte"]).dt.strftime("%Y-%m-%d")
    )

    return datos


def construir_pipeline(penalizacion, lambda_valor):
    transformacion = ColumnTransformer(
        transformers=[
            ("numericas", StandardScaler(), VARIABLES),
        ],
        remainder="drop",
    )

    clasificador = LogisticRegression(
        penalty=penalizacion,
        C=1.0 / lambda_valor,
        solver="liblinear",
        max_iter=5000,
        random_state=42,
    )

    return Pipeline([
        ("transformacion", transformacion),
        ("clasificador", clasificador),
    ])


def verificar_folds(datos, particiones):
    if not ASIGNACION.exists():
        raise ValueError("Primero ejecuta baseline.py para guardar los folds.")

    actual = datos[["unidad_id", "fecha_corte"]].copy()
    actual["fold"] = 0

    for numero, (_, validacion) in enumerate(particiones, start=1):
        actual.loc[validacion, "fold"] = numero

    anterior = pd.read_csv(
        ASIGNACION,
        dtype={"unidad_id": str, "fecha_corte": str},
    )

    claves = ["unidad_id", "fecha_corte"]

    anterior = anterior.sort_values(claves).reset_index(drop=True)
    actual = actual.sort_values(claves).reset_index(drop=True)

    if not actual.equals(anterior):
        raise ValueError(
            "La poblacion o los folds cambiaron respecto a los baselines."
        )


def evaluar_configuraciones(datos, particiones):
    variables = datos[VARIABLES]
    etiquetas = datos["etiqueta"].to_numpy(dtype=int)
    resultados = []
    predicciones = {}

    for penalizacion in ("l1", "l2"):
        for lambda_valor in LAMBDAS:
            probabilidades = np.full(len(datos), np.nan)

            for numero, (entrenamiento, validacion) in enumerate(
                particiones, start=1
            ):
                modelo = construir_pipeline(penalizacion, lambda_valor)

                with warnings.catch_warnings():
                    warnings.simplefilter("error", ConvergenceWarning)
                    modelo.fit(
                        variables.iloc[entrenamiento],
                        etiquetas[entrenamiento],
                    )

                prob_entrenamiento = modelo.predict_proba(
                    variables.iloc[entrenamiento]
                )[:, 1]
                prob_validacion = modelo.predict_proba(
                    variables.iloc[validacion]
                )[:, 1]

                probabilidades[validacion] = prob_validacion

                resultados.append({
                    "modelo": f"logistica_{penalizacion}",
                    "penalizacion": penalizacion,
                    "lambda": lambda_valor,
                    "C": 1.0 / lambda_valor,
                    "fold": numero,
                    "ap_entrenamiento": average_precision_score(
                        etiquetas[entrenamiento],
                        prob_entrenamiento,
                    ),
                    "ap_validacion": average_precision_score(
                        etiquetas[validacion],
                        prob_validacion,
                    ),
                })

            if not np.isfinite(probabilidades).all():
                raise ValueError("Hay unidades sin prediccion de validacion.")

            predicciones[(penalizacion, lambda_valor)] = probabilidades

            print(
                f"Completado: {penalizacion.upper()}, "
                f"lambda={lambda_valor:g}"
            )

    return pd.DataFrame(resultados), predicciones


def resumir(resultados):
    return resultados.groupby(
        ["modelo", "penalizacion", "lambda", "C"],
        as_index=False,
    ).agg(
        ap_entrenamiento_media=("ap_entrenamiento", "mean"),
        ap_validacion_media=("ap_validacion", "mean"),
        ap_validacion_desviacion=("ap_validacion", "std"),
    )


def graficar(resumen, mejores):
    figura, eje = plt.subplots(figsize=(8, 5))

    for penalizacion in ("l1", "l2"):
        filas = resumen[
            resumen["penalizacion"].eq(penalizacion)
        ].sort_values("lambda")

        eje.errorbar(
            filas["lambda"],
            filas["ap_validacion_media"],
            yerr=filas["ap_validacion_desviacion"],
            marker="o",
            capsize=3,
            label=penalizacion.upper(),
        )

        elegido = mejores[
            mejores["penalizacion"].eq(penalizacion)
        ].iloc[0]

        eje.scatter(
            elegido["lambda"],
            elegido["ap_validacion_media"],
            marker="*",
            s=220,
            color="black",
            zorder=5,
        )

    eje.set_xscale("log")
    eje.set_xlabel("Lambda: intensidad de regularizacion")
    eje.set_ylabel("Average Precision de validacion")
    eje.set_title("Regularizacion de la regresion logistica")
    eje.grid(alpha=0.25)
    eje.legend(title="Penalizacion; estrella = lambda elegido")
    figura.tight_layout()
    figura.savefig(CARPETA / "regularizacion_logistica.png", dpi=160)
    plt.close(figura)


def main():
    argumentos = argparse.ArgumentParser()
    argumentos.add_argument("--corte", required=True, choices=["A"])
    argumentos.parse_args()

    inicio = time.perf_counter()
    datos = cargar_datos()
    etiquetas = datos["etiqueta"].to_numpy(dtype=int)
    particiones = list(crear_folds().split(datos[VARIABLES], etiquetas))

    verificar_folds(datos, particiones)

    resultados, predicciones = evaluar_configuraciones(datos, particiones)
    resumen = resumir(resultados)

    ordenado = resumen.sort_values(
        ["ap_validacion_media", "lambda", "penalizacion"],
        ascending=[False, False, True],
    )

    mejores = ordenado.drop_duplicates("penalizacion").copy()
    ganador = mejores.iloc[0]
    penalizacion = ganador["penalizacion"]
    lambda_valor = float(ganador["lambda"])

    nuevas = datos[["unidad_id", "fecha_corte"]].copy()
    nuevas["modelo"] = "logistica"
    nuevas["prob"] = predicciones[(penalizacion, lambda_valor)]
    guardar_predicciones(nuevas)

    resultados_base, _, _ = evaluar_baselines(datos)
    resumen_base = resultados_base.groupby(
        "modelo", as_index=False
    ).agg(
        ap_entrenamiento_media=("ap_entrenamiento", "mean"),
        ap_validacion_media=("ap_validacion", "mean"),
        ap_validacion_desviacion=("ap_validacion", "std"),
    )

    tabla = pd.concat(
        [resumen_base, mejores],
        ignore_index=True,
        sort=False,
    )

    modelo_final = construir_pipeline(penalizacion, lambda_valor)

    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        modelo_final.fit(datos[VARIABLES], etiquetas)

    coeficientes = pd.DataFrame({
        "variable": VARIABLES,
        "coeficiente": modelo_final.named_steps["clasificador"].coef_[0],
    }).sort_values("coeficiente", ascending=False)

    coeficientes["odds_ratio_por_desviacion"] = np.exp(
        coeficientes["coeficiente"]
    )

    resultados.to_csv(CARPETA / "logistica_por_fold.csv", index=False)
    resumen.to_csv(CARPETA / "busqueda_logistica.csv", index=False)
    tabla.to_csv(CARPETA / "comparacion_fase1.csv", index=False)
    coeficientes.to_csv(
        CARPETA / "coeficientes_logistica.csv",
        index=False,
    )

    graficar(resumen, mejores)

    print("\nCOMPARACION DE FASE 1")
    print(tabla.round(6).to_string(index=False))

    print("\nLOGISTICA SELECCIONADA")
    print(f"Penalizacion: {penalizacion.upper()}")
    print(f"Lambda: {lambda_valor:g}")
    print(f"C: {1.0 / lambda_valor:g}")

    if lambda_valor in (min(LAMBDAS), max(LAMBDAS)):
        print(
            "AVISO: el lambda ganador esta en un extremo de la grilla; "
            "revisar la curva antes de cerrar la seleccion."
        )

    print("\nCOEFICIENTES DEL AJUSTE CON TODO A")
    print(coeficientes.round(6).to_string(index=False))

    print(f"\nIntercepto: {modelo_final.named_steps['clasificador'].intercept_[0]:.6f}")
    print(f"Tiempo total: {time.perf_counter() - inicio:.2f} segundos")
    print("Predicciones de logistica agregadas al CSV.")


if __name__ == "__main__":
    main()