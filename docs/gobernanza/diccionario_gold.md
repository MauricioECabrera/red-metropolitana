# Diccionario de campos Gold

Cada fila indica qué significa el campo publicado, de dónde procede y qué
transformación recibe. «Silver» identifica el modelo inmediatamente anterior;
los archivos y catálogos originales se indican cuando ayudan a rastrear el dato.
Las seis dimensiones son conformadas y pueden compartirse entre hechos.

## `gold.dim_fecha`

Fuente: `silver.dim_fecha`, calendario generado para 2026–2027. Gold copia
sus campos sin transformación adicional.

| Campo | Significado | Fuente y transformación |
|---|---|---|
| `fecha_key` | Llave de fecha AAAAMMDD. | Fecha generada; formato `%Y%m%d` convertido a entero. |
| `fecha` | Día calendario. | Serie diaria generada. |
| `anio` | Año. | `year(fecha)`. |
| `mes` | Mes numérico. | `month(fecha)`. |
| `nombre_mes` | Nombre del mes en español. | Correspondencia del número de mes. |
| `dia` | Día del mes. | `day(fecha)`. |
| `dia_semana_num` | Día ISO: lunes 1 a domingo 7. | `isodow(fecha)`. |
| `nombre_dia` | Nombre del día en español. | Correspondencia de `isodow(fecha)`. |
| `semana_iso` | Semana del año. | `weekofyear(fecha)`. |
| `es_dia_habil` | Lunes a viernes. | `isodow(fecha) <= 5`; no considera feriados. |
| `es_fin_de_semana` | Sábado o domingo. | `isodow(fecha) >= 6`. |

## `gold.dim_hora`

Fuente: `silver.dim_hora`, horas generadas de 0 a 23. Gold copia sus campos.

| Campo | Significado | Fuente y transformación |
|---|---|---|
| `hora_key` | Hora local de 0 a 23; llave de la dimensión. | Serie generada `range(0, 24)` convertida a entero. |
| `hora_etiqueta` | Hora presentada como `HH:00`. | Hora rellenada a dos dígitos. |
| `franja_horaria` | Pico mañana, pico tarde, valle o extremo. | Clasificación: 06–08, 16–18, 09–15 o resto. |
| `es_franja_pico` | Hora incluida en alguna franja pico. | Verdadero para 06–08 y 16–18; no evalúa si el día es hábil. |

## `gold.dim_modo`

Fuente: `silver.dim_modo`, catálogo definido en el modelo SQL. Gold copia
sus campos.

| Campo | Significado | Fuente y transformación |
|---|---|---|
| `modo_key` | Llave entera del operador. | Valores 1–4 convertidos a entero. |
| `modo_codigo` | Código TM, TU, MR o AM. | Catálogo definido en SQL. |
| `modo_nombre` | Nombre legible del operador. | Catálogo definido en SQL. |
| `unidad_registro` | Unidad del archivo original: abordaje o trayecto. | Catálogo definido en SQL; no cambia el grano de `fct_abordaje`. |
| `formato_origen` | CSV o JSON Lines de la fuente. | Catálogo definido en SQL. |

## `gold.dim_zona`

Fuente: `silver.dim_zona`; combina `seed_dim_zona` con puntos de
`silver.dim_estacion_parada`. Gold copia sus campos.

| Campo | Significado | Fuente y transformación |
|---|---|---|
| `zona_key` | Llave estable de zona. | `seed_dim_zona.zona_key`. |
| `zona_nombre` | Nombre normalizado de zona. | `seed_dim_zona.zona_nombre`. |
| `tipo_division` | Clase de división territorial. | `seed_dim_zona.tipo_division`. |
| `municipio` | Municipio asociado. | `seed_dim_zona.municipio`. |
| `puntos_de_abordaje` | Puntos catalogados en la zona. | Conteo de `dim_estacion_parada` por zona; cero si no hay. |
| `modos_con_servicio` | Cantidad de modos con puntos catalogados. | Conteo distinto de `modo_codigo` por zona; cero si no hay. |
| `modos_lista` | Códigos de los modos presentes. | Concatenación ordenada de códigos distintos; «Sin servicio» si no hay. |
| `tiene_servicio` | Indica al menos un modo con punto catalogado. | `modos_con_servicio > 0`; no mide frecuencia ni disponibilidad real. |

## `gold.dim_estacion`

Fuente: `silver.dim_estacion_parada`, que unifica los cuatro catálogos de
estaciones, paradas y torres. Gold omite `zona_origen` y `lote_origen`.

| Campo | Significado | Fuente y transformación |
|---|---|---|
| `estacion_key` | Llave única del punto entre operadores. | Concatenación de `modo_codigo`, dos puntos y `codigo_origen`. |
| `modo_key` | Llave del modo al que pertenece. | Unión por `modo_codigo` con `silver.dim_modo`. |
| `modo_codigo` | Código TM, TU, MR o AM. | Asignado según catálogo de origen. |
| `codigo_origen` | Identificador del punto en su operador. | `estacion_id`, `cod_parada`, `id_estacion` o `station_code`. |
| `nombre_punto` | Nombre o descripción del punto. | `nombre`, `descripcion`, `nombre_estacion` o `station_name`. |
| `linea_ruta` | Línea, ruta o eje del punto. | `linea`, `ruta`, constante «MetroRiel» o `axis`. |
| `zona_key` | Zona conformada del punto. | Texto de zona del catálogo normalizado mediante `seed_zona_alias`. |
| `latitud` | Coordenada norte-sur, cuando existe. | TM: `lat` convertida a número; otros modos: nulo. |
| `longitud` | Coordenada este-oeste, cuando existe. | TM: `lon` convertida a número; otros modos: nulo. |
| `km_trazado` | Posición kilométrica de MetroRiel. | MR: `km` convertido a número; otros modos: nulo. |

## `gold.dim_persona`

Fuente: `silver.dim_persona`, formada por identidades con abordajes y personas
del padrón CDC. Los atributos administrativos corresponden a la versión
vigente del historial SCD Tipo 2. Gold no publica la tarjeta ni `persona_key`.

| Campo | Significado | Fuente y transformación |
|---|---|---|
| `persona_sk` | Identificador seudonimizado estable de persona. | Macro `seudonimizar(persona_key)`: SHA-256 con sal secreta, truncado a 16 caracteres. |
| `tipo_identidad` | Identidad vinculada o conocida solo por Aerómetro. | Prefijo `AM:` en `persona_key` produce `solo_aerometro`; demás, `vinculada`. |
| `en_padron` | Indica aparición en el padrón CDC. | Existe una versión vigente SCD2 para esa `persona_key`. |
| `estado_padron` | Estado administrativo vigente. | Estado SCD2; `SIN_REGISTRO` si no está en el padrón. |
| `perfil_vigente` | Perfil administrativo vigente. | `perfil` de la versión vigente SCD2; puede ser nulo. |
| `zona_residencia_key` | Zona de residencia vigente. | Versión vigente SCD2; puede ser nula. |
| `formato_llave_padron` | Formato TM, TU o MR de la llave del padrón. | `formato_llave_origen` de SCD2; puede ser nulo. |
| `versiones_padron` | Número de versión vigente del historial. | `version` de SCD2; puede ser nulo fuera del padrón. |

## `gold.fct_abordaje`

Grano: una validación exitosa de entrada por fila. Fuente: unión de los
modelos Silver de abordajes de TM, TU, MR y AM. Los rechazos de validación
de Transurbano no entran. Una entrada de MetroRiel sin salida sí entra.

| Campo | Significado | Fuente y transformación |
|---|---|---|
| `abordaje_id` | Identificador único del abordaje. | ID de Silver con prefijo del operador; conserva trazabilidad. |
| `persona_sk` | Persona seudonimizada. | Macro `seudonimizar(persona_key)` sobre la llave Silver. |
| `modo_key` | Modo que registró la entrada. | `modo_codigo` Silver unido con `silver.dim_modo`. |
| `estacion_key` | Punto donde se abordó. | Llave del punto normalizada en Silver. |
| `zona_key` | Zona del punto de abordaje. | Resuelta en Silver con alias de zona; no es destino. |
| `fecha_key` | Fecha local de la entrada. | Llave de fecha normalizada en Silver. |
| `hora_key` | Hora local de la entrada. | Llave de hora normalizada en Silver. |
| `tipo_abordaje` | ENTRADA o TRANSBORDO según operador. | Atributo recibido de Silver; un transbordo cuenta como abordaje. |
| `es_hora_pico` | Entrada en día hábil y hora pico. | `dim_fecha.es_dia_habil AND dim_hora.es_franja_pico`. |
| `cantidad_abordajes` | Medida para sumar entradas exitosas. | Constante 1 por fila Gold. |
| `monto_q` | Cobro en quetzales. | Monto normalizado en Silver; TU convierte centavos a quetzales. |

## `gold.fct_trayecto_od`

Grano: un trayecto MetroRiel con entrada y salida válidas por fila. Fuente:
`silver.slv_mr_trayectos`. Los trayectos sin salida no aparecen aquí.

| Campo | Significado | Fuente y transformación |
|---|---|---|
| `trayecto_id` | Identificador único del trayecto. | ID normalizado de Silver, prefijo MR. |
| `persona_sk` | Persona seudonimizada. | Macro `seudonimizar(persona_key)` sobre Silver. |
| `estacion_origen_key` | Estación de entrada. | Llave normalizada en Silver; rol origen de `dim_estacion`. |
| `estacion_destino_key` | Estación de salida. | Llave normalizada en Silver; rol destino de `dim_estacion`. |
| `zona_origen_key` | Zona de la estación de entrada. | Resuelta en Silver; rol origen de `dim_zona`. |
| `zona_destino_key` | Zona de la estación de salida. | Resuelta en Silver; rol destino de `dim_zona`. |
| `fecha_key` | Fecha local de la entrada. | Llave de fecha de Silver. |
| `hora_key` | Hora local de la entrada. | Llave de hora de Silver. |
| `es_hora_pico` | Entrada en día hábil y hora pico. | `dim_fecha.es_dia_habil AND dim_hora.es_franja_pico`. |
| `cantidad_trayectos` | Medida para contar trayectos completos. | Constante 1 por fila Gold. |
| `duracion_s` | Tiempo entre entrada y salida, en segundos. | Calculado en Silver a partir de ambas marcas de tiempo. |
| `distancia_km` | Distancia del trayecto sobre el trazado. | Calculada en Silver a partir del kilometraje de las estaciones. |
| `monto_q` | Tarifa del trayecto en quetzales. | Tarifa normalizada en Silver; es el mismo cobro de su abordaje. |

## `gold.fct_estado_padron_diario`

Grano: una persona del padrón por día, según su versión SCD2 al cierre.
Fuente: `silver.slv_padron_scd2` unido al calendario `silver.dim_fecha`.
Una persona aparece desde su primer evento disponible del log.

| Campo | Significado | Fuente y transformación |
|---|---|---|
| `fecha_key` | Día de la fotografía del padrón. | `dim_fecha.fecha_key` para cada día del período CDC. |
| `persona_sk` | Persona seudonimizada. | Macro `seudonimizar(persona_key)` de SCD2. |
| `zona_residencia_key` | Zona vigente al cierre del día. | Versión SCD2 seleccionada para ese cierre. |
| `perfil` | Perfil vigente al cierre del día. | Versión SCD2 seleccionada para ese cierre. |
| `estado` | ACTIVA o INACTIVA al cierre del día. | Versión SCD2 seleccionada para ese cierre. |
| `cantidad_personas` | Medida de personas en la foto de ese día. | Constante 1 por fila; no sumar entre días. |
| `tarjetas_activas` | Tarjetas activas al cierre de ese día. | 1 si `estado = 'ACTIVA'`; de lo contrario 0. No sumar entre días. |

## Reglas para interpretar las medidas

- No sumar `monto_q` de abordajes y trayectos: el cobro MetroRiel aparece
  en ambos hechos.
- No sumar `tarjetas_activas` ni `cantidad_personas` a través de fechas:
  seleccionar el día de corte o calcular un promedio explícito.
- `COUNT(DISTINCT persona_sk)` no se obtiene sumando conteos de zonas o modos.
- Los 295,511 trayectos completos MetroRiel están representados también por
  su entrada dentro de los 1,651,158 abordajes de la red.
