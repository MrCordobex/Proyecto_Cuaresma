import pandas as pd
from pymongo import MongoClient

# --- CONFIGURACIÓN ---
# ⚠️ CAMBIA 'TU_CONTRASEÑA_AQUI' POR LA TUYA REAL
PASSWORD = "catequesiscuaresma2026"
URI = f"mongodb+srv://pedromarhuer03_db_user:{PASSWORD}@cluster0.ikalbov.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

try:
    # 1. Conectar a Mongo
    client = MongoClient(URI)
    db = client['catequesis_db']
    collection = db['usuarios']

    # 2. Leer el CSV
    df = pd.read_csv('catequesis_app - usuarios.csv')

    # 3. Limpieza de datos (Quitar espacios molestos)
    df.columns = df.columns.str.strip() # Limpia cabeceras
    
    # Renombrar a minúsculas para que coincida con la app
    df = df.rename(columns={'Grupo': 'grupo', 'Nombre': 'nombre', 'Password': 'password'})
    
    # Limpiar contenido
    df['grupo'] = df['grupo'].astype(str).str.strip()
    df['nombre'] = df['nombre'].astype(str).str.strip()
    df['password'] = "" # Asegurar que va vacía

    # 4. Convertir a diccionario y subir
    lista_usuarios = df.to_dict('records')
    
    # Borramos lo anterior por si lo ejecutas dos veces, para no duplicar
    collection.delete_many({}) 
    
    # Insertar
    collection.insert_many(lista_usuarios)
    
    print(f"✅ ¡ÉXITO! Se han subido {len(lista_usuarios)} usuarios a tu MongoDB.")
    print("Ya puedes borrar este archivo y lanzar la app.")

except Exception as e:
    print(f"❌ Error: {e}")