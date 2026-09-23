/*
Proyecto 1 - Red Metropolitana de Transporte
Autor: Diego de Jesus Urbina Chavez
*/
with bronze as (
    select count(*) as filas from {{ ref('brz_transmetro_validaciones') }}
),
silver as (
    select count(*) as filas from {{ ref('slv_tm_abordajes') }}
),
cuarentena as (
    select count(*) as filas from {{ ref('tm_cuarentena') }}
)
select *
from bronze b, silver s, cuarentena c
where b.filas != (s.filas + c.filas)