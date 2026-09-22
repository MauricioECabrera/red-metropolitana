# Reglas de calidad

Qué se considera un registro inválido en cada fuente, qué se hace con él y
cómo se verifica que no se perdió nada. Documento escrito antes del código que
lo implementa, según la sección 3.1 del enunciado.

## Principio

Ningún registro se descarta. Un registro que no cumple una regla se retiene en
`silver.cuarentena` con el motivo, el contenido original y las columnas que
permiten volver al archivo crudo. Descartar en silencio pierde la mitad de la
sección 1.3.

Cada fuente tiene un modelo `<fuente>_evaluado` con **todas** las filas de
Bronze y una columna `motivo_rechazo_<proceso>` por cada proceso que alimenta:
nula si la fila es válida para ese proceso, y si no, el nombre de la **primera**
regla que falla. Los modelos limpios de Silver filtran `motivo_rechazo is null`
y los modelos `<fuente>_cuarentena` se quedan con el resto.

## Precedencia

Una fila puede violar varias reglas a la vez. Se le asigna solo la primera
según el orden declarado en `reportes.cat_reglas_calidad`. Por eso el orden
cambia cómo se reparten los rechazos entre motivos, pero nunca cambia el total.

En Transurbano hay 3 filas que traen fecha del futuro **y** código de parada
vacío. Con el orden declarado quedan contadas como `fecha_futura`, no como
`estacion_desconocida`.

## Invariante de conservación

Para cada fuente y cada proceso:

```
filas en Bronze = filas válidas en Silver + filas en cuarentena
```

Se verifica con un test por fuente en `dbt/tests/assert_conservacion_*.sql`.
Si falla, el build se detiene: significa que un registro desapareció.

La cuarentena se aplica **por proceso, no por registro**. Un viaje de MetroRiel
sin salida es un abordaje válido y un trayecto inválido: aparece en
`slv_mr_abordajes` y en cuarentena con proceso `trayecto`. No se pierde de
ninguno de los dos.

## Fecha futura

Un evento es futuro si su marca de tiempo es posterior a la `_ingesta_ts` de su
lote. La regla no depende de una fecha fija escrita en el código, así que el
resultado no cambia según el día en que se corra el pipeline.

## Catálogo por fuente

43 reglas declaradas. El detalle vive en `reportes.cat_reglas_calidad` y los
conteos observados en `reportes.rpt_calidad`.

### Transurbano · proceso `transaccion` · 6 reglas

| # | Regla | Condición |
|---|---|---|
| 1 | `duplicado` | Segunda aparición o posterior de una transacción idéntica |
| 2 | `tarjeta_invalida` | `num_tarjeta` no cumple el patrón de diez dígitos |
| 3 | `fecha_invalida` | `fecha` y `hora`, que llegan en columnas separadas, no arman una marca de tiempo válida |
| 4 | `fecha_futura` | La marca de tiempo es posterior a la ingesta del lote |
| 5 | `estacion_desconocida` | `cod_parada` viene vacío o no existe en `dim_estacion_parada` |
| 6 | `monto_invalido` | Monto nulo o negativo después de convertir de centavos a quetzales |

Transurbano no entrega identificador de transacción. La llave se construye con
el lote y el número de fila de origen, que son estables entre corridas porque
el lote es la huella del contenido del archivo.

Los códigos de estado 7 (saldo insuficiente) y 9 (tarjeta inválida) **no son
una regla de calidad**: son transacciones bien formadas cuyo resultado fue un
rechazo del validador. No van a cuarentena. Ver D-006.

### MetroRiel · procesos `abordaje` y `trayecto` · 7 + 5 reglas

Abordaje: `identificador_invalido`, `duplicado`, `tarjeta_invalida`,
`fecha_invalida`, `fecha_futura`, `estacion_desconocida`, `monto_invalido`.

Trayecto: `viaje_sin_salida`, `fecha_invalida`, `salida_anterior_a_entrada`,
`estacion_desconocida`, `origen_igual_destino`. El proceso `trayecto` hereda
además el rechazo del proceso `abordaje`.

### Transmetro y Aerómetro · proceso `abordaje` · 7 reglas cada uno

Mismo conjunto que el abordaje de MetroRiel, con los patrones de tarjeta de
cada operador: `TC-` más ocho dígitos en Transmetro, hash de doce caracteres
hexadecimales en Aerómetro.

### Padrón CDC · proceso `padron` · 11 reglas

| # | Regla | Condición |
|---|---|---|
| 1 | `secuencia_invalida` | El número de secuencia del log no es entero. Sin secuencia no hay orden de aplicación |
| 2 | `duplicado` | Segunda aparición o posterior del mismo número de secuencia |
| 3 | `llave_centinela` | La tarjeta trae `SIN-TARJETA`. No identifica a nadie y colapsaría todos esos eventos en un registro. Ver D-005 |
| 4 | `tarjeta_invalida` | La tarjeta no corresponde a ninguno de los tres formatos del padrón |
| 5 | `operacion_invalida` | La operación no es INSERT, UPDATE ni DELETE |
| 6 | `fecha_invalida` | La marca de tiempo del commit no se puede interpretar |
| 7 | `fecha_futura` | El commit es posterior a la ingesta del lote |
| 8 | `perfil_invalido` | El perfil no es uno de los cuatro válidos. No aplica a los DELETE, que llegan sin cuerpo |
| 9 | `zona_desconocida` | La zona de residencia no resuelve contra `dim_zona`. No aplica a los DELETE |
| 10 | `actualizacion_sobre_baja` | Llega un UPDATE sobre una tarjeta cuya última operación fue DELETE |
| 11 | `baja_repetida` | Llega un DELETE sobre una tarjeta ya dada de baja |

El padrón entra a `silver.cuarentena` con fuente `cdc_padron` y proceso
`padron`. No aparece en `rpt_volumen_por_capa` porque no genera abordajes.

## Resultado medido

Con Transurbano, MetroRiel y el padrón integrados:

| Fuente | Proceso | Reglas | En cuarentena | % de su Bronze |
|---|---|---|---|---|
| Transurbano | `transaccion` | 6 | 5,003 | 0.6008 |
| MetroRiel | `abordaje` | 7 | 0 | 0.0000 |
| MetroRiel | `trayecto` | 5 | 3,589 | 1.1999 |
| Padrón CDC | `padron` | 11 | 2,768 | 8.9147 |
| Transmetro | `abordaje` | 7 | pendiente | |
| Aerómetro | `abordaje` | 7 | pendiente | |
| **Total** | | **43** | **11,360** | |

Desglose de los motivos que se dispararon:

| Fuente | Regla | Registros | % de su Bronze |
|---|---|---|---|
| Transurbano | `estacion_desconocida` | 4,186 | 0.5026 |
| MetroRiel | `viaje_sin_salida` | 3,589 | 1.1999 |
| Padrón CDC | `llave_centinela` | 2,206 | 7.1047 |
| Transurbano | `fecha_futura` | 817 | 0.0981 |
| Padrón CDC | `actualizacion_sobre_baja` | 423 | 1.3623 |
| Padrón CDC | `baja_repetida` | 139 | 0.4477 |

Las 37 reglas restantes se evaluaron y no fallaron. Una regla con cero rechazos
se reporta como cero: es evidencia de que se revisó, no de que falte.

Cuando el rol B integre Transmetro (1,115 por `duplicado`) y Aerómetro (0), el
total de la red llega a **12,475**.
