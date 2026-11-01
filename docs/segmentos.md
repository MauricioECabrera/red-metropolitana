# Segmentación con KMeans y PCA (sección 2.3)

**Responsable:** Eduardo Hernández

## Datos y preparación

- Fuente: `features.features_corte`, corte A (2026-07-01), 59,515 unidades.
  Es la tabla de Diego, que sale de Silver; no se lee Gold.
- Variables: las cinco del contrato (`viajes_28d`, `dias_desde_ultimo_viaje`,
  `gasto_28d_q`, `operadores_distintos_28d`, `abordajes_fin_semana_28d`).
- Todas pasan por `StandardScaler` antes de KMeans y antes de PCA. Sin
  escalar, `gasto_28d_q` (en quetzales) dominaría la distancia euclidiana
  sobre variables que van de 1 a 4.
- La etiqueta **no** entra al clustering. Se usa solo al final para la
  tasa de abandono por segmento.
- Solo se usa el corte A. El corte B no participa en ningún paso.

Comando:

```
python -m scripts.segmentacion --corte A --k-max 10
```

## Elección de k

Se ajustó KMeans (`n_init=10`, `random_state=42`) para k = 2 a 10. Para
cada k se guardó la inercia y la silueta media (muestra de 10,000 unidades,
porque la silueta completa sobre casi 60 mil filas es cuadrática).

| k | Inercia | Silueta |
|---:|---:|---:|
| 2 | 206,738 | 0.5435 |
| 3 | 159,241 | 0.3475 |
| 4 | 120,493 | 0.3915 |
| **5** | **96,969** | **0.4072** |
| 6 | 87,002 | 0.4033 |
| 7 | 78,449 | 0.3927 |
| 8 | 72,705 | 0.4059 |
| 9 | 67,434 | 0.3329 |
| 10 | 62,194 | 0.3467 |

**k elegido: 5.**

- **Codo:** la inercia cae fuerte hasta k = 5 (−23,524 de 4 a 5) y desde
  ahí las caídas son menores (−9,967 de 5 a 6, −8,553 de 6 a 7). El punto
  más alejado de la recta entre k = 2 y k = 10 es k = 5.
- **Silueta:** fuera de k = 2, el máximo es k = 5 (0.4072), por encima de
  k = 6 y k = 8. Una silueta mayor a 0.25 indica estructura razonable.
- **Por qué no k = 2**, aunque tenga la silueta más alta (0.5435): separa
  solo a 5,550 usuarios muy activos (mediana de 53 viajes, abandono 2.1 %)
  de los otros 53,965 (abandono 12.9 %). El grupo que más abandona queda
  escondido dentro del grupo grande, y con dos segmentos no se pueden
  diseñar acciones distintas para quien se está yendo y para quien
  simplemente viaja poco.

Regla en el script: el codo propone k y la silueta lo valida (≥ 0.25); si
no la cumple, se usa el k de mayor silueta.

Gráficas: `docs/segmentos/eleccion_k.png` (codo y silueta).

## Segmentos en dos componentes

Gráfica: `docs/segmentos/segmentos_pca.png`.

| Componente | Varianza explicada |
|---|---:|
| 1 | 55.18 % |
| 2 | 19.63 % |
| **Total** | **74.81 %** |

Cargas (`docs/segmentos/cargas_pca.csv`):

| Variable | Componente 1 | Componente 2 |
|---|---:|---:|
| viajes_28d | 0.571 | −0.135 |
| dias_desde_ultimo_viaje | −0.253 | −0.474 |
| gasto_28d_q | 0.534 | −0.206 |
| operadores_distintos_28d | 0.180 | 0.831 |
| abordajes_fin_semana_28d | 0.540 | −0.153 |

El componente 1 es **intensidad de uso** (viajes, gasto y fin de semana
cargan casi igual). El componente 2 es **multimodalidad**: sube con los
operadores distintos y baja con los días sin viajar. Por eso en la gráfica
los segmentos multimodales quedan arriba y los que están en enfriamiento
abajo a la izquierda. Las franjas diagonales salen de que
`operadores_distintos_28d` solo toma valores enteros de 1 a 4.

PCA se usa solo para visualizar; KMeans se ajusta sobre las cinco
variables escaladas, no sobre los dos componentes.

## Tabla de segmentos

Medianas del corte A (referencia de toda la población: 10 viajes, 3 días
desde el último viaje, Q14.70, 1 abordaje en fin de semana).

| Seg. | Nombre | Tamaño | % | Viajes 28d | Días desde último viaje | Gasto 28d (Q) | Operadores | Fin de semana | Tasa de abandono |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | Viajeros regulares | 26,128 | 43.9 | 8 | 2 | 13.00 | 1 | 1 | 0.0867 |
| 1 | Viajeros intensivos multimodales | 795 | 1.3 | 116 | 1 | 207.40 | 2 | 16 | 0.0252 |
| 2 | Viajeros regulares multimodales | 17,498 | 29.4 | 12 | 2 | 17.60 | 2 | 2 | 0.0618 |
| 3 | Viajeros frecuentes multimodales | 6,030 | 10.1 | 45 | 1 | 74.90 | 2 | 7 | 0.0227 |
| 4 | Viajeros en enfriamiento | 9,064 | 15.2 | 4 | 16 | 6.90 | 1 | 0 | 0.3965 |

El segmento 4 concentra el abandono: es el 15.2 % de la población, pero
3,594 de sus 9,064 unidades abandonan (0.3965), es decir, el 50.6 % de los
7,098 positivos del corte A. Su mediana de 16 días sin viajar ya es más de
la mitad de la ventana de 28 días.

**La tasa de abandono por segmento es descriptiva.** Muestra en qué grupo
se concentra el abandono, pero no prueba que pertenecer al segmento cause
que alguien deje la red: el segmento se construyó con las mismas
conductas (sobre todo los días sin viajar) que ya anticipan el abandono.

Archivos: `docs/segmentos/tabla_segmentos.csv` y la asignación de cada
unidad en `docs/segmentos/asignacion_segmentos_A.csv`.

## Acciones de retención

| Segmento | Acción |
|---|---|
| 4 · En enfriamiento | Contacto directo con recarga de cortesía de vigencia corta (por ejemplo, 7 días) para reactivar la tarjeta. Es donde se concentran los contactos del umbral de 2.2, porque es el único segmento con tasa de abandono por encima de 1/3 en promedio. |
| 0 · Regulares | Sin incentivo de dinero: mensajes de servicio (cambios de ruta, horarios, nuevas paradas en su zona). Con 8.7 % de abandono, la recarga de Q5 no se recupera si se manda a todo el segmento; solo se contacta a quien el modelo ponga sobre el umbral. |
| 2 · Regulares multimodales | Promoción de transbordo: descuento al combinar dos operadores en el mismo día, para reforzar el hábito que ya tienen. |
| 1 y 3 · Intensivos y frecuentes multimodales | No reciben campaña de retención (2.5 % y 2.3 % de abandono). Se cuidan con un programa de lealtad o tarifa mensual integrada, porque son los de mayor gasto por usuario. |

## Uso del segmento como feature

No se usó. Si se quisiera usar como feature del clasificador, KMeans
tendría que ajustarse dentro de cada fold (Pipeline con el escalado y
KMeans antes del clasificador); ajustarlo con todo el corte A y después
pasarlo como columna sería fuga.
