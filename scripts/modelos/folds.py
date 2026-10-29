"""
=====================================================================
  folds.py · Validacion cruzada compartida del corte A
  Proyecto 2 · Ciencia de Datos · Red Metropolitana
  Autor: Adrian

  Define los cinco folds estratificados del equipo.
  Los consumidores deben ordenar las filas por unidad_id antes
  de generar las particiones y utilizar solamente el corte A.
=====================================================================
"""

from sklearn.model_selection import StratifiedKFold


def crear_folds():
    return StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )