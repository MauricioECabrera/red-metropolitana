# Métricas medidas del proyecto

Todas las cifras salen de ejecutar el pipeline completo y consultar el warehouse.
Se reproducen con `python scripts/cifras_informe.py` y
`python -m orquestacion.verificar_idempotencia`.

## Volumen

| Fuente | Bronze | Silver | Cuarentena | Gold | No promovidas |
|---|---:|---:|---:|---:|---:|
| Aerómetro | 203,554 | 203,554 | 0 | 203,554 | 0 |
| MetroRiel | 299,100 | 299,100 | 3,589 | 299,100 | 0 |
| Transmetro | 363,221 | 363,221 | 1,115 | 362,106 | 1,115 |
| Transurbano | 832,791 | 827,788 | 5,003 | 786,398 | 41,390 |
| Padrón (CDC) | 31,050 | 31,050 | 2,768 | — | — |
| **Total** | **1,729,716** | | **12,475** | **1,651,158** | |

Las 41,390 de Transurbano no son errores: son rechazos del operador al momento
del cobro (saldo insuficiente o tarjeta inválida). Decisión D-006.

## Calidad

43 reglas declaradas, 7 con rechazos, 12,475 registros en cuarentena
(0.72 % del total ingerido).

| Fuente | Motivo | Registros | % de Bronze |
|---|---|---:|---:|
| Transurbano | estacion_desconocida | 4,186 | 0.503 % |
| MetroRiel | viaje_sin_salida | 3,589 | 1.200 % |
| Padrón | llave_centinela | 2,206 | 7.105 % |
| Transmetro | duplicado | 1,115 | 0.307 % |
| Transurbano | fecha_futura | 817 | 0.098 % |
| Padrón | actualizacion_sobre_baja | 423 | 1.362 % |
| Padrón | baja_repetida | 139 | 0.448 % |

Duplicados detectados: 1,115 (Transmetro, lecturas repetidas del torniquete).

## CDC

| Concepto | Valor |
|---|---:|
| Altas aplicadas | 10,800 |
| Cambios aplicados | 16,200 |
| Bajas aplicadas | 4,050 |
| Tarjetas antes de los borrados | 22,462 |
| Tarjetas después de los borrados | 22,462 |
| Activas al cierre | 19,110 |
| Dadas de baja | 3,352 |
| Versiones del SCD Tipo 2 | 27,428 |

El total no cambia porque una baja no elimina la fila: cierra la versión
vigente y abre una nueva con estado INACTIVA. Decisión D-010.

## Rendimiento

| Etapa | Duración |
|---|---:|
| Catálogos | 0.12 s |
| MetroRiel | 0.17 s |
| Transurbano | 0.18 s |
| Padrón (CDC) | 0.05 s |
| Productor de Kafka | 0.13 s |
| Consumidor de Kafka | 0.17 s |
| dbt build (50 modelos, 226 pruebas) | 34.19 s |
| Publicar Gold | 1.95 s |
| Exportar modelo | 0.09 s |
| **Total del flujo** | **37.04 s** |

| Capa | Tamaño en disco |
|---|---:|
| Datos crudos entregados (CSV y JSONL) | 130.7 MB |
| Bronze (lake en Parquet) | 51.5 MB |
| Silver y Gold (warehouse) | 617.0 MB |
| Gold publicado para el tablero | 41.3 MB |

Bronze ocupa 60 % menos que los archivos originales: Parquet es columnar y
comprimido. El warehouse pesa más que el crudo porque Silver materializa los
modelos de evaluación y Gold vuelve a materializar el modelo dimensional; es
espacio a cambio de velocidad de consulta.

| Consulta del tablero | Tiempo |
|---|---:|
| Demanda por modo, zona y hora | 0.040 s |
| Cobertura por zona | < 0.001 s |
| Usuarios multimodales | 0.065 s |
| Corredor MetroRiel origen–destino | 0.019 s |

## Idempotencia

| Corrida | Tablas | Filas |
|---|---:|---:|
| Primera | 52 | 9,080,860 |
| Segunda | 52 | 9,080,860 |
| Diferencias | 0 | 0 |

Además del conteo se compara una huella de contenido por tabla (XOR del hash
de cada fila), que no depende del orden y cambia si cambia un solo registro.
Las dos corridas resultaron idénticas en filas y en contenido.
Detalle en `docs/evidencias/idempotencia.md`.

## Cobertura

15 de 16 zonas con servicio. La única sin ningún punto de abordaje es
**Santa Catarina Pinula**.

| Concepto | Personas |
|---|---:|
| Un solo modo | 33,553 |
| Dos modos | 26,831 |
| Tres modos | 9,996 |
| **Usuarios multimodales** | **36,827** |
| **Total de personas** | **70,380** |

Aerómetro no se puede vincular con los otros operadores, así que la cifra de
multimodalidad es un piso, no un total.