# Importaciones de sistema y para variables de entorno
import os
import requests
from dotenv import load_dotenv

# Importaciones de LangChain y Google Generative AI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from langchain.agents import Tool
from langchain.prompts import PromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun # <-- Re-incorporamos la búsqueda general

# Importar las funciones 'request' y 'jsonify' de Flask
from flask import Flask, render_template, request, jsonify

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Crear una instancia de la aplicación Flask
app = Flask(__name__)

# --- FUNCIONES PARA LAS HERRAMIENTAS ---
def search_academic_database(query: str) -> str:
    """
    Busca en la base de datos de CORE (Connecting Repositories) artículos de investigación
    relevantes para la consulta y devuelve los títulos y resúmenes.
    Es útil para encontrar estudios específicos, datos y análisis académicos.
    """
    try:
        api_url = f"https://api.core.ac.uk/v3/search/works?q={query}&limit=5"
        response = requests.get(api_url)
        response.raise_for_status()
        results = response.json().get("results", [])
        if not results:
            return "No se encontraron artículos académicos sobre este tema en la base de datos de CORE."
        output = "Se encontraron los siguientes artículos académicos:\n"
        for item in results:
            title = item.get("title", "Título no disponible")
            abstract = item.get("abstract", "Resumen no disponible")[:500] + "..." # Acortamos el resumen
            output += f"- Título: {title}\n  Resumen: {abstract}\n\n"
        return output
    except Exception as e:
        return f"Ocurrió un error al contactar la API académica: {e}"

# --- CONFIGURACIÓN DEL AGENTE DE IA ---
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-latest",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# --- CONFIGURACIÓN DE HERRAMIENTAS ---
# Le damos al agente un arsenal de herramientas para máxima flexibilidad
web_search = DuckDuckGoSearchRun()
tools = [
    Tool(
        name="General Web Search",
        func=web_search.run,
        description="Úsalo para una búsqueda amplia en toda la web sobre cualquier tema. Es bueno para obtener un panorama general, encontrar noticias, y buscar información en fuentes no académicas.",
    ),
    Tool(
        name="Academic Database Search",
        func=search_academic_database,
        description="Úsalo DESPUÉS de la búsqueda general si necesitas encontrar estudios específicos, métricas, datos cuantitativos o informes en artículos de investigación y papers académicos.",
    )
]

# --- CREACIÓN DEL AGENTE ---
# Mantenemos el prompt más avanzado que le enseña a razonar.
system_message = """
## TU IDENTIDAD Y MISIÓN ##
Eres un analista de datos sociales experto en México, con un enfoque en Guadalajara. Tu misión es procesar las solicitudes del usuario para encontrar y presentar datos cuantitativos y verificables de múltiples fuentes.

## REGLA DE ORO ##
**RESPONDE SIEMPRE Y ÚNICAMENTE EN ESPAÑOL.**

## PROCESO DE RAZONAMIENTO OBLIGATORIO ##
1.  **Interpreta la Solicitud**: No seas literal. Identifica las entidades clave (lugar, fenómeno, rango de fechas).
2.  **Expande el Rango y los Términos**: Un rango como "1990-2010" significa que CUALQUIER dato dentro de ese intervalo es valioso. Un estudio de 1995 o un censo de 2000 son resultados correctos. Expande "desigualdad" a "coeficiente de Gini", "distribución del ingreso", "pobreza", etc.
3.  **Usa tus Herramientas Estratégicamente**: Comienza con "General Web Search" para tener una visión amplia. Si encuentras pistas de estudios o informes, usa "Academic Database Search" para intentar localizarlos.
4.  **Sintetiza, No te Rindas**: Tu deber es **sintetizar los datos que sí encuentres** dentro del rango. No digas "no encontré", en su lugar, reporta los datos parciales que sí localizaste.
5.  **Cita Todas las Fuentes**: Siempre menciona de dónde obtuviste cada dato.
6.  **Sugiere Vías Alternativas**: Si después de usar todas tus herramientas no encuentras datos numéricos, concluye sugiriendo que la información puede existir en bases de datos de suscripción (Scopus), archivos físicos o vía solicitudes de transparencia.
"""

original_prompt = hub.pull("hwchase17/react")
original_template = original_prompt.template
new_template = system_message + "\n\n" + original_template
prompt = PromptTemplate.from_template(new_template)

agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True) # Añadimos manejo de errores

# --- RUTAS DE LA APLICACIÓN ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/investigate', methods=['POST'])
def investigate():
    data = request.get_json()
    user_query = data.get('query')
    if not user_query:
        return jsonify({"error": "No se proporcionó ninguna consulta"}), 400
    try:
        response = agent_executor.invoke({"input": user_query})
        agent_response = response.get("output")
        return jsonify({"response": agent_response})
    except Exception as e:
        print(f"Error en la invocación del agente: {e}")
        return jsonify({"error": f"Ocurrió un error al procesar la solicitud: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)