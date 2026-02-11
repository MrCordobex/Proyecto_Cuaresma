import streamlit as st
import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import time
import certifi
from bson.objectid import ObjectId

# ==========================================
# 1. CONFIGURACIÓN Y CONEXIÓN
# ==========================================
st.set_page_config(page_title="Cuaresma GO", page_icon="✝️", layout="centered")

# ⚠️ TU CONTRASEÑA MAESTRA
MASTER_KEY = st.secrets["auth"]["master_key"]

# Leemos los secretos de la nube
try:
    USUARIO = st.secrets["mongo"]["user"]
    PASSWORD = st.secrets["mongo"]["password"]
    CLUSTER = st.secrets["mongo"]["cluster"]
except:
    st.error("No se detectan los 'secrets'. Si estás en local, asegúrate de tenerlos configurados.")
    st.stop()

MONGO_URI = f"mongodb+srv://{USUARIO}:{PASSWORD}@{CLUSTER}/?retryWrites=true&w=majority&appName=Cluster0"

@st.cache_resource
def init_connection():
    return MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)

try:
    client = init_connection()
    db = client['catequesis_db']
    client.admin.command('ping')
except Exception as e:
    st.error(f"Error conectando a la base de datos: {e}")
    st.stop()

# ==========================================
# 2. FUNCIONES DE GESTIÓN DE DATOS
# ==========================================

def get_data(collection_name):
    if collection_name == 'peticiones':
        return list(db[collection_name].find())
    return list(db[collection_name].find({}, {'_id': 0}))

def registrar_password(nombre, grupo, password):
    db.usuarios.update_one(
        {'nombre': nombre, 'grupo': grupo},
        {'$set': {'password': password}}
    )

def guardar_progreso(usuario, grupo, reflexion, titulo_reto):
    nuevo_dato = {
        "usuario": usuario,
        "grupo": grupo,
        "reto": titulo_reto, 
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "reflexion": reflexion,
        "hora": datetime.now().strftime("%H:%M:%S")
    }
    db.progreso.insert_one(nuevo_dato)

def guardar_peticion(usuario, grupo, texto, es_anonimo):
    nueva_peticion = {
        "usuario": usuario,
        "grupo": grupo,
        "texto": texto,
        "anonimo": es_anonimo,
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "hora": datetime.now().strftime("%H:%M:%S"),
        "orantes": [] 
    }
    db.peticiones.insert_one(nueva_peticion)

def toggle_oracion(id_peticion, usuario_actual):
    peticion = db.peticiones.find_one({'_id': ObjectId(id_peticion)})
    if peticion:
        lista_orantes = peticion.get('orantes', [])
        if usuario_actual in lista_orantes:
            db.peticiones.update_one({'_id': ObjectId(id_peticion)}, {'$pull': {'orantes': usuario_actual}})
        else:
            db.peticiones.update_one({'_id': ObjectId(id_peticion)}, {'$push': {'orantes': usuario_actual}})

# ==========================================
# 3. LÓGICA DE LA INTERFAZ (FRONTEND)
# ==========================================

if 'usuario' not in st.session_state: st.session_state['usuario'] = None
if 'grupo' not in st.session_state: st.session_state['grupo'] = None
if 'reset_mode' not in st.session_state: st.session_state['reset_mode'] = False

try:
    df_usuarios = pd.DataFrame(get_data('usuarios'))
    df_retos = pd.DataFrame(get_data('retos'))
    df_progreso = pd.DataFrame(get_data('progreso'))
except Exception as e:
    st.error("Error leyendo los datos. Revisa tu conexión a internet.")
    st.stop()

if 'reto' not in df_progreso.columns: df_progreso['reto'] = "" 
if 'password' not in df_usuarios.columns: df_usuarios['password'] = ""

# --- PANTALLA A: LOGIN ---
if not st.session_state['usuario']:
    st.title("✝️ Cuaresma GO")
    st.header("🔐 Acceso")

    if not df_usuarios.empty:
        lista_grupos = sorted(df_usuarios['grupo'].unique())
        grupo_sel = st.selectbox("Selecciona tu Grupo", [""] + lista_grupos)

        if grupo_sel:
            nombres = sorted(df_usuarios[df_usuarios['grupo'] == grupo_sel]['nombre'].tolist())
            nombre_sel = st.selectbox("¿Quién eres?", [""] + nombres)

            if nombre_sel:
                user_data = df_usuarios[(df_usuarios['nombre'] == nombre_sel) & (df_usuarios['grupo'] == grupo_sel)].iloc[0]
                pass_registrada = str(user_data['password'])
                es_nuevo = not pass_registrada or pass_registrada == "nan" or pass_registrada.strip() == ""

                if es_nuevo:
                    st.info("👋 Es tu primera vez. Crea tu clave:")
                    p1 = st.text_input("Nueva contraseña", type="password")
                    p2 = st.text_input("Repite contraseña", type="password")
                    if st.button("Registrar y Entrar"):
                        if p1 == p2 and len(p1) > 0:
                            registrar_password(nombre_sel, grupo_sel, p1)
                            st.success("¡Registrado!")
                            time.sleep(1)
                            st.session_state['usuario'] = nombre_sel; st.session_state['grupo'] = grupo_sel; st.rerun()
                        else:
                            st.error("Error en las contraseñas")
                elif st.session_state['reset_mode']:
                    st.warning(f"🛠️ MODO RECUPERACIÓN para: {nombre_sel}")
                    st.write("Introduce tu nueva contraseña personal:")
                    new_p1 = st.text_input("Nueva contraseña", type="password", key="new1")
                    new_p2 = st.text_input("Repítela", type="password", key="new2")
                    if st.button("Guardar Nueva Clave"):
                        if new_p1 == new_p2 and len(new_p1) > 0:
                            registrar_password(nombre_sel, grupo_sel, new_p1)
                            st.success("¡Contraseña cambiada!")
                            time.sleep(1)
                            st.session_state['usuario'] = nombre_sel; st.session_state['grupo'] = grupo_sel; st.session_state['reset_mode'] = False; st.rerun()
                        else:
                            st.error("Las contraseñas no coinciden.")
                    if st.button("Cancelar"):
                        st.session_state['reset_mode'] = False; st.rerun()
                else:
                    st.write(f"Hola **{nombre_sel}**, pon tu clave:")
                    p_input = st.text_input("Contraseña", type="password")
                    if st.button("Entrar"):
                        if p_input == pass_registrada:
                            st.session_state['usuario'] = nombre_sel; st.session_state['grupo'] = grupo_sel; st.rerun()
                        elif p_input == MASTER_KEY:
                            st.session_state['reset_mode'] = True; st.rerun()
                        else:
                            st.error("Contraseña incorrecta")
                            with st.expander("¿Se te ha olvidado la contraseña?"):
                                st.write("Habla con tu catequista o con Pedro.")
                                st.markdown("📞 **Pedro: 662 236 309**")
                                st.info("Pídeles la 'Clave Maestra' para resetear.")

# --- PANTALLA B: DENTRO DE LA APP ---
else:
    with st.sidebar:
        st.write(f"👤 **{st.session_state['usuario']}**")
        st.caption(f"🛡️ {st.session_state['grupo']}")
        st.divider()
        
        # MENU DE NAVEGACIÓN
        menu = st.radio("Ir a:", ["🏠 Reto de Hoy", "🙏 Muro de Peticiones", "📹 Historial"])
        
        st.divider()
        
        # --- ℹ️ INSTRUCCIONES DINÁMICAS (NUEVO) ---
        st.subheader("ℹ️ Instrucciones")
        
        if menu == "🏠 Reto de Hoy":
            st.info(
                """
                1. 👁️ **Mira** el vídeo del reto atentamente.
                2. 🔑 Encuentra la **clave** escondida...
                3. ✍️ Escribe tu **reflexión** sobre cómo has hecho el reto y qué has sentido.
                4. 🚀 ¡Envía y suma puntos para tu grupo!
                """
            )
        elif menu == "🙏 Muro de Peticiones":
            st.info(
                """
                ✍️ **Escribe** por quién quieres rezar.
                ❤️ Pulsa el corazón para rezar por un compañero.
                """
            )
        elif menu == "📹 Historial":
             st.info(
                """
                🔙 Recupera retos antiguos.
                📊 Mira la participación global.
                """
            )
        # ------------------------------------------
        
        st.divider()
        if st.button("Cerrar Sesión"):
            st.session_state['usuario'] = None
            st.rerun()

    hoy = datetime.now().strftime("%Y-%m-%d")

    # 1. RETO DE HOY
    if menu == "🏠 Reto de Hoy":
        retos_activos = df_retos[df_retos['fecha'] <= hoy]
        reto_actual = None
        if not retos_activos.empty:
            reto_actual = retos_activos.sort_values(by='fecha', ascending=False).iloc[0]

        ya_hecho = False
        if not df_progreso.empty and reto_actual is not None:
            check = df_progreso[(df_progreso['usuario'] == st.session_state['usuario']) & (df_progreso['reto'] == reto_actual['titulo'])]
            if not check.empty: ya_hecho = True

        if reto_actual is not None:
            # Cuenta atrás
            df_retos['fecha_dt'] = pd.to_datetime(df_retos['fecha'])
            hoy_dt = pd.to_datetime(datetime.now().strftime("%Y-%m-%d"))
            futuros = df_retos[df_retos['fecha_dt'] > hoy_dt].sort_values('fecha_dt')
            
            if not futuros.empty:
                siguiente = futuros.iloc[0]
                dias_restantes = (siguiente['fecha_dt'] - hoy_dt).days
                if dias_restantes == 1: st.warning(f"⏳ **¡Atención!** Queda **1 día** para el siguiente reto.")
                else: st.info(f"⏳ Tienes **{dias_restantes} días** para completar este reto.")
            else:
                st.success("🏁 ¡Recta final! No quedan más retos.")

            st.caption(f"📅 Publicado: {reto_actual['fecha']}")
            st.title(reto_actual['titulo'])
            if 'grupo_proponente' in reto_actual: st.markdown(f"📢 **Propone:** {reto_actual['grupo_proponente']} | **Pilar:** {reto_actual.get('pilar', '')}")
            if 'cita' in reto_actual: st.info(f"📖 {reto_actual['cita']}")
            
            st.video(f"https://youtu.be/{reto_actual['youtube_id']}")
            
            if not ya_hecho:
                st.divider(); st.subheader("🎯 Tu Misión")
                with st.form("formulario_reto"):
                    clave_input = st.text_input("🔑 Clave del vídeo:")
                    reflexion = st.text_area("✍️ Reflexión: ¿Has conseguido hacer el reto? ¿Qué has sentido?")
                    enviado = st.form_submit_button("🚀 ENVIAR RESPUESTA")
                    if enviado:
                        clave_ok = clave_input.upper().strip() == str(reto_actual['pass_video']).upper().strip()
                        largo_ok = len(reflexion) > 150
                        if not clave_ok: st.error("❌ Clave incorrecta.")
                        elif not largo_ok: st.warning("⚠️ Escribe un poco más... Seguro que puedes!!!")
                        else:
                            guardar_progreso(st.session_state['usuario'], st.session_state['grupo'], reflexion, reto_actual['titulo'])
                            st.balloons(); st.success("¡Enviado!"); time.sleep(2); st.rerun()
            else:
                st.success("✅ ¡Reto completado!")
        else:
            st.warning("⏳ Esperando el inicio de la Cuaresma.")

        st.divider()
        st.subheader("🏆 Carrera hacia la Pascua")
        if not df_usuarios.empty:
            todos_los_grupos = sorted(df_usuarios['grupo'].unique())
            total_retos_cuaresma = len(df_retos) if not df_retos.empty else 1
            ranking_data = []
            for grupo in todos_los_grupos:
                usuarios_del_grupo = df_usuarios[df_usuarios['grupo'] == grupo]
                activos = usuarios_del_grupo[usuarios_del_grupo['password'].astype(str).replace('nan', '').str.strip() != ""]
                n_activos = len(activos)
                puntos_totales = 0
                if not df_progreso.empty:
                    progreso_grupo = df_progreso[df_progreso['grupo'] == grupo]
                    if 'reto' in progreso_grupo.columns and not progreso_grupo.empty:
                         completados_unicos = progreso_grupo[['usuario', 'reto']].drop_duplicates()
                         puntos_totales = len(completados_unicos)
                porcentaje = int((puntos_totales / (n_activos * total_retos_cuaresma)) * 100) if n_activos > 0 else 0
                ranking_data.append({'Grupo': grupo, 'Porcentaje': min(porcentaje, 100), 'Activos': n_activos})
            df_rank = pd.DataFrame(ranking_data).sort_values('Porcentaje', ascending=False)
            for i, row in df_rank.iterrows():
                col1, col2 = st.columns([2, 3])
                col1.write(f"**{row['Grupo']}**"); col2.progress(row['Porcentaje'] / 100); col2.caption(f"{row['Porcentaje']}%")
                st.write("---")

    # 2. MURO DE PETICIONES
    elif menu == "🙏 Muro de Peticiones":
        st.title("🕊️ Muro de Oración")
        st.write("Escribe tus intenciones para que J1 rece por ti.")

        with st.expander("✍️ Escribir nueva petición", expanded=False):
            with st.form("form_peticion"):
                texto_peticion = st.text_area("¿Por qué o quién quieres que recemos?", max_chars=140, placeholder="Por mi abuelo que está enfermo...")
                es_anonimo = st.checkbox("Publicar como Anónimo")
                enviar_peticion = st.form_submit_button("Publicar Petición")
                if enviar_peticion:
                    if len(texto_peticion) > 5:
                        guardar_peticion(st.session_state['usuario'], st.session_state['grupo'], texto_peticion, es_anonimo)
                        st.success("Tu petición ha sido publicada."); time.sleep(1); st.rerun()
                    else:
                        st.warning("Escribe algo más largo.")
        st.divider()

        lista_peticiones = list(db.peticiones.find().sort([("fecha", -1), ("hora", -1)]))
        if not lista_peticiones:
            st.info("Aún no hay peticiones. ¡Sé el primero!")
        else:
            for peticion in lista_peticiones:
                with st.container(border=True):
                    col_texto, col_boton = st.columns([4, 1])
                    with col_texto:
                        st.markdown(f"### {peticion['texto']}")
                        if peticion.get('anonimo'): autor = "Anónimo"
                        else: autor = f"{peticion['usuario']} ({peticion['grupo']})"
                        st.caption(f"📝 {autor}  |  📅 {peticion['fecha']}")
                    with col_boton:
                        orantes = peticion.get('orantes', [])
                        num_orantes = len(orantes)
                        usuario_actual = st.session_state['usuario']
                        ya_rezado = usuario_actual in orantes
                        if ya_rezado: label = f"❤️ {num_orantes}"; tipo = "primary"
                        else: label = f"🤍 {num_orantes}"; tipo = "secondary"
                        if st.button(label, key=str(peticion['_id']), type=tipo):
                            toggle_oracion(peticion['_id'], usuario_actual); st.rerun()
                    if ya_rezado: st.caption("🙏 Ya estás rezando por esto.")

    # 3. HISTORIAL
    elif menu == "📹 Historial":
        st.header("📜 Historial de Retos")
        historial = df_retos[df_retos['fecha'] <= hoy]
        usuarios_registrados = df_usuarios[df_usuarios['password'].astype(str).replace('nan', '').str.strip() != ""]
        total_registrados = len(usuarios_registrados)

        if not historial.empty:
            historial = historial.sort_values(by='fecha', ascending=False)
            for index, reto in historial.iterrows():
                with st.container():
                    st.subheader(f"{reto['fecha']} - {reto['titulo']}")
                    if 'grupo_proponente' in reto: st.markdown(f"**Propuesto por:** {reto['grupo_proponente']}")
                    st.video(f"https://youtu.be/{reto['youtube_id']}")
                    participacion_pct = 0; num_hechos = 0
                    if not df_progreso.empty and total_registrados > 0:
                        hechos = df_progreso[df_progreso['reto'] == reto['titulo']]
                        num_hechos = len(hechos['usuario'].unique())
                        participacion_pct = int((num_hechos / total_registrados) * 100)
                    st.write(f"📊 Participación global:"); st.progress(min(participacion_pct / 100, 1.0))
                    st.caption(f"**{participacion_pct}%** ({num_hechos} de {total_registrados} personas)"); st.divider()
        else:
            st.info("Aún no se han publicado retos.")