/*
Proyecto 1 - Red Metropolitana de Transporte
Autor: Diego de Jesus Urbina Chavez
*/

select *
from {{ source('lake', 'transmetro_validaciones') }}