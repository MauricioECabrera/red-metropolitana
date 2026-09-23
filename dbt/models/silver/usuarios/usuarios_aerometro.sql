{#
=====================================================================
  usuarios_aerometro  ·  Catalogo minimo de usuarios de Aerometro
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Aerometro no entrega padron de usuarios. Este catalogo contiene
  unicamente los hashes distintos que aparecen en su archivo de
  operacion: sin nombre, sin fecha de alta, sin ningun atributo,
  porque el operador nunca entrego esa informacion.
=====================================================================
#}

select distinct
    user_hash as tarjeta
from {{ ref('brz_aerometro_boardings') }}
where user_hash is not null