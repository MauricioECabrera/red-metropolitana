{#
=====================================================================
  usuarios_metroriel  ·  Catalogo minimo de usuarios de MetroRiel
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  MetroRiel no entrega padron de usuarios. Este catalogo contiene
  unicamente las llaves distintas que aparecen en su archivo de
  operacion: sin nombre, sin fecha de alta, sin ningun atributo,
  porque el operador nunca entrego esa informacion.
=====================================================================
#}

select distinct
    payload->>'$.card' as tarjeta
from {{ ref('brz_metroriel_viajes') }}
where payload->>'$.card' is not null