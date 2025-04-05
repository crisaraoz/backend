#!/bin/bash
# Script para iniciar la aplicación FastAPI con procesamiento asíncrono
# Uso: ./start_with_worker.sh

# Asegurar que el script tenga permisos de ejecución
if [ ! -x "$0" ]; then
    chmod +x "$0"
    echo "Se han añadido permisos de ejecución al script."
fi

echo -e "\e[36mIniciando la aplicación FastAPI...\e[0m"
echo -e "\e[32mEsta versión utiliza un sistema de colas en memoria\e[0m"
echo -e "\e[32mNo se requiere Redis para esta implementación.\e[0m"

# Iniciar la aplicación FastAPI
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 