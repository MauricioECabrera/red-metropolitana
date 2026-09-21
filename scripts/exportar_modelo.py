"""
=====================================================================
  exportar_modelo.py  ·  DDL y diagrama del modelo dimensional Gold
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Genera dos documentos a partir del modelo publicado:
    docs/gobernanza/ddl_gold.sql       DDL de las tablas de Gold
    docs/gobernanza/modelo_gold.md     diagrama entidad-relacion

  Las columnas y tipos salen de warehouse/tablero_gold.duckdb. Las
  llaves primarias salen de los tests unique de dbt y las llaves
  foraneas de los tests relationships, leidos de dbt/target/
  manifest.json. El DDL refleja el contrato que dbt verifica.

  Ejecutar desde la raiz del repositorio, despues de dbt build y de
  publicar_gold.py:
    python scripts/exportar_modelo.py
=====================================================================
"""
import json
import pathlib
import re
import sys

import duckdb

RAIZ = pathlib.Path(__file__).resolve().parents[1]
TABLERO = RAIZ / "warehouse" / "tablero_gold.duckdb"
MANIFIESTO = RAIZ / "dbt" / "target" / "manifest.json"
SALIDA_DDL = RAIZ / "docs" / "gobernanza" / "ddl_gold.sql"
SALIDA_DIAGRAMA = RAIZ / "docs" / "gobernanza" / "modelo_gold.md"


def leer_restricciones():
    manifiesto = json.loads(MANIFIESTO.read_text(encoding="utf-8"))
    alias = {
        nodo["name"]: nodo.get("alias") or nodo["name"]
        for nodo in manifiesto["nodes"].values()
        if nodo["resource_type"] == "model" and nodo.get("schema") == "gold"
    }
    llaves_primarias = {}
    llaves_foraneas = []
    for nodo in manifiesto["nodes"].values():
        if nodo["resource_type"] != "test" or not nodo.get("test_metadata"):
            continue
        prueba = nodo["test_metadata"]
        modelo = nodo.get("attached_node", "") or ""
        modelo = modelo.split(".")[-1]
        if modelo not in alias:
            continue
        columna = nodo.get("column_name") or prueba.get("kwargs", {}).get("column_name")
        if prueba["name"] == "unique" and columna:
            llaves_primarias.setdefault(alias[modelo], set()).add(columna)
        if prueba["name"] == "unique_combination_of_columns":
            combinacion = prueba["kwargs"].get("combination_of_columns") or prueba["kwargs"].get("arguments", {}).get("combination_of_columns")
            llaves_primarias.setdefault(alias[modelo], set()).add(", ".join(combinacion))
        if prueba["name"] == "relationships" and columna:
            destino = re.search(r"ref\(['\"]([^'\"]+)['\"]\)", prueba["kwargs"]["to"]).group(1)
            if destino in alias:
                llaves_foraneas.append((alias[modelo], columna, alias[destino], prueba["kwargs"]["field"]))
    return llaves_primarias, sorted(set(llaves_foraneas))


def leer_columnas():
    con = duckdb.connect(str(TABLERO), read_only=True)
    filas = con.execute(
        "select table_name, column_name, data_type from information_schema.columns "
        "where table_schema = 'gold' order by table_name, ordinal_position"
    ).fetchall()
    con.close()
    tablas = {}
    for tabla, columna, tipo in filas:
        tablas.setdefault(tabla, []).append((columna, tipo))
    return tablas


def escribir_ddl(tablas, llaves_primarias, llaves_foraneas):
    orden = sorted(tablas, key=lambda t: (not t.startswith("dim_"), t))
    bloques = []
    for tabla in orden:
        lineas = [f"    {columna:<28}{tipo}" for columna, tipo in tablas[tabla]]
        for columna in sorted(llaves_primarias.get(tabla, [])):
            lineas.append(f"    primary key ({columna})")
        for origen, columna, destino, campo in llaves_foraneas:
            if origen == tabla:
                lineas.append(f"    foreign key ({columna}) references gold.{destino} ({campo})")
        bloques.append(f"create table gold.{tabla} (\n" + ",\n".join(lineas) + "\n);")
    encabezado = (
        "-- ==================================================================\n"
        "--  ddl_gold.sql  ·  DDL del modelo dimensional Gold\n"
        "--  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana\n"
        "--  Generado por scripts/exportar_modelo.py desde el warehouse y\n"
        "--  los tests unique y relationships de dbt.\n"
        "-- ==================================================================\n\n"
    )
    SALIDA_DDL.parent.mkdir(parents=True, exist_ok=True)
    SALIDA_DDL.write_text(encabezado + "\n\n".join(bloques) + "\n", encoding="utf-8")


def escribir_diagrama(tablas, llaves_primarias, llaves_foraneas):
    columnas_fk = {(o, c) for o, c, _, _ in llaves_foraneas}
    entidades = []
    for tabla in sorted(tablas, key=lambda t: (not t.startswith("dim_"), t)):
        filas = []
        for columna, tipo in tablas[tabla]:
            marca = []
            if any(columna in [c.strip() for c in llave.split(",")] for llave in llaves_primarias.get(tabla, set())):
                marca.append("PK")
            if (tabla, columna) in columnas_fk:
                marca.append("FK")
            tipo_corto = re.sub(r"\(.*\)", "", tipo).replace(" ", "_")
            filas.append(f"        {tipo_corto} {columna}" + (f" {', '.join(marca)}" if marca else ""))
        entidades.append(f"    {tabla} {{\n" + "\n".join(filas) + "\n    }")
    relaciones = [
        f'    {destino} ||--o{{ {origen} : "{columna}"'
        for origen, columna, destino, _ in llaves_foraneas
        if origen != destino
    ]
    contenido = (
        "# Modelo dimensional Gold\n\n"
        "Generado por `scripts/exportar_modelo.py` desde el warehouse y los tests de dbt. "
        "Las llaves primarias salen de los tests `unique` y las foráneas de los tests `relationships`.\n\n"
        "```mermaid\nerDiagram\n" + "\n".join(relaciones) + "\n\n" + "\n\n".join(entidades) + "\n```\n"
    )
    SALIDA_DIAGRAMA.write_text(contenido, encoding="utf-8")


def main():
    for requerido in (TABLERO, MANIFIESTO):
        if not requerido.exists():
            print(f"No existe {requerido.relative_to(RAIZ)}. Correr primero .\\scripts\\dbt.ps1 build y python scripts/publicar_gold.py")
            sys.exit(1)
    llaves_primarias, llaves_foraneas = leer_restricciones()
    tablas = leer_columnas()
    escribir_ddl(tablas, llaves_primarias, llaves_foraneas)
    escribir_diagrama(tablas, llaves_primarias, llaves_foraneas)
    print()
    print(f"{len(tablas)} tablas · {sum(len(v) for v in llaves_primarias.values())} llaves primarias · {len(llaves_foraneas)} llaves foraneas")
    print(f"Escrito {SALIDA_DDL.relative_to(RAIZ)}")
    print(f"Escrito {SALIDA_DIAGRAMA.relative_to(RAIZ)}")
    print()


if __name__ == "__main__":
    main()