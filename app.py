import streamlit as st
import ezdxf
import io
import json

# =====================================================================
# CONFIGURACIÓN DE LA PÁGINA
# =====================================================================
st.set_page_config(
    page_title="AI Electric Pro - Generador Automatizado",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ AI Electric Pro")
st.subheader("Plataforma automatizada de diseño eléctrico asistida por IA")
st.write("Sube el plano de arquitectura en formato DXF para que el sistema identifique los recintos y diseñe el proyecto eléctrico.")

# =====================================================================
# BARRA LATERAL (CONFIGURACIÓN Y CARGA)
# =====================================================================
with st.sidebar:
    st.header("1. Configuración")
    # Selector de normativa (Pensando en el futuro escalable)
    normativa = st.selectbox(
        "Selecciona la Normativa Eléctrica",
        ["Norma SEC (Chile)", "NEC (Internacional)", "NOM-001 (México)"]
    )
    
    st.write("---")
    st.header("2. Archivo de Entrada")
    archivo_subido = st.file_uploader("Sube tu plano de arquitectura (.dxf)", type=["dxf"])

# =====================================================================
# PANEL CENTRAL (PROCESAMIENTO)
# =====================================================================
if archivo_subido is not None:
    st.success("¡Archivo cargado con éxito en la plataforma!")
    
    # Leer el archivo DXF desde la memoria de Streamlit sin guardarlo en disco
    bytes_data = archivo_subido.read()
    string_data = bytes_data.decode("utf-8", errors="ignore")
    
    try:
        doc = ezdxf.readstring(string_data)
        msp = doc.modelspace()
        
        # -------------------------------------------------------------
        # MÓDULO DE RECONOCIMIENTO: SCRAPPER DE PYTHON
        # -------------------------------------------------------------
        with st.spinner("Python ejecutando el Scrapper Geométrico..."):
            
            # Extraer textos (Habitaciones, notas)
            textos_raspados = []
            for t in msp.query('TEXT MTEXT'):
                if t.dxf.text.strip():
                    textos_raspados.append({
                        "texto": t.dxf.text.strip(),
                        "x": round(t.dxf.insert.x, 2),
                        "y": round(t.dxf.insert.y, 2),
                        "capa": t.dxf.layer
                    })
            
            # Extraer bloques (Artefactos, muebles, sanitarios)
            bloques_raspados = []
            for b in msp.query('INSERT'):
                bloques_raspados.append({
                    "nombre_bloque": b.dxf.name,
                    "x": round(b.dxf.insert.x, 2),
                    "y": round(b.dxf.insert.y, 2),
                    "capa": b.dxf.layer
                })
        
        # Crear el JSON estructurado para el Agente de IA
        datos_para_ia = {
            "archivo": archivo_subido.name,
            "total_textos_detectados": len(textos_raspados),
            "total_bloques_detectados": len(bloques_raspados),
            "datos_scrapper": {
                "textos": textos_raspados,
                "bloques": bloques_raspados
            }
        }

        # Opciones de visualización mediante Pestañas (Tabs)
        tab1, tab2, tab3 = st.tabs(["📊 Datos del Scrapper (Python)", "🧠 Cerebro del Agente (IA)", "💾 Descargar Resultado"])
        
        with tab1:
            st.write("### Datos extraídos por Python listos para enviar a la IA:")
            
            # Mostrar métricas rápidas
            col1, col2 = st.columns(2)
            col1.metric("Textos Encontrados", len(textos_raspados))
            col2.metric("Bloques/Muebles Encontrados", len(bloques_raspados))
            
            # Mostrar el JSON que leerá la IA
            st.json(datos_para_ia)
            
        with tab2:
            st.write("### Razonamiento y Clasificación del Agente de IA")
            st.info("Aquí el Agente de IA leerá el JSON anterior, cruzará las coordenadas de los textos con los bloques y clasificará las habitaciones de forma inteligente.")
            
            # Simulador del botón que llamará a la API de Inteligencia Artificial
            if st.button("Iniciar Detección y Diseño con IA"):
                with st.spinner("El Agente de IA está analizando los espacios y aplicando normativas..."):
                    
                    # Aquí irá tu llamada real a OpenAI/Anthropic pasando 'datos_para_ia'
                    # Por ahora simulamos la respuesta estructurada que te dará el agente:
                    simulacion_respuesta_ia = {
                        "clasificacion_recintos": [
                            {"id": 1, "tipo": "Dormitorio Principal", "ancla_texto": "Dorm. 1", "coordenadas_aprox": [10.5, 5.2]},
                            {"id": 2, "tipo": "Baño", "ancla_texto": "Baño", "coordenadas_aprox": [14.2, 3.1]}
                        ],
                        "propuesta_electrica": [
                            {"elemento": "Interruptor 9/12", "x": 10.6, "y": 5.0, "capa": "ELEC_INTERRUPTORES"},
                            {"elemento": "Centro de Luz LED", "x": 12.0, "y": 6.5, "capa": "ELEC_LUMINARIAS"},
                            {"elemento": "Enchufe Doble 10A", "x": 9.2, "y": 5.2, "capa": "ELEC_ENCHUFES"}
                        ]
                    }
                    
                    st.success("¡Análisis de IA Completado!")
                    st.write("#### Plan de diseño generado por el Agente:")
                    st.json(simulacion_respuesta_ia)
                    
                    # Guardamos la simulación en el estado de la app para habilitar el paso 3
                    st.session_state['proyecto_listo'] = True
                    
        with tab3:
            st.write("### Exportar Proyecto Eléctrico")
            if st.session_state.get('proyecto_listo', False):
                st.write("La IA ha insertado los nuevos elementos en las capas eléctricas correspondientes.")
                
                # Convertir el archivo DXF modificado a bytes para la descarga
                out_stream = io.StringIO()
                doc.write(out_stream)
                dxf_bytes = out_stream.getvalue().encode()
                
                st.download_button(
                    label="⬇️ Descargar Plano Eléctrico Final (.dxf)",
                    data=dxf_bytes,
                    file_name=f"ELEC_{archivo_subido.name}",
                    mime="application/dxf"
                )
            else:
                st.warning("Primero debes ejecutar el análisis del Agente de IA en la pestaña anterior.")

    except Exception as e:
        st.error(f"Error al procesar el archivo DXF: {e}")

else:
    st.info("👋 Por favor, sube un archivo DXF en la barra lateral para comenzar la demostración.")
