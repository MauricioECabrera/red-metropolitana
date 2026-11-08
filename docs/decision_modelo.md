# Decisión del modelo de producción

**Proyecto 2 · Red Metropolitana · Responsable de modelado: Adrián**
**Fecha:** 8 de noviembre de 2026.
**Estado:** modelo seleccionado por el responsable de modelado; coordinación de umbral y despliegue pendiente con Eduardo y Mauricio.

## Decisión

Se selecciona el ensemble `HistGradientBoostingClassifier` con diez variables para producción.
Su AP de validación en A es 0.428920 ± 0.002403, frente a 0.407921 ± 0.004148 de la mejor logística evaluada, y la supera en los cinco folds.
La mejora de 0.021000 de AP justifica conservarlo, con 2.152028 segundos de entrenamiento acumulado frente a 0.607734 de L1.
Se acepta una brecha mayor, 0.040822 frente a −0.000108, y menor interpretabilidad que una regresión con coeficientes.
La elección usa únicamente A; Eduardo recalculará el umbral y Mauricio guardará el modelo final antes de la evaluación única en B.

## Evidencia de la elección

| Modelo | AP validación media | DE validación | AP entrenamiento media | Brecha AP | Entrenamiento de cinco folds (s) |
|---|---:|---:|---:|---:|---:|
| Baseline tasa | 0.119264 | 0.000046 | 0.119264 | 0.000000 | No aplica: regla fija |
| Baseline ranking | 0.389760 | 0.003588 | 0.389339 | -0.000421 | No aplica: regla fija |
| Logística L1, λ=100 | 0.407921 | 0.004148 | 0.407812 | -0.000108 | 0.607734 |
| Ensemble | 0.428920 | 0.002403 | 0.469742 | 0.040822 | 2.152028 |

La desviación estándar describe cinco folds; no es un intervalo de confianza. El ensemble supera al ranking en 0.039160 de AP. La ventaja sobre L1 es consistente en esos folds, sin constituir una prueba de significancia o de mayor ganancia económica. Los tiempos corresponden a una sola ejecución.

## Configuración y límites

Se conserva `construir_pipeline()` de `scripts/modelos/ensemble.py`, sin argumentos, con `learning_rate=0.1`, `max_iter=100`, `max_leaf_nodes=15`, `min_samples_leaf=20`, `l2_regularization=1.0`, `early_stopping=False` y `random_state=42`. La lista ordenada de diez predictores es `VARIABLES` en `scripts/modelos/variables.py`.

La alternativa logística es la mejor dentro de la grilla declarada: λ=100 está en su extremo superior y no se demuestra optimalidad fuera de ella. Las métricas de A se utilizaron para seleccionar y comparar modelos, por lo que no constituyen una evaluación independiente. La interpretación del ensemble se apoya en permutaciones de validación y no ofrece coeficientes con signo ni explicaciones causales.

## Registro y coordinación

Esta entrada documenta la decisión solicitada por Adrián a partir de los resultados entregados. No certifica una aprobación de Eduardo o Miguel ni confirma por sí sola si B fue ejecutado en otro equipo.

La validación local del CSV confirmó las 238,060 predicciones, las mismas unidades y folds, y la correspondencia entre las métricas recalculadas y las publicadas. Antes del test B quedan el registro de esta decisión en la bitácora, la confirmación de recepción de Eduardo y Miguel y la congelación del umbral recalculado con A. La fecha de confirmación conjunta se registrará cuando ocurra. No se reutilizan automáticamente el umbral 0.33 ni la ganancia de la versión de cinco variables.

Fuentes: [comparación completa](metricas_fase2_ensemble.md), [logísticas y baselines](metricas_fase1.md), `scripts/modelos/comparacion_fase2.csv`, `logistica_por_fold.csv`, `ensemble_por_fold.csv` y `configuracion_ensemble.json`.
