# Índice de scripts por entregable · Fase 1

Proyecto 1 · Agencia Metropolitana de Transporte · Red Metropolitana de Guatemala
Repositorio: https://github.com/MauricioECabrera/red-metropolitana

El código de los entregables de la Fase 1 se entrega en este repositorio. Esta tabla indica
en qué archivo está cada script solicitado. El documento de datos y conclusiones es
`docs/entrega_fase1/Informe_Fase_1.pdf`.

## 1.1 Scripts de carga por vía

| Entregable | Archivo |
|---|---|
| Productor que publica en Kafka línea por línea (Transmetro y Aerómetro) | `ingesta/streaming/productores/productor.py` |
| Consumidor de Kafka que escribe en Bronze | `ingesta/streaming/consumidores/consumidor.py` |
| Carga batch de catálogos (estaciones y paradas de los cuatro operadores) | `ingesta/batch/cargar_catalogos.py` |
| Carga batch de MetroRiel (JSON Lines) | `ingesta/batch/cargar_metroriel.py` |
| Carga batch de Transurbano | `ingesta/batch/cargar_transurbano.py` |
| Carga del log de CDC del padrón | `ingesta/cdc/cargar_cdc.py` |
| Contrato común de Bronze e idempotencia por huella de contenido | `ingesta/comun/bronze.py` |

## 1.2 CDC y catálogos de usuarios

| Entregable | Archivo |
|---|---|
| CDC que aplica INSERT, UPDATE y DELETE en orden de secuencia | `dbt/models/silver/padron/cdc_padron_evaluado.sql` |
| Cuarentena del CDC | `dbt/models/silver/padron/cdc_cuarentena.sql` |
| Llaves distintas de Transurbano | `dbt/models/silver/usuarios/usuarios_transurbano.sql` |
| Llaves distintas de MetroRiel | `dbt/models/silver/usuarios/usuarios_metroriel.sql` |
| Llaves distintas de Aerómetro | `dbt/models/silver/usuarios/usuarios_aerometro.sql` |

## 1.3 Silver, calidad e identidad

| Entregable | Archivo |
|---|---|
| Silver de MetroRiel (abordajes y trayectos) | `dbt/models/silver/metroriel/` |
| Silver de Transmetro | `dbt/models/silver/transmetro/` |
| Silver de Aerómetro (incluye conversión de UTC a hora local) | `dbt/models/silver/aerometro/` |
| Silver de Transurbano (incluye conversión de centavos a quetzales) | `dbt/models/silver/transurbano/` |
| Dimensión zona conformada y resolución de alias | `dbt/models/silver/_conformadas/dim_zona.sql`, `map_zona_alias.sql` |
| Identidad de usuario entre operadores | `dbt/models/silver/_conformadas/dim_persona.sql` |
| Dimensión de estaciones y paradas unificada | `dbt/models/silver/_conformadas/dim_estacion_parada.sql` |
| Cuarentena unificada de todas las fuentes | `dbt/models/silver/cuarentena/cuarentena.sql` |
| Catálogo de las 43 reglas de calidad | `dbt/models/reportes/cat_reglas_calidad.sql` |
| Conteo de registros por regla | `dbt/models/reportes/rpt_calidad.sql` |
| Volumen por capa | `dbt/models/reportes/rpt_volumen_por_capa.sql` |
| SCD Tipo 2 del padrón | `dbt/models/silver/padron/slv_padron_scd2.sql` |
| Seudonimización con sal | `dbt/macros/seudonimizar.sql` |
| Tests de conservación por fuente (Bronze = Silver válido + cuarentena) | `dbt/tests/assert_conservacion_*.sql` |

## 1.4 Modelo dimensional

| Entregable | Archivo |
|---|---|
| DDL de las tablas de hechos y dimensiones de Gold | `docs/gobernanza/ddl_gold.sql` |
| Diagrama del modelo (entidad-relación) | `docs/gobernanza/modelo_gold.md` |
| Matriz del bus | `docs/gobernanza/matriz_bus.md` |
| Modelos de Gold | `dbt/models/gold/` |
| Script que genera el DDL y el diagrama desde el warehouse | `scripts/exportar_modelo.py` |

## 1.5 Orquestación

| Entregable | Archivo |
|---|---|
| Flujo de orquestación con Prefect | `orquestacion/flujo.py` |
| Verificación de idempotencia (dos corridas con conteos y huellas) | `orquestacion/verificar_idempotencia.py` |
| Evidencia generada por la verificación | `docs/evidencias/idempotencia.md` |
| Publicación de Gold para el tablero | `scripts/publicar_gold.py` |

## Documentación de respaldo

| Contenido | Archivo |
|---|---|
| Bitácora de decisiones D-001 a D-012 | `docs/bitacora.md` |
| Documento de reglas de calidad | `docs/gobernanza/reglas_calidad.md` |
| Evidencia del CDC | `docs/evidencias/cdc.md` |
| Cifras del informe (script reproducible) | `scripts/cifras_informe.py` |

## Cómo reproducir todo

```
git clone https://github.com/MauricioECabrera/red-metropolitana
cd red-metropolitana
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.ejemplo .env          # configurar SEUDONIMIZACION_SAL
docker compose up -d
python -m orquestacion.verificar_idempotencia
```

El pipeline completo corre en menos de un minuto y termina imprimiendo `IDEMPOTENTE`.
