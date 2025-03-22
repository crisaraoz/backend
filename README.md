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

4. **Configurar la base de datos**
   
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

### Endpoints Disponibles

#### Columnas (Columns)
- `GET /api/v1/columns` - Obtener todas las columnas
  ```bash
  curl http://localhost:8000/api/v1/columns
  ```

- `POST /api/v1/columns` - Crear una nueva columna
  ```bash
  curl -X POST http://localhost:8000/api/v1/columns \
    -H "Content-Type: application/json" \
    -d '{"title": "Nueva Columna", "order": 1}'
  ```

#### Tareas (Tasks)
- `GET /api/v1/tasks` - Obtener todas las tareas
  ```bash
  curl http://localhost:8000/api/v1/tasks
  ```

- `GET /api/v1/tasks?column_id={id}` - Obtener tareas de una columna específica
  ```bash
  curl http://localhost:8000/api/v1/tasks?column_id=1
  ```

- `POST /api/v1/tasks` - Crear una nueva tarea
  ```bash
  curl -X POST http://localhost:8000/api/v1/tasks \
    -H "Content-Type: application/json" \
    -d '{
      "title": "Nueva Tarea",
      "description": "Descripción de la tarea",
      "column_id": 1,
      "order": 0
    }'
  ```

- `PUT /api/v1/tasks/{task_id}` - Actualizar una tarea
  ```bash
  curl -X PUT http://localhost:8000/api/v1/tasks/1 \
    -H "Content-Type: application/json" \
    -d '{
      "title": "Tarea Actualizada",
      "description": "Nueva descripción",
      "column_id": 1,
      "completed": true
    }'
  ```

- `DELETE /api/v1/tasks/{task_id}` - Eliminar una tarea
  ```bash
  curl -X DELETE http://localhost:8000/api/v1/tasks/1
  ```

#### Etiquetas (Labels)
- `GET /api/v1/labels` - Obtener todas las etiquetas
  ```bash
  curl http://localhost:8000/api/v1/labels
  ```

- `GET /api/v1/tasks/{task_id}/labels` - Obtener etiquetas de una tarea
  ```bash
  curl http://localhost:8000/api/v1/tasks/1/labels
  ```

## Probar la API con Swagger UI

1. Abre http://localhost:8000/docs en tu navegador
2. Verás una interfaz interactiva con todos los endpoints disponibles
3. Para probar un endpoint:
   - Haz clic en el endpoint que quieras probar
   - Haz clic en "Try it out"
   - Completa los parámetros necesarios
   - Haz clic en "Execute"
   - Verás la respuesta del servidor

## Estructura del Proyecto

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   │   ├── __init__.py
│   │   └── kanban.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints/
│   │       ├── __init__.py
│   │       └── kanban.py
│   └── models/
│       ├── __init__.py
│       ├── base.py
│       └── kanban.py
├── requirements.txt
└── README.md
```

## Solución de Problemas

1. **Error de conexión a la base de datos**
   - Verifica que PostgreSQL esté corriendo
   - Confirma que la base de datos "kanban" existe
   - Revisa las credenciales en `app/core/config.py`

2. **Error al crear las tablas**
   - Asegúrate de que no existan las tablas previamente
   - Si es necesario, elimina y vuelve a crear la base de datos

3. **Error al ejecutar el servidor**
   - Verifica que el entorno virtual esté activado
   - Confirma que todas las dependencias están instaladas
   - Revisa los logs para más detalles 