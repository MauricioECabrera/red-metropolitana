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

1. Modelo: **ensemble** (HistGradientBoosting), el de mejor AP de
   validación en `docs/metricas_fase2_ensemble.md` (0.4258 contra 0.4083 de
   la logística), acordado con Adrián.
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

| Dato | Valor |
|---|---:|
| **Umbral elegido** | **0.33** |
| Contactados | 5,689 de 59,515 (9.6 %) |
| Verdaderos positivos / falsos positivos | 2,649 / 3,040 |
| Precisión en el umbral | 2,649 / 5,689 = 0.4656 |
| Recall en el umbral | 2,649 / 7,098 = 0.3732 |
| **Ganancia observada** | 15 × 2,649 − 5 × 5,689 = **Q11,290** |
| Ganancia esperada (Σ 15p − 5) | Q11,441.78 |
| Umbral de máxima ganancia esperada | 0.33 |
| Contactar a todos (umbral 0) | −Q191,105 |
| No contactar a nadie | Q0 |

Comparación con la línea base: contactar a todos equivale a usar el
baseline de tasa constante (todos tienen la misma p = 0.1193 < 1/3, así
que con ese modelo la decisión correcta sería no contactar a nadie y la
ganancia sería Q0). El ensemble permite encontrar al 9.6 % de usuarios con
p ≥ 0.33 y convertir la campaña en Q11,290 de ganancia.

**Lectura.** El umbral observado (0.33) coincide con el de la ganancia
esperada y con el equilibrio teórico 1/3. Las dos curvas casi se
superponen, lo que indica que las probabilidades fuera de fold del
ensemble están razonablemente calibradas: cuando el modelo dice p, la
proporción real de abandono es cercana a p.

**Estabilidad entre folds** (mismo umbral 0.33):

| Fold | Contactados | VP | Precisión | Recall | Ganancia |
|---:|---:|---:|---:|---:|---:|
| 1 | 1,102 | 504 | 0.46 | 0.36 | Q2,050 |
| 2 | 1,148 | 548 | 0.48 | 0.39 | Q2,480 |
| 3 | 1,134 | 524 | 0.46 | 0.37 | Q2,190 |
| 4 | 1,211 | 555 | 0.46 | 0.39 | Q2,270 |
| 5 | 1,094 | 518 | 0.47 | 0.36 | Q2,300 |

Los cinco folds dan ganancia positiva con poca variación (Q2,050 a
Q2,480), así que el umbral no depende de un fold en particular.

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
