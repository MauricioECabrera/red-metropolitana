{#
=====================================================================
  usuarios_transurbano  ·  Catalogo minimo de usuarios de Transurbano
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Transurbano no entrega padron de usuarios. Este catalogo contiene
  unicamente las llaves distintas que aparecen en su archivo de
  operacion: sin nombre, sin fecha de alta, sin ningun atributo,
  porque el operador nunca entrego esa informacion.
=====================================================================
#}

select distinct
    num_tarjeta as tarjeta
from {{ ref('brz_transurbano_transacciones') }}
where num_tarjeta is not null