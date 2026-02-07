import streamlit as st
import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import time
import certifi

# ==========================================
# 1. CONFIGURACIÓN Y CONEXIÓN
# ==========================================
st.set_page_config(page_title="Cuaresma GO", page_icon="✝️", layout="centered")

# ⚠️ TU CONTRASEÑA MAESTRA PARA RESETEAR CUENTAS
MASTER_KEY = "MeQuieroConfirmarA+B=C"

# Leemos los secretos de la nube
try:
    USUARIO = st.secrets["mongo"]["user"]
    PASSWORD = st.secrets["mongo"]["password"]
    CLUSTER = st.secrets["mongo"]["cluster"]
except:
    # Por si lo ejecutas en local sin secretos, para que no falle (opcional)
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

# ==========================================
# 3. LÓGICA DE LA INTERFAZ (FRONTEND)
# ==========================================

if 'usuario' not in st.session_state: st.session_state['usuario'] = None
if 'grupo' not in st.session_state: st.session_state['grupo'] = None
if 'reset_mode' not in st.session_state: st.session_state['reset_mode'] = False

# Cargar datos
try:
    df_usuarios = pd.DataFrame(get_data('usuarios'))
    df_retos = pd.DataFrame(get_data('retos'))
    df_progreso = pd.DataFrame(get_data('progreso'))
except Exception as e:
    st.error("Error leyendo los datos. Revisa tu conexión a internet.")
    st.stop()

# --- PARCHE DE SEGURIDAD ---
if 'reto' not in df_progreso.columns:
    df_progreso['reto'] = "" 
if 'password' not in df_usuarios.columns:
    df_usuarios['password'] = ""

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

                # CASO 1: USUARIO NUEVO (REGISTRO)
                if es_nuevo:
                    st.info("👋 Es tu primera vez. Crea tu clave:")
                    p1 = st.text_input("Nueva contraseña", type="password")
                    p2 = st.text_input("Repite contraseña", type="password")

                    if st.button("Registrar y Entrar"):
                        if p1 == p2 and len(p1) > 0:
                            registrar_password(nombre_sel, grupo_sel, p1)
                            st.success("¡Registrado!")
                            time.sleep(1)
                            st.session_state['usuario'] = nombre_sel
                            st.session_state['grupo'] = grupo_sel
                            st.rerun()
                        else:
                            st.error("Error en las contraseñas")
                
                # CASO 2: MODO RECUPERACIÓN (SI HA METIDO LA CLAVE MAESTRA ANTES)
                elif st.session_state['reset_mode']:
                    st.warning(f"🛠️ MODO RECUPERACIÓN para: {nombre_sel}")
                    st.write("Introduce tu nueva contraseña personal:")
                    
                    new_p1 = st.text_input("Nueva contraseña", type="password", key="new1")
                    new_p2 = st.text_input("Repítela", type="password", key="new2")
                    
                    if st.button("Guardar Nueva Clave"):
                        if new_p1 == new_p2 and len(new_p1) > 0:
                            registrar_password(nombre_sel, grupo_sel, new_p1)
                            st.success("¡Contraseña cambiada con éxito!")
                            time.sleep(1)
                            st.session_state['usuario'] = nombre_sel
                            st.session_state['grupo'] = grupo_sel
                            st.session_state['reset_mode'] = False # Quitamos el modo reset
                            st.rerun()
                        else:
                            st.error("Las contraseñas no coinciden.")
                    
                    if st.button("Cancelar"):
                        st.session_state['reset_mode'] = False
                        st.rerun()

                # CASO 3: LOGIN NORMAL
                else:
                    st.write(f"Hola **{nombre_sel}**, pon tu clave:")
                    p_input = st.text_input("Contraseña", type="password")
                    
                    if st.button("Entrar"):
                        # A) Contraseña Correcta
                        if p_input == pass_registrada:
                            st.session_state['usuario'] = nombre_sel
                            st.session_state['grupo'] = grupo_sel
                            st.rerun()
                        
                        # B) Contraseña Maestra (Activa modo reset)
                        elif p_input == MASTER_KEY:
                            st.session_state['reset_mode'] = True
                            st.rerun()
                        
                        # C) Contraseña Incorrecta
                        else:
                            st.error("Contraseña incorrecta")
                            # Aquí mostramos el desplegable de ayuda
                            with st.expander("¿Se te ha olvidado la contraseña?"):
                                st.write("Si quieres recuperar la contraseña, habla con tu catequista o con Pedro.")
                                st.markdown("📞 **Pedro: 662 236 309**")
                                st.info("Pídeles la 'Clave Maestra' para poder cambiar tu contraseña aquí mismo.")

# --- PANTALLA B: DENTRO DE LA APP (LOGUEADO) ---
else:
    # --- BARRA LATERAL (MENU) ---
    with st.sidebar:
        st.write(f"👤 **{st.session_state['usuario']}**")
        st.caption(f"🛡️ {st.session_state['grupo']}")
        
        st.divider()
        menu = st.radio("Ir a:", ["🏠 Reto de Hoy", "📹 Historial"])
        st.divider()
        
        if st.button("Cerrar Sesión"):
            st.session_state['usuario'] = None
            st.rerun()

    hoy = datetime.now().strftime("%Y-%m-%d")

    # ==========================================
    # OPCIÓN 1: PANTALLA PRINCIPAL (RETO DE HOY)
    # ==========================================
    if menu == "🏠 Reto de Hoy":
        
        retos_activos = df_retos[df_retos['fecha'] <= hoy]
        reto_actual = None
        if not retos_activos.empty:
            reto_actual = retos_activos.sort_values(by='fecha', ascending=False).iloc[0]

        ya_hecho = False
        if not df_progreso.empty and reto_actual is not None:
            check = df_progreso[
                (df_progreso['usuario'] == st.session_state['usuario']) & 
                (df_progreso['reto'] == reto_actual['titulo'])
            ]
            if not check.empty:
                ya_hecho = True

        if reto_actual is not None:
            st.caption(f"📅 Publicado: {reto_actual['fecha']}")
            st.title(reto_actual['titulo'])
            
            if 'grupo_proponente' in reto_actual:
                st.markdown(f"📢 **Propone:** {reto_actual['grupo_proponente']} | **Pilar:** {reto_actual.get('pilar', '')}")
            
            if 'cita' in reto_actual:
                st.info(f"📖 {reto_actual['cita']}")
            
            st.video(f"https://youtu.be/{reto_actual['youtube_id']}")
            
            if not ya_hecho:
                st.divider()
                st.subheader("🎯 Tu Misión")

                with st.form("formulario_reto"):
                    clave_input = st.text_input("🔑 Clave del vídeo:")
                    reflexion = st.text_area("✍️ Reflexión (+50 caracteres):")
                    enviado = st.form_submit_button("🚀 ENVIAR RESPUESTA")
                    
                    if enviado:
                        clave_ok = clave_input.upper().strip() == str(reto_actual['pass_video']).upper().strip()
                        largo_ok = len(reflexion) > 50
                        
                        if not clave_ok:
                            st.error("❌ Clave incorrecta.")
                        elif not largo_ok:
                            st.warning(f"⚠️ Escribe un poco más.")
                        else:
                            guardar_progreso(
                                st.session_state['usuario'], 
                                st.session_state['grupo'], 
                                reflexion,
                                reto_actual['titulo']
                            )
                            st.balloons()
                            st.success("¡Enviado!")
                            time.sleep(2)
                            st.rerun()
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
                activos = usuarios_del_grupo[
                    usuarios_del_grupo['password'].astype(str).replace('nan', '').str.strip() != ""
                ]
                n_activos = len(activos)
                
                puntos_totales = 0
                if not df_progreso.empty:
                    progreso_grupo = df_progreso[df_progreso['grupo'] == grupo]
                    if 'reto' in progreso_grupo.columns and not progreso_grupo.empty:
                         completados_unicos = progreso_grupo[['usuario', 'reto']].drop_duplicates()
                         puntos_totales = len(completados_unicos)
                
                if n_activos > 0:
                    max_posibles = n_activos * total_retos_cuaresma
                    porcentaje = int((puntos_totales / max_posibles) * 100)
                else:
                    porcentaje = 0
                
                ranking_data.append({'Grupo': grupo, 'Porcentaje': min(porcentaje, 100), 'Activos': n_activos})
                
            df_rank = pd.DataFrame(ranking_data).sort_values('Porcentaje', ascending=False)
            
            for i, row in df_rank.iterrows():
                col1, col2 = st.columns([2, 3])
                with col1:
                    st.write(f"**{row['Grupo']}**")
                with col2:
                    st.progress(row['Porcentaje'] / 100)
                    st.caption(f"{row['Porcentaje']}% completado")
                st.write("---")

    # ==========================================
    # OPCIÓN 2: PANTALLA HISTORIAL
    # ==========================================
    elif menu == "📹 Historial":
        st.header("📜 Historial de Retos")
        
        historial = df_retos[df_retos['fecha'] <= hoy]
        
        usuarios_registrados = df_usuarios[
            df_usuarios['password'].astype(str).replace('nan', '').str.strip() != ""
        ]
        total_registrados = len(usuarios_registrados)

        if not historial.empty:
            historial = historial.sort_values(by='fecha', ascending=False)
            
            for index, reto in historial.iterrows():
                with st.container():
                    st.subheader(f"{reto['fecha']} - {reto['titulo']}")
                    
                    if 'grupo_proponente' in reto:
                        st.markdown(f"**Propuesto por:** {reto['grupo_proponente']}")
                    
                    st.video(f"https://youtu.be/{reto['youtube_id']}")
                    
                    participacion_pct = 0
                    num_hechos = 0
                    
                    if not df_progreso.empty and total_registrados > 0:
                        hechos = df_progreso[df_progreso['reto'] == reto['titulo']]
                        num_hechos = len(hechos['usuario'].unique())
                        
                        participacion_pct = int((num_hechos / total_registrados) * 100)
                    
                    st.write(f"📊 Participación global:")
                    st.progress(min(participacion_pct / 100, 1.0))
                    st.caption(f"**{participacion_pct}%** ({num_hechos} de {total_registrados} personas lo han completado)")
                    
                    st.divider()
        else:
            st.info("Aún no se han publicado retos.")