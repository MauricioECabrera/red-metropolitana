# Ensemble y comparación de modelos

## Alcance

Se evaluó un HistGradientBoostingClassifier sobre el corte A del
1 de julio de 2026, con 59,515 unidades y cinco variables predictoras.

Se utilizó la misma población, orden de filas, asignación de cinco folds
y métrica Average Precision de la Fase 1.
El programa verificó la coincidencia con asignacion_folds.csv.

Los scripts de modelado no consultaron las etiquetas de B.
Los datos del escenario son simulados.

## Configuración

- learning_rate: 0.1
- max_iter: 100
- max_leaf_nodes: 15
- min_samples_leaf: 20
- l2_regularization: 1.0
- early_stopping: False
- random_state: 42

Se evaluó una configuración fija, sin búsqueda adicional de hiperparámetros.
Se utilizó Pipeline con ColumnTransformer para seleccionar las variables.
Las variables se conservaron en su escala original.

En cada fold se entrenó un modelo nuevo y se predijeron las unidades
reservadas para validación.

## Comparación

| Modelo | AP entrenamiento media | AP validación media | Desviación validación | Brecha AP |
|---|---:|---:|---:|---:|
| Baseline tasa | 0.119264 | 0.119264 | 0.000046 | 0.000000 |
| Baseline ranking | 0.389339 | 0.389760 | 0.003588 | -0.000421 |
| Logística L1 | 0.408061 | 0.408296 | 0.004395 | -0.000235 |
| Logística L2 | 0.408062 | 0.408300 | 0.004403 | -0.000238 |
| Ensemble | 0.455987 | 0.425788 | 0.003353 | 0.030199 |

La brecha se define como AP de entrenamiento menos AP de validación.
Las desviaciones de validación son muestrales entre los cinco folds.
No representan intervalos de confianza.

El ensemble mejora a la logística L2 en 0.017488 de AP,
equivalente a 1.7488 puntos porcentuales y aproximadamente 4.28 %
de mejora relativa.

AP no es accuracy ni una medida directa de ganancia económica.
La comparación descriptiva no constituye una prueba de significancia.

## Sesgo y varianza

- Baseline tasa: capacidad predictiva limitada al asignar un valor constante;
  no utiliza diferencias de comportamiento entre unidades.
- Baseline ranking: captura información importante de inactividad,
  pero su capacidad se limita a una variable y una regla fija.
- Logística L1: rendimiento similar en entrenamiento y validación;
  no presenta una brecha indicativa de sobreajuste fuerte.
- Logística L2: comportamiento prácticamente igual al de L1;
  las relaciones lineales pueden limitar su capacidad.
- Ensemble: mayor rendimiento en entrenamiento y validación, con una brecha
  positiva de 0.030199 que indica sobreajuste respecto al entrenamiento.
  Aun así, mantiene la mejor AP media de validación.

Estas lecturas son indicios basados en las métricas observadas;
no constituyen una descomposición formal de sesgo y varianza.
Las pequeñas brechas negativas de otros modelos pueden deberse a la
composición de las particiones.

## Importancia por permutación

Las importancias se calcularon exclusivamente en la validación de cada fold,
con scoring="average_precision", diez repeticiones y random_state=42.

Se obtuvieron 50 mediciones por variable: cinco folds por diez repeticiones.
La importancia es la caída de AP al desordenar una variable manteniendo
el modelo entrenado.

| Variable | Importancia media | Desviación |
|---|---:|---:|
| dias_desde_ultimo_viaje | 0.278567 | 0.004808 |
| viajes_28d | 0.035629 | 0.012325 |
| gasto_28d_q | 0.012648 | 0.003327 |
| abordajes_fin_semana_28d | 0.003692 | 0.002935 |
| operadores_distintos_28d | 0.000512 | 0.002367 |

La inactividad reciente es la variable de la que más depende el modelo.
La frecuencia de viajes y el gasto aportan información adicional.
Los operadores distintos muestran un aporte marginal pequeño e inestable.

La desviación combina variabilidad entre folds y permutaciones;
no es un intervalo de confianza.
Las importancias no son porcentajes, no indican dirección del efecto
y no demuestran causalidad.
Las variables relacionadas pueden afectar sus importancias individuales.

La tabla actual contiene cinco variables, por lo que se reportan las cinco
disponibles. El requisito de diez importancias de la rúbrica queda pendiente
de ampliar las features o aclarar su aplicación con el catedrático.
Si se amplían, deben repetirse las comparaciones con una entrada común.

## Recomendación

Se propone el ensemble como candidato preferido por su AP de validación
de 0.425788 frente a 0.408300 de la logística.
Su tiempo de entrenamiento es bajo, aunque presenta mayor sobreajuste
y menor facilidad de interpretación.
La ventaja predictiva justifica considerarlo, pero no demuestra mayor
ganancia económica.
La decisión definitiva de modelo y umbral debe acordarse utilizando A
y registrarse antes de la evaluación única en B.

## Rendimiento

- Entrenamiento acumulado de los cinco folds: 3.67 segundos.
- Ejecución total: 19.95 segundos.

El tiempo total incluye lectura, evaluación, permutaciones y escritura.
No debe compararse directamente con los 16.27 segundos de logistica.py
como si ambos fueran tiempos exclusivos de entrenamiento:
la logística incluye una búsqueda de 60 ajustes y el ensemble incluye
importancia por permutación.

Los tiempos corresponden al equipo y ejecución utilizados.

## Predicciones publicadas

Archivo: ../scripts/modelos/predicciones_cv.csv

Columnas:
unidad_id, fecha_corte, modelo, prob.

Modelos y cantidad de filas:

- baseline_tasa: 59,515
- baseline_ranking: 59,515
- logistica: 59,515
- ensemble: 59,515

Total: 238,060 filas.

Se verificaron cero claves duplicadas, cero puntajes nulos,
valores dentro de [0, 1], las mismas unidades por modelo
y únicamente la fecha 2026-07-01.

Las predicciones del ensemble son fuera de fold.
baseline_ranking conserva un puntaje no calibrado, aunque la columna
contractual se denomine prob.

## Reproducción y evidencias

Con scikit-learn 1.5.2 y el entorno virtual activo:

python -m scripts.modelos.ensemble --corte A

Archivos generados en scripts/modelos/:

- ensemble_por_fold.csv
- comparacion_fase2.csv
- importancias_ensemble_detalle.csv
- importancias_ensemble.csv
- importancias_ensemble.png
- configuracion_ensemble.json
- predicciones_cv.csv

## Coordinación pendiente

Eduardo recibe las predicciones para analizar el umbral y la ganancia
utilizando A. Miguel recibe la configuración y el constructor del pipeline
del modelo que acuerde el equipo.

Modelo y umbral deben quedar congelados antes de evaluar B.
Después de observar B no deben reajustarse para mejorar ese resultado.

La decisión acordada se registrará con fecha en docs/bitacora.md.
Esta recomendación todavía no representa una decisión conjunta del equipo.