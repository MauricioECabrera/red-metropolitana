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
   la logística). *Confirmar con Adrián y con la decisión de 2.1 antes de
   evaluar B.*
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

*Pendiente: llenar con la salida del comando sobre el warehouse real.*

| Dato | Valor |
|---|---:|
| Umbral elegido | |
| Contactados | |
| Verdaderos positivos / falsos positivos | |
| Ganancia observada | Q |
| Umbral de máxima ganancia esperada | |
| Ganancia de contactar a todos | Q |

Gráfica: `docs/umbral/ganancia_umbral.png` (panel derecho con el detalle
de la zona positiva). Estabilidad por fold: `docs/umbral/ganancia_por_fold.csv`.

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
