# Importaciones de sistema y para variables de entorno
import os
from dotenv import load_dotenv

# Importaciones de LangChain y Google Generative AI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentType, initialize_agent, Tool
from langchain_community.tools import DuckDuckGoSearchRun

# Importar las funciones 'request' y 'jsonify' de Flask
from flask import Flask, render_template, request, jsonify

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Crear una instancia de la aplicación Flask
app = Flask(__name__)

# --- CONFIGURACIÓN DEL AGENTE DE IA ---
# Inicializar el modelo de lenguaje (LLM) de Gemini.
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
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
# Inicializar el agente combinando el LLM y las herramientas
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True  # Muestra los "pensamientos" del agente en la terminal
)
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
    Este endpoint recibe la consulta del usuario, la pasa al agente de IA
    y devuelve la respuesta generada.
    """
    data = request.get_json()
    user_query = data.get('query')

    if not user_query:
        return jsonify({"error": "No se proporcionó ninguna consulta"}), 400

    # Imprimir la consulta para depuración
    print(f"Consulta recibida: {user_query}")

    # Invocar al agente con la consulta del usuario
    # El agente procesará la consulta, usará las herramientas si es necesario,
    # y generará una respuesta.
    response = agent.invoke({"input": user_query})

    # Extraer la respuesta del diccionario de salida del agente
    agent_response = response.get("output")

    # Devolver la respuesta del agente al frontend
    return jsonify({"response": agent_response})


# Esto permite ejecutar la aplicación directamente con 'python app.py'
if __name__ == '__main__':
    app.run(debug=True)
