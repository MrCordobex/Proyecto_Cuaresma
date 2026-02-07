from pymongo import MongoClient
import pandas as pd

# ⚠️ PON TU CONTRASEÑA AQUÍ
PASSWORD = "catequesiscuaresma2026"
URI = f"mongodb+srv://pedromarhuer03_db_user:{PASSWORD}@cluster0.ikalbov.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# TU CALENDARIO EXACTO
lista_retos = [
    {
        "fecha": "2026-02-07",
        "grupo_proponente": "Candela y Pedro",
        "pilar": "🍖 Ayuno",
        "titulo": "Prueba",
        "cita": "Jueves de Ceniza - Inicio",
        "youtube_id": "_23p44TdBsc", 
        "pass_video": "Prueba"
    },
    {
        "fecha": "2026-02-19",
        "grupo_proponente": "Candela y Pedro",
        "pilar": "🍖 Ayuno",
        "titulo": "Semana 1: El desierto comienza",
        "cita": "Jueves de Ceniza - Inicio",
        "youtube_id": "dQw4w9WgXcQ", 
        "pass_video": "AYUNO"
    },
    {
        "fecha": "2026-02-23",
        "grupo_proponente": "Carmen y Javi (Atalaya)",
        "pilar": "🙏 Oración",
        "titulo": "Semana 2: Hablar con Él",
        "cita": "Lunes II de Cuaresma",
        "youtube_id": "dQw4w9WgXcQ", 
        "pass_video": "ORACION"
    },
    {
        "fecha": "2026-02-26",
        "grupo_proponente": "Crislo y Durán",
        "pilar": "❤️ Limosna",
        "titulo": "Semana 2: Darse a los demás",
        "cita": "Jueves II de Cuaresma",
        "youtube_id": "dQw4w9WgXcQ", 
        "pass_video": "LIMOSNA"
    },
    {
        "fecha": "2026-03-02",
        "grupo_proponente": "Laura y Alberto",
        "pilar": "🍖 Ayuno",
        "titulo": "Semana 3: Menos yo, más Él",
        "cita": "Lunes III de Cuaresma",
        "youtube_id": "dQw4w9WgXcQ", 
        "pass_video": "AYUNO"
    },
    {
        "fecha": "2026-03-05",
        "grupo_proponente": "Ana y Manu",
        "pilar": "🙏 Oración",
        "titulo": "Semana 3: El silencio",
        "cita": "Jueves III de Cuaresma",
        "youtube_id": "dQw4w9WgXcQ", 
        "pass_video": "ORACION"
    },
    {
        "fecha": "2026-03-09",
        "grupo_proponente": "Elena y Antonio",
        "pilar": "❤️ Limosna",
        "titulo": "Semana 4: Corazón abierto",
        "cita": "Lunes IV de Cuaresma",
        "youtube_id": "dQw4w9WgXcQ", 
        "pass_video": "LIMOSNA"
    },
    {
        "fecha": "2026-03-12",
        "grupo_proponente": "Ana y Fernando",
        "pilar": "🍖 Ayuno",
        "titulo": "Semana 4: Preparando el camino",
        "cita": "Jueves IV de Cuaresma",
        "youtube_id": "dQw4w9WgXcQ", 
        "pass_video": "AYUNO"
    },
    {
        "fecha": "2026-03-16",
        "grupo_proponente": "Teruca y Juan",
        "pilar": "🙏 Oración",
        "titulo": "Semana 5: Cierre del camino",
        "cita": "Lunes V de Cuaresma",
        "youtube_id": "dQw4w9WgXcQ", 
        "pass_video": "CIERRE"
    }
]

try:
    client = MongoClient(URI)
    db = client['catequesis_db']
    
    # Borramos y subimos
    db.retos.delete_many({})
    db.retos.insert_many(lista_retos)
    
    print(f"✅ ¡Calendario subido! {len(lista_retos)} retos programados.")

except Exception as e:
    print(f"❌ Error: {e}")