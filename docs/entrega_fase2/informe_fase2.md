# Informe de la Fase 2 — Churn de la Red Metropolitana de Transporte

Universidad Rafael Landívar · Ciencia de Datos · Segundo Semestre 2026
Proyecto 2 · Agencia Metropolitana de Transporte
Repositorio: https://github.com/MauricioECabrera/red-metropolitana · etiqueta `fase-2`
Equipo: Miguel Cabrera (integración y producción), Diego Urbina (etiqueta, población y
features), Adrián (modelos), Eduardo Hernández (umbral, test B y segmentación)

## 1. El problema

Con lo que la Agencia sabe de un usuario hasta la fecha de corte, ¿qué tan probable es que
deje de usar la red en los próximos 30 días? Y con esa probabilidad, ¿a quién conviene
contactar con la campaña de retención, que no alcanza para todos?

Es un problema de clasificación binaria por unidad y fecha de corte: todo lo que el modelo
ve es anterior al corte, y la etiqueta se calcula solo con datos desde el corte en adelante.
Los datos son simulados, igual que en el Proyecto 1, con el mismo periodo de 90 días
(1 de junio al 29 de agosto de 2026) usado en los tres cortes del proyecto.

- **Unidad:** la Persona (`persona_key`), para modelar el abandono real de la red integrada
  y no confundir con abandono a quien solo cambia de tarjeta. Definición completa y costo de
  esta elección en `docs/etiqueta_y_features.md`.
- **Etiqueta:** positivo (1) si la persona no tiene ningún abordaje válido en los 30 días
  que empiezan en la fecha de corte; negativo (0) en otro caso.
- **Población por corte:**

| Corte | Fecha | Población | Positivos | Tasa positiva |
|---|---|---:|---:|---:|
| A (entrenamiento) | 2026-07-01 | 59,515 | 7,098 | 0.1193 |
| B (test único) | 2026-07-31 | 58,128 | 6,383 | 0.1098 |
| C (producción) | 2026-08-30 | 57,711 | — | Etiqueta oculta |

## 2. Sección 2.1 — Ensemble y sesgo-varianza

Se entrenó un ensemble `HistGradientBoostingClassifier` con las mismas diez variables y los
mismos cinco folds de validación cruzada estratificada usados por las líneas base y la
logística de la Fase 1, para que la comparación sea justa.

| Modelo | AP validación | DE | AP entrenamiento | Brecha | Entrenamiento 5 folds (s) |
|---|---:|---:|---:|---:|---:|
| Baseline tasa constante | 0.1193 | 0.00005 | 0.1193 | 0.0000 | — |
| Baseline ranking | 0.3898 | 0.0036 | 0.3893 | −0.0004 | — |
| Logística L1 (λ=100) | 0.4079 | 0.0041 | 0.4078 | −0.0001 | 0.61 |
| Logística L2 | 0.4066 | 0.0042 | 0.4071 | 0.0006 | — |
| **Ensemble (elegido)** | **0.4289** | **0.0024** | **0.4697** | **0.0408** | **2.15** |

El ensemble supera a la mejor logística (L1, λ=100) en los cinco folds, con diferencias de
0.0149 a 0.0260 de AP, y a la línea base de ranking en 0.0392.

**Sesgo y varianza por modelo:**
- *Baseline tasa:* sin brecha, pero sin capacidad: usa solo la tasa global.
- *Baseline ranking:* brecha −0.0004, equilibrado pero limitado por depender de una sola
  variable con regla fija.
- *Logística L1:* brecha −0.0001, equilibrada; su techo es la estructura lineal regularizada.
- *Logística L2:* brecha 0.0006, también equilibrada, con menor AP que L1.
- *Ensemble:* brecha 0.0408 (AP entrenamiento 0.4697 vs. validación 0.4289), el de mayor
  varianza del grupo — es decir, el que más se ajusta a su propio entrenamiento — pero aun
  así el de mejor AP de validación, por lo que se acepta el sobreajuste relativo a cambio de
  la mejora.

**Diez importancias por permutación** (calculadas sobre la validación de cada fold, no sobre
entrenamiento; caída media de Average Precision):

| Variable | Caída media de AP |
|---|---:|
| dias_desde_ultimo_viaje | 0.2577 |
| tendencia_viajes_14d | 0.0221 |
| gasto_28d_q | 0.0089 |
| dias_activos_28d | 0.0076 |
| viajes_28d | 0.0059 |
| viajes_7d | 0.0041 |
| gasto_promedio_viaje_q | 0.0037 |
| abordajes_fin_semana_28d | 0.0022 |
| proporcion_hora_pico_28d | 0.0019 |
| operadores_distintos_28d | 0.0002 |

La recencia (días desde el último viaje) domina por mucho al resto; la tendencia de viajes
entre quincenas aparece en segundo lugar.

**Decisión:** se lleva el ensemble a producción. La mejora de +0.021 de AP sobre la mejor
logística, consistente en los cinco folds, justifica su mayor complejidad y menor
interpretabilidad; se compensa la falta de coeficientes con signo con las importancias por
permutación. Detalle completo en `docs/decision_modelo.md` y `docs/metricas_fase2_ensemble.md`.

## 3. Sección 2.2 — Umbral según costo y test único

**Escenario de costos** (fijo para todos los grupos): contactar cuesta Q5; si el usuario se
iba a ir, la campaña lo retiene el 25 % de las veces; un usuario retenido vale Q60.

Ganancia esperada por contacto: `E[G] = 15p − 5`. Conviene contactar cuando `p > 1/3 ≈ 0.3333`
(el umbral teórico del punto de equilibrio).

El umbral de producción no es ese 1/3 teórico, sino **0.31**: el que maximiza la ganancia
**observada** (no la esperada) sobre las predicciones fuera de fold del corte A, con las
etiquetas reales. Se prefiere así porque no depende de que el modelo esté bien calibrado. La
diferencia con el máximo de ganancia esperada (umbral 0.33, Q11,728.60) es de solo Q220 sobre
Q11,510 observados en 0.31 — las dos curvas casi se superponen, señal de que el modelo está
razonablemente calibrado en A. Con la versión de cinco variables de la Fase 1 el umbral había
sido 0.33; al recalcularlo con el ensemble de diez variables bajó a 0.31, con Q220 más de
ganancia y 964 contactos más. Derivación completa y curva de ganancia en
`docs/metricas_umbral.md`.

**Evaluación única en el corte B** (commit `2ba297c903766f792e1aea29d872f2a8c2974d24`,
2026-11-08 12:25:50 — registrada una sola vez; el script se niega a correr de nuevo si el
registro ya existe):

| Dato | Validación cruzada en A | Test en B |
|---|---:|---:|
| Average Precision | 0.4276 | 0.3712 |
| Contactados con umbral 0.31 | 6,653 | 6,602 |
| Precisión en el umbral | 0.4487 | 0.4055 |
| Recall en el umbral | 0.4205 | 0.4194 |
| Ganancia observada | Q11,510 | Q7,145 |

La política sigue siendo rentable en B (Q7,145 contra −Q194,895 de contactar a todos y Q0 de
no contactar a nadie), pero la ganancia cae. El recall casi no cambia; lo que baja es la
precisión. Se revisaron tres hipótesis: distribución distinta entre cortes (explica una
parte: la tasa positiva bajó de 0.1193 a 0.1098), varianza de muestra (insuficiente: la caída
observada está unas 23 desviaciones estándar por debajo de los folds de A) y desfase temporal
de calibración (causa principal: entre los contactados de mayor riesgo, p > 0.5, el modelo
predijo en promedio 0.6100 en B pero solo abandonó el 0.5034, mientras que en A ambas cifras
estaban cerca). El umbral se aplicó tal como estaba congelado y no se ajustó después de ver
B. Diagnóstico completo en `docs/test_b.md`.

## 4. Sección 2.3 — Segmentación con KMeans y PCA

Se aplicó KMeans sobre las diez features del corte A, escaladas con `StandardScaler`; la
etiqueta no participa en el ajuste, solo se usa después para describir la tasa de abandono
por segmento.

**Elección de k = 6** (con las cinco variables de la versión anterior había sido 5): el codo
de la inercia es el criterio principal (caídas de 28 a 60 mil hasta k=6, luego 19 mil o
menos); la silueta queda casi plana con diez variables (0.1958 a 0.2214) y no distingue un k
claro, pero k=6 (0.2151) es su máximo local. Se descarta k=2 pese a tener la silueta más alta
(0.3838) porque solo separa a los muy activos del resto y esconde al grupo que más abandona
dentro del 84 % restante de la población.

**PCA a dos componentes:** 42.10 % + 13.08 % = 55.18 % de varianza explicada. El componente 1
es intensidad de uso; el componente 2 es tendencia reciente (sube con más viajes en las
últimas dos semanas que en las dos anteriores).

| Seg. | Nombre | Tamaño | % | Tasa de abandono |
|---:|---|---:|---:|---:|
| 0 | Viajeros regulares | 15,832 | 26.6 | 0.0916 |
| 1 | Viajeros frecuentes multimodales | 8,286 | 13.9 | 0.0181 |
| 2 | Viajeros ocasionales de tarifa alta | 10,532 | 17.7 | 0.1106 |
| 3 | Viajeros intensivos multimodales | 1,128 | 1.9 | 0.0177 |
| 4 | Viajeros en enfriamiento | 8,062 | 13.5 | 0.4092 |
| 5 | Viajeros regulares multimodales | 15,675 | 26.3 | 0.0647 |

El segmento 4 (en enfriamiento: mediana de 17 días sin viajar, tendencia −3) concentra el
46.5 % de los positivos del corte A con solo el 13.5 % de la población. La tasa de abandono
por segmento es descriptiva, no causal: el segmento se construyó con las mismas conductas que
ya anticipan el abandono.

**Acciones de retención** (al menos dos exigidas, se definieron cinco): contacto directo con
recarga de cortesía de corta vigencia para el segmento 4; paquete de descuento en Aerómetro
para el segmento 2 (paga Q3.50 por viaje, el segundo con más abandono); mensajes de servicio
sin incentivo monetario para el segmento 0; promoción de transbordo para el segmento 5; y sin
campaña de retención (solo programa de lealtad) para los segmentos 1 y 3, de abandono mínimo.
Reporte completo en `docs/segmentos.md`.

## 5. Sección 2.4 — MLOps: predicción, modelo guardado y ficha

`predecir.py` recibe la carpeta de datos y la fecha de corte
(`python predecir.py --datos <carpeta> --fecha-corte 2026-08-30`), compara sus conteos contra
Bronze antes de predecir, carga `modelos/modelo_churn_v1.joblib` sin reentrenar, y produce un
CSV con `unidad_id`, `tarjetas` (llaves originales separadas por `;`), `puntaje` y
`contactar`.

**Predicciones oficiales del corte C (2026-08-30):** 57,711 filas, 7,408 contactados
(12.8 %), umbral 0.31. Archivo `predicciones/predicciones_2026-08-30.csv`, SHA-256
`ef3c2a3cea1f7c47827a7e049b94a522db06fe09ee279ba0684124926660c74c`.

**Entorno reproducible:** todas las dependencias en `requirements.txt` con versión fija
(`==`), semilla 42 en folds, modelos y KMeans, y un `README.md` con los pasos para correr el
proyecto completo en otra máquina.

**Ficha del modelo** (`docs/ficha_modelo.md`): modelo, versión y commit de entrenamiento;
datos y período; unidad; población por corte; etiqueta; comparación de modelos; métricas en
validación y en B; lógica de negocio del umbral; predicciones de producción; validaciones de
integridad; limitaciones; y el aviso de que los datos son simulados.

## 6. Validaciones de integridad

| Validación | Resultado | Bitácora |
|---|---|---|
| Fuga de datos en las features del modelo (prueba de recorte, corte B) | Sin fuga: `puntaje` y `contactar` idénticos en las 58,128 filas | D-016 |
| Fuga de datos futura en `features.unidad_tarjetas` | Encontrada (2,642 de 58,128 filas) y corregida acotando a `fecha_corte` | D-016, D-017 |
| Idempotencia del flujo completo (dos corridas desde entorno vacío) | Idéntico: 19,712,750 filas iguales en las 25 tablas de todas las capas | D-021 |
| Umbral y modelo congelados antes de evaluar B | Sin fuga de selección: B se evaluó una sola vez, sin reajustar nada después | D-019, D-020 |

## 7. Limitaciones

- El modelo pierde calibración de un mes a otro (ver diagnóstico de B en la sección 3): hay
  que vigilar en producción la precisión real de los contactados y reentrenar cuando haya
  etiqueta del corte más reciente.
- El ensemble no da coeficientes con signo ni explicaciones causales; su interpretación se
  apoya en importancias por permutación, no en una relación causal declarada.
- La evaluación de B es única e irrepetible por diseño: no hay forma de "reintentar" el
  umbral con B sin invalidar la prueba.
- La segmentación es descriptiva: la tasa de abandono por segmento no prueba que pertenecer
  al segmento cause el abandono.
- Los datos son simulados, igual que en el Proyecto 1; las cifras de negocio (ganancia,
  costos) son ilustrativas del método, no observaciones reales de la Agencia.

## Fuentes

`docs/etiqueta_y_features.md`, `docs/metricas_fase2_ensemble.md`, `docs/decision_modelo.md`,
`docs/metricas_umbral.md`, `docs/test_b.md`, `docs/segmentos.md`, `docs/ficha_modelo.md`,
`docs/umbral/umbral_elegido.json`, `docs/umbral/registro_test_b.json`,
`modelos/modelo_churn_v1.json`, `docs/bitacora.md` (D-013 a D-021),
`docs/evidencias/idempotencia.md`. Índice completo de scripts por entregable en
`docs/entrega_fase2/indice_scripts.md`.
