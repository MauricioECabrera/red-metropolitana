# Segmentación con KMeans y PCA (sección 2.3)

**Responsable:** Eduardo Hernández

## Datos y preparación

- Fuente: `features.features_corte`, corte A (2026-07-01), la tabla de
  Diego. No se lee Gold.
- Variables: las cinco del contrato (`viajes_28d`, `dias_desde_ultimo_viaje`,
  `gasto_28d_q`, `operadores_distintos_28d`, `abordajes_fin_semana_28d`).
- Todas pasan por `StandardScaler` antes de KMeans y antes de PCA. Sin
  escalar, `gasto_28d_q` (en quetzales) dominaría la distancia euclidiana
  sobre variables que van de 1 a 4.
- La etiqueta **no** entra al clustering. Se usa solo al final para la
  tasa de abandono por segmento.

Comando:

```
python -m scripts.segmentacion --corte A --k-max 10
```

## Elección de k

Se ajustó KMeans (`n_init=10`, `random_state=42`) para k = 2 a 10. Para
cada k se guardó la inercia y la silueta media (muestra de 10,000 unidades,
porque la silueta completa sobre ~60 mil filas es cuadrática).

Regla: el codo propone k y la silueta lo valida. El codo se ubica como el
punto de la curva de inercia más alejado de la recta entre k = 2 y k = 10.
Si la silueta de ese k es al menos 0.25 (estructura razonable) se usa ese
k; si no, el de mayor silueta.

No se usa directamente el máximo de silueta porque casi siempre cae en
k = 2, que solo separa "viaja mucho" de "viaja poco" y no alcanza para
diseñar acciones distintas.

*Pendiente con datos reales:*

| | Valor |
|---|---|
| k sugerido por el codo | |
| Silueta en ese k | |
| k de máxima silueta | |
| **k elegido** | |

Gráficas: `docs/segmentos/eleccion_k.png` (codo y silueta).

## Segmentos en dos componentes

Gráfica: `docs/segmentos/segmentos_pca.png`.
Cargas de cada variable: `docs/segmentos/cargas_pca.csv`.

| Componente | Varianza explicada |
|---|---:|
| 1 | |
| 2 | |
| Total | |

PCA se usa solo para visualizar; KMeans se ajusta sobre las cinco
variables escaladas, no sobre los dos componentes.

## Tabla de segmentos

*Pendiente: copiar de `docs/segmentos/tabla_segmentos.csv` y revisar el
nombre que propone el script contra las medianas.*

| Segmento | Nombre | Tamaño | Viajes 28d | Días desde último viaje | Gasto 28d (Q) | Operadores | Fin de semana | Tasa de abandono |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| | | | | | | | | |

**La tasa de abandono por segmento es descriptiva.** Muestra en qué grupo
se concentra el abandono, pero no prueba que pertenecer al segmento cause
que alguien deje la red: el segmento se construyó con las mismas
conductas (por ejemplo, días sin viajar) que ya anticipan el abandono.

## Acciones de retención

*Ajustar a los segmentos que salgan con los datos reales.*

| Segmento | Acción |
|---|---|
| Viajeros en enfriamiento (muchos días sin viajar) | Contacto directo en la primera semana sin viajes: recarga de bonificación con vigencia corta para reactivar la tarjeta. Es el segmento donde el umbral de 2.2 concentra los contactos. |
| Viajeros ocasionales | Sin incentivo de dinero: recordatorios de rutas y horarios cerca de su zona de abordaje, porque el costo de Q5 por contacto no se recupera en un grupo de baja tasa de abandono. |
| Viajeros frecuentes multimodales | Programa de lealtad con tarifa integrada entre operadores; se protegen porque son los de mayor gasto. |
| Viajeros de fin de semana | Promociones de fin de semana (paseos, eventos) en lugar de mensajes de horario laboral. |

## Uso del segmento como feature

No se usó. Si Adrián lo quisiera como feature del clasificador, KMeans
tendría que ajustarse dentro de cada fold (Pipeline con el escalado y
KMeans antes del clasificador); ajustarlo con todo el corte A y después
pasarlo como columna sería fuga.
