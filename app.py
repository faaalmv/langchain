
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

# Definir la lista de herramientas que el agente podrá usar
# Cada herramienta tiene un nombre y una descripción que el agente usa para decidir cuál elegir
tools = [
    Tool(
        name="Web Search",
        func=search.run,
        description="useful for when you need to answer questions about current events or the current state of the world",
    ),
]
# ------------------------------------

# Definir la ruta principal (la raíz del sitio)
@app.route('/')
def index():
    """
    Esta función se ejecuta cuando alguien visita la página principal.
    Renderiza y devuelve el archivo 'index.html' de la carpeta 'templates'.
    """
    return render_template('index.html')

# Definir la ruta para la API de investigación
@app.route('/api/investigate', methods=['POST'])
def investigate():
    """
    Este endpoint ahora lee el JSON de la petición,
    extrae la consulta del usuario y la imprime en la terminal.
    """
    # Obtener los datos JSON enviados en la petición
    data = request.get_json()

    # Extraer el valor asociado a la clave 'query'
    user_query = data.get('query')

    # Por ahora, simplemente imprimimos la consulta en la consola del servidor
    print(f"Consulta recibida: {user_query}")

    # Devolvemos una respuesta JSON confirmando la consulta recibida
    return jsonify({"status": "recibido", "query_recibida": user_query})

# Esto permite ejecutar la aplicación directamente con 'python app.py'
if __name__ == '__main__':
    app.run(debug=True)
