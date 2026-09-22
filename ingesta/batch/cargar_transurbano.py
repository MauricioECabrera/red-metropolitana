"""
=====================================================================
  cargar_transurbano.py  ·  Ingesta batch de transacciones de
  Transurbano a Bronze
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Via batch: Transurbano entrega el archivo completo del periodo, no
  un flujo de eventos. Decision D-004 de la bitacora.

  Ejecutar desde la raiz del repositorio:
    python -m ingesta.batch.cargar_transurbano
=====================================================================
"""
from ingesta.comun.bronze import cargar, imprimir_resumen


def main():
    imprimir_resumen([cargar("transurbano_transacciones", "transurbano_transacciones.csv")])


if __name__ == "__main__":
    main()
