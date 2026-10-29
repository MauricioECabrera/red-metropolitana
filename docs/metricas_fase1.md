# Modelos supervisados de la Fase 1

## Datos y alcance

Se utilizaron datos simulados de la Red Metropolitana de Transporte.
La entrada fue la tabla features.features_corte, derivada de Silver,
filtrada al corte A del 1 de julio de 2026.

La población evaluada contiene 59,515 unidades: 7,098 con etiqueta 1
y 52,417 con etiqueta 0. La tasa positiva es:

7,098 / 59,515 = 0.119264, aproximadamente 11.9264 %.

Las verificaciones básicas encontraron cero identificadores nulos,
cero claves duplicadas y cero valores nulos en las variables utilizadas.

Las features corresponden a los 28 días anteriores al corte.
La etiqueta indica ausencia de abordajes válidos durante los 30 días
que comienzan en el corte. Los scripts de modelado utilizan únicamente A.

Estas comprobaciones no sustituyen la auditoría temporal de población
y features realizada por el responsable de datos.

## Variables predictoras

- viajes_28d
- dias_desde_ultimo_viaje
- gasto_28d_q
- operadores_distintos_28d
- abordajes_fin_semana_28d

unidad_id y fecha_corte se utilizan para identificar las filas.
etiqueta es la respuesta y no forma parte de las variables predictoras.

## Métrica elegida

Se utilizó Average Precision, calculada con average_precision_score.
La métrica resume la relación entre precisión y recall y permite comparar
el orden de riesgo antes de elegir un umbral de contacto.
Resulta apropiada ante el desbalance de clases, pues una accuracy alta
podría obtenerse prediciendo siempre continuidad.
AP no representa el porcentaje de clasificaciones correctas y no se
calculó como área trapezoidal bajo la curva precisión-recall.

## Validación y preprocesamiento

Se utilizó StratifiedKFold con cinco particiones, shuffle=True
y random_state=42, definido en scripts/modelos/folds.py.

Los datos se ordenaron por unidad_id antes de generar las particiones.
La asignación se conserva en scripts/modelos/asignacion_folds.csv.
La logística verificó que sus particiones coincidieran con las de
los baselines.

Las logísticas utilizaron ColumnTransformer y Pipeline con
StandardScaler. El escalador y el clasificador se ajustaron únicamente
con el entrenamiento de cada fold.

Se reporta la media de AP de los cinco folds y su desviación estándar
muestral, con ddof=1.

## Baselines

baseline_tasa asigna a todas las unidades la tasa positiva de todo A,
siguiendo la definición exigida por el enunciado.
Esta referencia utiliza las etiquetas de todo A para calcular su constante;
no debe describirse como una tasa estimada exclusivamente dentro del
entrenamiento de cada fold.

baseline_ranking utiliza dias_desde_ultimo_viaje / 28.
La hipótesis es que una mayor inactividad reciente puede anticipar abandono.
Es un puntaje fijo, sin entrenamiento, y no una probabilidad calibrada.
Aunque se publica en la columna contractual prob, sus valores no deben
interpretarse directamente como probabilidades de abandono.

## Regularización

Se compararon penalizaciones L1 y L2 con solver liblinear,
max_iter=5000 y random_state=42.

Valores de lambda evaluados:
0.001, 0.01, 0.1, 1, 10 y 100.

Se utilizó C = 1 / lambda.
Se realizaron 60 ajustes de validación: dos penalizaciones,
seis valores de lambda y cinco folds.

La selección utiliza la mayor AP media de validación.
Los empates exactos se resuelven por mayor lambda y luego por L1.

La mejor configuración de ambas penalizaciones fue lambda=1 y C=1.
La gráfica está en ../scripts/modelos/regularizacion_logistica.png.
Las barras representan una desviación estándar entre folds,
no intervalos de confianza.

## Resultados

| Modelo | AP entrenamiento media | AP validación media | Desviación validación |
|---|---:|---:|---:|
| Baseline tasa | 0.119264 | 0.119264 | 0.000046 |
| Baseline ranking | 0.389339 | 0.389760 | 0.003588 |
| Logística L1 | 0.408061 | 0.408296 | 0.004395 |
| Logística L2 | 0.408062 | 0.408300 | 0.004403 |

Se seleccionó L2 con lambda=1 y C=1 por obtener la mayor media.
Su diferencia respecto a L1 es de solo 0.000004 de AP:
ambas configuraciones presentan resultados prácticamente iguales.

L2 supera al baseline de ranking en 0.018540 de AP.
La inactividad reciente ya explica una parte importante del orden de riesgo.

La AP de entrenamiento y validación es similar.
No se observa una brecha que sugiera sobreajuste fuerte en estas métricas.
Esto no garantiza el mismo comportamiento en períodos futuros.

Las métricas de A se utilizaron para seleccionar hiperparámetros y pueden
ser optimistas por esa selección. No constituyen un test independiente.

## Interpretación de coeficientes

Los coeficientes corresponden a la logística L2 ajustada con todo A,
después de seleccionar su configuración.
Ese ajuste se utilizó para interpretación, no para reemplazar las
predicciones de validación.

Cada efecto corresponde a una desviación estándar de la variable,
manteniendo constantes las demás.

| Variable | Coeficiente | Odds ratio | Interpretación |
|---|---:|---:|---|
| dias_desde_ultimo_viaje | 0.844718 | 2.327321 | Mayor inactividad se asocia con mayores odds de abandono. |
| abordajes_fin_semana_28d | 0.062727 | 1.064736 | Asociación positiva pequeña, condicionada a las otras variables. |
| operadores_distintos_28d | -0.098626 | 0.906081 | Usar más operadores se asocia con menores odds de abandono. |
| gasto_28d_q | -0.296883 | 0.743131 | Mayor gasto se asocia con menores odds de abandono. |
| viajes_28d | -0.569543 | 0.565784 | Mayor frecuencia se asocia con menores odds de abandono. |

Intercepto: -2.531890.

Solo dos coeficientes son positivos; los otros tres tienen asociación
negativa con el abandono estimado.
Las asociaciones no demuestran causalidad.
Las variables relacionadas pueden afectar la estabilidad e interpretación
de los coeficientes. Un odds ratio no es un multiplicador de probabilidad.

## Predicciones de validación

Archivo: ../scripts/modelos/predicciones_cv.csv

Columnas:
unidad_id, fecha_corte, modelo, prob.

Se publicaron 59,515 filas por cada modelo:

- baseline_tasa
- baseline_ranking
- logistica

Total: 178,545 filas.
La logística publicada corresponde a L2, lambda=1 y C=1.

Las probabilidades de logística se obtuvieron cuando cada unidad
perteneció al fold de validación.
La selección de configuración se realizó con los resultados de A.

La comprobación del archivo encontró cero claves duplicadas,
cero puntajes nulos y todos los puntajes dentro de [0, 1].
La única fecha publicada es 2026-07-01.

## Entorno y reproducción

- scikit-learn: 1.5.2
- matplotlib: 3.9.2
- joblib: 1.4.2

Desde la raíz del repositorio, con el entorno virtual activo:

python -m scripts.modelos.baseline --corte A
python -m scripts.modelos.logistica --corte A

Tiempo total reportado por logistica.py: 16.27 segundos.
Incluye búsqueda, ajuste para interpretación y generación de salidas;
no corresponde exclusivamente al entrenamiento de un modelo.

## Límites y siguiente etapa

No se evaluaron modelos con la etiqueta de B ni se eligió un umbral
económico en estos scripts.

La comparación L1/L2 no muestra una ventaja material entre penalizaciones.
Las cinco variables disponibles pueden limitar la capacidad predictiva.

El siguiente paso es comparar un ensemble con los mismos folds y la
misma métrica. El modelo y el umbral se seleccionarán utilizando A,
antes de realizar la evaluación única en B.