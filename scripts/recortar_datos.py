"""
=====================================================================
  recortar_datos.py  ·  Copia de datos_red truncada a una fecha
  Proyecto 2  ·  Ciencia de Datos  ·  Red Metropolitana

  python -m scripts.recortar_datos --hasta 2026-07-30 --salida datos_recortados

  Copia los nueve archivos crudos a una carpeta nueva. En los cuatro
  archivos de viajes y en el log de CDC quita las filas cuyo evento
  ocurre despues de --hasta (inclusive esa fecha). Los catalogos de
  estaciones y paradas se copian completos: no tienen fecha.

  Cada archivo trae su propia columna y formato de fecha:
    transmetro_validaciones.csv  fecha_hora     AAAA-MM-DD HH:MM:SS
    transurbano_transacciones.csv fecha          DD/MM/AAAA
    aerometro_boardings.csv      timestamp_utc  AAAA-MM-DDTHH:MM:SSZ, en UTC
    metroriel_viajes.jsonl       entry.ts       isoformato local
    cdc_padron_usuarios.csv      commit_ts      AAAA-MM-DDTHH:MM:SS

  Sirve para el ensayo de invarianza: correr el flujo con los datos
  completos y con los datos recortados y comparar las predicciones
  del corte B, que solo necesita datos hasta un dia antes de su
  fecha de corte.
=====================================================================
"""
import argparse
import csv
import datetime
import json

from ingesta.comun.bronze import DATOS_CRUDOS, RAIZ


CATALOGOS = ["tm_estaciones.csv", "tu_paradas.csv", "mr_estaciones.csv", "am_estaciones.csv"]
DESPLAZAMIENTO_AEROMETRO_UTC = datetime.timedelta(hours=6)


def copiar_catalogo(origen, destino, archivo):
    with (origen / archivo).open("rb") as entrada, (destino / archivo).open("wb") as salida:
        salida.write(entrada.read())


def recortar_csv(origen, destino, archivo, columna, limite, convertir):
    with (origen / archivo).open(newline="", encoding="utf-8") as entrada, \
         (destino / archivo).open("w", newline="", encoding="utf-8") as salida:
        lector = csv.reader(entrada)
        escritor = csv.writer(salida)
        encabezado = next(lector)
        indice = encabezado.index(columna)
        escritor.writerow(encabezado)

        for fila in lector:
            if convertir(fila[indice]) <= limite:
                escritor.writerow(fila)


def recortar_metroriel(origen, destino, limite):
    with (origen / "metroriel_viajes.jsonl").open(encoding="utf-8") as entrada, \
         (destino / "metroriel_viajes.jsonl").open("w", encoding="utf-8") as salida:
        for linea in entrada:
            registro = json.loads(linea)
            fecha = datetime.date.fromisoformat(registro["entry"]["ts"][:10])
            if fecha <= limite:
                salida.write(linea)


def recortar(hasta, salida, origen=None):
    origen = origen or DATOS_CRUDOS
    limite = datetime.date.fromisoformat(hasta)
    destino = RAIZ / salida
    destino.mkdir(parents=True, exist_ok=True)

    for archivo in CATALOGOS:
        copiar_catalogo(origen, destino, archivo)

    recortar_csv(
        origen, destino, "transmetro_validaciones.csv", "fecha_hora", limite,
        convertir=lambda valor: datetime.date.fromisoformat(valor[:10]),
    )

    recortar_csv(
        origen, destino, "transurbano_transacciones.csv", "fecha", limite,
        convertir=lambda valor: datetime.datetime.strptime(valor, "%d/%m/%Y").date(),
    )

    recortar_csv(
        origen, destino, "aerometro_boardings.csv", "timestamp_utc", limite,
        convertir=lambda valor: (
            datetime.datetime.strptime(valor, "%Y-%m-%dT%H:%M:%SZ")
            - DESPLAZAMIENTO_AEROMETRO_UTC
        ).date(),
    )

    recortar_csv(
        origen, destino, "cdc_padron_usuarios.csv", "commit_ts", limite,
        convertir=lambda valor: datetime.date.fromisoformat(valor[:10]),
    )

    recortar_metroriel(origen, destino, limite)

    print(f"Datos recortados hasta {hasta} en {destino}")

    return destino


def main():
    argumentos = argparse.ArgumentParser()
    argumentos.add_argument("--hasta", required=True)
    argumentos.add_argument("--salida", default="datos_recortados")
    parametros = argumentos.parse_args()

    recortar(parametros.hasta, parametros.salida)


if __name__ == "__main__":
    main()
