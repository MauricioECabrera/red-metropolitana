# Bitácora de decisiones

Cada decisión se registra antes de escribir el código que la implementa.
Formato: contexto, opciones, decisión, evidencia, consecuencia asumida.

---

## D-001 · Grano de las tablas de hechos
**Estado:** cerrada · **Responsable:** A

**Contexto.** MetroRiel registra el trayecto completo (entrada y salida en la
misma fila). Transmetro, Transurbano y Aerómetro registran abordajes sueltos.

**Opciones.**
1. Grano "viaje puerta a puerta": exige inferir el viaje en tres de los cuatro
   sistemas. La inferencia no tiene sustento en estos datos.
2. Grano "abordaje": MetroRiel pierde el destino.
3. Dos procesos, dos granos.

**Decisión.** Opción 3.

- `fct_abordaje` — una fila es una validación exitosa de una tarjeta al
  ingresar a un vehículo o estación, en cualquiera de los cuatro modos.
  MetroRiel aporta su entrada.
- `fct_trayecto_od` — una fila es un trayecto de MetroRiel con entrada y
  salida validadas. Solo MetroRiel.

**Reglas que se derivan del grano.**
- Un TRANSBORDO de Transmetro es un abordaje. El tipo queda como atributo.
- Una transacción rechazada de Transurbano (estados 7 y 9) no es un abordaje
  exitoso y no entra a `fct_abordaje`. Su destino lo define D-006.
- Un viaje de MetroRiel sin salida (3,589) sí aporta su abordaje de entrada
  a `fct_abordaje`, y va a cuarentena para `fct_trayecto_od` con motivo
  `viaje_sin_salida`. La cuarentena se aplica por proceso, no por registro.

**Clasificación de medidas.**
| Medida | Tabla | Tipo |
|---|---|---|
| cantidad_abordajes | fct_abordaje | aditiva |
| monto_q | fct_abordaje, fct_trayecto_od | aditiva |
| distancia_km | fct_trayecto_od | aditiva |
| duracion_s | fct_trayecto_od | aditiva en suma; su promedio es no aditivo |
| tarjetas_activas | snapshot del padrón | semi-aditiva (no suma entre fechas) |
| usuarios_distintos | derivada | no aditiva |
| proporcion_hora_pico | derivada | no aditiva |

**Consecuencia asumida.** No se reporta "viajes puerta a puerta" para los
modos de abordaje. El destino solo existe para MetroRiel.

---

## D-002 · Estrategia de identidad del usuario
**Estado:** cerrada · **Responsable:** A

**Contexto.** Cuatro formatos de llave: `TC-00012345` (Transmetro),
`0000012345` (Transurbano), `MR0012345` (MetroRiel), hash de 12 caracteres
(Aerómetro). No existe tabla que las relacione.

**Hipótesis.** Transmetro, Transurbano y MetroRiel emiten tarjetas desde una
numeración común. La parte numérica identifica a la persona.

**Evidencia (prueba falsable).** El padrón CDC registra a cada persona con su
primera tarjeta en orden Transmetro → Transurbano → MetroRiel. Si la
numeración es común, una llave de formato Transurbano en el CDC implica que
esa persona no tiene tarjeta de Transmetro.

| Llaves del CDC | Cantidad | Número presente en Transmetro | En Transurbano | Esperado si fuera independiente |
|---|---|---|---|---|
| Formato Transurbano | 4,038 | 0 | — | ~2,900 |
| Formato MetroRiel | 992 | 0 | 0 | ~710 / ~600 |

**Decisión.**
- `persona_id` = parte numérica de la llave de Transmetro, Transurbano o
  MetroRiel.
- Aerómetro: identidad propia, no vinculable. El hash no contiene parte
  numérica y no existe atributo compartido que permita enlazarlo.

**Resultado.** 55,884 personas distintas entre Transmetro, Transurbano y
MetroRiel; 36,827 usan dos o más de esos sistemas.

**Límites declarados.**
- El transbordo que involucra Aerómetro no es medible. La cifra de usuarios
  multimodales es un piso, no un total.
- Los 14,496 usuarios de Aerómetro cuentan como personas distintas, lo que
  sobreestima el total de personas de la red.
- Si la numeración común dejara de cumplirse en datos futuros, la prueba
  anterior lo detecta y debe correrse en cada carga.

---

## D-003 · Bronze en lake o en warehouse
**Estado:** cerrada · **Responsable:** A

**Decisión.** Bronze vive en el lake: archivos Parquet en
`lake/bronze/<fuente>/fecha_ingesta=AAAA-MM-DD/<lote_id>.parquet`.
Silver y Gold viven en el warehouse DuckDB.

**Justificación.**
- MetroRiel llega como JSON anidado. En el lake se guarda como tipo JSON
  nativo, exactamente como llegó, sin aplanar. En una tabla del warehouse
  habría que aplanarlo (transformar en Bronze) o guardarlo como texto.
- Bronze solo se acumula y nunca lo consulta Gold. No necesita motor de
  base de datos, solo almacenamiento barato. MetroRiel pasa de 53 MB en
  JSONL a 13 MB en Parquet comprimido.
- Todas las columnas se guardan como texto (`all_varchar`). Bronze no
  interpreta tipos: una fecha inválida llega a Silver tal como vino y ahí
  se decide si va a cuarentena.

**Particionado por fecha de ingesta, no por fecha del evento.** Bronze
registra cuándo llegó el dato. Particionar por fecha del evento obligaría
a interpretar la fecha en Bronze, y Transurbano trae 817 fechas del futuro
que crearían particiones de 2027.

**Idempotencia.** Cada archivo cargado se nombra con la huella SHA-256 de
su contenido (normalizando fin de línea). Si la huella ya existe en el
lake, la carga se omite. Correr el flujo N veces produce el mismo lake.

**Hash por fila.** `_hash_fila` se calcula sobre el contenido parseado,
nunca sobre la línea cruda: el mismo registro da el mismo hash en Windows
(CRLF) y en Linux o Mac (LF).

**Evidencia.** Bitácora de cargas en `lake/bronze/_control/bitacora_cargas.csv`:
primera corrida CARGADO, segunda OMITIDO, conteos idénticos.

## D-004 · Vía de ingesta de Transurbano
**Estado:** cerrada · **Responsable:** C

**Contexto.** El enunciado deja la vía de Transurbano a criterio del equipo.
Transurbano entrega `transurbano_transacciones.csv`, 832,791 transacciones del
periodo completo, con fecha y hora en columnas separadas, monto en centavos y
el estado del viaje como código numérico.

**Opciones.**
1. Streaming por Kafka, simulando la publicación del CSV línea por línea, como
   se hace con Transmetro y Aerómetro.
2. Batch, cargando el archivo completo con `cargar()`.

**Decisión.** Opción 2, batch.

**Por qué.** El archivo no trae marca de llegada por transacción ni orden
garantizado dentro del archivo: no hay nada en el dato que se comporte como un
flujo. Simularlo como evento agregaría un punto de falla (el broker) y un
componente que operar, sin agregar información. La vía se elige por cómo el
operador entrega el dato, no por la herramienta que se quiere lucir.

**Evidencia.** La carga es idempotente por el mismo mecanismo que MetroRiel: el
`lote_id` es la huella del contenido del archivo. La segunda corrida reporta
`OMITIDO` con `lote_id = 89057a42ddbc8e5f` y 832,791 filas, sin reescribir el
Parquet.

**Consecuencia asumida.** La latencia de Transurbano es la del archivo, no la
del evento: el tablero ve las transacciones cuando llega el corte, no cuando
ocurren. Si mañana el operador publicara eventos, cambia la vía de ingesta y no
cambia el contrato de Bronze ni nada aguas abajo.

---

## D-005 · Dueño del padrón del archivo CDC
**Estado:** cerrada · **Responsable:** A

**Contexto.** El enunciado lo llama padrón de Transmetro, pero la columna
`tarjeta` mezcla cuatro formatos: 22,326 eventos con llave de Transmetro,
5,223 de Transurbano, 1,295 de MetroRiel y 2,206 con el valor `SIN-TARJETA`.

**Decisión.** Es un padrón central de personas, no de un operador. Cada fila
se resuelve a `persona_id` por la misma regla de D-002.

**Evidencia.** La prueba de D-002 demuestra que la llave de cada evento es la
tarjeta principal de la persona, no una tarjeta de Transmetro.

**Tratamiento de `SIN-TARJETA`.** Los 2,206 eventos con ese valor colapsarían
en un solo registro. Van a cuarentena con motivo `llave_centinela`: no
identifican a ninguna persona.

**Consecuencia asumida.** El conteo de tarjetas activas y dadas de baja se
reporta sobre personas identificables, excluyendo la llave centinela.

---

## D-006 · Tratamiento de los códigos de estado 7 y 9 de Transurbano
**Estado:** cerrada · **Responsable:** C

**Contexto.** `cod_estado` toma los valores 1, 2 y 3 para validaciones
exitosas, 7 para saldo insuficiente y 9 para tarjeta inválida. D-001 ya
estableció que una transacción con estado 7 o 9 no es un abordaje exitoso y no
entra a `fct_abordaje`, y dejó abierto su destino. Son 41,390 transacciones,
el 5.0% de las que pasan las reglas de calidad.

**Opciones.**
1. Mandarlas a cuarentena con un motivo `estado_no_exitoso`.
2. Descartarlas al construir Silver.
3. Conservarlas en Silver como transacciones y excluirlas del modelo de
   abordajes.

**Decisión.** Opción 3.

**Por qué.** Una transacción rechazada por el validador es un hecho real y bien
formado del operador: sabemos exactamente qué pasó y por qué. La cuarentena es
para registros que no podemos interpretar. Mezclar las dos cosas rompe el
significado del reporte de calidad: la tasa de rechazo del validador pasaría a
leerse como tasa de error de datos, y `rpt_calidad` dejaría de medir calidad.
La opción 2 queda descartada de entrada porque viola la regla estructural de
que nada se descarta en silencio.

**Implementación.** `slv_tu_transacciones` conserva las 827,788 transacciones
bien formadas con su `cod_estado`, su lectura en texto `estado_validacion` y la
bandera `es_abordaje_exitoso`. `slv_tu_abordajes` filtra por esa bandera y deja
786,398 abordajes, que son los que entran a `fct_abordaje`.

**Evidencia.** 827,788 = 786,398 abordajes + 41,390 no exitosas. El test
`assert_conservacion_transurbano` verifica las dos igualdades: contra Bronze
(827,788 + 5,003 = 832,791) y contra el corte de abordajes.

**Consecuencia asumida.** `slv_tu_transacciones` y `slv_tu_abordajes` no tienen
el mismo conteo, y la diferencia hay que explicarla cada vez que se compare
Silver con Gold. `rpt_volumen_por_capa` la publica en la columna
`filas_no_promovidas_a_gold` justamente para que nadie la lea como una pérdida.
A cambio, la Agencia puede medir la tasa de rechazo por parada y por hora, que
se perdería si esas filas cayeran en cuarentena.

## D-007 · Estrategia de seudonimización antes de Gold
**Estado:** cerrada · **Responsable:** A

**Decisión.** Gold nunca contiene la tarjeta original ni la `persona_key`.
Contiene `persona_sk`: los primeros 16 caracteres del SHA-256 de una sal
secreta concatenada con la `persona_key` de Silver.

**Por qué con sal.** Sin sal, cualquiera puede calcular el hash de las 60,000
tarjetas posibles y revertirlo en segundos. Aerómetro entrega justamente un
hash sin sal de 12 caracteres, y se verificó que el 100% de sus 14,496 valores
se revierte con un diccionario. La sal convierte ese ataque en inviable.

**Dónde vive la sal.** En `.env`, que no se versiona. El repositorio solo
tiene `.env.example` con un valor de ejemplo. La macro `seudonimizar` detiene
la compilación de Gold si la sal falta o es la de ejemplo. El equipo comparte
la misma sal por un canal privado para que la misma persona tenga el mismo
`persona_sk` en todas las máquinas.

**Qué se preserva.** El tablero puede contar personas distintas y seguir a la
misma persona entre modos, sin saber qué tarjeta es.

**Límite.** Quien tenga la sal y Silver puede revertir la seudonimización.
El acceso a Silver y a la sal queda restringido según el documento de
seguridad (sección 3.3).

---

## D-008 · Definición de día hábil y hora pico
**Estado:** cerrada · **Responsable:** A

**Decisión.**
- Día hábil: lunes a viernes. No hay feriados nacionales considerados en el
  periodo 2026-06-01 a 2026-07-15.
- Hora pico mañana: 06:00 a 08:59. Hora pico tarde: 16:00 a 18:59. Solo en
  día hábil.

**Evidencia.** Distribución observada sobre 363,221 validaciones de
Transmetro: 06–08 concentra 26.0% y 16–18 concentra 23.5%. Las horas
contiguas caen a 2.0% (05) y 3.4% (19). Seis horas acumulan 49.5% de la
demanda.


---

## D-009 · Patrón de cuarentena
**Estado:** cerrada · **Responsable:** A

**Decisión.** Cada fuente tiene un modelo `<fuente>_evaluado` con todas las
filas de Bronze y una columna `motivo_rechazo_<proceso>` por cada proceso que
alimenta. Nula si la fila es válida para ese proceso; si no, la primera regla
que falla. Los modelos Silver limpios filtran `motivo_rechazo is null`. La
tabla `cuarentena` une los rechazados de todas las fuentes.

**Invariante.** Para cada fuente y proceso, filas de Bronze = filas de Silver
+ filas en cuarentena. Se verifica con un test de conservación por fuente;
si falla, un registro desapareció en silencio y el build se detiene.

**Cuarentena por proceso.** Un viaje de MetroRiel sin salida es un abordaje
válido y un trayecto inválido. Aparece en `slv_mr_abordajes` y en cuarentena
con proceso trayecto, nunca se pierde de ninguno de los dos.

**Fecha futura.** Un evento es futuro si su marca de tiempo es posterior a la
`_ingesta_ts` de su lote. La regla no depende de una fecha fija en el código.

**Resultado MetroRiel.** 299,100 en Bronze; 299,100 abordajes válidos;
295,511 trayectos válidos; 3,589 en cuarentena por `viaje_sin_salida`.

---

## D-010 · Aplicación del CDC y SCD Tipo 2 del padrón
**Estado:** cerrada · **Responsable:** A

**Contexto.** El log no empieza en un padrón vacío. De las 22,462 personas,
11,740 aparecen por primera vez con un UPDATE y 2,877 con un DELETE: el
padrón existía antes del log y nunca se entregó su foto inicial. Además,
hay UPDATE sobre tarjetas dadas de baja, DELETE repetidos, y 103 eventos
cuyo `commit_ts` es anterior al del evento previo de la misma persona.

**Decisiones.**
- **Orden.** Las operaciones se aplican por `seq`, como pide el enunciado.
  `commit_ts` no es monótono y no se usa para ordenar.
- **Persona preexistente.** Un UPDATE o DELETE sobre una llave nunca vista
  significa que la persona existía antes del log. El UPDATE la registra
  como activa; el DELETE, como inactiva sin atributos conocidos.
- **INSERT sobre una persona activa** reemplaza sus atributos.
- **UPDATE sobre una tarjeta dada de baja** va a cuarentena
  (`actualizacion_sobre_baja`): el log se contradice, y no se reactiva
  una tarjeta cancelada sin un INSERT explícito.
- **DELETE sobre una tarjeta ya dada de baja** va a cuarentena
  (`baja_repetida`).
- **Un DELETE nunca borra.** Cierra la versión vigente y abre una
  INACTIVA con los últimos atributos conocidos. El historial de viajes
  de esa persona se conserva.
- **SCD Tipo 2 desde el log, no con `dbt snapshot`.** El snapshot marca
  las versiones con la hora de ejecución de dbt: dos corridas darían dos
  historiales distintos y se rompería la idempotencia. Desde el log, el
  historial es siempre el mismo.
- **Vigencia.** `vigente_desde` es el máximo acumulado de `commit_ts` de
  la persona, para que las vigencias nunca retrocedan.

**Resultado.**

| Métrica | Valor |
|---|---|
| Eventos en el log | 31,050 |
| Altas aplicadas | 10,003 |
| Cambios aplicados | 14,646 |
| Bajas aplicadas | 3,633 |
| En cuarentena | 2,768 (llave_centinela 2,206; actualizacion_sobre_baja 423; baja_repetida 139) |
| Personas en el padrón | 22,462 |
| Activas antes de aplicar las bajas | 19,824 |
| Activas después de aplicar las bajas | 19,110 |
| Inactivas después | 3,352 |
| Versiones en el historial | 27,428 |

---

## D-011 · Dimensión de persona y foto diaria del padrón
**Estado:** cerrada · **Responsable:** A

**Dimensión de persona.** `dim_persona` tiene una fila por cada persona
conocida por la red: toda persona con al menos un abordaje en las fuentes
integradas, más toda persona del padrón aunque no haya viajado. Los
atributos del padrón (perfil, zona de residencia, estado) son los de la
versión vigente del SCD Tipo 2. Las personas que viajan pero no están en
el padrón quedan con estado `SIN_REGISTRO`. En Gold se publica solo con
`persona_sk`.

**Tercer hecho: `fct_estado_padron_diario`.** Grano: una persona del
padrón por día calendario, con la versión vigente al cierre del día. Una
persona aparece desde el día de su primer evento en el log. 559,718 filas
en 45 días.

**Por qué existe.** Es el único proceso del modelo con una medida
semi-aditiva real. `tarjetas_activas` se suma entre zonas y perfiles de un
mismo día, pero no entre días:

| Día | Tarjetas activas |
|---|---|
| 2026-06-01 | 539 |
| 2026-06-30 | 13,924 |
| 2026-07-15 | 19,110 |
| Suma de los 45 días (sin sentido) | 479,760 |

Entre días se reporta el valor del último día o el promedio. Un test
verifica que las activas del último día coinciden con el padrón vigente.

**Clasificación de medidas completa del modelo.**

| Medida | Hecho | Tipo |
|---|---|---|
| cantidad_abordajes, monto_q | fct_abordaje | aditiva |
| cantidad_trayectos, distancia_km, monto_q | fct_trayecto_od | aditiva |
| duracion_s | fct_trayecto_od | aditiva en suma; su promedio es no aditivo |
| tarjetas_activas, cantidad_personas | fct_estado_padron_diario | semi-aditiva |
| personas distintas, proporción en hora pico, duración promedio | derivadas | no aditivas |

---

## D-012 · Orquestación y demostración de idempotencia
**Estado:** cerrada · **Responsable:** A

**Orquestador.** Prefect, la opción recomendada del curso: corre sin
servidor dedicado y el flujo es código Python versionado. Un solo comando,
`python -m orquestacion.flujo`, corre todas las etapas en orden: catálogos,
MetroRiel, Transurbano, padrón CDC, productor y consumidor de Kafka,
`dbt build`, publicación de Gold y exportación del modelo.

**Etapas de otros roles.** Si el módulo de una etapa todavía no existe en
el repositorio, la etapa se registra como `OMITIDA` y el flujo continúa.
Cuando el rol correspondiente integra su código, la etapa se activa sola.

**Reintentos.** Las etapas de ingesta reintentan dos veces con 5 segundos
de espera. `dbt build` no reintenta: es determinista, y si falla, falla
por un error que hay que corregir.

**Bitácora de ejecución.** Cada etapa de cada corrida queda en
`lake/bronze/_control/ejecuciones.csv` con estado y duración. Es la fuente
de las métricas de rendimiento.

**Por qué el flujo es idempotente.** Cada etapa lo es por construcción:
las cargas a Bronze se identifican por la huella del contenido del archivo
y se omiten si ya existen; Silver y Gold se reconstruyen completos desde
Bronze; el SCD Tipo 2 se deriva del log y no de la hora de ejecución; y
ningún modelo usa la fecha actual.

**Demostración.** `python -m orquestacion.verificar_idempotencia` corre el
flujo dos veces seguidas y compara todas las tablas de todas las capas por
cantidad de filas y por una huella de contenido (XOR del hash de cada fila,
independiente del orden). Resultado en `docs/evidencias/idempotencia.md`.
El mismo comando se corre en vivo el día de la presentación.

---

## D-013 · Carga de los datos del Proyecto 2 desde cero
**Estado:** cerrada · **Responsable:** Miguel

**Contexto.** Los datos del Proyecto 2 (1 de junio al 29 de agosto de 2026)
reemplazan a los del Proyecto 1: mismos nueve archivos y columnas, otros
usuarios y otros hábitos. Si se cargan encima, Bronze, Kafka y el warehouse
mezclan las dos versiones sin avisar.

**Opciones.**
1. Vaciar a mano lake, warehouse y Kafka antes de cada carga y dejar Kafka como
   paso manual del README.
2. Que el flujo borre lo existente antes de cargar.
3. Vaciar fuera del flujo, con un procedimiento documentado, y que el flujo
   levante Kafka por su cuenta.

**Decisión.** Opción 3.

La opción 2 se descarta: un flujo que borra lo que ya cargó deja de ser
idempotente, y `verificar_idempotencia` perdería sentido. La opción 1 deja un
paso manual, que el enunciado pide eliminar.

Vaciar significa borrar `lake/bronze/`, `lake/staging/`, `warehouse/` y
`dbt/target/`, y bajar Kafka con `docker compose down -v`. Los mensajes viven
en el contenedor: sin bajarlo, el consumidor (`auto.offset.reset: earliest`)
releería los mensajes de la carga anterior y duplicaría Bronze. El proyecto no
usa snapshots, y los modelos incrementales de población y features (D-014) viven en el warehouse, que también se vacía, así que no hay más estado.

El flujo levanta Kafka como etapa propia (`docker compose up -d --wait`),
registrada en `ejecuciones.csv` con su duración.

**Evidencia.** Corrida desde entorno vacío: 12 etapas, 109.87 s, `dbt build`
con PASS=228 y ERROR=0, y 9 de 9 archivos con diferencia 0
(`docs/evidencias/conteos_bronze.md` y `docs/evidencias/tiempos_flujo.md`).

**Consecuencia asumida.** Quien carga datos nuevos debe vaciar el entorno
antes de correr el flujo (README, sección "Corrida desde cero"). Las filas
esperadas de `scripts/conteos_bronze.py` son las del LEEME de esta entrega: con
otro juego de datos, por ejemplo el de la prueba de invarianza, la tabla
mostrará diferencias que hay que explicar y no son un error del pipeline.

---

## D-014 · Cortes B y C dentro del comando único
**Estado:** cerrada · **Responsable:** Miguel

**Contexto.** La población y las features reciben la fecha de corte como
parámetro (`fecha_corte`, por defecto 2026-07-01). El `dbt build` del flujo solo
calculaba el corte A: `features.features_corte` quedaba con 59,515 filas y los
cortes B y C dependían de correr `features/calcular.py` a mano, así que el
comando único no dejaba la tabla con los tres cortes.

**Opciones.**
1. Dejar B y C como paso manual con `features/calcular.py`.
2. Cambiar el valor por defecto de `fecha_corte` para calcular los tres cortes
   en un solo build.
3. Agregar al flujo una etapa que corra `poblacion` y `features_corte` para B y
   C justo después del `dbt build`.

**Decisión.** Opción 3.

La opción 1 deja un paso manual, que el enunciado pide eliminar. La opción 2
mezcla la lógica de tres cortes en un parámetro pensado para uno solo. La etapa
`features_cortes` invoca dbt como módulo de Python, igual que `dbt_build`, y
evita la dependencia de PowerShell de `calcular.py`. Los modelos son
incrementales con llave `(unidad_id, fecha_corte)`: repetir la etapa no duplica
filas.

**Evidencia.** Corrida desde entorno vacío: 12 etapas, 109.87 s, `dbt build`
con PASS=228 y ERROR=0, y 9 de 9 archivos con diferencia 0. `features_corte` y
`poblacion` quedan con 175,354 filas (cortes A, B y C). La prueba de
idempotencia da IDEMPOTENTE con 19,537,396 filas en las dos corridas
(`docs/evidencias/idempotencia.md`).

**Consecuencia asumida.** Como estos modelos son incrementales, su estado vive
en el warehouse: al cargar datos nuevos hay que vaciarlo junto con el lake
(README, sección "Corrida desde cero").

## D-015: Ampliación a 10 features predictivas para modelo de churn
- **Fecha:** 2026-11-02
- **Autor:** Diego de Jesús Urbina Chávez (Rol 2)
- **Decisión:** Se amplió la tabla `features_corte` de 5 a 10 variables predictivas (`viajes_7d`, `dias_activos_28d`, `gasto_promedio_viaje_q`, `proporcion_hora_pico_28d`, `tendencia_viajes_14d`) y se creó la tabla `features.unidad_tarjetas`.
- **Justificación:** Satisfacer el requerimiento de rúbrica de la sección 2.1 (top 10 importancias) y proveer mayor capacidad predictiva temporal y de comportamiento sin incurrir en fuga de datos (validado con 0 diferencias en prueba de recorte).

## D-016 · Ensayo de invarianza del corte B (prueba de recorte)
**Estado:** cerrada
**Fecha:** 2026-11-03 · **Commit:** 831f1336d7768447b0c75ac4c6dae7dd8a714cc7

**Contexto.** El corte B (2026-07-31) solo necesita datos hasta el 30 de
julio. Si el pipeline usara información posterior a esa fecha, el score del
churn estaría contaminado con datos del futuro. Se construyó
`scripts/recortar_datos.py` para generar una copia de `datos_red` truncada
al 30 de julio, respetando el formato y la zona horaria de cada uno de los
nueve archivos.

**Procedimiento.** Se corrió el flujo completo dos veces desde un entorno
vacío: una con `datos_red` completo (salida `salidas/B_completo.csv`) y
otra con la copia recortada (salida `salidas/B_recortado.csv`), prediciendo
el corte B en ambos casos con el mismo `modelos/modelo_churn_v1.joblib`.

**Resultado.**
| Comparación | Filas | Diferencias |
|---|---|---|
| `unidad_id` (conjunto) | 58,128 | 0 |
| `puntaje` | 58,128 | 0 |
| `contactar` | 58,128 | 0 |
| `tarjetas` | 58,128 | 2,642 |

El score del modelo (`puntaje`) y la decisión de contacto (`contactar`) son
idénticos fila por fila entre las dos corridas: las diez variables de
`features.features_corte` no tienen fuga de datos futuros.

La columna `tarjetas`, que viene de `features.unidad_tarjetas` y se adjunta
al CSV solo como dato informativo (no entra a `predict_proba`), sí difiere
en 2,642 filas. Esa tabla no está acotada por `fecha_corte`: cuenta tarjetas
vistas en todo el histórico cargado en el warehouse, así que con datos
completos ve tarjetas usadas después del 31 de julio.

**Evidencia.** `sha256sum salidas/B_completo.csv salidas/B_recortado.csv`
da hashes distintos (`d8c677b6...` vs `d33438fd...`) por la columna
`tarjetas`; comparando columna por columna con pandas, `puntaje` y
`contactar` dan 0 diferencias en las 58,128 filas.

**Consecuencia asumida.** El churn model queda validado contra fuga de
datos. `unidad_tarjetas` sí tiene fuga de información futura y contradice
la validación de D-015 ("0 diferencias en prueba de recorte"); se le avisa
a Diego con esta evidencia para que la acote a `fecha_corte`. Mientras no
se corrija, el campo `tarjetas` de las predicciones no debe usarse para
decisiones basadas en el estado del corte, solo `puntaje` y `contactar`.

## D-017: Corrección de fuga en features.unidad_tarjetas por fecha de corte
- **Fecha:** 2026-11-03
- **Autor:** Diego de Jesús Urbina Chávez (Rol 2)
- **Decisión:** Se modificó `features.unidad_tarjetas` para que sea incremental por `(unidad_id, fecha_corte)` y filtre estrictamente `abordaje_ts < fecha_corte`.
- **Justificación:** Corregir la fuga temporal detectada en D-016 donde 2,642 registros del Corte B incluían tarjetas observadas en agosto. Con este cambio, la prueba de invarianza y recorte es determinista y libre de fuga futura.


---

## D-018 · Selección del ensemble con diez variables

**Fecha:** 2026-11-08

**Responsable:** Adrián

**Estado:** decisión de modelado registrada; pendiente de confirmación
de Eduardo y Miguel para coordinar umbral y producción.

**Contexto.** Después de ampliar el contrato a diez variables, se
repitieron los baselines, las logísticas regularizadas y el ensemble
sobre el corte A (2026-07-01), con las mismas 59,515 unidades,
cinco folds estratificados y semilla 42. La selección utiliza
Average Precision de validación.

**Opciones.**

1. Baseline de tasa: AP de validación 0.119264.
2. Baseline de ranking: AP de validación 0.389760.
3. Logística L1 con lambda=100 y C=0.01: AP de validación 0.407921.
4. Logística L2 con lambda=100 y C=0.01: AP de validación 0.406560.
5. Ensemble HistGradientBoostingClassifier: AP de validación 0.428920.

**Decisión.** Se selecciona el ensemble con las diez variables del
contrato v2. Se conserva la configuración evaluada, sin modificar
hiperparámetros después de observar estos resultados.

**Justificación.** El ensemble supera a la mejor logística en los cinco
folds, con una mejora media de 0.021000 de AP. Su desviación entre folds
es 0.002403, frente a 0.004148 de L1. El entrenamiento acumulado de los
cinco folds requirió 2.152028 segundos, frente a 0.607734 de L1.
Se considera que la mejora predictiva justifica el costo adicional
en el equipo utilizado.

**Consecuencias y límites.** Se acepta una mayor brecha entre
entrenamiento y validación: 0.040822 para el ensemble frente a
-0.000108 para L1, y menor facilidad de interpretación.
La ventaja observada no demuestra significancia estadística ni
garantiza mayor ganancia económica. El mejor lambda de las logísticas
está en el extremo superior de la grilla; la comparación se limita
a las configuraciones evaluadas.

**Contrato de entrega.**

- Variables: `VARIABLES` en `scripts/modelos/variables.py`.
- Constructor: `construir_pipeline()` en `scripts/modelos/ensemble.py`,
  sin argumentos.
- Predicciones de A: `scripts/modelos/predicciones_cv.csv`.
- Configuración: `scripts/modelos/configuracion_ensemble.json`.

**Evidencia.** La verificación local confirmó 238,060 predicciones,
cuatro modelos, las mismas unidades y folds, ausencia de nulos y
duplicados, puntajes finitos entre 0 y 1 y únicamente la fecha
2026-07-01. Las medias y desviaciones de AP recalculadas desde las
predicciones coinciden con las tablas publicadas. Se entregan diez
importancias por permutación en validación, con 500 mediciones.

Documentación: `docs/metricas_fase1.md`,
`docs/metricas_fase2_ensemble.md` y `docs/decision_modelo.md`.

**Coordinación para producción.** Eduardo debe recalcular y congelar
el umbral usando las nuevas predicciones fuera de fold de A.
El umbral anterior de 0.33 no se traslada automáticamente.
Mauricio debe preparar el modelo final con todo A, las diez variables
y la configuración seleccionada.



Las confirmaciones se registrarán con su fecha real. Antes de la
evaluación única en B deben quedar congelados y versionados el modelo
seleccionado y el umbral. Esta entrada no certifica si B fue evaluado
previamente en otro equipo; ese estado debe comprobarse entre los
responsables antes de ejecutarlo.

---

## D-019 · Umbral de contacto recalculado con el ensemble de diez variables

**Fecha:** 2026-11-08

**Responsable:** Eduardo

**Estado:** cerrada; umbral congelado antes de la evaluación única en B.

**Contexto.** Con D-018 cambiaron las probabilidades fuera de fold del
corte A, así que el umbral de 0.33 de la versión de cinco variables no se
trasladó. Se volvió a correr
`python -m scripts.modelos.umbral --modelo ensemble --corte-eval A` sobre
el `predicciones_cv.csv` nuevo (59,515 unidades, 7,098 positivos). El
corte B no participa.

**Opciones.**

1. Umbral teórico 1/3, que solo vale si el modelo está calibrado.
2. Umbral de máxima ganancia esperada (Σ 15p − 5): 0.33, Q11,728.60.
3. Umbral de máxima ganancia observada (15 × VP − 5 × contactados): 0.31.

**Decisión.** Umbral 0.31 con el ensemble, por la regla declarada desde
la primera versión: máxima ganancia observada, que no depende de la
calibración.

**Resultado en A.** 6,653 contactados, 2,985 verdaderos positivos,
precisión 0.4487, recall 0.4205 y ganancia 15 × 2,985 − 5 × 6,653 =
Q11,510. Contactar a todos da −Q191,105 y no contactar a nadie Q0. Los
cinco folds dan ganancia positiva, de Q2,210 a Q2,400.

**Consecuencias.** La cima de la curva es plana: 0.31, 0.32 y 0.33 se
separan por Q20, así que la decisión es robusta a la opción elegida. Se
contacta a 964 personas más que con la versión anterior. El umbral queda
en `docs/umbral/umbral_elegido.json`; este commit es el congelamiento y
B se evalúa sobre él sin cambiar modelo ni umbral.

Documentación: `docs/metricas_umbral.md`.
