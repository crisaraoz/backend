#!/usr/bin/env python
"""
Script para cambiar rápidamente entre configuraciones de desarrollo y producción.
Modifica el archivo .env para usar la URL de API apropiada.
"""

import os
import re
from pathlib import Path

# Definiciones de URLs
DEV_URL = "http://localhost:8010/api/v1/services/aigc/text-generation/generation"
PROD_URL = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

def switch_environment(env_type):
    """Cambia el entorno modificando el archivo .env"""
    env_file = Path(__file__).parent / ".env"
    
    if not env_file.exists():
        print(f"Error: No se encontró el archivo .env en {env_file.absolute()}")
        return
    
    # Leer el contenido actual
    with open(env_file, "r") as f:
        content = f.read()
    
    # Definir los patrones y reemplazos
    if env_type == "dev":
        # Pasar a modo desarrollo (URL local)
        print("Configurando para entorno de DESARROLLO...")
        new_content = re.sub(
            r"#?\s*QWEN_API_URL=.*",
            f"QWEN_API_URL={DEV_URL}",
            content
        )
        # Comentar la URL de producción si existe
        new_content = re.sub(
            r"(QWEN_API_URL={})".format(PROD_URL),
            r"# \1",
            new_content
        )
    elif env_type == "prod":
        # Pasar a modo producción (URL de DashScope)
        print("Configurando para entorno de PRODUCCIÓN...")
        new_content = re.sub(
            r"#?\s*QWEN_API_URL=.*",
            f"QWEN_API_URL={PROD_URL}",
            content
        )
        # Comentar la URL de desarrollo si existe
        new_content = re.sub(
            r"(QWEN_API_URL={})".format(DEV_URL),
            r"# \1",
            new_content
        )
    else:
        print(f"Error: Tipo de entorno '{env_type}' no reconocido. Use 'dev' o 'prod'.")
        return
    
    # Escribir las modificaciones al archivo
    with open(env_file, "w") as f:
        f.write(new_content)
    
    print(f"Configuración actualizada exitosamente para entorno: {env_type.upper()}")
    print(f"URL de la API: {DEV_URL if env_type == 'dev' else PROD_URL}")
    
    if env_type == "dev":
        print("\nRecuerda ejecutar el proxy local con: npx local-cors-proxy --proxyUrl https://dashscope-intl.aliyuncs.com --port 8010 --proxyPartial \"\"")
        print("O usa el script start_proxy.sh/ps1 incluido.")
    
    print("\nReinicia el servidor para aplicar los cambios.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2 or sys.argv[1] not in ["dev", "prod"]:
        print("Uso: python switch_environment.py [dev|prod]")
        print("  dev: Configura para desarrollo local (usando proxy)")
        print("  prod: Configura para producción (conexión directa a DashScope)")
        sys.exit(1)
    
    switch_environment(sys.argv[1]) 