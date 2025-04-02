# Script para iniciar el proxy local para DashScope en Windows
Write-Host "Iniciando proxy local para DashScope en puerto 8010..." -ForegroundColor Green

# Verifica si local-cors-proxy está instalado
if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
    Write-Host "Error: npx no está instalado. Por favor, instala Node.js y npm." -ForegroundColor Red
    exit 1
}

# Inicia el proxy
Write-Host "Ejecutando proxy para DashScope..." -ForegroundColor Yellow
npx local-cors-proxy --proxyUrl https://dashscope-intl.aliyuncs.com --port 8010 --proxyPartial ""

Write-Host "Proxy iniciado en http://localhost:8010" -ForegroundColor Green 