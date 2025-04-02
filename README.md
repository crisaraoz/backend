# Kanban Board Backend

Este es el backend para la aplicación Kanban Board, construido con FastAPI y PostgreSQL.

## Requisitos Previos

- Python 3.8 o superior
- PostgreSQL
- pip (gestor de paquetes de Python)

## Configuración del Entorno

1. **Clonar el repositorio**
   ```bash
   git clone <url-del-repositorio>
   cd backend
   ```

2. **Crear un entorno virtual**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar las variables de entorno**

   Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

   ```
   # Configuración de la base de datos
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/kanban

   # API de Qwen
   QWEN_API_KEY=tu_clave_api_aquí
   
   # Entorno de desarrollo (proxy local)
   QWEN_API_URL=http://localhost:8010/api/v1/services/aigc/text-generation/generation
   
   # Para producción, comentar la línea anterior y descomentar esta:
   # QWEN_API_URL=https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/text-generation/generation
   ```

5. **Configuración del proxy para desarrollo local**

   Para desarrollo local, es necesario ejecutar un proxy CORS para comunicarse con la API de Qwen:

   ```bash
   # Instalar el proxy
   npm install -g local-cors-proxy

   # Ejecutar el proxy (en una terminal separada)
   npx local-cors-proxy --proxyUrl https://dashscope-intl.aliyuncs.com --port 8010 --proxyPartial ""
   ```

   También puedes usar los scripts incluidos:
   ```bash
   # En Linux/Mac
   ./start_proxy.sh

   # En Windows
   .\start_proxy.ps1
   ```

6. **Configurar la base de datos**
   
   Asegúrate de tener PostgreSQL instalado y corriendo. Luego crea una base de datos:
   ```sql
   CREATE DATABASE kanban;
   ```

   La configuración por defecto asume:
   - Usuario: postgres
   - Contraseña: postgres
   - Host: localhost
   - Puerto: 5432
   - Base de datos: kanban

   Si necesitas modificar estos valores, puedes hacerlo en `app/core/config.py`

## Ejecutar el Proyecto

1. **Activar el entorno virtual (si no está activado)**
   ```bash
   # Windows
   .\venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

2. **Iniciar el servidor**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

   El servidor estará disponible en http://localhost:8000

## Documentación de la API

La documentación interactiva está disponible en dos formatos:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Probar la API con Swagger UI

1. Abre http://localhost:8000/docs en tu navegador
2. Verás una interfaz interactiva con todos los endpoints disponibles
3. Para probar un endpoint:
   - Haz clic en el endpoint que quieras probar
   - Haz clic en "Try it out"
   - Completa los parámetros necesarios
   - Haz clic en "Execute"
   - Verás la respuesta del servidor
