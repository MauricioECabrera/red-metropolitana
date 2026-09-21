"""
=====================================================================
  cargar_catalogos.py  ·  Ingesta batch de catalogos a Bronze
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Carga los cuatro catalogos de estaciones y paradas.
  Via batch: los catalogos cambian rara vez y llegan completos.

  Ejecutar desde la raiz del repositorio:
    python -m ingesta.batch.cargar_catalogos
=====================================================================
"""
from ingesta.comun.bronze import cargar, imprimir_resumen

CATALOGOS = [
    ("tm_estaciones", "tm_estaciones.csv"),
    ("tu_paradas", "tu_paradas.csv"),
    ("mr_estaciones", "mr_estaciones.csv"),
    ("am_estaciones", "am_estaciones.csv"),
]


def main():
    resultados = [cargar(fuente, archivo) for fuente, archivo in CATALOGOS]
    imprimir_resumen(resultados)


if __name__ == "__main__":
    main()