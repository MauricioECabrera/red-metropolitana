# Guion de la presentación — Fase 2 (15 min + prueba de invariancia en vivo)

Repositorio: https://github.com/MauricioECabrera/red-metropolitana · etiqueta `fase-2`

## 1. El problema (1 min) — Miguel

"Con lo que sabemos de un usuario hasta hoy, ¿qué tan probable es que deje de usar la red en
los próximos 30 días? Y con esa probabilidad, ¿a quién conviene contactar?"

Clasificación binaria por unidad y fecha de corte. Unidad: la Persona, para no confundir
cambio de tarjeta con abandono real. Datos simulados, mismo periodo de 90 días que el
Proyecto 1 (1 jun–29 ago 2026), reemplazando los datos anteriores. Tres cortes: A (entreno,
1 jul), B (test único, 31 jul), C (producción, 30 ago, etiqueta oculta).

## 2. Datos nuevos y auditoría de fuga (1-2 min) — Miguel / Diego

Un solo comando (`python -m orquestacion.flujo`) carga desde cero sobre la capa Silver del
Proyecto 1. Prueba de recorte en las features: 0 diferencias en los tres cortes. Un ensayo
adicional de invarianza (recortando datos en vez de la fecha) encontró una fuga real en una
columna auxiliar (`tarjetas`, no usada por el modelo) — se corrigió acotándola a
`fecha_corte` (bitácora D-016/D-017). Las features del modelo (`puntaje`, `contactar`) nunca
tuvieron fuga.

## 3. Ensemble y sesgo-varianza (2-3 min) — Adrián

Mostrar la tabla de 5 modelos (baseline tasa, baseline ranking, L1, L2, ensemble) con AP de
validación, DE y brecha entrenamiento-validación. Mensaje clave: el ensemble gana en los 5
folds (+0.021 de AP sobre la mejor logística) pero con la mayor brecha (0.0408) — más
varianza, se acepta por la mejora consistente. Importancias por permutación en validación:
`dias_desde_ultimo_viaje` domina (0.2577), muy por encima de todo lo demás.

## 4. Umbral por costo y test único en B (2-3 min) — Eduardo

Derivar en vivo o mostrar la fórmula: `E[G] = 15p − 5`, punto de equilibrio teórico p > 1/3.
Umbral elegido: 0.31, por ganancia **observada** máxima en A (no la esperada) — casi igual al
óptimo teórico (diferencia de Q220). Mostrar la caída en B: AP 0.4276 → 0.3712, ganancia
Q11,510 → Q7,145, pero la política sigue siendo rentable frente a contactar a todos
(−Q194,895) o a nadie (Q0). Explicar la causa: no es que el modelo deje de encontrar a los
mismos abandonos (el recall casi no cambia), es que pierde calibración de un mes a otro — en
B sobreestima el riesgo de los contactados de mayor probabilidad.

## 5. Segmentación (2 min) — Eduardo / Miguel

k=6 por el codo (silueta casi plana con 10 variables, no sirve de criterio único). PCA: 55 %
de varianza en 2 componentes (intensidad de uso + tendencia reciente). Mostrar la tabla de
segmentos y enfatizar el segmento 4 ("en enfriamiento"): 13.5 % de la población, pero 46.5 %
de todo el abandono del corte A. Una acción de retención por segmento (al menos citar la de
los segmentos 4 y 2).

## 6. Producción: predecir.py, modelo y ficha (2 min) — Miguel

`predecir.py` carga el modelo guardado, no reentrena, compara conteos contra Bronze antes de
predecir. Predicciones oficiales del corte C: 57,711 filas, 7,408 contactados (12.8 %), con
su hash SHA-256 registrado. Ficha del modelo completa en `docs/ficha_modelo.md`. Idempotencia
verificada: dos corridas desde cero, 19,712,750 filas idénticas.

## 7. Cierre y limitaciones (1 min) — Miguel

La calibración se degrada de un mes a otro: hay que vigilar precisión real y reentrenar con
etiqueta reciente. El ensemble no da explicaciones causales. La evaluación de B es
irrepetible por diseño. Los datos son simulados.

## Prueba de invariancia en vivo

El catedrático entrega los mismos datos con 30 días más. Correr: `python -m orquestacion.flujo`
y luego `python predecir.py --datos <carpeta_nueva> --fecha-corte 2026-08-30`. Las predicciones
deben salir idénticas a `predicciones/predicciones_2026-08-30.csv` (mismo hash SHA-256). Si no
coinciden, el pipeline está usando datos posteriores al corte — ya se probó esto en la sesión
de cierre (D-021) con datos recortados y con datos completos, sin diferencias.

## Decisión ajena — cada integrante explica la de otro

Sugerencia de asignación (cada quien debe poder sostenerla con solvencia, no solo leerla):

| Quien explica | Decisión de | Qué explicar |
|---|---|---|
| Miguel | Diego (unidad = Persona, D-002/etiqueta_y_features.md) | Por qué Persona y no tarjeta; qué alternativa había (tarjeta) y qué se perdía con ella (usuarios multimodales que cambian de tarjeta aparecerían como abandono falso) |
| Diego | Adrián (ensemble sobre logística, D-018) | Por qué el ensemble pese a su mayor brecha entrenamiento-validación; qué alternativa (quedarse con L1) y por qué se descartó (0.021 menos de AP, consistente en los 5 folds) |
| Adrián | Eduardo (umbral por ganancia observada, no esperada, D-019) | Por qué no usar el 1/3 teórico directamente; qué alternativa (umbral de máxima ganancia esperada, 0.33) y por qué se prefirió 0.31 (no depende de calibración, diferencia de solo Q220) |
| Eduardo | Miguel (predecir.py no reentrena / CorteVacio, cierre del repo) | Por qué el modelo se congela y predecir.py solo carga; cómo se manejó el corte C vacío en la prueba de recorte sin romper el flujo normal |

Ajustar según quién se sienta más cómodo, pero que cada quien repase la decisión ajena antes
de la defensa — el catedrático puede preguntar a cualquiera.

## Preguntas de fondo — preparar respuesta corta

**¿Dónde pudo haber fuga en tu proyecto y cómo lo sabes?**
Dos lugares posibles: (1) en las features del modelo, descartado por la prueba de recorte (0
diferencias en los tres cortes) y por el ensayo de invarianza con datos recortados (`puntaje`
y `contactar` idénticos en 58,128 filas); (2) en una columna auxiliar no usada por el modelo
(`tarjetas`), donde sí hubo fuga real — encontrada porque no estaba acotada por
`fecha_corte`, corregida y vuelta a verificar.

**¿Por qué esa métrica y de dónde salió tu umbral?**
Average Precision para comparar modelos porque la clase positiva es minoritaria (11.9 % en
A) y la calibración es defectuosa (así no se castiga una sola decisión de corte). El umbral
0.31 sale de maximizar la ganancia observada — no la esperada — sobre las predicciones fuera
de fold de A, usando el escenario de costos dado (Q5 contactar, 25 % de retención, Q60 el
usuario retenido); se prefirió la ganancia observada porque no asume que el modelo esté bien
calibrado, y resultó casi igual al óptimo teórico de 1/3.
