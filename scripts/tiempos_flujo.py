"""
=====================================================================
  tiempos_flujo.py  ·  Tiempo por etapa de la ultima ejecucion
  Proyecto 2  ·  Ciencia de Datos  ·  Red Metropolitana

  Lee lake/bronze/_control/ejecuciones.csv, toma la ultima ejecucion
  del flujo y deja una fila por etapa con su duracion en segundos.
  Imprime la tabla y la escribe en docs/evidencias/tiempos_flujo.md.

  Ejecutar desde la raiz del repositorio, despues del flujo:
    python scripts/tiempos_flujo.py
=====================================================================
"""
import csv
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[1]
BITACORA = RAIZ / "lake" / "bronze" / "_control" / "ejecuciones.csv"
SALIDA = RAIZ / "docs" / "evidencias" / "tiempos_flujo.md"


def main():
    with BITACORA.open(newline="", encoding="utf-8") as f:
        registros = list(csv.DictReader(f))
    ejecucion_id = registros[-1]["ejecucion_id"]
    etapas = [r for r in registros if r["ejecucion_id"] == ejecucion_id]
    total = sum(float(r["segundos"]) for r in etapas)
    ancho = max(len(r["etapa"]) for r in etapas)

    print()
    print(f"Ejecucion {ejecucion_id}")
    print(f"{'etapa':<{ancho}}  {'estado':<8}  {'segundos':>9}")
    print("-" * (ancho + 21))
    for r in etapas:
        print(f"{r['etapa']:<{ancho}}  {r['estado']:<8}  {float(r['segundos']):>9.2f}")
    print("-" * (ancho + 21))
    print(f"{'total':<{ancho}}  {'':<8}  {total:>9.2f}")
    print()

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA.open("w", encoding="utf-8", newline="\n") as f:
        f.write("# Tiempos por etapa del flujo\n\n")
        f.write(f"Ejecucion: {ejecucion_id}\n\n")
        f.write("| etapa | estado | segundos |\n")
        f.write("|---|---|---:|\n")
        for r in etapas:
            f.write(f"| {r['etapa']} | {r['estado']} | {float(r['segundos']):.2f} |\n")
        f.write(f"| **total** | | **{total:.2f}** |\n")


if __name__ == "__main__":
    main()