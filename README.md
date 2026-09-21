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
driver ODBC de DuckDB para Tableau.

## Instalacion

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    Copy-Item .env.example .env
    python .\generador\generar_red_metropolitana.py
    docker compose up -d
    cd dbt
    dbt deps
    dbt seed

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