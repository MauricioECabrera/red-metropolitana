# Segmentación con KMeans y PCA (sección 2.3)

**Responsable:** Eduardo Hernández

## Datos y preparación

- Fuente: `features.features_corte`, corte A (2026-07-01), 59,515 unidades.
  Es la tabla de Diego, que sale de Silver; no se lee Gold.
- Variables: las diez del contrato v2, leídas de
  `scripts/modelos/variables.py` (la misma lista que usan los modelos de
  Adrián): `viajes_28d`, `dias_desde_ultimo_viaje`, `gasto_28d_q`,
  `operadores_distintos_28d`, `abordajes_fin_semana_28d`, `viajes_7d`,
  `dias_activos_28d`, `gasto_promedio_viaje_q`, `proporcion_hora_pico_28d`
  y `tendencia_viajes_14d`.
- Todas pasan por `StandardScaler` antes de KMeans y antes de PCA. Sin
  escalar, `gasto_28d_q` (en quetzales) dominaría la distancia euclidiana
  sobre variables que van de 0 a 1 (como la proporción en hora pico) o de 1 a 4.
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

| k | Inercia | Caída desde k − 1 | Silueta |
|---:|---:|---:|---:|
| 2 | 451,062 | | 0.3838 |
| 3 | 391,500 | −59,562 | 0.1958 |
| 4 | 348,350 | −43,150 | 0.1992 |
| 5 | 312,488 | −35,863 | 0.2113 |
| **6** | **284,070** | **−28,418** | **0.2151** |
| 7 | 265,106 | −18,963 | 0.2132 |
| 8 | 249,955 | −15,151 | 0.2109 |
| 9 | 236,944 | −13,012 | 0.2165 |
| 10 | 227,174 | −9,770 | 0.2214 |

**k elegido: 6** (con las cinco variables de la versión anterior era 5).

- **Codo:** la inercia cae entre 28 y 60 mil por cada k hasta k = 6 y
  después las caídas bajan a 19 mil o menos. El punto más alejado de la
  recta entre k = 2 y k = 10 es k = 6.
- **Silueta:** fuera de k = 2, la silueta es casi plana (0.1958 a 0.2214)
  y no distingue un k sobre otro; k = 6 (0.2151) es el máximo local entre
  3 y 8. Queda por debajo de 0.25: con diez variables los grupos se
  traslapan más que con cinco (la silueta de k = 5 bajó de 0.4072 a
  0.2113). Se reporta como una limitación: los segmentos sirven para
  describir y priorizar, no son grupos completamente separados.
- **Por qué no k = 2**, aunque tenga la silueta más alta (0.3838): separa
  solo a 9,487 usuarios muy activos (mediana de 40 viajes, abandono 1.8 %)
  de los otros 50,028 (abandono 13.85 %). El grupo que más abandona queda
  escondido dentro del 84 % de la población y no se pueden diseñar
  acciones distintas para quien se está yendo y para quien viaja poco.

Regla en el script: el codo elige k y la silueta se reporta como control.
Si la silueta del codo queda por debajo de 0.25 el script lo avisa, pero
no cae a k = 2 por el motivo anterior. Con las cinco variables esta regla
también daba k = 5, el mismo de la versión anterior.

Gráficas: `docs/segmentos/eleccion_k.png` (codo y silueta).

## Segmentos en dos componentes

Gráfica: `docs/segmentos/segmentos_pca.png`.

| Componente | Varianza explicada |
|---|---:|
| 1 | 42.10 % |
| 2 | 13.08 % |
| **Total** | **55.18 %** |

Cargas (`docs/segmentos/cargas_pca.csv`):

| Variable | Componente 1 | Componente 2 |
|---|---:|---:|
| viajes_28d | 0.461 | −0.143 |
| dias_desde_ultimo_viaje | −0.228 | −0.474 |
| gasto_28d_q | 0.414 | −0.252 |
| operadores_distintos_28d | 0.138 | 0.173 |
| abordajes_fin_semana_28d | 0.423 | −0.199 |
| viajes_7d | 0.432 | 0.188 |
| dias_activos_28d | 0.417 | −0.015 |
| gasto_promedio_viaje_q | −0.021 | −0.320 |
| proporcion_hora_pico_28d | −0.034 | 0.150 |
| tendencia_viajes_14d | 0.067 | 0.679 |

El componente 1 es **intensidad de uso** (viajes, viajes de la última
semana, días activos, gasto y fin de semana cargan casi igual). El
componente 2 es **tendencia reciente**: sube cuando la persona viaja más
en las últimas dos semanas que en las dos anteriores y baja con los días
sin viajar y con el gasto por viaje. Por eso los viajeros en enfriamiento
quedan abajo a la izquierda y los intensivos se estiran hacia la derecha.
Con diez variables, dos componentes explican el 55.18 % de la varianza
(antes 74.81 % con cinco), así que en la gráfica los segmentos del centro
se ven encimados aunque en las diez dimensiones estén separados.

PCA se usa solo para visualizar; KMeans se ajusta sobre las diez
variables escaladas, no sobre los dos componentes.

## Tabla de segmentos

Medianas del corte A. Referencia de toda la población: 10 viajes, 3 días
desde el último viaje, Q14.70, 1 operador, 1 abordaje en fin de semana,
2 viajes en 7 días, 7 días activos, Q1.30 por viaje, 0.625 en hora pico y
tendencia 0.

| Seg. | Nombre | Tamaño | % | Viajes 28d | Días desde último | Gasto 28d (Q) | Operadores | Fin de semana | Viajes 7d | Días activos | Q por viaje | Hora pico | Tendencia 14d | Tasa de abandono |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | Viajeros regulares | 15,832 | 26.6 | 8 | 2 | 8.00 | 1 | 1 | 2 | 6 | 1.30 | 0.667 | 1 | 0.0916 |
| 1 | Viajeros frecuentes multimodales | 8,286 | 13.9 | 38 | 1 | 55.90 | 2 | 5 | 10 | 18 | 1.30 | 0.591 | 1 | 0.0181 |
| 2 | Viajeros ocasionales de tarifa alta | 10,532 | 17.7 | 6 | 3 | 21.00 | 1 | 1 | 2 | 5 | 3.50 | 0.643 | 0 | 0.1106 |
| 3 | Viajeros intensivos multimodales | 1,128 | 1.9 | 102 | 1 | 177.90 | 2 | 14 | 27 | 25 | 1.43 | 0.513 | 2 | 0.0177 |
| 4 | Viajeros en enfriamiento | 8,062 | 13.5 | 4 | 17 | 6.00 | 1 | 0 | 0 | 3 | 1.30 | 0.600 | −3 | 0.4092 |
| 5 | Viajeros regulares multimodales | 15,675 | 26.3 | 11 | 2 | 16.00 | 2 | 1 | 3 | 8 | 1.38 | 0.667 | 1 | 0.0647 |

El segmento 4 concentra el abandono: es el 13.5 % de la población, pero
unas 3,299 de sus 8,062 unidades abandonan (0.4092), es decir, el 46.5 %
de los 7,098 positivos del corte A. Su mediana de 17 días sin viajar ya
es más de la mitad de la ventana de 28 días, no viajó en la última semana
y su tendencia es −3 viajes entre quincenas.

El segmento 2 es nuevo respecto a la versión de cinco variables: aparece
gracias a `gasto_promedio_viaje_q`. Paga Q3.50 por viaje, casi el triple
de la mediana, y el 78.0 % de sus abordajes del periodo son de Aerómetro
(el resto, 22.0 %, de MetroRiel). Es el segundo con más abandono
(0.1106).

**La tasa de abandono por segmento es descriptiva.** Muestra en qué grupo
se concentra el abandono, pero no prueba que pertenecer al segmento cause
que alguien deje la red: el segmento se construyó con las mismas
conductas (sobre todo los días sin viajar y la tendencia) que ya anticipan
el abandono.

Archivos: `docs/segmentos/tabla_segmentos.csv` y la asignación de cada
unidad en `docs/segmentos/asignacion_segmentos_A.csv`.

## Acciones de retención

| Segmento | Acción |
|---|---|
| 4 · En enfriamiento | Contacto directo con recarga de cortesía de vigencia corta (por ejemplo, 7 días) para reactivar la tarjeta. Es donde se concentran los contactos del umbral de 2.2, porque es el único segmento con tasa de abandono por encima de 1/3 en promedio. |
| 2 · Ocasionales de tarifa alta (Aerómetro) | Paquete de viajes con descuento en Aerómetro o tarifa combinada Aerómetro + MetroRiel. El precio por viaje es lo que los distingue, así que la acción ataca el costo y no la frecuencia. Solo se contacta a quien el modelo ponga sobre el umbral. |
| 0 · Regulares | Sin incentivo de dinero: mensajes de servicio (cambios de ruta, horarios, nuevas paradas en su zona). Con 9.2 % de abandono, una recarga para todo el segmento no se recupera. |
| 5 · Regulares multimodales | Promoción de transbordo: descuento al combinar dos operadores en el mismo día, para reforzar el hábito que ya tienen. |
| 1 y 3 · Frecuentes e intensivos multimodales | No reciben campaña de retención (1.8 % de abandono). Se cuidan con un programa de lealtad o tarifa mensual integrada, porque son los de mayor gasto por usuario. |

## Uso del segmento como feature

No se usó. Si se quisiera usar como feature del clasificador, KMeans
tendría que ajustarse dentro de cada fold (Pipeline con el escalado y
KMeans antes del clasificador); ajustarlo con todo el corte A y después
pasarlo como columna sería fuga.
