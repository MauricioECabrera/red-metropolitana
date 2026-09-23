"""
Proyecto 1 - Red Metropolitana de Transporte
Autor: Diego de Jesus Urbina Chavez
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from confluent_kafka import Consumer
from ingesta.comun.bronze import cargar, STAGING, imprimir_resumen, lector_csv

def procesar_fuente(fuente, topico, nombre_archivo):
    conf = {
        'bootstrap.servers': os.environ['KAFKA_BOOTSTRAP_SERVERS'],
        'group.id': os.environ['KAFKA_CONSUMER_GROUP'],
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False
    }
    
    consumidor = Consumer(conf)
    consumidor.subscribe([topico])
    
    mensajes = []
    
    # Leer mensajes hasta que pasen 15 segundos seguidos sin nada nuevo
    while True:
        msg = consumidor.poll(timeout=15.0)
        if msg is None:
            break
        if msg.error():
            break
        mensajes.append(msg.value().decode('utf-8'))
        
    if not mensajes:
        print(f"sin mensajes nuevos para la fuente {fuente}")
        consumidor.close()
        return None

    # Si llegaron mensajes, preparar el archivo en staging
    ruta_staging_dir = STAGING / fuente
    ruta_staging_dir.mkdir(parents=True, exist_ok=True)
    ruta_staging_archivo = ruta_staging_dir / nombre_archivo
    ruta_original = Path('datos_red') / nombre_archivo
    
    # Leer el encabezado exacto del archivo original
    with open(ruta_original, 'r', encoding='utf-8') as f_orig:
        encabezado = f_orig.readline()
        
    # Escribir el encabezado y los mensajes en staging con saltos de línea (\n)
    with open(ruta_staging_archivo, 'w', newline='\n', encoding='utf-8') as f_out:
        f_out.write(encabezado)
        for m in mensajes:
            f_out.write(m + '\n')
            
    # Cargar a Bronze usando la función de la librería del proyecto
    resultado = cargar(fuente, nombre_archivo, lector_csv, directorio=ruta_staging_dir)
        
    # Confirmar offsets en Kafka y borrar el archivo de staging solo si cargó bien
    consumidor.commit(asynchronous=False)
    ruta_staging_archivo.unlink()
    consumidor.close()
    
    return resultado

def main():
    load_dotenv()
    
    fuentes_a_procesar = [
        ('transmetro_validaciones', os.environ['KAFKA_TOPIC_TRANSMETRO'], 'transmetro_validaciones.csv'),
        ('aerometro_boardings', os.environ['KAFKA_TOPIC_AEROMETRO'], 'aerometro_boardings.csv')
    ]
    
    resultados = []
    for fuente, topico, nombre_archivo in fuentes_a_procesar:
        res = procesar_fuente(fuente, topico, nombre_archivo)
        if res:
            resultados.append(res)
            
    if resultados:
        imprimir_resumen(resultados)

if __name__ == '__main__':
    main()