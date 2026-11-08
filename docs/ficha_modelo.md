# Ficha del modelo — Churn de Red Metropolitana

**Modelo:** ensemble (`HistGradientBoostingClassifier`, scikit-learn)
**Versión:** v1 · **Commit de entrenamiento:** `80173bf6e7ae86a74ad40116b0d35b99104b1593`
**Variables (10):** `viajes_28d`, `dias_desde_ultimo_viaje`, `gasto_28d_q`,
`operadores_distintos_28d`, `abordajes_fin_semana_28d`, `viajes_7d`,
`dias_activos_28d`, `gasto_promedio_viaje_q`, `proporcion_hora_pico_28d`,
`tendencia_viajes_14d`
**Entrenamiento final:** 59,515 unidades (corte A completo), 0.18 s,
semilla 42, scikit-learn 1.9.1. Archivos: `modelos/modelo_churn_v1.joblib`
y `modelos/modelo_churn_v1.json`.
**Umbral de contacto:** 0.31 (congelado, ver "Lógica de negocio").

## Comparación de modelos (corte A, validación cruzada de 5 folds)

| Modelo | AP validación | DE | AP entrenamiento | Brecha | Entrenamiento 5 folds (s) |
|---|---:|---:|---:|---:|---:|
| Baseline tasa constante | 0.1193 | 0.00005 | 0.1193 | 0.0000 | — |
| Baseline ranking | 0.3898 | 0.0036 | 0.3893 | −0.0004 | — |
| Logística L1 (λ=100) | 0.4079 | 0.0041 | 0.4078 | −0.0001 | 0.61 |
| **Ensemble (elegido)** | **0.4289** | **0.0024** | 0.4697 | 0.0408 | 2.15 |

El ensemble supera a la mejor logística en los cinco folds (+0.0210 de AP)
y a la línea base de ranking (+0.0392). Se acepta su mayor brecha
entrenamiento-validación y su menor interpretabilidad por la mejora
consistente. Detalle completo en `docs/decision_modelo.md`.

## Tabla de rendimiento: validación en A vs. evaluación única en B

| Dato | Validación cruzada en A | Evaluación única en B |
|---|---:|---:|
| Unidades | 59,515 | 58,128 |
| Tasa de abandono real | 0.1193 | 0.1098 |
| Average Precision | 0.4276 (oof) | 0.3712 |
| Contactados (umbral 0.31) | 6,653 (11.2 %) | 6,602 (11.4 %) |
| Verdaderos positivos / falsos positivos | 2,985 / 3,668 | 2,677 / 3,925 |
| Precisión en el umbral | 0.4487 | 0.4055 |
| Recall en el umbral | 0.4205 | 0.4194 |
| Ganancia observada | Q11,510.00 | Q7,145.00 |
| Ganancia esperada (Σ 15p−5) | Q11,566.04 | Q12,601.97 |
| Ganancia por unidad | Q0.1934 | Q0.1229 |
| Contactar a todos | −Q191,105.00 | −Q194,895.00 |
| No contactar a nadie | Q0.00 | Q0.00 |

La política de contactar con el umbral congelado es rentable en ambos
cortes y muy superior a contactar a todos o a nadie, aunque la ganancia
cae de A a B. El recall casi no cambia (0.4205 → 0.4194); lo que baja es
la precisión (0.4487 → 0.4055), es decir, el modelo pierde calibración de
un mes a otro, no deja de encontrar a los mismos abandonos. Diagnóstico
completo, con las tres hipótesis descartadas o confirmadas, en
`docs/test_b.md`.

## Lógica de negocio del umbral

Costo de contactar Q5, probabilidad de retención si se contacta a quien
se iba a ir 0.25, valor de un usuario retenido Q60. Ganancia esperada por
contacto: `E[G] = 15p − 5`; conviene contactar cuando `p > 1/3 ≈ 0.3333`.

El umbral de producción no es ese 1/3 teórico sino **0.31**, el que
maximiza la ganancia **observada** (no la esperada) sobre las predicciones
fuera de fold del corte A, con las etiquetas reales — se prefiere así
porque no depende de que el modelo esté bien calibrado. La diferencia con
el máximo de ganancia esperada (0.33, Q11,728.60) es de solo Q220 sobre
Q11,510, y ambas curvas casi se superponen, señal de que el modelo está
razonablemente calibrado en A. Derivación completa y curva de ganancia
en `docs/metricas_umbral.md`.

Respecto a la versión de cinco variables (Fase 1): el umbral no se
trasladó, se recalculó con las predicciones fuera de fold del ensemble de
diez variables y bajó de 0.33 a 0.31, con Q220 más de ganancia y 964
contactos más.

## Predicciones de producción (corte C, 2026-08-30)

| Dato | Valor |
|---|---:|
| Filas | 57,711 |
| Contactados | 7,408 (12.8 %) |
| Umbral usado | 0.31 |
| Modelo | `modelos/modelo_churn_v1.joblib` (commit `80173bf`) |

Archivo: `predicciones/predicciones_2026-08-30.csv`.
SHA-256: `ef3c2a3cea1f7c47827a7e049b94a522db06fe09ee279ba0684124926660c74c`.

## Validaciones de integridad

| Validación | Resultado | Bitácora |
|---|---|---|
| Fuga de datos en las features del modelo (ensayo de invarianza, corte B, datos completos vs. recortados al 30/jul) | Sin fuga: `puntaje` y `contactar` idénticos en las 58,128 filas | D-016 |
| Fuga de datos futura en `features.unidad_tarjetas` | Encontrada (2,642/58,128 filas) y corregida acotando a `fecha_corte` | D-016, D-017 |
| Idempotencia del flujo completo (dos corridas desde entorno vacío) | IDEMPOTENTE: 19,712,750 filas idénticas en las 25 tablas de todas las capas | D-021 |
| Umbral y modelo congelados antes de evaluar B | Sin fuga de selección: B se evaluó una sola vez, sin reajustar nada después de verlo | D-019, D-020 |

## Limitaciones

- El modelo pierde calibración de un mes a otro: en B, entre los
  contactados de mayor riesgo (p > 0.5) la probabilidad media fue 0.6100
  y la tasa real de abandono 0.5034, mientras que en A ambas estaban
  cerca (0.6018 y 0.6107). Hay que vigilar en producción la precisión real
  de los contactados y la tasa de abandono de cada corte, y reentrenar
  cuando haya etiqueta del corte más reciente.
- El ensemble no da coeficientes con signo ni explicaciones causales; su
  interpretación se apoya en importancias por permutación
  (`scripts/modelos/importancias_ensemble.csv`), no en una relación
  causal declarada.
- La evaluación de B es única e irrepetible por diseño: el script se
  niega a correr de nuevo si ya existe `docs/umbral/registro_test_b.json`.
  No hay forma de "reintentar" el umbral con B sin invalidar la prueba.

## Fuentes

`docs/decision_modelo.md`, `docs/metricas_umbral.md`, `docs/test_b.md`,
`docs/umbral/umbral_elegido.json`, `docs/umbral/registro_test_b.json`,
`modelos/modelo_churn_v1.json`, `docs/bitacora.md` (D-015 a D-021).
