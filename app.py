# Importaciones de sistema y para variables de entorno
import os
import requests # Asegúrate que esta importación esté al principio
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

# --- FUNCIÓN PARA LA NUEVA HERRAMIENTA ACADÉMICA ---
def search_academic_database(query: str) -> str:
    """
    Busca en la base de datos de CORE (Connecting Repositories) artículos de investigación
    relevantes para la consulta y devuelve los títulos y resúmenes.
    Es útil para encontrar estudios específicos, datos y análisis académicos.
    """
    try:
        # Puedes obtener una API key gratuita en https://core.ac.uk/api-keys/register
        # Por ahora, usaremos una búsqueda sin key que es más limitada.
        api_url = f"https://api.core.ac.uk/v3/search/works?q={query}&limit=5"
        response = requests.get(api_url)
        response.raise_for_status()  # Lanza un error si la petición falla
        
        results = response.json().get("results", [])
        
        if not results:
            return "No se encontraron artículos académicos sobre este tema en la base de datos de CORE."

        output = "Se encontraron los siguientes artículos académicos:\n"
        for item in results:
            title = item.get("title", "Título no disponible")
            abstract = item.get("abstract", "Resumen no disponible")
            output += f"- Título: {title}\n  Resumen: {abstract}\n\n"
        
        return output

    except requests.RequestException as e:
        return f"Error al contactar la API académica: {e}"
    except Exception as e:
        return f"Ocurrió un error inesperado al procesar la búsqueda académica: {e}"

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
        description="Útil para búsquedas generales, noticias y temas de actualidad. Úsalo primero para tener un panorama general.",
    ),
    Tool(
        name="Academic Database Search",
        func=search_academic_database,
        description="Útil para encontrar datos específicos, métricas, estudios, informes y análisis cuantitativos en artículos de investigación y papers académicos. Úsalo cuando la búsqueda web general no arroje resultados estadísticos.",
    )
]

# --- CREACIÓN DEL AGENTE ---

# 1. Definimos las nuevas instrucciones con un enfoque en el razonamiento y el criterio.
system_message = """
## TU IDENTIDAD Y MISIÓN ##
Eres un analista de datos sociales experto en México, con un enfoque en Guadalajara. Tu misión es procesar las solicitudes del usuario para encontrar y presentar datos cuantitativos y verificables de múltiples fuentes.

## REGLA DE ORO ##
**RESPONDE SIEMPRE Y ÚNICAMENTE EN ESPAÑOL.**

## PROCESO DE RAZONAMIENTO OBLIGATORIO ##
Antes de usar cualquier herramienta, debes seguir estos pasos mentales:

1.  **Interpreta la Solicitud del Usuario**: No tomes la pregunta de forma literal. Identifica las entidades clave (ej. lugar: Guadalajara, fenómeno: desigualdad, rango de fechas: 1990 a 2010).
2.  **Expande el Rango y los Términos**:
    * **Fechas**: Un rango como "1990-2010" significa que CUALQUIER dato dentro de ese intervalo es valioso. Un estudio de 1995, un censo de 2000 o un informe de 2008 son todos resultados correctos y útiles.
    * **Términos**: Si te piden "desigualdad", tu mente debe expandir eso a buscar "coeficiente de Gini", "distribución del ingreso", "brecha salarial", "índice de desarrollo humano", "niveles de pobreza", etc.
3.  **Planifica tu Búsqueda**: Formula una estrategia de búsqueda que utilice estos términos expandidos. Empieza de forma general y luego profundiza.

## REGLAS DE EJECUCIÓN ##
- **Prioriza Datos Cuantitativos**: Tu objetivo son las cifras, porcentajes, estadísticas, etc.
- **Sintetiza, No te Rindas**: Si no encuentras un único informe que cubra todo el rango de fechas, tu deber es **sintetizar los datos que sí encuentres**. Por ejemplo: "No encontré un informe único para 1990-2010, pero un estudio de la UdeG de 1998 reportó que el Gini era de 0.45, y datos del INEGI del censo de 2010 lo sitúan en 0.48".
- **Cita Todas las Fuentes**: Siempre menciona de dónde obtuviste cada dato.
- **Sugiere Vías Alternativas**: Si la web pública no arroja resultados, menciona (como ya lo haces) que la información puede existir en bases de datos académicas de suscripción (Scopus, etc.), archivos físicos o vía solicitudes de transparencia.
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