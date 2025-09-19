# Importar las funciones 'request' y 'jsonify' de Flask
from flask import Flask, render_template, request, jsonify

# Crear una instancia de la aplicación Flask
app = Flask(__name__)

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
    # Usamos .get() para evitar errores si la clave no existe
    user_query = data.get('query')

    # Por ahora, simplemente imprimimos la consulta en la consola del servidor
    # para verificar que la estamos recibiendo correctamente.
    print(f"Consulta recibida: {user_query}")

    # Devolvemos una respuesta JSON confirmando la consulta recibida
    return jsonify({"status": "recibido", "query_recibida": user_query})

# Esto permite ejecutar la aplicación directamente con 'python app.py'
if __name__ == '__main__':
    app.run(debug=True)