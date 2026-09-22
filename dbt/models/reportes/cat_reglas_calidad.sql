{#
=====================================================================
  cat_reglas_calidad  ·  Catalogo de reglas de calidad de la red
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Una fila por regla declarada, por fuente y por proceso. El catalogo
  se declara completo aunque una regla nunca llegue a dispararse: una
  regla con cero rechazos es un resultado, no una regla que falta.

  El orden es la precedencia con que se evalua la regla dentro de su
  proceso. Una fila toma el motivo de la PRIMERA regla que falla, por
  eso el orden cambia el reparto entre motivos, nunca el total.

  Al integrarse una fuente nueva se agrega su bloque aqui y en
  rpt_calidad. Decision D-009 de la bitacora.
=====================================================================
#}

select
    cast(orden as integer) as orden,
    fuente,
    proceso,
    regla,
    descripcion
from (
    values
        ('transmetro',  'abordaje',    1,  'identificador_invalido',   'validacion_id no se puede convertir a entero'),
        ('transmetro',  'abordaje',    2,  'duplicado',                'Segunda aparicion o posterior del mismo validacion_id. El torniquete duplica lecturas'),
        ('transmetro',  'abordaje',    3,  'tarjeta_invalida',         'La tarjeta no cumple el patron TC mas ocho digitos'),
        ('transmetro',  'abordaje',    4,  'fecha_invalida',           'La marca de tiempo no se puede interpretar'),
        ('transmetro',  'abordaje',    5,  'fecha_futura',             'La marca de tiempo es posterior a la ingesta del lote'),
        ('transmetro',  'abordaje',    6,  'estacion_desconocida',     'La estacion no existe en dim_estacion_parada'),
        ('transmetro',  'abordaje',    7,  'monto_invalido',           'Monto nulo o negativo. Cero es valido, es la tarifa del adulto mayor'),

        ('transurbano', 'transaccion', 1,  'duplicado',                'Segunda aparicion o posterior de una transaccion identica'),
        ('transurbano', 'transaccion', 2,  'tarjeta_invalida',         'El numero de tarjeta no cumple el patron de diez digitos'),
        ('transurbano', 'transaccion', 3,  'fecha_invalida',           'La fecha y la hora, que llegan en columnas separadas, no arman una marca de tiempo valida'),
        ('transurbano', 'transaccion', 4,  'fecha_futura',             'La marca de tiempo es posterior a la ingesta del lote. Reloj mal configurado en la unidad'),
        ('transurbano', 'transaccion', 5,  'estacion_desconocida',     'El codigo de parada viene vacio o no existe en dim_estacion_parada'),
        ('transurbano', 'transaccion', 6,  'monto_invalido',           'Monto nulo o negativo despues de convertir de centavos a quetzales'),

        ('metroriel',   'abordaje',    1,  'identificador_invalido',   'trip_id no se puede convertir a entero'),
        ('metroriel',   'abordaje',    2,  'duplicado',                'Segunda aparicion o posterior del mismo trip_id'),
        ('metroriel',   'abordaje',    3,  'tarjeta_invalida',         'La tarjeta no cumple el patron MR mas siete digitos'),
        ('metroriel',   'abordaje',    4,  'fecha_invalida',           'La marca de tiempo de entrada no se puede interpretar'),
        ('metroriel',   'abordaje',    5,  'fecha_futura',             'La entrada es posterior a la ingesta del lote'),
        ('metroriel',   'abordaje',    6,  'estacion_desconocida',     'La estacion de entrada no existe en dim_estacion_parada'),
        ('metroriel',   'abordaje',    7,  'monto_invalido',           'Tarifa nula o negativa'),

        ('metroriel',   'trayecto',    1,  'viaje_sin_salida',         'El viaje no registra salida. El pasajero no valido al salir'),
        ('metroriel',   'trayecto',    2,  'fecha_invalida',           'La marca de tiempo de salida no se puede interpretar'),
        ('metroriel',   'trayecto',    3,  'salida_anterior_a_entrada','La salida ocurre antes que la entrada'),
        ('metroriel',   'trayecto',    4,  'estacion_desconocida',     'La estacion de salida no existe en dim_estacion_parada'),
        ('metroriel',   'trayecto',    5,  'origen_igual_destino',     'La estacion de salida es la misma que la de entrada'),

        ('aerometro',   'abordaje',    1,  'identificador_invalido',   'boarding_id no se puede convertir a entero'),
        ('aerometro',   'abordaje',    2,  'duplicado',                'Segunda aparicion o posterior del mismo boarding_id'),
        ('aerometro',   'abordaje',    3,  'tarjeta_invalida',         'El hash de usuario no cumple el patron de doce caracteres hexadecimales'),
        ('aerometro',   'abordaje',    4,  'fecha_invalida',           'La marca de tiempo no se puede interpretar despues de convertir de UTC a hora local'),
        ('aerometro',   'abordaje',    5,  'fecha_futura',             'La marca de tiempo es posterior a la ingesta del lote'),
        ('aerometro',   'abordaje',    6,  'estacion_desconocida',     'La torre no existe en dim_estacion_parada'),
        ('aerometro',   'abordaje',    7,  'monto_invalido',           'Tarifa nula o negativa'),

        ('cdc_padron',  'padron',      1,  'secuencia_invalida',       'El numero de secuencia del log no se puede convertir a entero. Sin secuencia no hay orden de aplicacion'),
        ('cdc_padron',  'padron',      2,  'duplicado',                'Segunda aparicion o posterior del mismo numero de secuencia'),
        ('cdc_padron',  'padron',      3,  'llave_centinela',          'La tarjeta trae el valor SIN-TARJETA. No identifica a ninguna persona y colapsaria todos esos eventos en un solo registro. Decision D-005'),
        ('cdc_padron',  'padron',      4,  'tarjeta_invalida',         'La tarjeta no corresponde a ninguno de los tres formatos del padron, ni Transmetro ni Transurbano ni MetroRiel'),
        ('cdc_padron',  'padron',      5,  'operacion_invalida',       'La operacion no es INSERT, UPDATE ni DELETE'),
        ('cdc_padron',  'padron',      6,  'fecha_invalida',           'La marca de tiempo del commit no se puede interpretar'),
        ('cdc_padron',  'padron',      7,  'fecha_futura',             'El commit es posterior a la ingesta del lote'),
        ('cdc_padron',  'padron',      8,  'perfil_invalido',          'El perfil no es estudiante, trabajador, adulto_mayor ni general. No aplica a los DELETE, que llegan sin cuerpo'),
        ('cdc_padron',  'padron',      9,  'zona_desconocida',         'La zona de residencia no resuelve contra dim_zona. No aplica a los DELETE'),
        ('cdc_padron',  'padron',      10, 'actualizacion_sobre_baja', 'Llega un UPDATE sobre una tarjeta cuya ultima operacion fue DELETE. Actualizar una baja reviviria la tarjeta'),
        ('cdc_padron',  'padron',      11, 'baja_repetida',            'Llega un DELETE sobre una tarjeta que ya estaba dada de baja')
) as t(fuente, proceso, orden, regla, descripcion)
