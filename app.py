# Importaciones de sistema y para variables de entorno
import os
from dotenv import load_dotenv

# Importaciones de LangChain y Google Generative AI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from langchain.agents import Tool
from langchain_community.tools import DuckDuckGoSearchRun

# Importar las funciones 'request' y 'jsonify' de Flask
from flask import Flask, render_template, request, jsonify

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Crear una instancia de la aplicación Flask
app = Flask(__name__)

# --- CONFIGURACIÓN DEL AGENTE DE IA ---
# Cambiamos al modelo que especificaste:
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# --- CONFIGURACIÓN DE HERRAMIENTAS ---
# Inicializar la herramienta de búsqueda web
search = DuckDuckGoSearchRun()

tools = [
    Tool(
        name="Web Search",
        func=search.run,
        description="useful for when you need to answer questions about current events or the current state of the world",
    ),
]

# --- CREACIÓN DEL AGENTE ---

# 1. Definimos las nuevas instrucciones con un enfoque más amplio y proactivo.
system_message = """
Eres un asistente de investigación especializado en sociología y análisis de datos para Guadalajara, México.
Tu MISIÓN PRINCIPAL es encontrar y presentar DATOS ESTADÍSTICOS, MÉTRICAS CUANTIFICABLES, RESULTADOS DE INFORMES y EVALUACIONES de la MAYOR VARIEDAD DE FUENTES POSIBLE.

REGLAS ESTRICTAS:
- **Prioriza los datos duros**: Busca siempre porcentajes, cifras, índices (como el Gini), tasas de crecimiento, presupuestos, etc.
- **Cita TODAS las fuentes**: Menciona siempre la fuente de tus datos, sin importar cuál sea (portales de noticias, blogs de análisis, estudios académicos, informes gubernamentales, bases de datos, etc.). El usuario decidirá la validez de la fuente.
- **Amplía tu búsqueda**: No te limites a fuentes oficiales como INEGI o CONEVAL. Busca activamente en repositorios universitarios, artículos de investigación y bases de datos especializadas.
- **Evita resúmenes cualitativos**: No expliques los fenómenos en términos generales. En lugar de decir "la educación mejoró", di "la tasa de alfabetización pasó de X% a Y% según [fuente]".
- **Enfócate en el contexto**: Limita tus búsquedas y respuestas al contexto de Guadalajara y su área metropolitana para el rango de años especificado (1979-2025).
- **Si no encuentras datos en la web pública, sugiere otras posibles fuentes**: Menciona explícitamente que la información podría existir en bases de datos académicas de acceso restringido (como Scopus, Web of Science), archivos históricos no digitalizados o que podría obtenerse a través de solicitudes de transparencia gubernamentales.
"""

# 2. Jalar el prompt original desde el Hub
original_prompt = hub.pull("hwchase17/react")

# 3. Creamos una nueva plantilla de texto combinando nuestras instrucciones y la plantilla original
from langchain.prompts import PromptTemplate

# Extraemos el texto de la plantilla original
original_template = original_prompt.template

# Creamos la nueva plantilla completa
new_template = system_message + "\n\n" + original_template

# Creamos el objeto PromptTemplate final
prompt = PromptTemplate.from_template(new_template)


# 4. Crear el agente, uniendo el LLM, las herramientas y nuestro NUEVO prompt modificado.
agent = create_react_agent(llm, tools, prompt)

# 5. Crear el Ejecutor del Agente.
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
# ------------------------------------


# Definir la ruta principal (la raíz del sitio)
@app.route('/')
def index():
    """
    Esta función se ejecuta cuando alguien visita la página principal.
    Renderiza y devuelve el archivo 'index.html' de la carpeta 'templates'.
    """
    return render_template('index.html')

@app.route('/api/investigate', methods=['POST'])
def investigate():
    """
    Este endpoint ahora maneja posibles errores del agente de forma robusta.
    """
    data = request.get_json()
    user_query = data.get('query')

    if not user_query:
        return jsonify({"error": "No se proporcionó ninguna consulta"}), 400

    print(f"Consulta recibida: {user_query}")

    try:
        # Invocar al agente dentro de un bloque try/except
        response = agent_executor.invoke({"input": user_query})
        agent_response = response.get("output")
        return jsonify({"response": agent_response})
    
    except Exception as e:
        # Si algo sale mal con el agente, capturamos el error
        print(f"Error en la invocación del agente: {e}")
        # Y devolvemos un mensaje de error claro al frontend
        return jsonify({"error": f"Ocurrió un error al procesar la solicitud: {e}"}), 500


# Esto permite ejecutar la aplicación directamente con 'python app.py'
if __name__ == '__main__':
    app.run(debug=True)