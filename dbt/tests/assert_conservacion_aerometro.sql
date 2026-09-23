/*
Proyecto 1 - Red Metropolitana de Transporte
Autor: Diego de Jesus Urbina Chavez
*/
with bronze as (
    select count(*) as filas from {{ ref('brz_aerometro_boardings') }}
),
silver as (
    select count(*) as filas from {{ ref('slv_am_abordajes') }}
),
cuarentena as (
    select count(*) as filas from {{ ref('am_cuarentena') }}
)
select *
from bronze b, silver s, cuarentena c
where b.filas != (s.filas + c.filas)