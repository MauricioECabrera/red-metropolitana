# Seguridad y acceso al tablero

## Datos publicados

Tableau consume el esquema `gold` de DuckDB. La identidad visible es
`persona_sk`, un identificador seudonimizado; Gold no publica el número de
tarjeta ni la llave de persona usada en Silver.

La sal para construir `persona_sk` se guarda en `.env`. Ese archivo está
excluido por `.gitignore` y no debe incluirse en el workbook, capturas,
documentación ni commits. `persona_sk` sigue siendo un dato que permite
relacionar registros de una misma persona; se debe tratar como sensible.

## Acceso propuesto

| Perfil | Acceso necesario |
|---|---|
| Público que consulta resultados | Tableros agregados, sin identificadores por persona |
| Analista del tablero | Tablas Gold y workbook; acceso a `persona_sk` solo si necesita calcular usuarios distintos |
| Equipo de ingeniería autorizado | Silver y mecanismos de generación de Gold, según su tarea |
| Responsable de la sal | Archivo `.env` compartido por un canal privado y con acceso limitado |

Esta tabla es una **política propuesta**. El prototipo usa un archivo DuckDB
local: no implementa por sí mismo usuarios, roles ni permisos de servidor.
Si se publica en una plataforma compartida, allí deben configurarse los
permisos efectivos y comprobarse con cuentas de prueba.

## Controles al compartir

1. Versionar el archivo `.twb` y la documentación, no `.env`, datos crudos,
   archivos `.duckdb` ni extractos con datos de personas.
2. Revisar la conexión y las rutas locales guardadas en el workbook antes de
   compartirlo; cada integrante debe generar su propio Gold.
3. Mostrar agregados en los tableros compartidos. Evitar publicar hojas de
   detalle con `persona_sk` o atributos individuales del padrón.
4. Restringir Bronze, Silver y la sal al equipo autorizado. La sal junto con
   Silver permitiría reconstruir la correspondencia de identidades.
5. Si cambia la sal, regenerar Gold y el tablero: los valores `persona_sk`
   anteriores y nuevos dejarán de coincidir.

## Límites analíticos

Aerómetro carece de una llave enlazable con los otros tres operadores.
La métrica de multimodalidad no identifica conexiones con Aerómetro.
Los abordajes de otros modos en una zona y los trayectos MetroRiel en esa zona
no prueban que una misma persona haya hecho un transbordo.