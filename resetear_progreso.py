from pymongo import MongoClient

PASSWORD = "catequesiscuaresma2026"
MONGO_URI = f"mongodb+srv://pedromarhuer03_db_user:{PASSWORD}@cluster0.ikalbov.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(MONGO_URI)
db = client['catequesis_db']
db.progreso.delete_many({})
print("✅ Progreso reseteado. Base de datos limpia.")