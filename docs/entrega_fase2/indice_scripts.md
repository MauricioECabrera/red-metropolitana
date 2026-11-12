# Índice de scripts por entregable · Fase 2

Proyecto 2 · Agencia Metropolitana de Transporte · Red Metropolitana de Guatemala
Repositorio: https://github.com/MauricioECabrera/red-metropolitana (etiqueta `fase-2`)

El código de los entregables de la Fase 2 se entrega en este repositorio. Esta tabla indica
en qué archivo está cada script solicitado. El documento de datos y conclusiones es
`docs/entrega_fase2/Informe_Fase_2.pdf`.

## 2.1 Ensemble y sesgo-varianza

| Entregable | Archivo |
|---|---|
| Entrenamiento y comparación del ensemble con los mismos folds | `scripts/modelos/ensemble.py` |
| Folds compartidos de validación cruzada | `scripts/modelos/folds.py` |
| Contrato de variables (las diez del modelo) | `scripts/modelos/variables.py` |
| Tabla de modelos, sesgo-varianza por modelo e importancias por permutación | `docs/metricas_fase2_ensemble.md` |
| Decisión del modelo de producción | `docs/decision_modelo.md` |
| Evidencia (comparación, folds, importancias) | `scripts/modelos/comparacion_fase2.csv`, `ensemble_por_fold.csv`, `importancias_ensemble.csv`, `importancias_ensemble_detalle.csv`, `importancias_ensemble.png`, `configuracion_ensemble.json` |

## 2.2 Umbral según costo y test único

| Entregable | Archivo |
|---|---|
| Ganancia, curva de ganancia, umbral elegido y evaluación única en B | `scripts/modelos/umbral.py` |
| Derivación de la fórmula de ganancia y curva de ganancia contra umbral | `docs/metricas_umbral.md` |
| Umbral elegido y congelado | `docs/umbral/umbral_elegido.json` |
| Evidencia de la curva de ganancia | `docs/umbral/curva_ganancia_cv.csv`, `docs/umbral/ganancia_por_fold.csv`, `docs/umbral/ganancia_umbral.png` |
| Resultado de la única evaluación en B (fecha y commit) | `docs/test_b.md`, `docs/umbral/registro_test_b.json` |

## 2.3 Segmentación con KMeans y PCA

| Entregable | Archivo |
|---|---|
| KMeans, elección de k, PCA y segmentos | `scripts/segmentacion.py` |
| Reporte de segmentos y acciones de retención | `docs/segmentos.md` |
| Evidencia (tabla, asignación, gráficas, cargas PCA) | `docs/segmentos/tabla_segmentos.csv`, `docs/segmentos/asignacion_segmentos_A.csv`, `docs/segmentos/segmentos_pca.png`, `docs/segmentos/eleccion_k.png`, `docs/segmentos/cargas_pca.csv` |

## 2.4 MLOps: predecir, guardar y documentar

| Entregable | Archivo |
|---|---|
| Entrenamiento y guardado del modelo final | `scripts/entrenar_modelo.py` |
| Script de predicción en producción (no reentrena) | `predecir.py` |
| Modelo guardado con versión | `modelos/modelo_churn_v1.joblib`, `modelos/modelo_churn_v1.json` |
| Ficha del modelo | `docs/ficha_modelo.md` |
| Predicciones oficiales del corte C (2026-08-30) | `predicciones/predicciones_2026-08-30.csv` |
| Auditoría de fuga / prueba de recorte (extendida a Fase 2) | `scripts/prueba_recorte.py` |
| Verificación de idempotencia del flujo completo | `orquestacion/verificar_idempotencia.py`, `docs/evidencias/idempotencia.md` |
| Orquestación (incluye la predicción del corte C como etapa) | `orquestacion/flujo.py` |

## Documentación de respaldo

| Contenido | Archivo |
|---|---|
| Bitácora de decisiones de la Fase 2 (D-013 a D-021) | `docs/bitacora.md` |
| Definición de etiqueta, unidad, población y diccionario de features | `docs/etiqueta_y_features.md` |
| Tiempos del flujo completo | `docs/evidencias/tiempos_flujo.md` |
| Conteos de Bronze | `docs/evidencias/conteos_bronze.md` |

## Cómo reproducir todo

git clone https://github.com/MauricioECabrera/red-metropolitana
cd red-metropolitana
git checkout fase-2
python -m venv .venv
source .venv/Scripts/activate # Git Bash en Windows
pip install -r requirements.txt
cp .env.example .env # configurar la sal del equipo, no se versiona

Copiar los nueve archivos de datos del Proyecto 2 a datos_red/

python -m orquestacion.flujo
python predecir.py --datos datos_red --fecha-corte 2026-08-30


El flujo deja en `docs/evidencias/` la tabla de conteos y la de tiempos por etapa. `predecir.py`
escribe `predicciones/predicciones_2026-08-30.csv` y no reentrena: carga
`modelos/modelo_churn_v1.joblib`.
