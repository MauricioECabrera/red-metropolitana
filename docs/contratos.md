# Contratos del equipo - Proyecto 2

Proyecto 2 - Ciencia de Datos - Red Metropolitana

Este documento fija lo que todos programan contra. Los nombres y tipos de abajo
no cambian sin avisar al equipo el mismo dia que se decide.

## Cortes

| Corte | Fecha | Uso |
|---|---|---|
| A | 2026-07-01 | Entrenamiento y validacion cruzada |
| B | 2026-07-31 | Prueba de un solo uso. Su etiqueta no se usa para entrenar ni ajustar nada |
| C | 2026-08-30 | Produccion. La etiqueta no existe (NULL) |

Ventana de features: maximo 28 dias antes del corte. Ventana de la etiqueta: 30 dias desde el corte.
Ninguna feature se calcula con datos posteriores a la fecha de corte de esa fila.

## Poblacion y unidad

Entran a un corte las unidades con al menos 2 abordajes validos (en cualquier operador)
en los 28 dias antes del corte, y sin un DELETE de CDC aplicado antes del corte.
La unidad (persona o tarjeta) la decide quien tiene la seccion 1.2, con el mismo criterio
de identidad del Proyecto 1 (persona_key / dim_persona).

## Etiqueta

1 si la unidad no tiene ningun abordaje valido, en ningun operador, en los 30 dias que
empiezan en el corte. 0 en otro caso. Dejar de viajar no es darse de baja en el CDC del
padron: la etiqueta se calcula solo con abordajes.

## Folds fijos

StratifiedKFold(n_splits=5, shuffle=True, random_state=42), solo sobre el corte A.
Todos los modelos usan exactamente los mismos folds y la misma metrica.

## Contrato 1: tabla de features

Esquema `features`. La publica quien tiene la seccion 1.3. Una fila por (unidad_id, fecha_corte).

| Columna | Tipo | Definición y Ventana | Origen Silver |
| :--- | :--- | :--- | :--- |
| `unidad_id` | VARCHAR | Llave única de la persona (`persona_key`) | Múltiples |
| `fecha_corte` | DATE | Fecha de análisis del corte | Múltiples |
| `viajes_28d` | INTEGER | Abordajes válidos en la ventana (28 días) | Abordajes unificados |
| `dias_desde_ultimo_viaje` | INTEGER | Días desde el último viaje al corte (28 días) | Abordajes unificados |
| `gasto_28d_q` | DECIMAL | Suma de montos gastados en quetzales (28 días) | Abordajes unificados |
| `operadores_distintos_28d` | INTEGER | Modos de transporte distintos usados (28 días) | Abordajes unificados |
| `abordajes_fin_semana_28d` | INTEGER | Abordajes realizados en domingo o sábado (28 días) | Abordajes unificados |
| `etiqueta` | INTEGER | 1 si abandonó, 0 si continuó. (Null en Corte C). | Abordajes unificados |

Puede crecer con mas columnas. Estas no cambian de nombre ni de tipo.

## Contrato 2: predicciones de validacion cruzada

Archivo `predicciones_cv.csv`. Lo publica quien tiene 1.4/2.1 y lo consume quien tiene 2.2.

| Columna | Contenido |
|---|---|
| unidad_id | igual que en la tabla de features |
| fecha_corte | siempre el corte A |
| modelo | baseline_tasa, baseline_ranking, logistica o ensemble |
| prob | probabilidad de baja en [0, 1] |

Una fila por unidad del corte A, en su fold de validacion, por cada modelo.

## Escenario de costo

Contactar a un usuario cuesta Q5. Si el usuario se iba a ir, la campana lo retiene en el 25%
de los casos. Un usuario retenido vale Q60. Es fijo para todo el curso.

## Reglas que no se rompen

1. Gold nunca lee Bronze. Siempre pasa por Silver.
2. Features nunca lee Gold. Siempre pasa por Silver.
3. Ningun registro se descarta en silencio: todo invalido va a cuarentena con un motivo.
4. El flujo completo es idempotente: correrlo dos veces da los mismos conteos.
5. Todo dbt se ejecuta con el wrapper del proyecto, nunca con dbt directo.
6. Ni credenciales ni la sal de seudonimizacion en el repositorio.
7. No se entrena ni se ajusta nada con la etiqueta del corte B.
8. No se calcula ninguna feature con datos posteriores a la fecha de corte de esa fila.

## Como correr todo

    python -m orquestacion.flujo

Requiere el entorno virtual activo, `.env` con la misma sal que el resto del equipo,
Docker Desktop abierto y los nueve archivos de datos en `datos_red/`.