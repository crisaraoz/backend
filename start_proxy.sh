#!/bin/bash

# Script para iniciar el proxy local para DashScope
echo "Iniciando proxy local para DashScope en puerto 8010..."

# Si estás en Windows, instala local-cors-proxy con npm si no lo tienes
# npm install -g local-cors-proxy

# Inicia el proxy
npx local-cors-proxy --proxyUrl https://dashscope-intl.aliyuncs.com --port 8010 --proxyPartial ""

echo "Proxy iniciado en http://localhost:8010" 