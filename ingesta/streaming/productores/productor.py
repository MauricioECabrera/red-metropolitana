"""
Proyecto 1 - Red Metropolitana de Transporte
Autor: Diego de Jesus Urbina Chavez
"""
import os
import csv
from datetime import datetime
from dotenv import load_dotenv
from confluent_kafka import Producer
from ingesta.comun.bronze import huella_archivo

def main():
    load_dotenv()
    
    conf = {
        'bootstrap.servers': os.environ['KAFKA_BOOTSTRAP_SERVERS'],
        'enable.idempotence': True,
        'linger.ms': 50
    }
    productor = Producer(conf)
    
    ruta_registro = os.path.join('lake', 'bronze', '_control', 'publicaciones.csv')
    registro = set()
    if os.path.exists(ruta_registro):
        with open(ruta_registro, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                registro.add((row['topico'], row['huella']))
                
    archivos_a_procesar = [
        (os.environ['KAFKA_TOPIC_TRANSMETRO'], os.path.join('datos_red', 'transmetro_validaciones.csv')),
        (os.environ['KAFKA_TOPIC_AEROMETRO'], os.path.join('datos_red', 'aerometro_boardings.csv'))
    ]
    
    resumen = []
    
    for topico, ruta_archivo in archivos_a_procesar:
        huella = huella_archivo(ruta_archivo)
        
        if (topico, huella) in registro:
            resumen.append((topico, ruta_archivo, 0, 'OMITIDO'))
            continue
            
        mensajes_publicados = 0
        ejecucion_ts = datetime.now().isoformat()
        
        with open(ruta_archivo, 'r', newline='', encoding='utf-8') as f:
            next(f)
            for linea in f:
                linea_limpia = linea.rstrip('\r\n')
                llave = linea_limpia.split(',')[0]
                
                while True:
                    try:
                        productor.produce(
                            topic=topico,
                            key=llave.encode('utf-8'),
                            value=linea_limpia.encode('utf-8')
                        )
                        productor.poll(0)
                        break
                    except BufferError:
                        productor.poll(1)
                        
                mensajes_publicados += 1
        
        productor.flush()
        
        existe_registro = os.path.exists(ruta_registro)
        os.makedirs(os.path.dirname(ruta_registro), exist_ok=True)
        with open(ruta_registro, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            if not existe_registro:
                writer.writerow(['ejecucion_ts', 'topico', 'archivo', 'huella', 'mensajes'])
            writer.writerow([ejecucion_ts, topico, ruta_archivo, huella, mensajes_publicados])
            
        resumen.append((topico, ruta_archivo, mensajes_publicados, 'PUBLICADO'))
        
    print(f"{'Tópico':<30} | {'Archivo':<40} | {'Mensajes':<10} | {'Acción'}")
    print("-" * 95)
    for t, a, m, ac in resumen:
        print(f"{t:<30} | {a:<40} | {m:<10} | {ac}")

if __name__ == '__main__':
    main()