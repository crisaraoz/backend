# Script para iniciar la aplicación FastAPI con procesamiento asíncrono
# Uso: ./start_with_worker.ps1

Write-Host "Iniciando la aplicación FastAPI..." -ForegroundColor Cyan
Write-Host "Esta versión utiliza un sistema de colas en memoria para Windows" -ForegroundColor Green
Write-Host "No se requiere Redis para esta implementación." -ForegroundColor Green

# Iniciar la aplicación FastAPI
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 