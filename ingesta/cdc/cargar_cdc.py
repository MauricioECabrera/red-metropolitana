"""
=====================================================================
  cargar_cdc.py  ·  Ingesta del log CDC del padron de usuarios
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Via CDC: el padron es la unica fuente que se actualiza y se borra.
  El archivo es un log de cambios con operaciones INSERT, UPDATE y
  DELETE en orden de secuencia. Bronze guarda el log tal como llego;
  las operaciones se aplican en Silver.

  Ejecutar desde la raiz del repositorio:
    python -m ingesta.cdc.cargar_cdc
=====================================================================
"""
from ingesta.comun.bronze import cargar, imprimir_resumen


def main():
    imprimir_resumen([cargar("cdc_padron_usuarios", "cdc_padron_usuarios.csv")])


if __name__ == "__main__":
    main()