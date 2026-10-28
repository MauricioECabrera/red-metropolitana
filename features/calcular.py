"""
Proyecto 2 - Red Metropolitana de Transporte
Autor: Diego de Jesus Urbina Chavez
"""
import argparse
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fecha-corte', required=True)
    args = parser.parse_args()

    cmd = [
        "powershell", "-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\dbt.ps1", "build",
        "--select", "poblacion", "features_corte",
        "--vars", f'{{"fecha_corte": "{args.fecha_corte}"}}'
    ]
    
    print(f"Calculando features para el corte: {args.fecha_corte}")
    resultado = subprocess.run(cmd)
    sys.exit(resultado.returncode)

if __name__ == '__main__':
    main()