# Matriz del bus

Procesos de negocio contra dimensiones conformadas. Una X indica que el hecho
se relaciona con la dimensión. Todas las dimensiones son compartidas: la misma
tabla, la misma llave y el mismo dueño para todos los procesos.

| Proceso | Hecho | Grano | Fecha | Hora | Zona | Modo | Estación | Persona |
|---|---|---|---|---|---|---|---|---|
| Abordaje | `fct_abordaje` | una validación exitosa de entrada | X | X | X | X | X | X |
| Trayecto origen-destino | `fct_trayecto_od` | un trayecto de MetroRiel con entrada y salida | X | X | X (origen y destino) | fijo MR | X (origen y destino) | X |
| Estado del padrón | `fct_estado_padron_diario` | una persona del padrón por día | X | | X (residencia) | | | X |

## Dimensiones conformadas

| Dimensión | Modelo Gold | Dueño | Fuente |
|---|---|---|---|
| Fecha | `gold.dim_fecha` | A | generada |
| Hora | `gold.dim_hora` | A | generada |
| Zona | `gold.dim_zona` | A | `seed_dim_zona`, `seed_zona_alias` y catálogos |
| Modo | `gold.dim_modo` | A | definida en el modelo |
| Estación | `gold.dim_estacion` | A | los cuatro catálogos de estaciones y paradas |
| Persona | `gold.dim_persona` | A | abordajes de todas las fuentes y el padrón SCD Tipo 2, bitácora D-002, D-007 y D-011 |

## Dimensiones de rol

`fct_trayecto_od` usa Zona y Estación dos veces, como origen y como destino.
Es la misma dimensión física con dos llaves foráneas.