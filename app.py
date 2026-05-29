import streamlit as st
import ezdxf
import io
import json
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List

# =====================================================================
# CONFIGURACIÓN DE LA PÁGINA E INTERFAZ
# =====================================================================
st.set_page_config(page_title="AI Electric Pro", page_icon="⚡", layout="wide")

st.title("⚡ AI Electric Pro")
st.subheader("Plataforma automatizada de diseño eléctrico asistida por IA")

# =====================================================================
# MODELOS DE DATOS PARA FORZAR LA RESPUESTA ESTRUCTURADA DE LA IA
# =====================================================================
class ElementoElectrico(BaseModel):
    elemento: str = Field(description="Tipo de elemento: 'LUMINARIA', 'ENCHUFE', 'INTERRUPTOR' o 'TABLERO'")
    x: float = Field(description="Coordenada X exacta para ubicar el elemento")
    y: float = Field(description="Coordenada Y exacta para ubicar el elemento")
    capa: str = Field(description="Nombre de la capa destino, ej: 'ELEC_LUMINARIAS', 'ELEC_ENCHUFES'")

class PropuestaProyecto(BaseModel):
    razonamiento_agente: str = Field(description="Breve justificación técnica del diseño propuesto")
    elementos_a_dibujar: List[ElementoElectrico]

# =====================================================================
# BARRA LATERAL: ENTRADAS Y LLAVES
# =====================================================================
with st.sidebar:
    st.header("1. Credenciales")
    api_key = st.text_input("Introduce tu OpenAI API Key", type="password")
    
    st.write("---")
    st.header("2. Configuración")
    normativa = st.selectbox("Normativa Eléctrica", ["Norma SEC (Chile)", "NEC (USA/Internacional)", "NOM-001 (México)"])
    
    st.write("---")
    st.header("3. Archivo de Entrada")
    archivo_subido = st.file_uploader("Sube tu plano de arquitectura (.dxf)", type=["dxf"])

# =====================================================================
# FLUJO PRINCIPAL DE LA APLICACIÓN
# =====================================================================
if archivo_subido is not None:
    if not api_key:
        st.warning("⚠️ Por favor, introduce tu OpenAI API Key en la barra lateral para activar el Agente de IA.")
        st.stop()
        
    st.success("¡Archivo de arquitectura cargado correctamente!")
    
    # Leer el DXF de la memoria
    bytes_data = archivo_subido.read()
    string_data = bytes_data.decode("utf-8", errors="ignore")
    
    try:
        doc = ezdxf.readstring(string_data)
        msp = doc.modelspace()
        
        # -------------------------------------------------------------
        # PASO 1: SCRAPPER GEOMÉTRICO (PYTHON)
        # -------------------------------------------------------------
        textos_raspados = []
        for t in msp.query('TEXT MTEXT'):
            if t.dxf.text.strip():
                textos_raspados.append({
                    "texto": t.dxf.text.strip(),
                    "x": round(t.dxf.insert.x, 2),
                    "y": round(t.dxf.insert.y, 2)
                })
                
        datos_para_ia = {
            "normativa_solicitada": normativa,
            "elementos_arquitectura": textos_raspados
        }
        
        tab1, tab2, tab3 = st.tabs(["📊 Scrapper (Python)", "🧠 Agente de IA", "💾 Descargar Plano"])
        
        with tab1:
            st.write("### Datos extraídos listos para enviar al Agente:")
            st.metric("Textos de referencia encontrados", len(textos_raspados))
            st.json(datos_para_ia)
            
        with tab2:
            st.write("### Análisis del Agente de IA en tiempo real")
            
            if st.button("🚀 Iniciar Diseño Inteligente"):
                with st.spinner("El Agente de IA está calculando la distribución eléctrica..."):
                    
                    # Conectar con la API de OpenAI usando el cliente oficial
                    client = OpenAI(api_key=api_key)
                    
                    prompt_sistema = (
                        "Eres un ingeniero eléctrico experto senior. Tu tarea es recibir las coordenadas de los textos "
                        "de un plano de arquitectura, identificar qué habitaciones existen y proponer la ubicación exacta (X, Y) "
                        "de las luminarias (idealmente en el centro o cerca del texto descriptivo), interruptores (cerca de los accesos) "
                        "y enchufes según la normativa seleccionada. Debes devolver estrictamente el formato estructurado solicitado."
                    )
                    
                    # Llamada al modelo con Structured Outputs (Garantiza respuesta JSON perfecta)
                    completion = client.beta.chat.completions.parse(
                        model="gpt-4o-mini", # Usamos mini por coste y velocidad, puedes cambiar a gpt-4o
                        messages=[
                            {"role": "system", "content": prompt_sistema},
                            {"role": "user", "content": json.dumps(datos_para_ia)}
                        ],
                        response_format=PropuestaProyecto,
                    )
                    
                    respuesta_ia = completion.choices[0].message.parsed
                    
                    # Guardar la respuesta en el estado global de la sesión
                    st.session_state['respuesta_ia'] = respuesta_ia
                    st.success("¡El Agente de IA ha terminado el diseño!")
                    
            # Si el análisis ya se ejecutó, mostrar los resultados
            if 'respuesta_ia' in st.session_state:
                res = st.session_state['respuesta_ia']
                st.info(f"**Justificación técnica del Agente:** {res.razonamiento_agente}")
                st.write("#### Elementos Eléctricos Propuestos:")
                st.write(res.elementos_a_dibujar)
                
        with tab3:
            st.write("### Inyección geométrica y descarga")
            if 'respuesta_ia' in st.session_state:
                res = st.session_state['respuesta_ia']
                
                # -------------------------------------------------------------
                # PASO 3: DIBUJAR DE VUELTA EN EL DXF (PYTHON)
                # -------------------------------------------------------------
                # Recorrer lo que dictaminó la IA y dibujarlo físicamente en el plano original
                for item in res.elementos_a_dibujar:
                    if item.elemento == "LUMINARIA":
                        # Dibuja un círculo amarillo para la lámpara
                        msp.add_circle(center=(item.x, item.y), radius=0.15, dxfattribs={'layer': item.capa, 'color': 2})
                    elif item.elemento == "ENCHUFE":
                        # Dibuja un pequeño cuadrado para el enchufe
                        msp.add_lwpolyline([(item.x-0.1, item.y-0.1), (item.x+0.1, item.y-0.1), (item.x+0.1, item.y+0.1), (item.x-0.1, item.y+0.1)], close=True, dxfattribs={'layer': item.capa, 'color': 4})
                    else:
                        # Puntos genéricos para otros elementos
                        msp.add_point(location=(item.x, item.y), dxfattribs={'layer': item.capa, 'color': 1})
                
                # Preparar el archivo modificado para la descarga
                out_stream = io.StringIO()
                doc.write(out_stream)
                dxf_bytes = out_stream.getvalue().encode()
                
                st.download_button(
                    label="⬇️ Descargar Plano Eléctrico Terminado (.dxf)",
                    data=dxf_bytes,
                    file_name=f"PROYECTO_ELEC_{archivo_subido.name}",
                    mime="application/dxf"
                )
            else:
                st.warning("Debes ejecutar el diseño del Agente de IA en la pestaña anterior para generar el archivo.")
                
    except Exception as e:
        st.error(f"Error crítico en el procesamiento: {e}")
else:
    st.info("👋 Sube un archivo DXF en la barra lateral e ingresa tu API Key para ver la magia en acción.")
