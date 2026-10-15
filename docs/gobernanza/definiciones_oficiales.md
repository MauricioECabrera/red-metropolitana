# Definiciones de negocio y responsables propuestos

Estas definiciones fijan cómo interpretar los indicadores publicados.
Los responsables indicados son una propuesta del equipo y deben confirmarse
antes de presentarlos como dueños institucionales de los datos.

## ¿Qué cuenta como un viaje?

**Viaje registrado para comparar los cuatro modos:** una validación exitosa
de entrada, representada por un abordaje en `gold.fct_abordaje`. Se mide con
`SUM(cantidad_abordajes)`. Un transbordo que genera otra validación cuenta
como otro abordaje. No representa necesariamente un desplazamiento completo
desde el origen hasta el destino final de una persona.

**Trayecto completo con origen y destino:** una entrada y una salida válidas
de MetroRiel, representadas en `gold.fct_trayecto_od` y medidas con
`SUM(cantidad_trayectos)`. No se suman los trayectos a los abordajes de la red:
la entrada de cada trayecto MetroRiel ya está incluida en los abordajes.
Los 3,589 registros sin salida cuentan como abordaje, pero no como trayecto
completo.

**Dueño propuesto de la definición:** Adrián, como responsable de gobernanza
e indicadores. **Validación técnica:** Mauricio, responsable del grano Gold,
con Diego y Eduardo para las reglas de sus respectivos operadores.

## ¿Qué cuenta como un usuario activo?

**Definición propuesta:** una persona se considera activa en un período de
análisis si tiene al menos un abordaje exitoso dentro de ese período. Se
calcula con `COUNT(DISTINCT persona_sk)` sobre `gold.fct_abordaje`, aplicando
el mismo filtro de fechas a todas las comparaciones. Siempre debe mostrarse
el período utilizado; por ejemplo, «personas activas del 1 al 30 de junio».

No equivale a una **tarjeta activa del padrón**: esa es la condición
administrativa registrada al cierre de un día en
`gold.fct_estado_padron_diario`. Una persona puede tener tarjeta activa y
no haber abordado, o abordar sin figurar en el padrón. Aerómetro no se puede
vincular con los otros modos; por eso el total de personas únicas de toda
la red puede estar sobreestimado.

**Dueño propuesto de la definición:** Adrián, como responsable de gobernanza
e indicadores. **Validación técnica:** Mauricio, responsable de identidad,
padrón y seudonimización.

## Responsables propuestos por dominio y dimensión conformada

| Dominio | Dimensión Gold | Responsable propuesto | Decisiones que debe validar |
|---|---|---|---|
| Calendario | `dim_fecha` | Mauricio | Fecha local, día hábil y calendario usado. |
| Tiempo operativo | `dim_hora` | Mauricio | Hora local y definición de franja pico. |
| Geografía y cobertura | `dim_zona` | Eduardo | Catálogo de zonas, alias y criterio de cobertura. |
| Puntos de acceso | `dim_estacion` | Eduardo | Códigos de estaciones/paradas, ubicación y zona asignada. |
| Operadores | `dim_modo` | Diego | Código, nombre y significado del registro de cada modo. |
| Identidad y padrón | `dim_persona` | Mauricio | Vinculación entre fuentes, CDC, SCD2 y seudonimización. |

Adrián mantiene el diccionario y verifica que el tablero use estas
definiciones. Asignar un responsable a una dimensión significa que esa
persona revisa cambios en su significado, llaves y fuente; no implica que
sea la única persona que pueda editar su código.
