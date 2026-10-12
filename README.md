# Red Metropolitana de Transporte

Proyecto 1 · Ciencia de Datos · Segundo Semestre 2026
Universidad Rafael Landivar · Facultad de Ingenieria

Plataforma de datos integrada de los cuatro operadores de transporte del area
metropolitana de Guatemala: Transmetro, Transurbano, MetroRiel y Aerometro.

## Arquitectura

Lake en Parquet particionado por fecha (Bronze), warehouse en DuckDB
(Silver y Gold), transformacion con dbt, ingesta por tres vias
(streaming con Kafka, batch y CDC), orquestacion con Prefect y
visualizacion en Tableau.

Regla estructural: Gold nunca lee de Bronze. Los registros invalidos van a
cuarentena, nunca se descartan. Las features salen de Silver.

## Requisitos

Windows 11, Python 3.11 o superior, Docker Desktop, Git, Tableau Desktop,
conector DuckDB/MotherDuck para Tableau y controlador JDBC de DuckDB

## Instalación y ejecución · Git Bash en Windows

    ```bash
    python -m venv .venv
    source .venv/Scripts/activate
    python -m pip install -r requirements.txt
    cp .env.example .env
    # Editar .env y configurar la sal compartida por el equipo.
    python generador/generar_red_metropolitana.py
    docker compose up -d
    python -m orquestacion.flujo
    ```

El flujo carga las fuentes, ejecuta dbt y publica
`warehouse/tablero_gold.duckdb`. La sal real se comparte de forma privada;
`.env` no se sube al repositorio. Para volver a publicar Gold, cerrar Tableau
antes de ejecutar el flujo.

## Reglas del repositorio

- Cada integrante crea archivos unicamente dentro de las carpetas de su rol.
- dbt_project.yml, dbt/seeds/ y dbt/models/silver/_conformadas/ tienen dueno unico.
- Nadie hace merge sin que dbt test pase en su propia maquina.
- El warehouse, el lake y los datos crudos no se versionan. Se regeneran.
- El workbook de Tableau es binario y tiene dueno unico.
- Commits diarios, aunque sean parciales.

## Dueno por carpeta

| Carpeta | Rol |
|---|---|
| dbt/seeds/, dbt/models/silver/_conformadas/, dbt/models/gold/, ingesta/cdc/, orquestacion/ | A |
| ingesta/streaming/, bronze y silver de transmetro y aerometro, dbt/models/features/ | B |
| ingesta/batch/, bronze y silver de catalogos, transurbano y metroriel, silver/cuarentena/ | C |
| tableau/, docs/ | D |

## Tableros y gobernanza

El workbook `tableau/red_metropolitana_tablero.twb` contiene dos tableros:
**Panorama de la red** y **Corredor MetroRiel**. Se conecta únicamente a
`warehouse/tablero_gold.duckdb`, que se genera localmente y contiene el
esquema `gold`. Al abrir el workbook en otra computadora puede ser necesario
actualizar la ruta de la conexión.

Las definiciones y límites de sus indicadores están en
`docs/gobernanza/diccionario_tablero.md`. La política de acceso propuesta y
los controles de publicación están en
`docs/gobernanza/seguridad_tablero.md`.

La recomendación del corredor propone evaluar un piloto en las zonas 6 y 8:
se observaron 16,131 trayectos MetroRiel de 6 a 8 y 15,797 en sentido
contrario en la ejecución analizada. Son trayectos origen–destino, no
transbordos comprobados desde otros modos.