"""
=====================================================================
  segmentacion.py · Segmentos de usuarios con KMeans y PCA
  Proyecto 2 · Ciencia de Datos · Red Metropolitana
  Autor: Eduardo Hernandez

  Lee la tabla features.features_corte de un corte (por defecto A),
  escala las diez features del contrato con StandardScaler y ajusta
  KMeans para k = 2..k_max. Guarda la curva del codo (inercia) y la
  silueta, elige k, proyecta los segmentos con PCA a dos componentes
  y describe cada segmento con medianas y tasa de abandono.

  La etiqueta no entra a KMeans ni a PCA: solo se usa despues para
  la tasa de abandono por segmento, que es descriptiva y no prueba
  que el segmento cause el abandono.

  Regla de eleccion si no se pasa --k: el codo elige k y la silueta
  se reporta como control. Si la silueta del codo queda por debajo de
  0.25 se avisa que la estructura es debil, pero no se cae a k = 2:
  ese k solo separa a los muy activos y esconde al grupo que abandona.

  Ejecutar desde la raiz del repositorio:
    python -m scripts.segmentacion --corte A --k-max 10
    python -m scripts.segmentacion --corte A --k-max 10 --k 4
=====================================================================
"""

import argparse

import duckdb
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from scripts.modelos.baseline import RAIZ, WAREHOUSE
from scripts.modelos.variables import VARIABLES


CORTES = {"A": "2026-07-01", "B": "2026-07-31", "C": "2026-08-30"}

SEMILLA = 42
MUESTRA_SILUETA = 10000
MUESTRA_GRAFICA = 15000
SILUETA_MINIMA = 0.25

CARPETA = RAIZ / "docs" / "segmentos"


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

    if datos[VARIABLES].isna().any().any():
        raise ValueError(f"Hay nulos en las features del corte {fecha}.")

    if datos.duplicated(["unidad_id", "fecha_corte"]).any():
        raise ValueError(f"Hay claves duplicadas en el corte {fecha}.")

    datos[VARIABLES] = datos[VARIABLES].astype(float)
    datos["unidad_id"] = datos["unidad_id"].astype(str)

    return datos


def construir_pipeline(k):
    return Pipeline([
        ("escalado", StandardScaler()),
        ("kmeans", KMeans(n_clusters=k, n_init=10, random_state=SEMILLA)),
    ])


def evaluar_k(variables, k_max):
    escaladas = StandardScaler().fit_transform(variables)
    filas = []

    for k in range(2, k_max + 1):
        kmeans = KMeans(n_clusters=k, n_init=10, random_state=SEMILLA)
        grupos = kmeans.fit_predict(escaladas)

        silueta = silhouette_score(
            escaladas,
            grupos,
            sample_size=min(MUESTRA_SILUETA, len(escaladas)),
            random_state=SEMILLA,
        )

        filas.append({"k": k, "inercia": kmeans.inertia_, "silueta": silueta})
        print(f"k={k:>2} | inercia={kmeans.inertia_:,.0f} | silueta={silueta:.4f}")

    return pd.DataFrame(filas)


def k_del_codo(evaluacion):
    k = evaluacion["k"].to_numpy(dtype=float)
    inercia = evaluacion["inercia"].to_numpy(dtype=float)

    x = (k - k.min()) / (k.max() - k.min())
    y = (inercia - inercia.min()) / (inercia.max() - inercia.min())
    distancia = (1 - x) - y

    return int(k[np.argmax(distancia)])


def graficar_eleccion(evaluacion, k_elegido, k_codo):
    figura, ejes = plt.subplots(1, 2, figsize=(13, 4.5))

    ejes[0].plot(evaluacion["k"], evaluacion["inercia"], marker="o")
    ejes[0].axvline(k_codo, color="gray", linestyle=":", label=f"Codo k = {k_codo}")
    ejes[0].axvline(k_elegido, color="red", label=f"Elegido k = {k_elegido}")
    ejes[0].set_xlabel("k")
    ejes[0].set_ylabel("Inercia (suma de distancias al centroide)")
    ejes[0].set_title("Metodo del codo")
    ejes[0].legend()

    ejes[1].plot(evaluacion["k"], evaluacion["silueta"], marker="o", color="tab:green")
    ejes[1].axvline(k_elegido, color="red", label=f"Elegido k = {k_elegido}")
    ejes[1].set_xlabel("k")
    ejes[1].set_ylabel("Silueta media")
    ejes[1].set_title("Coeficiente de silueta")
    ejes[1].legend()

    for eje in ejes:
        eje.set_xticks(evaluacion["k"])

    figura.tight_layout()
    figura.savefig(CARPETA / "eleccion_k.png", dpi=160)
    plt.close(figura)


def nombrar_segmentos(medianas, referencia):
    nombres = {}

    for segmento, fila in medianas.iterrows():
        partes = []

        if fila["dias_desde_ultimo_viaje"] >= max(2 * referencia["dias_desde_ultimo_viaje"], 7):
            partes.append("en enfriamiento")
        elif fila["viajes_28d"] >= 6 * referencia["viajes_28d"]:
            partes.append("intensivos")
        elif fila["viajes_28d"] >= 1.5 * referencia["viajes_28d"]:
            partes.append("frecuentes")
        elif fila["viajes_28d"] <= 0.6 * referencia["viajes_28d"]:
            partes.append("ocasionales")
        else:
            partes.append("regulares")

        if fila["operadores_distintos_28d"] >= 2:
            partes.append("multimodales")

        if fila["gasto_promedio_viaje_q"] >= 2 * referencia["gasto_promedio_viaje_q"]:
            partes.append("de tarifa alta")

        proporcion = fila["abordajes_fin_semana_28d"] / max(fila["viajes_28d"], 1)
        proporcion_ref = (
            referencia["abordajes_fin_semana_28d"] / max(referencia["viajes_28d"], 1)
        )
        if proporcion >= 1.5 * proporcion_ref and proporcion >= 0.3:
            partes.append("de fin de semana")

        nombres[segmento] = "viajeros " + " ".join(partes)

    repetidos = pd.Series(nombres).value_counts()
    vistos = {}
    for segmento in sorted(nombres):
        nombre = nombres[segmento]
        if repetidos[nombre] > 1:
            vistos[nombre] = vistos.get(nombre, 0) + 1
            nombres[segmento] = f"{nombre} ({vistos[nombre]})"

    return nombres


def describir(datos):
    hay_etiqueta = datos["etiqueta"].notna().all()

    medianas = datos.groupby("segmento")[VARIABLES].median()
    referencia = datos[VARIABLES].median()
    nombres = nombrar_segmentos(medianas, referencia)

    tabla = medianas.add_prefix("mediana_")
    tabla.insert(0, "tamano", datos.groupby("segmento").size())
    tabla.insert(1, "porcentaje", (tabla["tamano"] / len(datos) * 100).round(2))
    tabla.insert(0, "nombre", pd.Series(nombres))

    if hay_etiqueta:
        tabla["tasa_abandono"] = datos.groupby("segmento")["etiqueta"].mean().round(4)
    else:
        tabla["tasa_abandono"] = np.nan

    return tabla.reset_index(), nombres


def graficar_pca(pca, escaladas, segmentos, nombres):
    varianza = pca.explained_variance_ratio_
    puntos = pca.transform(escaladas)

    rng = np.random.default_rng(SEMILLA)
    indices = rng.choice(len(puntos), size=min(MUESTRA_GRAFICA, len(puntos)), replace=False)

    figura, eje = plt.subplots(figsize=(9, 6.5))

    for segmento in sorted(nombres):
        seleccion = indices[segmentos[indices] == segmento]
        eje.scatter(
            puntos[seleccion, 0],
            puntos[seleccion, 1],
            s=6,
            alpha=0.45,
            label=f"{segmento}: {nombres[segmento]}",
        )

    eje.set_xlabel(f"Componente 1 ({varianza[0] * 100:.1f} % de la varianza)")
    eje.set_ylabel(f"Componente 2 ({varianza[1] * 100:.1f} % de la varianza)")
    eje.set_title(
        "Segmentos en dos componentes principales "
        f"(total explicado {varianza.sum() * 100:.1f} %)"
    )
    eje.legend(markerscale=3, fontsize=8)
    figura.tight_layout()
    figura.savefig(CARPETA / "segmentos_pca.png", dpi=160)
    plt.close(figura)


def main():
    argumentos = argparse.ArgumentParser()
    argumentos.add_argument("--corte", default="A", choices=list(CORTES))
    argumentos.add_argument("--k-max", type=int, default=10)
    argumentos.add_argument("--k", type=int, default=None)
    parametros = argumentos.parse_args()

    if parametros.k_max < 3:
        raise ValueError("--k-max debe ser al menos 3 para ver un codo.")

    CARPETA.mkdir(parents=True, exist_ok=True)

    datos = cargar_corte(CORTES[parametros.corte])
    variables = datos[VARIABLES]

    print(f"Corte {parametros.corte}: {len(datos):,} unidades\n")
    evaluacion = evaluar_k(variables, parametros.k_max)

    k_silueta = int(evaluacion.loc[evaluacion["silueta"].idxmax(), "k"])
    k_codo = k_del_codo(evaluacion)
    silueta_codo = float(evaluacion.loc[evaluacion["k"].eq(k_codo), "silueta"].iloc[0])

    k_elegido = parametros.k or k_codo

    if silueta_codo < SILUETA_MINIMA:
        print(
            f"\nAviso: la silueta del codo ({silueta_codo:.4f}) es menor que "
            f"{SILUETA_MINIMA}; la estructura de los segmentos es debil."
        )

    evaluacion.to_csv(CARPETA / "eleccion_k.csv", index=False)
    graficar_eleccion(evaluacion, k_elegido, k_codo)

    modelo = construir_pipeline(k_elegido).fit(variables)
    segmentos = modelo.predict(variables)
    datos["segmento"] = segmentos

    tabla, nombres = describir(datos)

    escaladas = modelo.named_steps["escalado"].transform(variables)
    pca = PCA(n_components=2, random_state=SEMILLA).fit(escaladas)
    varianza = pca.explained_variance_ratio_
    graficar_pca(pca, escaladas, segmentos, nombres)

    cargas = pd.DataFrame(
        pca.components_.T,
        index=VARIABLES,
        columns=["componente_1", "componente_2"],
    )

    tabla.to_csv(CARPETA / "tabla_segmentos.csv", index=False)
    cargas.to_csv(CARPETA / "cargas_pca.csv")
    datos[["unidad_id", "fecha_corte", "segmento"]].to_csv(
        CARPETA / f"asignacion_segmentos_{parametros.corte}.csv",
        index=False,
    )

    print(
        f"\nk por silueta: {k_silueta} | k por codo: {k_codo} "
        f"(silueta {silueta_codo:.4f}) | k usado: {k_elegido}"
    )
    print(
        f"Varianza explicada PCA: {varianza[0]:.4f} + {varianza[1]:.4f}"
        f" = {varianza.sum():.4f}"
    )
    print("\nCARGAS DE PCA (escaladas)")
    print(cargas.round(3).to_string())
    print("\nTABLA DE SEGMENTOS")
    print(tabla.to_string(index=False))
    print(
        "\nLa tasa de abandono por segmento es descriptiva: "
        "no prueba que el segmento cause el abandono."
    )
    print(f"\nSalidas en {CARPETA}")


if __name__ == "__main__":
    main()
