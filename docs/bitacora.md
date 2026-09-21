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
**Estado:** pendiente · **Responsable:** A

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
**Estado:** pendiente · **Responsable:** A

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