# Evidencia del CDC del padrón de usuarios

Entregable de la sección 1.2. Detalle de las decisiones en la bitácora, D-005 y D-010.

## Operaciones del log

| Operación | En el log | Aplicadas | En cuarentena |
|---|---|---|---|
| INSERT | 10,003 | 10,003 | 0 |
| UPDATE | 15,069 | 14,646 | 423 |
| DELETE | 3,772 | 3,633 | 139 |
| Llave SIN-TARJETA | 2,206 | 0 | 2,206 |
| **Total** | **31,050** | **28,282** | **2,768** |

## Tarjetas antes y después de aplicar los borrados

| | Personas |
|---|---|
| Activas aplicando solo INSERT y UPDATE | 19,824 |
| Activas aplicando las tres operaciones | 19,110 |
| Dadas de baja (INACTIVA) | 3,352 |
| De ellas, preexistentes cuyo único evento es la baja | 2,638 |

Ninguna baja borra un registro: las 3,352 personas inactivas siguen en
`silver.slv_padron_scd2` con su historial completo.

## Formato de llave de las personas del padrón

| Formato | Personas |
|---|---|
| Transmetro (TC-) | 17,432 |
| Transurbano (10 dígitos) | 4,038 |
| MetroRiel (MR) | 992 |

## Historial SCD Tipo 2

| Versiones por persona | Personas |
|---|---|
| 1 | 18,143 |
| 2 | 3,749 |
| 3 | 499 |
| 4 | 66 |
| 5 | 4 |
| 6 | 1 |
| **Total de versiones** | **27,428** |