{#
=====================================================================
  dim_modo  ·  Dimension conformada de modo de transporte
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
  Autor: Miguel Eduardo Cabrera Giron
=====================================================================
#}

select
    cast(modo_key as integer) as modo_key,
    modo_codigo,
    modo_nombre,
    unidad_registro,
    formato_origen
from (
    values
        (1, 'TM', 'Transmetro',  'abordaje', 'CSV'),
        (2, 'TU', 'Transurbano', 'abordaje', 'CSV'),
        (3, 'MR', 'MetroRiel',   'trayecto', 'JSON Lines'),
        (4, 'AM', 'Aerometro',   'abordaje', 'CSV')
) as t(modo_key, modo_codigo, modo_nombre, unidad_registro, formato_origen)