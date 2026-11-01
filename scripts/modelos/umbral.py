"""
=====================================================================
  umbral.py · Umbral de contacto segun costo y evaluacion unica en B
  Proyecto 2 · Ciencia de Datos · Red Metropolitana
  Autor: Eduardo Hernandez

  Escenario fijo de la Agencia: contactar cuesta Q5, la campana
  retiene al 25 % de quienes se iban a ir y un retenido vale Q60.
  Ganancia esperada por contactado = p x 0.25 x 60 - 5 = 15p - 5.
  Ganancia observada de una politica = 15 x TP - 5 x contactados.

  --corte-eval A: usa predicciones_cv.csv del corte A (fuera de fold),
  calcula la curva de ganancia contra umbral, elige el umbral que la
  maximiza y lo congela en docs/umbral/umbral_elegido.json.

  --corte-eval B: entrena el modelo elegido con todo el corte A y lo
  evalua UNA SOLA VEZ en el corte B con el umbral congelado. Se niega
  a correr si ya existe un registro de B, si el umbral no esta
  versionado o si hay cambios sin commit. Registra fecha y commit en
  docs/test_b.md y docs/bitacora.md.

  Ejecutar desde la raiz del repositorio:
    python -m scripts.modelos.umbral --modelo ensemble --corte-eval A
    python -m scripts.modelos.umbral --modelo ensemble --corte-eval B
=====================================================================
"""

import argparse
import json
import subprocess
from datetime import datetime

import duckdb
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, confusion_matrix

from scripts.modelos.baseline import ASIGNACION, RAIZ, SALIDA, WAREHOUSE
from scripts.modelos.logistica import VARIABLES


COSTO_CONTACTO = 5.0
TASA_RETENCION = 0.25
VALOR_RETENIDO = 60.0
BENEFICIO_POSITIVO = TASA_RETENCION * VALOR_RETENIDO
UMBRAL_TEORICO = COSTO_CONTACTO / BENEFICIO_POSITIVO

CORTES = {"A": "2026-07-01", "B": "2026-07-31"}
MODELOS = ["ensemble", "logistica", "baseline_ranking"]
UMBRALES = np.round(np.arange(0.0, 1.0001, 0.01), 2)

CARPETA = RAIZ / "docs" / "umbral"
CURVA = CARPETA / "curva_ganancia_cv.csv"
GRAFICA = CARPETA / "ganancia_umbral.png"
ELEGIDO = CARPETA / "umbral_elegido.json"
REGISTRO_B = CARPETA / "registro_test_b.json"
DOC_TEST_B = RAIZ / "docs" / "test_b.md"
BITACORA = RAIZ / "docs" / "bitacora.md"
COMPARACION = RAIZ / "scripts" / "modelos" / "comparacion_fase2.csv"


def cargar_corte(fecha):
    columnas = ", ".join(VARIABLES)

    with duckdb.connect(str(WAREHOUSE), read_only=True) as conexion:
        datos = conexion.execute(
            f"""
            select unidad_id, fecha_corte, {columnas}, etiqueta
            from features.features_corte
            where fecha_corte = cast(? as date)
            order by unidad_id
            """,
            [fecha],
        ).df()

    if datos.empty:
        raise ValueError(f"El corte {fecha} esta vacio.")

    if datos.isna().any().any():
        raise ValueError(f"Hay nulos en el corte {fecha}.")

    if datos.duplicated(["unidad_id", "fecha_corte"]).any():
        raise ValueError(f"Hay claves duplicadas en el corte {fecha}.")

    if not datos["etiqueta"].isin([0, 1]).all():
        raise ValueError(f"Hay etiquetas distintas de 0 y 1 en {fecha}.")

    datos[VARIABLES] = datos[VARIABLES].astype(float)
    datos["etiqueta"] = datos["etiqueta"].astype(int)
    datos["unidad_id"] = datos["unidad_id"].astype(str)
    datos["fecha_corte"] = (
        pd.to_datetime(datos["fecha_corte"]).dt.strftime("%Y-%m-%d")
    )

    return datos


def cargar_predicciones_cv(modelo):
    predicciones = pd.read_csv(
        SALIDA,
        dtype={"unidad_id": str, "fecha_corte": str, "modelo": str},
    )

    predicciones = predicciones[
        predicciones["modelo"].eq(modelo)
        & predicciones["fecha_corte"].eq(CORTES["A"])
    ]

    if predicciones.empty:
        raise ValueError(f"predicciones_cv.csv no tiene el modelo {modelo}.")

    etiquetas = cargar_corte(CORTES["A"])[
        ["unidad_id", "fecha_corte", "etiqueta"]
    ]

    unidas = etiquetas.merge(
        predicciones[["unidad_id", "fecha_corte", "prob"]],
        on=["unidad_id", "fecha_corte"],
        how="outer",
        indicator=True,
        validate="one_to_one",
    )

    if not unidas["_merge"].eq("both").all():
        raise ValueError(
            "Las unidades de predicciones_cv.csv no coinciden con el corte A."
        )

    folds = pd.read_csv(ASIGNACION, dtype={"unidad_id": str, "fecha_corte": str})
    unidas = unidas.drop(columns="_merge").merge(
        folds,
        on=["unidad_id", "fecha_corte"],
        how="left",
        validate="one_to_one",
    )

    if unidas["fold"].isna().any():
        raise ValueError("Hay unidades sin fold en asignacion_folds.csv.")

    return unidas


def ganancia_en_umbral(prob, etiqueta, umbral):
    contactados = prob >= umbral
    positivos = int((contactados & (etiqueta == 1)).sum())
    falsos = int((contactados & (etiqueta == 0)).sum())
    total = positivos + falsos

    return {
        "umbral": float(umbral),
        "contactados": total,
        "verdaderos_positivos": positivos,
        "falsos_positivos": falsos,
        "ganancia_observada_q": BENEFICIO_POSITIVO * positivos
        - COSTO_CONTACTO * total,
        "ganancia_esperada_q": float(
            (BENEFICIO_POSITIVO * prob[contactados] - COSTO_CONTACTO).sum()
        ),
    }


def curva_ganancia(prob, etiqueta):
    return pd.DataFrame([
        ganancia_en_umbral(prob, etiqueta, umbral) for umbral in UMBRALES
    ])


def elegir_umbral(curva):
    maximo = curva["ganancia_observada_q"].max()
    empatados = curva[curva["ganancia_observada_q"].eq(maximo)]
    return empatados.sort_values("umbral", ascending=False).iloc[0]


def graficar(curva, elegido, modelo):
    figura, ejes = plt.subplots(1, 2, figsize=(14, 5))

    for eje in ejes:
        dibujar_curva(eje, curva, elegido)

    positivos = curva[curva["ganancia_observada_q"] > 0]
    if not positivos.empty:
        margen = 0.05
        ejes[1].set_xlim(
            max(positivos["umbral"].min() - margen, 0),
            min(positivos["umbral"].max() + margen, 1),
        )
        ejes[1].set_ylim(
            -0.1 * elegido["ganancia_observada_q"],
            1.25 * elegido["ganancia_observada_q"],
        )

    ejes[0].set_title(f"Ganancia contra umbral · {modelo} · corte A fuera de fold")
    ejes[1].set_title("Detalle de la zona con ganancia positiva")
    ejes[1].get_legend().remove()
    figura.tight_layout()
    figura.savefig(GRAFICA, dpi=160)
    plt.close(figura)


def dibujar_curva(eje, curva, elegido):
    eje.plot(
        curva["umbral"],
        curva["ganancia_observada_q"],
        label="Ganancia observada (15 x TP - 5 x contactados)",
    )
    eje.plot(
        curva["umbral"],
        curva["ganancia_esperada_q"],
        linestyle="--",
        label="Ganancia esperada (suma de 15p - 5)",
    )
    eje.axvline(
        elegido["umbral"],
        color="red",
        linewidth=1.2,
        label=f"Umbral elegido = {elegido['umbral']:.2f}",
    )
    eje.axvline(
        UMBRAL_TEORICO,
        color="gray",
        linestyle=":",
        label="Equilibrio teorico p = 1/3",
    )
    eje.scatter(
        [elegido["umbral"]],
        [elegido["ganancia_observada_q"]],
        color="red",
        zorder=3,
    )
    eje.annotate(
        f"Q{elegido['ganancia_observada_q']:,.0f}",
        (elegido["umbral"], elegido["ganancia_observada_q"]),
        textcoords="offset points",
        xytext=(8, 8),
    )
    eje.axhline(0, color="black", linewidth=0.8)
    eje.set_xlabel("Umbral de probabilidad para contactar")
    eje.set_ylabel("Ganancia total (Q)")
    eje.legend(loc="lower right", fontsize=8)


def ejecutar_git(*argumentos):
    resultado = subprocess.run(
        ["git", *argumentos],
        cwd=RAIZ,
        capture_output=True,
        text=True,
    )

    if resultado.returncode != 0:
        raise RuntimeError(f"git {' '.join(argumentos)} fallo: {resultado.stderr}")

    return resultado.stdout.strip()


def evaluar_a(modelo):
    if REGISTRO_B.exists():
        raise RuntimeError(
            "El corte B ya fue evaluado. El umbral esta congelado y no se "
            "puede volver a elegir."
        )

    datos = cargar_predicciones_cv(modelo)
    prob = datos["prob"].to_numpy(dtype=float)
    etiqueta = datos["etiqueta"].to_numpy(dtype=int)

    curva = curva_ganancia(prob, etiqueta)
    elegido = elegir_umbral(curva)
    esperado = curva.loc[curva["ganancia_esperada_q"].idxmax()]

    por_fold = []
    for numero, grupo in datos.groupby("fold"):
        fila = ganancia_en_umbral(
            grupo["prob"].to_numpy(dtype=float),
            grupo["etiqueta"].to_numpy(dtype=int),
            elegido["umbral"],
        )
        fila["fold"] = int(numero)
        fila["unidades"] = len(grupo)
        por_fold.append(fila)

    por_fold = pd.DataFrame(por_fold)

    CARPETA.mkdir(parents=True, exist_ok=True)
    curva.to_csv(CURVA, index=False)
    por_fold.to_csv(CARPETA / "ganancia_por_fold.csv", index=False)
    graficar(curva, elegido, modelo)

    contactar_todos = curva.loc[curva["umbral"].eq(0.0)].iloc[0]

    decision = {
        "modelo": modelo,
        "umbral": float(elegido["umbral"]),
        "criterio": "maxima ganancia observada en predicciones fuera de fold del corte A",
        "ganancia_cv_q": float(elegido["ganancia_observada_q"]),
        "contactados_cv": int(elegido["contactados"]),
        "verdaderos_positivos_cv": int(elegido["verdaderos_positivos"]),
        "unidades_cv": int(len(datos)),
        "umbral_max_ganancia_esperada": float(esperado["umbral"]),
        "umbral_teorico": UMBRAL_TEORICO,
        "ganancia_contactar_todos_q": float(
            contactar_todos["ganancia_observada_q"]
        ),
        "escenario": {
            "costo_contacto_q": COSTO_CONTACTO,
            "tasa_retencion": TASA_RETENCION,
            "valor_retenido_q": VALOR_RETENIDO,
        },
        "fecha_decision": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    ELEGIDO.write_text(
        json.dumps(decision, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Modelo: {modelo} | unidades del corte A: {len(datos):,}")
    print(f"Tasa positiva: {etiqueta.mean():.6f}")
    print(f"AP fuera de fold: {average_precision_score(etiqueta, prob):.6f}")
    print("\nUMBRAL ELEGIDO")
    print(elegido.to_string())
    print(
        f"\nUmbral de maxima ganancia esperada: {esperado['umbral']:.2f}"
        f" | equilibrio teorico: {UMBRAL_TEORICO:.4f}"
    )
    print(
        "Contactar a todos: "
        f"Q{contactar_todos['ganancia_observada_q']:,.2f}"
    )
    print("\nGANANCIA POR FOLD EN EL UMBRAL ELEGIDO")
    print(por_fold.round(2).to_string(index=False))
    print(f"\nCurva: {CURVA}\nGrafica: {GRAFICA}\nDecision: {ELEGIDO}")
    print(
        "\nAntes de evaluar B: hace commit de docs/umbral/ y registra la "
        "decision en docs/bitacora.md."
    )


def construir_modelo_final(modelo):
    if modelo == "ensemble":
        from scripts.modelos.ensemble import construir_pipeline

        return construir_pipeline()

    if modelo == "logistica":
        from scripts.modelos.logistica import construir_pipeline

        comparacion = pd.read_csv(COMPARACION)
        logisticas = comparacion[comparacion["modelo"].str.startswith("logistica")]
        mejor = logisticas.sort_values(
            "ap_validacion_media", ascending=False
        ).iloc[0]

        return construir_pipeline(mejor["penalizacion"], float(mejor["lambda"]))

    raise ValueError(
        "baseline_ranking es una regla fija; no se entrena un modelo final."
    )


def verificar_candados(modelo):
    if REGISTRO_B.exists():
        raise RuntimeError(
            f"El corte B ya fue evaluado (ver {REGISTRO_B}). "
            "Solo se permite una evaluacion."
        )

    if not ELEGIDO.exists():
        raise RuntimeError("Primero elegi el umbral con --corte-eval A.")

    decision = json.loads(ELEGIDO.read_text(encoding="utf-8"))

    if decision["modelo"] != modelo:
        raise RuntimeError(
            f"El umbral congelado es del modelo {decision['modelo']}, "
            f"no de {modelo}."
        )

    ruta = ELEGIDO.relative_to(RAIZ).as_posix()

    if not ejecutar_git("ls-files", ruta):
        raise RuntimeError(f"{ruta} no esta versionado. Hace commit antes de B.")

    if ejecutar_git("status", "--porcelain", "--untracked-files=no"):
        raise RuntimeError(
            "Hay cambios sin commit. El commit registrado debe ser "
            "exactamente el codigo que evalua B."
        )

    return decision


def evaluar_b(modelo):
    decision = verificar_candados(modelo)
    umbral = decision["umbral"]
    commit = ejecutar_git("rev-parse", "HEAD")

    entrenamiento = cargar_corte(CORTES["A"])
    prueba = cargar_corte(CORTES["B"])

    modelo_final = construir_modelo_final(modelo)
    modelo_final.fit(
        entrenamiento[VARIABLES],
        entrenamiento["etiqueta"].to_numpy(dtype=int),
    )

    prob = modelo_final.predict_proba(prueba[VARIABLES])[:, 1]
    etiqueta = prueba["etiqueta"].to_numpy(dtype=int)
    prediccion = (prob >= umbral).astype(int)

    vn, fp, fn, vp = confusion_matrix(etiqueta, prediccion, labels=[0, 1]).ravel()
    resultado = ganancia_en_umbral(prob, etiqueta, umbral)
    todos = ganancia_en_umbral(prob, etiqueta, 0.0)

    registro = {
        "fecha_evaluacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "commit": commit,
        "modelo": modelo,
        "umbral": umbral,
        "unidades_entrenamiento_a": int(len(entrenamiento)),
        "unidades_b": int(len(prueba)),
        "tasa_positiva_b": float(etiqueta.mean()),
        "ap_b": float(average_precision_score(etiqueta, prob)),
        "precision_b": float(vp / (vp + fp)) if vp + fp else 0.0,
        "recall_b": float(vp / (vp + fn)) if vp + fn else 0.0,
        "matriz_confusion": {
            "verdaderos_negativos": int(vn),
            "falsos_positivos": int(fp),
            "falsos_negativos": int(fn),
            "verdaderos_positivos": int(vp),
        },
        "contactados": int(resultado["contactados"]),
        "ganancia_observada_q": float(resultado["ganancia_observada_q"]),
        "ganancia_esperada_q": float(resultado["ganancia_esperada_q"]),
        "ganancia_contactar_todos_q": float(todos["ganancia_observada_q"]),
        "referencia_cv": {
            "ganancia_cv_q": decision["ganancia_cv_q"],
            "contactados_cv": decision["contactados_cv"],
            "unidades_cv": decision["unidades_cv"],
        },
    }

    REGISTRO_B.write_text(
        json.dumps(registro, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    escribir_documento_b(registro)
    anotar_bitacora(registro)

    print(json.dumps(registro, indent=2, ensure_ascii=False))
    print(f"\nRegistro: {REGISTRO_B}\nDocumento: {DOC_TEST_B}")
    print("Hace commit de estos archivos. No vuelvas a correr B.")


def escribir_documento_b(registro):
    matriz = registro["matriz_confusion"]
    cv = registro["referencia_cv"]
    por_unidad_b = registro["ganancia_observada_q"] / registro["unidades_b"]
    por_unidad_cv = cv["ganancia_cv_q"] / cv["unidades_cv"]

    texto = f"""# Evaluación única del corte B

| Dato | Valor |
|---|---|
| Fecha de la evaluación | {registro['fecha_evaluacion']} |
| Commit evaluado | `{registro['commit']}` |
| Modelo | {registro['modelo']} entrenado con todo el corte A ({registro['unidades_entrenamiento_a']:,} unidades) |
| Umbral (congelado en A) | {registro['umbral']:.2f} |
| Unidades del corte B | {registro['unidades_b']:,} |
| Tasa positiva en B | {registro['tasa_positiva_b']:.4f} |

## Métrica

| Métrica | Valor |
|---|---:|
| Average Precision | {registro['ap_b']:.4f} |
| Precisión en el umbral | {registro['precision_b']:.4f} |
| Recall en el umbral | {registro['recall_b']:.4f} |

## Matriz de confusión en el umbral

| | Predicho 0 (no contactar) | Predicho 1 (contactar) |
|---|---:|---:|
| Real 0 (sigue viajando) | {matriz['verdaderos_negativos']:,} | {matriz['falsos_positivos']:,} |
| Real 1 (abandona) | {matriz['falsos_negativos']:,} | {matriz['verdaderos_positivos']:,} |

## Ganancia en quetzales

| Política | Ganancia |
|---|---:|
| Contactar con el umbral {registro['umbral']:.2f} ({registro['contactados']:,} contactados) | Q{registro['ganancia_observada_q']:,.2f} |
| Contactar a todos | Q{registro['ganancia_contactar_todos_q']:,.2f} |
| No contactar a nadie | Q0.00 |

Ganancia = 15 × {matriz['verdaderos_positivos']:,} − 5 × {registro['contactados']:,}.

Ganancia por unidad: Q{por_unidad_b:.4f} en B frente a Q{por_unidad_cv:.4f}
en la validación cruzada de A.

## Lectura del resultado

(Completar sin reajustar nada: comparar contra la validación y explicar
la diferencia, por ejemplo cambio de tasa positiva entre julio y agosto.)

Esta es la única evaluación del corte B. Después de verla no se cambió el
umbral, el modelo ni ningún hiperparámetro.
"""

    DOC_TEST_B.write_text(texto, encoding="utf-8")


def anotar_bitacora(registro):
    entrada = f"""

---

## Evaluación única del corte B
**Estado:** cerrada · **Responsable:** Eduardo

- **Fecha:** {registro['fecha_evaluacion']}
- **Commit:** `{registro['commit']}`
- **Modelo y umbral:** {registro['modelo']}, umbral {registro['umbral']:.2f}, ambos congelados en A antes de esta corrida.
- **Resultado:** AP {registro['ap_b']:.4f}, ganancia Q{registro['ganancia_observada_q']:,.2f} con {registro['contactados']:,} contactados.
- **Detalle:** `docs/test_b.md` y `docs/umbral/registro_test_b.json`.

Se evaluó una sola vez. No se ajustó nada después de ver la etiqueta de B.
"""

    with BITACORA.open("a", encoding="utf-8") as archivo:
        archivo.write(entrada)


def main():
    argumentos = argparse.ArgumentParser()
    argumentos.add_argument("--modelo", required=True, choices=MODELOS)
    argumentos.add_argument("--corte-eval", required=True, choices=["A", "B"])
    parametros = argumentos.parse_args()

    if parametros.corte_eval == "A":
        evaluar_a(parametros.modelo)
    else:
        evaluar_b(parametros.modelo)


if __name__ == "__main__":
    main()
