"""
=====================================================================
  conteos_bronze.py  ·  Conteo de filas por fuente en Bronze
  Proyecto 2  ·  Ciencia de Datos  ·  Red Metropolitana

  Compara, para cada uno de los nueve archivos crudos, las filas
  esperadas (tabla del LEEME que se publica con los datos) contra
  las filas que llegaron a Bronze. Imprime la tabla y la escribe en
  docs/evidencias/conteos_bronze.md.

  Ejecutar desde la raiz del repositorio, despues de la ingesta:
    python scripts/conteos_bronze.py
=====================================================================
"""
import datetime
import pathlib

import duckdb

RAIZ = pathlib.Path(__file__).resolve().parents[1]
LAKE_BRONZE = RAIZ / "lake" / "bronze"
SALIDA = RAIZ / "docs" / "evidencias" / "conteos_bronze.md"

ESPERADAS = {
    "aerometro_boardings.csv": 387053,
    "am_estaciones.csv": 14,
    "cdc_padron_usuarios.csv": 77636,
    "metroriel_viajes.jsonl": 590844,
    "mr_estaciones.csv": 22,
    "tm_estaciones.csv": 104,
    "transmetro_validaciones.csv": 713786,
    "transurbano_transacciones.csv": 1635788,
    "tu_paradas.csv": 328,
}


def contar_bronze(con, fuente):
    carpeta = LAKE_BRONZE / fuente
    if not list(carpeta.glob("fecha_ingesta=*/*.parquet")):
        return 0
    patron = carpeta.as_posix() + "/fecha_ingesta=*/*.parquet"
    return con.execute(f"select count(*) from read_parquet('{patron}')").fetchone()[0]


def main():
    con = duckdb.connect()
    filas = []
    for archivo, esperadas in ESPERADAS.items():
        cargadas = contar_bronze(con, pathlib.Path(archivo).stem)
        filas.append((archivo, esperadas, cargadas, cargadas - esperadas))

    con_diferencia = sum(1 for f in filas if f[3] != 0)
    ancho = max(len(f[0]) for f in filas)

    print()
    print(f"{'archivo':<{ancho}}  {'esperadas':>12}  {'cargadas':>12}  {'diferencia':>10}")
    print("-" * (ancho + 42))
    for archivo, esperadas, cargadas, diferencia in filas:
        print(f"{archivo:<{ancho}}  {esperadas:>12,}  {cargadas:>12,}  {diferencia:>10,}")
    print("-" * (ancho + 42))
    print(f"Archivos con diferencia: {con_diferencia} de {len(filas)}")
    print()

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA.open("w", encoding="utf-8", newline="\n") as f:
        f.write("# Conteos de Bronze contra filas esperadas\n\n")
        f.write(f"Generado: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n\n")
        f.write("| archivo | filas esperadas | filas cargadas | diferencia |\n")
        f.write("|---|---:|---:|---:|\n")
        for archivo, esperadas, cargadas, diferencia in filas:
            f.write(f"| {archivo} | {esperadas:,} | {cargadas:,} | {diferencia:,} |\n")
        f.write(f"\nArchivos con diferencia: {con_diferencia} de {len(filas)}\n")


if __name__ == "__main__":
    main()
