"""
=====================================================================
  cargar_metroriel.py  ·  Ingesta batch de viajes de MetroRiel a Bronze
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Via batch: MetroRiel entrega el viaje ya cerrado, con entrada y
  salida en el mismo registro. El JSON anidado se guarda tal como
  llego, como tipo JSON, sin aplanar.

  Ejecutar desde la raiz del repositorio:
    python -m ingesta.batch.cargar_metroriel
=====================================================================
"""
from ingesta.comun.bronze import cargar, imprimir_resumen, lector_jsonl


def main():
    imprimir_resumen([cargar("metroriel_viajes", "metroriel_viajes.jsonl", lector_jsonl)])


if __name__ == "__main__":
    main()