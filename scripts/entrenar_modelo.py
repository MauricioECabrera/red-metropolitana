"""
=====================================================================
  entrenar_modelo.py  ·  Entrenamiento del modelo final de churn
  Proyecto 2  ·  Ciencia de Datos  ·  Red Metropolitana

  Entrena, con todo el corte A, el mismo modelo que Eduardo evalua
  en el corte B: construir_modelo_final() de scripts/modelos/umbral.py
  sobre los mismos datos que carga cargar_corte(). No se reescribe
  ningun pipeline aqui, solo se llama a lo que ya existe.

  El modelo y el umbral se leen de docs/umbral/umbral_elegido.json en
  el momento de entrenar y se copian a los metadatos. predecir.py no
  depende de ese archivo: lee todo del .json de metadatos del modelo.

  Se niega a correr si el arbol de git tiene cambios sin commit,
  porque el commit queda anotado en los metadatos. No toca el corte
  B bajo ningun motivo: ni lo lee ni lo menciona.

  Ejecutar desde la raiz del repositorio:
    python -m scripts.entrenar_modelo
=====================================================================
"""
import json
import subprocess
import time

import joblib
import sklearn

from scripts.modelos.baseline import RAIZ
from scripts.modelos.logistica import VARIABLES
from scripts.modelos.umbral import CORTES, ELEGIDO, cargar_corte, construir_modelo_final


VERSION = "v1"
SEMILLA = 42
CARPETA_MODELOS = RAIZ / "modelos"
RUTA_MODELO = CARPETA_MODELOS / f"modelo_churn_{VERSION}.joblib"
RUTA_METADATOS = CARPETA_MODELOS / f"modelo_churn_{VERSION}.json"


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


def verificar_arbol_limpio():
    if ejecutar_git("status", "--porcelain", "--untracked-files=no", "--", ".", ":!tableau"):
        raise RuntimeError(
            "Hay cambios sin commit. El commit evaluado queda anotado en "
            "los metadatos del modelo: hace commit antes de entrenar."
        )


def cargar_decision():
    if not ELEGIDO.exists():
        raise RuntimeError(
            f"No existe {ELEGIDO}. Primero elegi el umbral con "
            "python -m scripts.modelos.umbral --modelo <modelo> --corte-eval A."
        )

    return json.loads(ELEGIDO.read_text(encoding="utf-8"))


def entrenar():
    verificar_arbol_limpio()
    decision = cargar_decision()
    commit = ejecutar_git("rev-parse", "HEAD")

    datos = cargar_corte(CORTES["A"])
    etiquetas = datos["etiqueta"].to_numpy(dtype=int)

    modelo = construir_modelo_final(decision["modelo"])

    inicio = time.perf_counter()
    modelo.fit(datos[VARIABLES], etiquetas)
    segundos_entrenamiento = time.perf_counter() - inicio

    CARPETA_MODELOS.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, RUTA_MODELO)

    metadatos = {
        "version": VERSION,
        "fecha_entrenamiento": time.strftime("%Y-%m-%d %H:%M:%S"),
        "commit": commit,
        "version_scikit_learn": sklearn.__version__,
        "semilla": SEMILLA,
        "variables": VARIABLES,
        "modelo": decision["modelo"],
        "umbral": decision["umbral"],
        "filas_entrenamiento": int(len(datos)),
        "segundos_entrenamiento": segundos_entrenamiento,
    }

    RUTA_METADATOS.write_text(
        json.dumps(metadatos, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Modelo: {decision['modelo']} | umbral: {decision['umbral']:.2f}")
    print(f"Variables ({len(VARIABLES)}): {', '.join(VARIABLES)}")
    print(f"Filas de entrenamiento: {len(datos):,}")
    print(f"Segundos de entrenamiento: {segundos_entrenamiento:.2f}")
    print(f"Commit anotado: {commit}")
    print(f"\nModelo: {RUTA_MODELO}\nMetadatos: {RUTA_METADATOS}")

    return metadatos


if __name__ == "__main__":
    entrenar()
