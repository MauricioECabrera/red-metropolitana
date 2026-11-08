# Umbral de contacto según costo (sección 2.2)

**Responsable:** Eduardo Hernández

## Escenario de la Agencia

| Parámetro | Valor |
|---|---|
| Costo de contactar a un usuario | Q5 |
| Probabilidad de retener a quien se iba a ir | 0.25 |
| Valor de un usuario retenido | Q60 |

## Derivación de la ganancia

Para un usuario contactado definimos dos variables aleatorias:

- `Y` = 1 si el usuario iba a abandonar, 0 si no. P(Y = 1) = p, la
  probabilidad que da el modelo.
- `R` = 1 si la campaña lo retiene, 0 si no. Solo importa cuando Y = 1,
  y P(R = 1 | Y = 1) = 0.25.

La ganancia de contactarlo es lo que se recupera menos lo que se paga:

```
G = 60 · Y · R − 5
```

Si el usuario no se iba a ir (Y = 0), el contacto no recupera nada y solo
se pierden los Q5. Si se iba a ir, se recuperan Q60 únicamente cuando la
campaña funciona.

Valor esperado:

```
E[G] = 60 · E[Y · R] − 5
     = 60 · P(Y = 1) · P(R = 1 | Y = 1) − 5
     = 60 · p · 0.25 − 5
     = 15p − 5
```

Contactar conviene cuando E[G] > 0:

```
15p − 5 > 0   ⇔   p > 5 / 15   ⇔   p > 1/3 ≈ 0.3333
```

Ese es el umbral de equilibrio teórico: solo vale si las probabilidades
del modelo están bien calibradas.

**Ganancia total de una política con umbral t.** Se contacta a todo
usuario con p ≥ t. Sumando sobre el conjunto C(t) de contactados:

```
G_esperada(t) = Σ_{i ∈ C(t)} (15 · p_i − 5)
             = 15 · Σ_{i ∈ C(t)} p_i − 5 · |C(t)|
```

Con la etiqueta real del corte A (predicciones fuera de fold) se puede
calcular la ganancia **observada**, reemplazando la esperanza de Y por lo
que pasó de verdad y conservando la esperanza de R, que no se observa:

```
G_observada(t) = Σ_{i ∈ C(t)} (15 · y_i − 5)
              = 15 · TP(t) − 5 · (TP(t) + FP(t))
```

Cada verdadero positivo aporta 0.25 × 60 − 5 = Q10 y cada falso positivo
cuesta Q5. Los falsos negativos no cuestan dinero en la cuenta, pero son
ganancia que se deja de ganar.

## Cómo se eligió el umbral

1. Modelo: **ensemble** (HistGradientBoosting con las diez variables de
   `scripts/modelos/variables.py`), el seleccionado por Adrián en
   `docs/decision_modelo.md` y en la bitácora (D-018): AP de validación
   0.4289 contra 0.4079 de la mejor logística.
2. Se usan las predicciones fuera de fold del corte A
   (`scripts/modelos/predicciones_cv.csv`) unidas con la etiqueta de A.
   Ninguna fila del corte B participa.
3. Se recorren umbrales de 0.00 a 1.00 en pasos de 0.01 y en cada uno se
   calculan G_observada y G_esperada.
4. Se elige el umbral que maximiza **G_observada**. Se prefiere la
   observada sobre la esperada porque no depende de que el ensemble esté
   calibrado; la esperada y el 1/3 teórico quedan como control. Si dos
   umbrales empatan se toma el mayor (menos contactos por la misma
   ganancia).
5. El umbral se congela en `docs/umbral/umbral_elegido.json`. Ese mismo
   valor es el que usa la evaluación de B: el script lo lee de ese archivo
   y no recibe el umbral como parámetro.

Comando:

```
python -m scripts.modelos.umbral --modelo ensemble --corte-eval A
```

## Resultado en validación cruzada (corte A)

Población: 59,515 unidades, 7,098 positivos (7,098 / 59,515 = 0.1193).
AP de las predicciones fuera de fold juntas: 0.4276 (la media por fold que
reporta Adrián es 0.4289; la diferencia es solo la forma de promediar).

| Dato | Valor |
|---|---:|
| **Umbral elegido** | **0.31** |
| Contactados | 6,653 de 59,515 (11.2 %) |
| Verdaderos positivos / falsos positivos | 2,985 / 3,668 |
| Precisión en el umbral | 2,985 / 6,653 = 0.4487 |
| Recall en el umbral | 2,985 / 7,098 = 0.4205 |
| **Ganancia observada** | 15 × 2,985 − 5 × 6,653 = 44,775 − 33,265 = **Q11,510** |
| Ganancia esperada en 0.31 (Σ 15p − 5) | Q11,566.04 |
| Umbral de máxima ganancia esperada | 0.33 (Q11,728.60) |
| Contactar a todos (umbral 0) | 15 × 7,098 − 5 × 59,515 = **−Q191,105** |
| No contactar a nadie | Q0 |

Comparación con la línea base: contactar a todos equivale a usar el
baseline de tasa constante (todos tienen la misma p = 0.1193 < 1/3, así
que con ese modelo la decisión correcta sería no contactar a nadie y la
ganancia sería Q0). El ensemble permite encontrar al 11.2 % de usuarios
con p ≥ 0.31 y convertir la campaña en Q11,510 de ganancia.

**Cambio respecto a la versión de cinco variables.** Con el ensemble de
cinco variables el umbral era 0.33 con Q11,290. No se trasladó: se
recalculó con las predicciones fuera de fold nuevas y bajó a 0.31, con
Q220 más de ganancia y 964 contactos más (6,653 contra 5,689).

**Lectura.** La cima de la curva es casi plana:

| Umbral | Contactados | VP | Ganancia observada | Ganancia esperada |
|---:|---:|---:|---:|---:|
| 0.30 | 7,098 | 3,115 | Q11,235 | Q11,377.48 |
| **0.31** | **6,653** | **2,985** | **Q11,510** | Q11,566.04 |
| 0.32 | 6,231 | 2,844 | Q11,505 | Q11,683.05 |
| 0.33 | 5,874 | 2,724 | Q11,490 | Q11,728.60 |
| 0.34 | 5,559 | 2,610 | Q11,355 | Q11,721.13 |

Entre 0.31 y 0.33 la ganancia observada cambia solo Q20, así que el
umbral elegido, el de la ganancia esperada (0.33) y el equilibrio teórico
(1/3) dan prácticamente la misma decisión. Las dos curvas casi se
superponen, señal de que las probabilidades fuera de fold del ensemble
están razonablemente calibradas. Se mantiene la regla declarada antes de
ver los números: se usa el máximo de la ganancia observada, que no
depende de la calibración.

**Estabilidad entre folds** (mismo umbral 0.31):

| Fold | Contactados | VP | Precisión | Recall | Ganancia |
|---:|---:|---:|---:|---:|---:|
| 1 | 1,300 | 584 | 0.45 | 0.41 | Q2,260 |
| 2 | 1,400 | 623 | 0.44 | 0.44 | Q2,345 |
| 3 | 1,283 | 575 | 0.45 | 0.40 | Q2,210 |
| 4 | 1,377 | 612 | 0.44 | 0.43 | Q2,295 |
| 5 | 1,293 | 591 | 0.46 | 0.42 | Q2,400 |

Los cinco folds dan ganancia positiva con poca variación (Q2,210 a
Q2,400), así que el umbral no depende de un fold en particular. La suma de
los cinco es Q11,510.

Gráfica: `docs/umbral/ganancia_umbral.png` (panel derecho con el detalle
de la zona positiva). Curva completa: `docs/umbral/curva_ganancia_cv.csv`.

## Evaluación única en B

Se corre **una sola vez**, cuando todo lo anterior esté en un commit:

```
python -m scripts.modelos.umbral --modelo ensemble --corte-eval B
```

El script entrena el ensemble con todo el corte A (sin folds), predice B y
aplica el umbral congelado. Para evitar romper la regla, se niega a correr
si ya existe `docs/umbral/registro_test_b.json`, si `umbral_elegido.json`
no está versionado o si hay cambios sin commit. Después de B, el modo A
también queda bloqueado, para que el umbral no se pueda volver a elegir.

Resultados: `docs/test_b.md` y la entrada en `docs/bitacora.md`.

**Resultado (8 de noviembre de 2026, commit `2ba297c`).** AP 0.3712,
precisión 0.4055, recall 0.4194 y ganancia 15 × 2,677 − 5 × 6,602 =
Q7,145 con 6,602 contactados, contra −Q194,895 de contactar a todos. La
explicación de la diferencia con A está en `docs/test_b.md`.
