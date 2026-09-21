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
**Estado:** pendiente · **Responsable:** C

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
**Estado:** pendiente · **Responsable:** C

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