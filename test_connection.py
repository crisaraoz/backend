from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

def test_connection():
    load_dotenv()
    
    # Obtener las credenciales del archivo .env
    DB_USER = os.getenv("POSTGRES_USER")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    DB_HOST = os.getenv("POSTGRES_SERVER")
    DB_NAME = os.getenv("POSTGRES_DB")
    
    # Crear la URL de conexión
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
    
    try:
        # Crear el engine
        engine = create_engine(DATABASE_URL)
        
        # Intentar conectar y ejecutar una consulta simple
        with engine.connect() as connection:
            result = connection.execute(text("SELECT current_timestamp"))
            timestamp = result.scalar()
            print("¡Conexión exitosa!")
            print(f"Timestamp del servidor: {timestamp}")
            
            # Intentar consultar las tablas
            result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            print("\nTablas en la base de datos:")
            for row in result:
                print(f"- {row[0]}")
                
    except Exception as e:
        print("Error al conectar a la base de datos:")
        print(str(e))

if __name__ == "__main__":
    test_connection() 