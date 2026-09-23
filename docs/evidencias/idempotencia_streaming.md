# Evidencia de Idempotencia - Vía Streaming (Rol B)
**Autor:** Diego de Jesus Urbina Chavez
**Fecha de ejecución:** 23 de septiembre de 2026

## 1. Primera Corrida (Ingesta inicial)

### Productor de Kafka
**Salida de consola:**
```text
Tópico                         | Archivo                                  | Mensajes   | Acción
-----------------------------------------------------------------------------------------------
rm.transmetro.validaciones     | datos_red\transmetro_validaciones.csv    | 363221     | PUBLICADO
rm.aerometro.boardings         | datos_red\aerometro_boardings.csv        | 203554     | PUBLICADO

Consumidor de Kafka
Salida de consola:

Carga completada. Resumen:
- transmetro_validaciones: 363221 filas cargadas (lote: 7ce830becf569fb7) -> CARGADO
- aerometro_boardings: 203554 filas cargadas (lote: 9e034031c3648122) -> CARGADO

2. Segunda Corrida (Prueba de Idempotencia)
Productor de Kafka
Salida de consola:
Tópico                         | Archivo                                  | Mensajes   | Acción
-----------------------------------------------------------------------------------------------
rm.transmetro.validaciones     | datos_red\transmetro_validaciones.csv    | 0          | OMITIDO
rm.aerometro.boardings         | datos_red\aerometro_boardings.csv        | 0          | OMITIDO

Consumidor de Kafka
Salida de consola:

sin mensajes nuevos para la fuente transmetro_validaciones
sin mensajes nuevos para la fuente aerometro_boardings
Carga completada. Resumen:

3. Integración en dbt
Última línea de dbt build:

Finished 'build' with 1 warning and 0 errors for target 'dev' [52.0s]
Processed: 48 models | 170 tests | 2 seeds
Summary: 220 total | 165 success | 0 error | 55 skipped
Done. PASS=165 WARN=1 ERROR=0 SKIP=55 TOTAL=220

4. Tabla Comparativa de Idempotencia
Fuente,Filas en Primera Corrida,Filas en Segunda Corrida,Resultado
Transmetro (slv_tm_abordajes),"362,106 válidas + 1,115 cuarentena","362,106 válidas + 1,115 cuarentena",Idéntico (Sin duplicados)
Aerómetro (slv_am_abordajes),"203,554 válidas + 0 cuarentena","203,554 válidas + 0 cuarentena",Idéntico (Sin duplicados)

Conclusión:
El flujo es completamente idempotente. El productor registra la huella del archivo para no volver a publicar eventos ya procesados, y el consumidor de Kafka no procesa lotes adicionales si no hay mensajes nuevos en el tópico. La capa Bronze no registró duplicados en la segunda ejecución.