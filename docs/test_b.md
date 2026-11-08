# Evaluación única del corte B

| Dato | Valor |
|---|---|
| Fecha de la evaluación | 2026-11-08 12:25:50 |
| Commit evaluado | `2ba297c903766f792e1aea29d872f2a8c2974d24` |
| Modelo | ensemble entrenado con todo el corte A (59,515 unidades) |
| Umbral (congelado en A) | 0.31 |
| Unidades del corte B | 58,128 |
| Tasa positiva en B | 0.1098 |

## Métrica

| Métrica | Valor |
|---|---:|
| Average Precision | 0.3712 |
| Precisión en el umbral | 0.4055 |
| Recall en el umbral | 0.4194 |

## Matriz de confusión en el umbral

| | Predicho 0 (no contactar) | Predicho 1 (contactar) |
|---|---:|---:|
| Real 0 (sigue viajando) | 47,820 | 3,925 |
| Real 1 (abandona) | 3,706 | 2,677 |

## Ganancia en quetzales

| Política | Ganancia |
|---|---:|
| Contactar con el umbral 0.31 (6,602 contactados) | Q7,145.00 |
| Contactar a todos | −Q194,895.00 |
| No contactar a nadie | Q0.00 |

Ganancia = 15 × 2,677 − 5 × 6,602 = 40,155 − 33,010 = Q7,145.

Ganancia por unidad: Q0.1229 en B frente a Q0.1934
en la validación cruzada de A.

## Lectura del resultado

El resultado es peor que en la validación de A, pero la política sigue
siendo rentable: Q7,145 contra −Q194,895 de contactar a todos y Q0 de no
contactar a nadie.

| Dato | Validación en A | Test en B |
|---|---:|---:|
| Average Precision | 0.4276 | 0.3712 |
| Contactados con 0.31 | 6,653 | 6,602 |
| Precisión en el umbral | 0.4487 | 0.4055 |
| Recall en el umbral | 0.4205 | 0.4194 |
| Ganancia | Q11,510 | Q7,145 |
| Ganancia por unidad | Q0.1934 | Q0.1229 |

**De dónde sale la diferencia de ganancia.** El modelo contactó casi a la
misma cantidad de personas (6,602 contra 6,653) y el recall casi no cambió
(0.4194 contra 0.4205). Lo que bajó fue la precisión: de cada 100
contactados abandonaron 41 y no 45. Si la precisión de A se hubiera
mantenido con los mismos 6,602 contactos, la ganancia habría sido
15 × 2,962 − 5 × 6,602 = Q11,420. La pérdida está en los verdaderos
positivos que faltaron, no en contactar de más.

Se revisaron las tres explicaciones posibles, cada una con su cifra:

1. **Distribución distinta entre cortes (sí explica una parte).** La tasa
   de abandono bajó de 0.1193 en A a 0.1098 en B. La AP depende de esa
   tasa: un modelo al azar tendría AP igual a la tasa. Aun así, la AP
   dividida entre la tasa también bajó, de 0.4276 / 0.1193 = 3.58 a
   0.3712 / 0.1098 = 3.38, así que no todo es la tasa: el ordenamiento
   también se debilitó un poco. Las features se movieron hacia más uso en
   B (media de `viajes_28d` 16.13 → 16.98, de `dias_activos_28d`
   8.76 → 9.04 y de `tendencia_viajes_14d` 0.168 → 0.233).
2. **Variación de muestra (no alcanza).** En A, la ganancia por unidad de
   los cinco folds fue de Q0.1857 a Q0.2016 y la desviación de la AP entre
   folds fue 0.0024. B queda en Q0.1229 y su AP está 0.056 por debajo,
   unas 23 desviaciones. Es una diferencia demasiado grande para ser solo
   ruido de muestra.
3. **Desfase temporal (es la causa principal).** El modelo aprendió con
   la conducta de junio y la etiqueta de julio, y en B se aplica a julio
   con la etiqueta de agosto. En A sus probabilidades estaban calibradas:
   entre los contactados la probabilidad media era 0.4492 y abandonó el
   0.4487. En B la probabilidad media de los contactados fue 0.4606 y
   abandonó solo el 0.4055. El desajuste está en el riesgo alto: con
   p > 0.5 el modelo dice 0.6100 y abandonó el 0.5034 (en A, 0.6018 contra
   0.6107). En agosto, perfiles que en julio se iban dejaron de irse con la
   misma frecuencia. Por eso la ganancia esperada en B (Q12,601.97) quedó
   muy por encima de la observada (Q7,145).

**Qué significa para producción.** El umbral se aplicó como estaba
congelado y no se cambia. La lectura es que las probabilidades del modelo
pierden calibración de un mes a otro: hay que vigilar en producción la
precisión real de los contactados y la tasa de abandono de cada corte, y
reentrenar con el corte más reciente cuando haya etiqueta. Con el corte C
el modelo guardado se usa tal cual; este diagnóstico solo sirve para
interpretar el resultado.

El diagnóstico de esta sección es descriptivo: se calculó después de la
evaluación, sin volver a elegir umbral, modelo ni hiperparámetros.

Esta es la única evaluación del corte B. Después de verla no se cambió el
umbral, el modelo ni ningún hiperparámetro.
